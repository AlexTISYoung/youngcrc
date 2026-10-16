"""Behavioral checks for selective downloads and offline integrity verification."""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "case_data.py"
SPEC = importlib.util.spec_from_file_location("case_data", SCRIPT)
case_data = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(case_data)


def metadata(content=b"released data"):
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def manifest(content=b"released data"):
    return {
        "schema_version": "1.1", "release": "test",
        "files": [{"path": "data/clinical.json", **metadata(content)}],
        "external_files": [{
            "release_file_id": "M-RAW-001", "filename": "reads.bam",
            "download_url": "https://example.org/releases/reads.bam",
            "availability": "verified_public_download", **metadata(content),
        }],
    }


class Response(io.BytesIO):
    status = 200
    headers = {}


class ManifestTests(unittest.TestCase):
    def test_distinguishes_bundled_paths_from_declared_external_urls(self):
        files = case_data.manifest_files(manifest())
        self.assertEqual(files[0]["download_url"], "https://youngcrc.com/data/clinical.json")
        self.assertEqual(files[0]["storage"], "bundled")
        self.assertEqual(files[1]["download_url"], "https://example.org/releases/reads.bam")
        self.assertEqual(files[1]["storage"], "external")
        self.assertEqual(case_data.select_file(files, "M-RAW-001"), files[1])
        self.assertEqual(case_data.select_file(files, "data/clinical.json"), files[0])
        with self.assertRaisesRegex(case_data.CaseDataError, "exact path"):
            case_data.select_file(files, "clinical.json")

    def test_never_guesses_a_pending_file_url(self):
        data = manifest()
        data["external_files"][0].update(availability="pending", download_url=None)
        files = case_data.manifest_files(data)
        self.assertIsNone(files[1]["download_url"])
        with self.assertRaisesRegex(case_data.CaseDataError, "not declared"):
            case_data.select_file(files, "M-RAW-001")

    def test_rejects_ambiguous_selector_and_duplicate_ids(self):
        data = manifest()
        data["files"][0]["path"] = "reads.bam"
        with self.assertRaisesRegex(case_data.CaseDataError, "Ambiguous"):
            case_data.select_file(case_data.manifest_files(data), "reads.bam")
        data["external_files"].append({**data["external_files"][0], "filename": "another.bam"})
        with self.assertRaisesRegex(case_data.CaseDataError, "duplicate release_file_id"):
            case_data.manifest_files(data)

    def test_rejects_malformed_data(self):
        cases = [{}, {"files": {}}, {"files": [], "external_files": {}},
                 {"files": [{"path": "a", "bytes": True, "sha256": "f" * 64}]},
                 {"files": [{"path": "a", "release_file_id": [], **metadata()}]},
                 {"files": [{"path": "a", "bytes": 0, "sha256": "bad"}]}]
        for data in cases:
            with self.subTest(data=data), self.assertRaises(case_data.CaseDataError):
                case_data.manifest_files(data)

    def test_rejects_path_traversal_and_unsafe_urls(self):
        for value in ("../secret", "/etc/passwd", "data/../../secret", "data\\secret",
                      "data/%2e%2e/secret", "data/%252e%252e/secret", "a//b", "C:/secret"):
            with self.subTest(value=value), self.assertRaises(case_data.CaseDataError):
                case_data.safe_path(value)
        for value in ("http://example.org/a", "file:///etc/passwd", "https://user:pass@example.org/a",
                      "https://localhost/a", "https://127.0.0.1/a", "https://[::1]/a",
                      "https://127.1/a", "https://0x7f.0.0.1/a", "https://example.org:8443/a",
                      "https://example.org/../secret", "https://example.org/%252e%252e/secret"):
            with self.subTest(value=value), self.assertRaises(case_data.CaseDataError):
                case_data.safe_https_url(value)

    def test_offline_list_json_does_not_open_network(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "manifest.json"
            source.write_text(json.dumps(manifest()))
            output = io.StringIO()
            with patch.object(case_data, "open_url") as request, contextlib.redirect_stdout(output):
                result = case_data.main(["--manifest", str(source), "list", "--storage", "external", "--json"])
            self.assertEqual(result, 0)
            request.assert_not_called()
            data = json.loads(output.getvalue())
            self.assertEqual(data["file_count"], 1)
            self.assertEqual(data["files"][0]["release_file_id"], "M-RAW-001")


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.content = b"verified public bytes\n" * 100
        self.entry = case_data.manifest_files(manifest(self.content))[1]
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "data.bam"

    def download(self, content=None, max_bytes=100_000):
        with patch.object(case_data, "open_url", return_value=Response(self.content if content is None else content)):
            return case_data.fetch_file(self.entry, self.output, max_bytes)

    def test_streams_and_publishes_only_verified_bytes(self):
        result = self.download()
        self.assertTrue(result["ok"])
        self.assertEqual(self.output.read_bytes(), self.content)
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_checksum_failure_leaves_no_output_or_temporary_file(self):
        with self.assertRaisesRegex(case_data.CaseDataError, "SHA-256 mismatch"):
            self.download(b"x" * len(self.content))
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.output.parent.iterdir()), [])

    def test_byte_mismatch_and_oversized_stream_leave_no_output(self):
        for content in (self.content[:-1], self.content + b"x"):
            with self.subTest(size=len(content)), self.assertRaises(case_data.CaseDataError):
                self.download(content)
            self.assertFalse(self.output.exists())
            self.assertEqual(list(self.output.parent.iterdir()), [])

    def test_preflight_cap_and_existing_output_make_no_request(self):
        with patch.object(case_data, "open_url") as request:
            with self.assertRaisesRegex(case_data.CaseDataError, "exceeds --max-bytes"):
                case_data.fetch_file(self.entry, self.output, 1)
            self.output.write_bytes(b"keep this")
            with self.assertRaisesRegex(case_data.CaseDataError, "already exists"):
                case_data.fetch_file(self.entry, self.output, 100_000)
            request.assert_not_called()
        self.assertEqual(self.output.read_bytes(), b"keep this")

    def test_output_created_during_download_is_never_overwritten(self):
        def open_and_race(url):
            self.output.write_bytes(b"created by another process")
            return Response(self.content)
        with patch.object(case_data, "open_url", side_effect=open_and_race):
            with self.assertRaisesRegex(case_data.CaseDataError, "already exists"):
                case_data.fetch_file(self.entry, self.output, 100_000)
        self.assertEqual(self.output.read_bytes(), b"created by another process")
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_redirect_cannot_downgrade_https_or_change_origin(self):
        request = case_data.Request("https://example.org/data")
        handler = case_data.SafeRedirectHandler()
        for url in ("http://example.org/data", "https://other.example/data"):
            with self.subTest(url=url), self.assertRaises(case_data.CaseDataError):
                handler.redirect_request(request, None, 302, "Found", {}, url)


class SnapshotTests(unittest.TestCase):
    def test_verifies_content_and_reports_changed_or_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "data.json"
            path.write_bytes(b"original")
            snapshot = {"files": [{"path": "data.json", **metadata(b"original")}]} 
            self.assertTrue(case_data.verify_snapshot(snapshot, root)["ok"])
            path.write_bytes(b"modified")
            result = case_data.verify_snapshot(snapshot, root)
            self.assertFalse(result["ok"])
            self.assertEqual(result["failures"][0]["error"], "SHA-256 mismatch")
            path.unlink()
            self.assertEqual(case_data.verify_snapshot(snapshot, root)["failures"][0]["error"], "missing file")

    def test_accepts_path_mapping_and_rejects_traversal_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data.json").write_bytes(b"safe")
            self.assertTrue(case_data.verify_snapshot({"files": {"data.json": metadata(b"safe")}}, root)["ok"])
            for path in ("../secret", "/etc/passwd"):
                with self.subTest(path=path), self.assertRaises(case_data.CaseDataError):
                    case_data.verify_snapshot({"files": [{"path": path, **metadata()}]}, root)
            (root / "link.json").symlink_to(root / "data.json")
            with self.assertRaisesRegex(case_data.CaseDataError, "symlinks"):
                case_data.verify_snapshot({"files": [{"path": "link.json", **metadata(b"safe")}]}, root)

    def test_rejects_malformed_snapshot_entries_instead_of_skipping_them(self):
        with self.assertRaisesRegex(case_data.CaseDataError, "must map"):
            case_data.verify_snapshot({"files": {"data.json": metadata(), "missing.json": None}})


if __name__ == "__main__":
    unittest.main()
