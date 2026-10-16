"""Offline checks for upload integrity and explicit execution boundaries."""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import upload_r2 as upload


class Response(io.BytesIO):
    def __init__(self, body=b"", status=200, headers=None):
        super().__init__(body)
        self.status = status
        self.headers = headers or {}


class MemoryClient:
    def __init__(self):
        self.objects = {}
        self.puts = 0

    def head(self, key):
        if key not in self.objects:
            return None
        body, digest = self.objects[key]
        return {"content-length": str(len(body)), "x-amz-meta-sha256": digest}

    def put(self, key, path, digest):
        self.objects[key] = (path.read_bytes(), digest)
        self.puts += 1

    def request(self, method, key, headers=None):
        body = self.objects[key][0]
        if headers and "range" in headers:
            last = int(headers["range"].split("-")[1])
            return Response(body[:last + 1], 206)
        return Response(body)


class UploadTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / "public"
        self.root.mkdir()
        self.source = self.root / "example.txt"
        self.source.write_bytes(b"approved contents\n")
        self.row = {"path": "example.txt", "bytes": self.source.stat().st_size,
                    "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest()}

    def tearDown(self):
        self.temp.cleanup()

    def test_manifest_requires_real_size_and_digest(self):
        self.assertEqual(upload.manifest_files(self.root, {"files": [self.row]}), [self.row])
        for field, value in (("sha256", None), ("bytes", 100), ("bytes", True)):
            bad = dict(self.row, **{field: value})
            with self.assertRaises(upload.UploadError):
                upload.manifest_files(self.root, {"files": [bad]})

    def test_dry_run_does_not_require_credentials_or_network(self):
        manifest = self.base / "manifest.json"
        manifest.write_text(json.dumps({"files": [self.row]}))
        report = self.base / "report.json"
        argv = ["upload_r2", "--root", str(self.root), "--manifest", str(manifest),
                "--bucket", "test-bucket", "--prefix", "v1", "--report", str(report)]
        with patch.object(sys, "argv", argv), patch.object(upload, "R2Client", side_effect=AssertionError("no network")), \
             redirect_stdout(io.StringIO()):
            self.assertEqual(upload.main(), 0)
        result = json.loads(report.read_text())
        self.assertFalse(result["credentials_used"])
        self.assertEqual(result["results"][0]["status"], "not_uploaded")

    def test_partial_validation_cannot_claim_verified_url(self):
        results = upload.transfer(MemoryClient(), self.root, [self.row], "v1", False, "https://data.example.org")
        self.assertEqual(results[0]["status"], "uploaded_partial_validation")
        self.assertIsNone(results[0]["public_url"])

    def test_full_readback_yields_verified_result(self):
        client = MemoryClient()
        results = upload.transfer(client, self.root, [self.row], "v1", True, "https://data.example.org")
        self.assertEqual(results[0]["status"], "verified")
        self.assertEqual(results[0]["public_url"], "https://data.example.org/v1/example.txt")
        upload.transfer(client, self.root, [self.row], "v1", True)
        self.assertEqual(client.puts, 1)

    def test_existing_different_object_is_not_overwritten(self):
        client = MemoryClient()
        client.objects["v1/example.txt"] = (b"previous", "0" * 64)
        with self.assertRaises(upload.UploadError):
            upload.transfer(client, self.root, [self.row], "v1", True)
        self.assertEqual(client.puts, 0)

    def test_local_hash_mismatch_blocks_before_upload(self):
        client = MemoryClient()
        bad = dict(self.row, sha256="0" * 64)
        with self.assertRaises(upload.UploadError):
            upload.transfer(client, self.root, [bad], "v1", True)
        self.assertEqual(client.puts, 0)

    def test_full_hash_detects_corruption_beyond_range_sample(self):
        body = b"a" * 9000
        self.source.write_bytes(body)
        row = dict(self.row, bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
        client = MemoryClient()
        client.objects["v1/example.txt"] = (body[:-1] + b"b", row["sha256"])
        with self.assertRaises(upload.UploadError):
            upload.verify_remote(client, "v1/example.txt", self.source, row, True)

    def test_sigv4_is_deterministic_and_payload_bound(self):
        stamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
        args = ("GET", "example.r2.cloudflarestorage.com", "/bucket/object", "", "0" * 64,
                "EXAMPLEKEY", "example-secret")
        first = upload.signing_headers(*args, now=stamp)
        self.assertEqual(first, upload.signing_headers(*args, now=stamp))
        other = upload.signing_headers(*args[:4], "1" * 64, *args[5:], now=stamp)
        self.assertNotEqual(first["authorization"], other["authorization"])
        self.assertNotIn("example-secret", json.dumps(first))
        self.assertIn("/auto/s3/aws4_request", first["authorization"])

    def test_multipart_parts_reconstruct_the_original(self):
        self.source.write_bytes(b"abcdefghijklmn")
        client = upload.R2Client("https://example.r2.cloudflarestorage.com", "test-bucket", "key", "secret")
        parts = []
        def request(method, key, query=None, body=None, headers=None):
            if method == "POST" and "uploads" in (query or {}):
                return Response(b"<InitiateMultipartUploadResult><UploadId>test</UploadId></InitiateMultipartUploadResult>")
            if method == "PUT":
                parts.append(body)
                return Response(headers={"ETag": '"part-' + str(len(parts)) + '"'})
            return Response(b"<CompleteMultipartUploadResult/>")
        with patch.object(client, "request", side_effect=request), patch.object(upload, "SMALL_BYTES", 4), \
             patch.object(upload, "PART_BYTES", 5), patch.object(upload, "MIB", 1):
            client.put("v1/example", self.source, self.row["sha256"])
        self.assertEqual(b"".join(parts), self.source.read_bytes())
        self.assertEqual(len(parts), 3)

    def test_multipart_failure_attempts_abort(self):
        self.source.write_bytes(b"abcdefghijklmn")
        client = upload.R2Client("https://example.r2.cloudflarestorage.com", "test-bucket", "key", "secret")
        methods = []
        def request(method, key, query=None, body=None, headers=None):
            methods.append(method)
            if method == "POST":
                return Response(b"<InitiateMultipartUploadResult><UploadId>test</UploadId></InitiateMultipartUploadResult>")
            if method == "PUT":
                raise upload.UploadError("simulated failure")
            return Response()
        with patch.object(client, "request", side_effect=request), patch.object(upload, "SMALL_BYTES", 4):
            with self.assertRaises(upload.UploadError):
                client.put("v1/example", self.source, self.row["sha256"])
        self.assertEqual(methods[-1], "DELETE")


if __name__ == "__main__":
    unittest.main()
