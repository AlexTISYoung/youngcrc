"""Checks for publication boundaries and reproducible release packaging."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release_tool as release
import prepare_raw


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "project"
        self.root.mkdir()
        (self.root / "site").mkdir()
        (self.root / "data").mkdir()
        (self.root / "site/index.html").write_text("<!doctype html><p>Public case</p>")
        (self.root / "data/example.json").write_text('{"value": 1}')
        self.policy = self.base / "policy.json"
        self.policy.write_text(json.dumps({"version": 1, "rules": [{"pattern": "BLOCKED_[A-Z]+"}]}))
        self.allowlist = self.base / "allowlist.json"
        self.doc = {"version": 1, "scan_roots": ["site", "data"], "entries": [
            {"source": "site/index.html", "destination": "index.html"},
            {"source": "data/example.json", "destination": "data/example.json"}]}
        self.save_allowlist()

    def tearDown(self):
        self.temp.cleanup()

    def save_allowlist(self):
        self.allowlist.write_text(json.dumps(self.doc))

    def build(self, execute=False, output="build"):
        return release.create_export(self.root, self.allowlist, self.policy,
                                     self.base / output, "v1-test", execute)

    def test_default_dry_run_does_not_write(self):
        report = self.build()
        self.assertEqual(report["status"], "passed")
        self.assertFalse(report["executed"])
        self.assertFalse((self.base / "build").exists())

    def test_archive_manifest_and_checksum_are_complete(self):
        self.assertEqual(self.build(True)["status"], "passed")
        built = self.base / "build"
        manifest = json.loads((built / "manifest.json").read_text())
        for row in manifest["files"]:
            contents = (built / row["path"]).read_bytes()
            self.assertEqual(len(contents), row["bytes"])
            self.assertEqual(hashlib.sha256(contents).hexdigest(), row["sha256"])
        checked = set()
        for line in (built / "checksums.sha256").read_text().splitlines():
            digest, rel = line.split("  ", 1)
            checked.add(rel)
            self.assertEqual(digest, hashlib.sha256((built / rel).read_bytes()).hexdigest())
        expected = {p.relative_to(built).as_posix() for p in built.rglob("*") if p.is_file()}
        self.assertEqual(checked, expected - {"checksums.sha256"})
        with zipfile.ZipFile(built / "downloads/source.zip") as archive:
            self.assertEqual(set(archive.namelist()), {"site/index.html", "data/example.json"})
        with zipfile.ZipFile(built / "downloads/curated-data.zip") as archive:
            self.assertEqual(archive.namelist(), ["data/example.json"])

    def test_build_is_reproducible(self):
        self.build(True, "one")
        self.build(True, "two")
        for path in (self.base / "one").rglob("*"):
            if path.is_file():
                self.assertEqual(path.read_bytes(), (self.base / "two" / path.relative_to(self.base / "one")).read_bytes())

    @staticmethod
    def external_wsi_record():
        return {
            "release_file_id": "IHC-WSI-003", "source_file_id": "IHC-SOURCE-003",
            "assay_id": "IHC-ASSAY-001", "sample_ids": ["IHC-SAMPLE-001"],
            "filename": "cea_reviewed.svs", "format": "SVS", "reference_build": None,
            "bytes": 123456789, "sha256": "a" * 64,
            "download_url": "https://example.invalid/pathology/cea_reviewed.svs",
            "storage": "external", "availability": "verified_public_download",
            "included_in_release": True, "public_read_without_credentials": True,
            "companion_file_id": None, "verified_at": "2026-10-07T12:00:00Z",
        }

    def add_pathology_catalogue(self, row):
        rel = "data/pathology_release_catalog.json"
        (self.root / rel).write_text(json.dumps({"records": [row]}))
        self.doc["entries"].append({"source": rel, "destination": rel})
        self.save_allowlist()

    def test_verified_wsi_is_referenced_with_checksum_but_not_bundled(self):
        row = self.external_wsi_record()
        self.add_pathology_catalogue(row)
        self.assertEqual(self.build(True)["status"], "passed")
        built = self.base / "build"
        manifest = json.loads((built / "manifest.json").read_text())
        self.assertEqual(len(manifest["external_files"]), 1)
        external = manifest["external_files"][0]
        for key in ("release_file_id", "source_file_id", "assay_id", "sample_ids",
                    "filename", "format", "reference_build", "bytes", "sha256",
                    "download_url", "storage", "availability", "companion_file_id", "verified_at"):
            self.assertEqual(external[key], row[key])
        self.assertEqual((built / "external-checksums.sha256").read_text(),
                         row["sha256"] + "  " + row["filename"] + "\n")
        self.assertFalse(any(p.name == row["filename"] for p in built.rglob("*")))
        for archive_path in ("downloads/source.zip", "downloads/curated-data.zip"):
            with zipfile.ZipFile(built / archive_path) as archive:
                self.assertFalse(any(name.endswith(".svs") for name in archive.namelist()))

    def test_existing_external_identifier_formats_remain_accepted(self):
        for identifier, catalogue in (
                ("M-RAW-001", "data/molecular/raw_release_catalog.json"),
                ("M-RELEASE-001", "data/molecular/processed_release_catalog.json"),
                ("I-RAW-001", "data/imaging_release_catalog.json")):
            with self.subTest(identifier=identifier):
                row = dict(self.external_wsi_record(), release_file_id=identifier)
                result = release.external_files_from_outputs({
                    catalogue: json.dumps({"records": [row]}).encode()})
                self.assertEqual(result[0]["release_file_id"], identifier)

    def test_unverified_or_invalid_wsi_metadata_is_rejected(self):
        invalid_fields = (
            ("availability", "pending_verification"), ("included_in_release", False),
            ("public_read_without_credentials", False), ("storage", "local"),
            ("release_file_id", "IHC-WSI-3"), ("release_file_id", "IHC-WSI-0003"),
            ("release_file_id", "IHC-OTHER-003"), ("bytes", 0), ("bytes", True),
            ("sha256", "not-a-sha256"), ("filename", "../cea.svs"),
            ("download_url", "https://example.invalid/cea.svs?token=secret"),
            ("download_url", "https://user:password@example.invalid/cea.svs"),
        )
        for key, value in invalid_fields:
            with self.subTest(field=key, value=value), self.assertRaises(release.ReleaseError):
                row = dict(self.external_wsi_record(), **{key: value})
                release.external_files_from_outputs({
                    "data/pathology_release_catalog.json": json.dumps({"records": [row]}).encode()})

    def test_unverified_wsi_prevents_export_writes(self):
        self.add_pathology_catalogue(dict(self.external_wsi_record(),
                                         public_read_without_credentials=False))
        with self.assertRaises(release.ReleaseError):
            self.build(True)
        self.assertFalse((self.base / "build").exists())

    def test_pathology_duplicates_across_external_catalogues_are_rejected(self):
        row = self.external_wsi_record()
        other = dict(row, release_file_id="I-RAW-001")
        with self.assertRaisesRegex(release.ReleaseError, "Duplicate"):
            release.external_files_from_outputs({
                "data/pathology_release_catalog.json": json.dumps({"records": [row]}).encode(),
                "data/imaging_release_catalog.json": json.dumps({"records": [other]}).encode(),
            })

    def test_unreviewed_file_fails_closed(self):
        (self.root / "data/unreviewed.txt").write_text("Unknown")
        with self.assertRaises(release.ReleaseError):
            self.build(True)
        self.assertFalse((self.base / "build").exists())

    def test_policy_failure_never_echoes_matched_value(self):
        (self.root / "site/index.html").write_text("BLOCKED_SENTINEL")
        report = self.build(True)
        self.assertEqual(report["status"], "blocked")
        self.assertNotIn("BLOCKED_SENTINEL", json.dumps(report))
        self.assertFalse((self.base / "build").exists())

    def test_empty_library_key_placeholder_is_not_a_credential(self):
        (self.root / "site/index.html").write_text('<script>const endpoint="https://example.invalid/?api_key=";</script>')
        self.assertEqual(self.build()["status"], "passed")
        for key in ('api_key', 'access_token', 'X-Amz-' + 'Signature'):
            value = '?' + key + '=' + ('' if key.startswith('X-Amz-') else 'test-sentinel')
            with self.subTest(value=value):
                (self.root / "site/index.html").write_text(value)
                self.assertEqual(self.build()["status"], "blocked")

    def test_json_unicode_escape_is_scanned(self):
        value = "BLOCKED_SENTINEL"
        escaped = "".join("\\u" + format(ord(char), "04x") for char in value)
        (self.root / "data/example.json").write_text('{"value":"' + escaped + '"}')
        self.assertEqual(self.build()["status"], "blocked")

    def test_paths_and_symlinks_are_rejected(self):
        for value in ("../escape", "/absolute", "a/../b", "a\\b", ".git/config"):
            with self.subTest(value=value), self.assertRaises(release.ReleaseError):
                release.relative_path(value)
        (self.root / "data/example.json").unlink()
        (self.root / "data/example.json").symlink_to(self.policy)
        with self.assertRaises(release.ReleaseError):
            self.build()

    def test_existing_output_is_not_overwritten(self):
        self.build(True)
        with self.assertRaises(release.ReleaseError):
            self.build(True)

    def test_policy_cannot_enter_public_tree(self):
        policy = self.root / "policy.json"
        policy.write_bytes(self.policy.read_bytes())
        with self.assertRaises(release.ReleaseError):
            release.load_policy(policy, self.root)

    def test_opaque_binary_file_is_rejected(self):
        (self.root / "data/example.json").write_bytes(b"\x00\x01")
        with self.assertRaises(release.ReleaseError):
            self.build()

    def test_local_path_detection(self):
        text = "/" + "Users" + "/example/record.txt"
        (self.root / "site/index.html").write_text(text)
        self.assertEqual(self.build()["status"], "blocked")

    def test_gzip_content_and_archive_are_scanned(self):
        rel = "data/calls.vcf.gz"
        path = self.root / rel
        self.doc["entries"].append({"source": rel, "destination": rel})
        self.save_allowlist()
        path.write_bytes(gzip.compress(b"##fileformat=VCFv4.2\n", mtime=0))
        self.assertEqual(self.build()["status"], "passed")
        path.write_bytes(gzip.compress(b"BLOCKED_SENTINEL", mtime=0))
        self.assertEqual(self.build()["status"], "blocked")

    def test_gzip_embedded_filename_is_rejected(self):
        buffer = io.BytesIO()
        with gzip.GzipFile(fileobj=buffer, mode="wb", filename="unreviewed-name") as handle:
            handle.write(b"safe body")
        with self.assertRaises(release.ReleaseError):
            release.decode_payload(buffer.getvalue(), "data/test.txt.gz")

    def test_raw_default_never_reads_contents_or_hashes(self):
        source = self.base / "input.bam"
        source.write_bytes(b"not actually a BAM")
        jobs = {"version": 1, "jobs": [{"id": "job1", "sample_id": "sample1", "assay_id": "assay1",
                "source": str(source), "public_path": "raw/example.bam", "kind": "bam"}]}
        with patch.object(prepare_raw, "inspect_header", side_effect=AssertionError("must not read")):
            report = prepare_raw.plan_jobs(jobs, self.root, self.policy, self.base)
        self.assertEqual(report["raw_files_prepared"], 0)
        self.assertIsNone(report["jobs"][0]["sha256"])
        self.assertNotIn(str(source), json.dumps(report))
        self.assertEqual(source.read_bytes(), b"not actually a BAM")

    def test_nonresident_input_is_not_opened(self):
        jobs = {"version": 1, "jobs": [{"id": "job1", "sample_id": "sample1", "assay_id": "assay1",
                "source": str(self.base / "input.bam"), "public_path": "raw/example.bam", "kind": "bam"}]}
        with patch.object(prepare_raw, "file_state", return_value={"state": "nonresident", "bytes": 100}), \
             patch.object(prepare_raw, "inspect_header", side_effect=AssertionError("must not read")):
            report = prepare_raw.plan_jobs(jobs, self.root, self.policy, self.base, read_headers=True)
        self.assertEqual(report["jobs"][0]["header_inspection"]["status"], "not_read")

    def test_raw_header_findings_omit_content(self):
        source = self.base / "calls.vcf"
        source.write_text("##fileformat=VCFv4.2\n##comment=BLOCKED_SENTINEL\n#CHROM\tPOS\n")
        rules = release.load_policy(self.policy, self.root)
        report = prepare_raw.inspect_header(source, "vcf", rules)
        self.assertTrue(report["findings"])
        self.assertNotIn("BLOCKED_SENTINEL", json.dumps(report))

    def reviewed_document(self):
        rel = "reports/laboratory/reviewed.pdf"
        content = b"%PDF-1.7\nreviewed fixture\n%%EOF\n"
        target = self.root / rel
        target.parent.mkdir(parents=True)
        target.write_bytes(content)
        self.doc["scan_roots"].append("reports")
        self.doc["entries"].append({"source": rel, "destination": rel})
        self.save_allowlist()
        row = {"source": rel, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest(),
               "policy_sha256": hashlib.sha256(self.policy.read_bytes()).hexdigest(),
               "status": "approved_for_publication", "text_review": "passed",
               "visual_review": "passed", "metadata_review": "passed"}
        review_path = self.base / "review.json"
        review_path.write_text(json.dumps({"version": 1, "files": [row]}))
        return target, row, review_path

    def test_reviewed_document_is_in_manifest_and_source_archive(self):
        target, row, review_path = self.reviewed_document()
        result = release.create_export(self.root, self.allowlist, self.policy,
                                       self.base / "build", "test", True, review_path)
        self.assertEqual(result["status"], "passed")
        with zipfile.ZipFile(self.base / "build/downloads/source.zip") as archive:
            self.assertEqual(archive.read(row["source"]), target.read_bytes())
        manifest = json.loads((self.base / "build/manifest.json").read_text())
        self.assertIn(row["sha256"], [r["sha256"] for r in manifest["files"]])

    def test_document_change_invalidates_review(self):
        target, row, review_path = self.reviewed_document()
        target.write_bytes(target.read_bytes() + b"unreviewed")
        with self.assertRaises(release.ReleaseError):
            release.create_export(self.root, self.allowlist, self.policy,
                                  self.base / "build", "test", True, review_path)
        self.assertFalse((self.base / "build").exists())

    def test_document_missing_review_or_changed_policy_is_rejected(self):
        target, row, review_path = self.reviewed_document()
        with self.assertRaises(release.ReleaseError):
            self.build(True)
        self.policy.write_text(json.dumps({"version": 1, "rules": [{"pattern": "DIFFERENT_POLICY"}]}))
        with self.assertRaises(release.ReleaseError):
            release.create_export(self.root, self.allowlist, self.policy,
                                  self.base / "build", "test", True, review_path)


if __name__ == "__main__":
    unittest.main()
