#!/usr/bin/env python3
"""Upload exactly the files in a reviewed SHA-256 manifest to an existing R2 bucket.

Dry run is the default. Credentials are read only from environment variables.
No account creation, bucket creation, ACL/public-access changes or source edits.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import hmac
import json
import math
import mimetypes
import os
from pathlib import Path
import re
import stat
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
from release_tool import ReleaseError, checked_file, relative_path

MIB = 1024 * 1024
PART_BYTES = 64 * MIB
SMALL_BYTES = 16 * MIB


class UploadError(ValueError):
    pass


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * MIB), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_files(root: Path, document: dict) -> list[dict]:
    files = document.get("files")
    if not isinstance(files, list) or not files:
        raise UploadError("A nonempty reviewed file manifest is required")
    rows, seen = [], set()
    for item in files:
        rel = relative_path(item.get("path"))
        if rel in seen:
            raise UploadError("Duplicate manifest path")
        seen.add(rel)
        size, digest = item.get("bytes"), item.get("sha256")
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            raise UploadError("Invalid manifest byte count")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise UploadError("Every upload requires a final SHA-256")
        source = checked_file(root, rel)
        if source.stat().st_size != size:
            raise UploadError("A source size differs from the approved manifest")
        rows.append({"path": rel, "bytes": size, "sha256": digest})
    return rows


def signing_headers(method: str, host: str, canonical_uri: str, canonical_query: str,
                    payload_hash: str, access_key: str, secret_key: str,
                    extra_headers: dict | None = None, now: datetime | None = None) -> dict:
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    day = stamp[:8]
    headers = {"host": host, "x-amz-date": stamp, "x-amz-content-sha256": payload_hash}
    headers.update({key.lower(): " ".join(str(value).split()) for key, value in (extra_headers or {}).items()})
    names = ";".join(sorted(headers))
    canonical_headers = "".join(key + ":" + headers[key] + "\n" for key in sorted(headers))
    request = "\n".join([method, canonical_uri, canonical_query, canonical_headers, names, payload_hash])
    scope = day + "/auto/s3/aws4_request"
    to_sign = "AWS4-HMAC-SHA256\n" + stamp + "\n" + scope + "\n" + hashlib.sha256(request.encode()).hexdigest()
    key = ("AWS4" + secret_key).encode()
    for value in (day, "auto", "s3", "aws4_request"):
        key = hmac.new(key, value.encode(), hashlib.sha256).digest()
    signature = hmac.new(key, to_sign.encode(), hashlib.sha256).hexdigest()
    headers["authorization"] = ("AWS4-HMAC-SHA256 Credential=" + access_key + "/" + scope +
                                ", SignedHeaders=" + names + ", Signature=" + signature)
    return headers


class R2Client:
    def __init__(self, endpoint: str, bucket: str, access_key: str, secret_key: str):
        parsed = urlsplit(endpoint)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or
                parsed.query or parsed.fragment or parsed.path not in {"", "/"}):
            raise UploadError("Use an HTTPS account S3 endpoint without path or credentials")
        if not parsed.hostname.endswith(".r2.cloudflarestorage.com"):
            raise UploadError("The endpoint must be an R2 S3 endpoint")
        if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket):
            raise UploadError("Invalid bucket name")
        self.endpoint = endpoint.rstrip("/")
        self.host, self.bucket = parsed.netloc, bucket
        self.access_key, self.secret_key = access_key, secret_key

    def request(self, method: str, key: str, query: dict | None = None,
                body: bytes | None = None, headers: dict | None = None):
        uri = "/" + quote(self.bucket + "/" + key, safe="/-_.~")
        query_text = urlencode(sorted((query or {}).items()), quote_via=quote, safe="-_.~")
        url = self.endpoint + uri + ("?" + query_text if query_text else "")
        payload_hash = hashlib.sha256(body or b"").hexdigest()
        last_error = None
        for attempt in range(3):
            signed = signing_headers(method, self.host, uri, query_text, payload_hash,
                                     self.access_key, self.secret_key, headers)
            request = Request(url, data=body, headers=signed, method=method)
            try:
                return urlopen(request, timeout=120)
            except HTTPError as exc:
                last_error = exc
                if exc.code not in {429, 500, 502, 503, 504}:
                    raise
            except URLError as exc:
                last_error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
        raise UploadError("R2 request failed after bounded retries") from last_error

    def head(self, key: str) -> dict | None:
        try:
            with self.request("HEAD", key) as response:
                return {name.lower(): value for name, value in response.headers.items()}
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise UploadError("R2 object metadata request was denied or failed") from exc

    def put(self, key: str, path: Path, digest: str) -> None:
        size = path.stat().st_size
        metadata = {"x-amz-meta-sha256": digest,
                    "content-type": mimetypes.guess_type(key)[0] or "application/octet-stream"}
        if size <= SMALL_BYTES:
            with self.request("PUT", key, body=path.read_bytes(), headers=metadata):
                return
        part_bytes = max(PART_BYTES, math.ceil(size / 9999 / MIB) * MIB)
        if part_bytes > 256 * MIB:
            raise UploadError("Object exceeds the bounded-memory multipart configuration")
        with self.request("POST", key, query={"uploads": ""}, body=b"", headers=metadata) as response:
            tree = ET.fromstring(response.read())
        upload_id = tree.findtext("{*}UploadId")
        if not upload_id:
            raise UploadError("R2 did not return a multipart upload identifier")
        try:
            parts = []
            with path.open("rb") as handle:
                for number, data in enumerate(iter(lambda: handle.read(part_bytes), b""), 1):
                    with self.request("PUT", key, query={"partNumber": str(number), "uploadId": upload_id},
                                      body=data) as response:
                        etag = response.headers.get("ETag")
                    if not etag:
                        raise UploadError("Multipart part acknowledgement is missing")
                    parts.append((number, etag))
            complete = ET.Element("CompleteMultipartUpload")
            for number, etag in parts:
                part = ET.SubElement(complete, "Part")
                ET.SubElement(part, "PartNumber").text = str(number)
                ET.SubElement(part, "ETag").text = etag
            with self.request("POST", key, query={"uploadId": upload_id}, body=ET.tostring(complete),
                              headers={"content-type": "application/xml"}) as response:
                result = ET.fromstring(response.read())
            if result.tag.endswith("Error"):
                raise UploadError("R2 multipart completion returned an error")
        except BaseException:
            try:
                with self.request("DELETE", key, query={"uploadId": upload_id}):
                    pass
            except Exception:
                pass
            raise


def verify_remote(client, key: str, source: Path, row: dict, full: bool) -> dict:
    metadata = client.head(key)
    if metadata is None or int(metadata.get("content-length", -1)) != row["bytes"]:
        raise UploadError("Remote object size verification failed")
    if metadata.get("x-amz-meta-sha256") != row["sha256"]:
        raise UploadError("Remote checksum metadata verification failed")
    range_status = "not_applicable_empty_file"
    if row["bytes"]:
        length = min(row["bytes"], 4096)
        with source.open("rb") as handle:
            expected = handle.read(length)
        with client.request("GET", key, headers={"range": "bytes=0-" + str(length - 1)}) as response:
            actual = response.read(length + 1)
            if response.status != 206 or actual != expected:
                raise UploadError("Remote HTTP Range verification failed")
        range_status = "passed"
    if full:
        digest, received = hashlib.sha256(), 0
        with client.request("GET", key) as response:
            for chunk in iter(lambda: response.read(8 * MIB), b""):
                received += len(chunk)
                digest.update(chunk)
        if received != row["bytes"] or digest.hexdigest() != row["sha256"]:
            raise UploadError("Full remote SHA-256 verification failed")
    return {"head": "passed", "range": range_status,
            "full_readback_sha256": "passed" if full else "not_performed",
            "status": "verified" if full else "uploaded_partial_validation"}


def transfer(client, root: Path, rows: list[dict], prefix: str, full: bool,
             public_base: str | None = None) -> list[dict]:
    results = []
    for row in rows:
        source = checked_file(root, row["path"])
        if hash_file(source) != row["sha256"]:
            raise UploadError("A source SHA-256 differs from the approved manifest")
        before = source.stat()
        key = prefix.rstrip("/") + "/" + row["path"]
        existing = client.head(key)
        if existing is None:
            client.put(key, source, row["sha256"])
            action = "uploaded"
        elif (int(existing.get("content-length", -1)) == row["bytes"] and
              existing.get("x-amz-meta-sha256") == row["sha256"]):
            action = "existing_object_checked"
        else:
            raise UploadError("Existing object differs; use a new version prefix instead of overwriting")
        after = source.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise UploadError("Source changed during upload; do not release the remote object")
        result = dict(row, object_key=key, action=action, **verify_remote(client, key, source, row, full))
        result["public_url"] = (public_base.rstrip("/") + "/" + quote(key, safe="/-_.~")) if full and public_base else None
        results.append(result)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--public-base-url")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--verify-full", action="store_true", help="Stream back all bytes and verify SHA-256")
    args = parser.parse_args()
    try:
        root = args.root.resolve()
        prefix = relative_path(args.prefix)
        if root in args.report.resolve().parents or args.report.exists():
            raise UploadError("Use a new private report outside the upload root")
        if args.public_base_url:
            url = urlsplit(args.public_base_url)
            if url.scheme != "https" or not url.netloc or url.username or url.password or url.query or url.fragment:
                raise UploadError("Public base URL must be stable HTTPS without credentials or query parameters")
        rows = manifest_files(root, json.loads(args.manifest.read_text()))
        report = {"mode": "upload" if args.execute else "dry_run", "files": len(rows),
                  "bytes": sum(row["bytes"] for row in rows), "source_files_modified": False,
                  "credentials_used": False, "bucket_permissions_changed": False, "results": []}
        if args.execute:
            names = ("R2_S3_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")
            credentials = {name: os.environ.get(name) for name in names}
            if not all(credentials.values()):
                raise UploadError("Required R2 environment credentials are unavailable")
            client = R2Client(credentials[names[0]], args.bucket, credentials[names[1]], credentials[names[2]])
            report["credentials_used"] = True
            report["results"] = transfer(client, root, rows, prefix, args.verify_full, args.public_base_url)
        else:
            report["results"] = [dict(row, status="not_uploaded", public_url=None) for row in rows]
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"status": "completed" if args.execute else "planned", "files": len(rows),
                          "full_readback_requested": args.verify_full if args.execute else False}))
        return 0
    except (UploadError, ReleaseError) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}), file=sys.stderr)
        return 2
    except Exception:
        print(json.dumps({"status": "blocked", "error": "Transfer failed; inspect local configuration without exposing credentials"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
