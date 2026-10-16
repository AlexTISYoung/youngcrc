#!/usr/bin/env python3
"""List, selectively fetch, and verify YoungCRC release data (Python 3.10+)."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "release" / "website-manifest.json"
DEFAULT_SNAPSHOT = REPO_ROOT / "release" / "snapshot.json"
SITE_URL = "https://youngcrc.com"
DEFAULT_MAX_BYTES = 100_000_000
MAX_MANIFEST_BYTES = 10_000_000
CHUNK_BYTES = 1024 * 1024
SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


class CaseDataError(Exception):
    """An invalid manifest, unsafe request, or verification failure."""


def safe_path(value: Any) -> str:
    """Require an unambiguous, portable path relative to a release root."""
    if not isinstance(value, str) or not value:
        raise CaseDataError("File path must be a nonempty string")
    decoded = value
    for _ in range(5):
        new = unquote(decoded)
        if new == decoded:
            break
        decoded = new
    for candidate in (value, decoded):
        if (
            candidate.startswith("/")
            or "\\" in candidate
            or ":" in candidate
            or any(ord(char) < 32 or ord(char) == 127 for char in candidate)
            or any(part in ("", ".", "..") for part in candidate.split("/"))
        ):
            raise CaseDataError(f"Unsafe relative file path: {value!r}")
    return value


def safe_https_url(value: Any) -> str:
    """Accept HTTPS URLs without credentials, local literals, or odd ports."""
    if not isinstance(value, str) or any(ord(c) <= 32 for c in value):
        raise CaseDataError("Download URL must be an HTTPS URL")
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise CaseDataError(f"Invalid HTTPS URL: {value!r}") from exc
    if (
        parsed.scheme != "https"
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or port not in (None, 443)
        or "\\" in value
    ):
        raise CaseDataError(f"Unsafe HTTPS URL: {value!r}")
    hostname = hostname.rstrip(".").lower()
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        public_hostname = re.fullmatch(r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]*", hostname)
        if not public_hostname or hostname.endswith((".localhost", ".local", ".internal")):
            raise CaseDataError(f"Local download host is not allowed: {hostname}")
    else:
        if not address.is_global:
            raise CaseDataError(f"Nonpublic download address is not allowed: {hostname}")
    decoded_path = parsed.path
    for _ in range(5):
        decoded_path = unquote(decoded_path)
        if ("\\" in decoded_path or any(ord(char) < 32 or ord(char) == 127 for char in decoded_path)
                or any(part == ".." for part in decoded_path.split("/"))):
            raise CaseDataError(f"Unsafe URL path: {value!r}")
    return value


class SafeRedirectHandler(HTTPRedirectHandler):
    """Keep a declared download on its declared HTTPS origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        safe_https_url(newurl)
        if urlsplit(req.full_url).netloc != urlsplit(newurl).netloc:
            raise CaseDataError("Cross-origin redirects are not accepted; use the published URL")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def open_url(url: str):
    safe_https_url(url)
    request = Request(url, headers={"User-Agent": "youngcrc-case-data/1.0", "Accept-Encoding": "identity"})
    return build_opener(SafeRedirectHandler()).open(request, timeout=60)


def checked_metadata(entry: Any) -> tuple[int, str]:
    if not isinstance(entry, dict):
        raise CaseDataError("Each manifest file must be an object")
    size = entry.get("bytes")
    digest = entry.get("sha256")
    if not isinstance(size, int) or isinstance(size, bool) or size < 0:
        raise CaseDataError("Each file must declare a nonnegative integer byte count")
    if not isinstance(digest, str) or not SHA256_PATTERN.fullmatch(digest):
        raise CaseDataError("Each file must declare a 64-character SHA-256 digest")
    return size, digest.lower()


def manifest_files(manifest: Any) -> list[dict[str, Any]]:
    """Normalize the website's bundled and external manifest shapes."""
    if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
        raise CaseDataError("Manifest must be an object with a files array")
    external = manifest.get("external_files", [])
    if not isinstance(external, list):
        raise CaseDataError("Manifest external_files must be an array")
    result = []
    for storage, entries in (("bundled", manifest["files"]), ("external", external)):
        for entry in entries:
            size, digest = checked_metadata(entry)
            release_id = entry.get("release_file_id")
            if release_id is not None and (not isinstance(release_id, str) or not release_id
                    or any(ord(char) < 32 or ord(char) == 127 for char in release_id)):
                raise CaseDataError("release_file_id must be a nonempty string when supplied")
            path = safe_path(entry.get("path") if storage == "bundled" else entry.get("filename"))
            if storage == "bundled":
                url = SITE_URL + "/" + quote(path, safe="/-._~")
                downloadable = True
            else:
                url = entry.get("download_url")
                downloadable = entry.get("availability") == "verified_public_download" and bool(url)
                if url:
                    safe_https_url(url)
            result.append({
                **entry,
                "path": path,
                "storage": storage,
                "bytes": size,
                "sha256": digest,
                "download_url": url,
                "downloadable": downloadable,
            })
    paths = [(item["storage"], item["path"]) for item in result]
    if len(paths) != len(set(paths)):
        raise CaseDataError("Manifest contains duplicate paths within a storage class")
    ids = [item["release_file_id"] for item in result if item.get("release_file_id")]
    if len(ids) != len(set(ids)):
        raise CaseDataError("Manifest contains duplicate release_file_id values")
    return result


def load_json(source: str | Path) -> Any:
    source = str(source)
    if source.startswith("https://"):
        with open_url(source) as response:
            raw = response.read(MAX_MANIFEST_BYTES + 1)
        if len(raw) > MAX_MANIFEST_BYTES:
            raise CaseDataError("Remote JSON exceeds the 10 MB manifest limit")
    elif "://" in source:
        raise CaseDataError("Remote manifests must use HTTPS")
    else:
        path = Path(source)
        if path.stat().st_size > MAX_MANIFEST_BYTES:
            raise CaseDataError("JSON exceeds the 10 MB manifest limit")
        raw = path.read_bytes()
    try:
        return json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise CaseDataError(f"Invalid JSON in {source}") from exc


def select_file(files: list[dict[str, Any]], selector: str) -> dict[str, Any]:
    matches = [entry for entry in files if selector in (entry["path"], entry.get("release_file_id"))]
    if not matches:
        raise CaseDataError(f"No manifest file has this exact path or release_file_id: {selector}")
    if len(matches) != 1:
        raise CaseDataError(f"Ambiguous selector; use a release_file_id: {selector}")
    if not matches[0]["downloadable"]:
        raise CaseDataError("The selected file is not declared as a verified public download")
    return matches[0]


def fetch_file(entry: dict[str, Any], output: Path, max_bytes: int) -> dict[str, Any]:
    if max_bytes <= 0:
        raise CaseDataError("--max-bytes must be positive")
    size, expected_digest = checked_metadata(entry)
    if size > max_bytes:
        raise CaseDataError(f"Declared size {size} exceeds --max-bytes {max_bytes}; raise the limit explicitly")
    if os.path.lexists(output):
        raise CaseDataError(f"Output already exists: {output}")
    url = safe_https_url(entry.get("download_url"))
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=f".{output.name}.", suffix=".part", dir=output.parent, delete=False) as handle:
            temporary = Path(handle.name)
            digest = hashlib.sha256()
            received = 0
            with open_url(url) as response:
                if response.status != 200:
                    raise CaseDataError(f"Expected HTTP 200, received {response.status}")
                content_encoding = response.headers.get("Content-Encoding", "identity").lower()
                if content_encoding != "identity":
                    raise CaseDataError("Server returned encoded content; exact released bytes are required")
                while True:
                    block = response.read(min(CHUNK_BYTES, size - received + 1, max_bytes - received + 1))
                    if not block:
                        break
                    received += len(block)
                    if received > max_bytes or received > size:
                        raise CaseDataError("Download exceeds its declared size or the transfer limit")
                    digest.update(block)
                    handle.write(block)
            if received != size:
                raise CaseDataError(f"Byte count mismatch: expected {size}, received {received}")
            actual_digest = digest.hexdigest()
            if actual_digest != expected_digest:
                raise CaseDataError(f"SHA-256 mismatch: expected {expected_digest}, received {actual_digest}")
            handle.flush()
            os.fsync(handle.fileno())
        # A same-directory hard link commits the verified file atomically and
        # refuses an output that appeared during transfer, without overwriting it.
        try:
            os.link(temporary, output)
        except FileExistsError as exc:
            raise CaseDataError(f"Output already exists: {output}") from exc
        return {"ok": True, "path": entry["path"], "release_file_id": entry.get("release_file_id"),
                "output": str(output.resolve()), "bytes": received, "sha256": actual_digest, "download_url": url}
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def verify_snapshot(snapshot: Any, root: Path = REPO_ROOT) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        raise CaseDataError("Snapshot must be an object")
    entries = snapshot.get("files", snapshot)
    if isinstance(entries, dict):
        if any(not isinstance(metadata, dict) for metadata in entries.values()):
            raise CaseDataError("Every snapshot path must map to file metadata")
        entries = [{**metadata, "path": path} for path, metadata in entries.items()]
    if not isinstance(entries, list) or not entries:
        raise CaseDataError("Snapshot must contain a nonempty files array or path-to-metadata mapping")
    root = root.resolve()
    failures = []
    seen = set()
    for entry in entries:
        size, expected = checked_metadata(entry)
        relative = safe_path(entry.get("path"))
        if relative in seen:
            raise CaseDataError(f"Duplicate snapshot path: {relative}")
        seen.add(relative)
        path = root.joinpath(*PurePosixPath(relative).parts)
        try:
            path.resolve().relative_to(root)
        except ValueError as exc:
            raise CaseDataError(f"Snapshot path escapes the repository: {relative}") from exc
        if any(parent.is_symlink() for parent in (path, *path.parents) if parent != root and root in parent.parents):
            raise CaseDataError(f"Snapshot symlinks are not supported: {relative}")
        if not path.is_file():
            failures.append({"path": relative, "error": "missing file"})
            continue
        if path.stat().st_size != size:
            failures.append({"path": relative, "error": "byte count mismatch"})
            continue
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(CHUNK_BYTES), b""):
                digest.update(block)
        if digest.hexdigest() != expected:
            failures.append({"path": relative, "error": "SHA-256 mismatch"})
    return {"ok": not failures, "checked_files": len(entries), "failures": failures}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Local manifest path or HTTPS URL (default: bundled release manifest)")
    commands = result.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="List declared files; never download data")
    listing.add_argument("--storage", choices=("bundled", "external"))
    listing.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    fetch = commands.add_parser("fetch", help="Fetch one exact manifest path or release_file_id")
    fetch.add_argument("selector")
    fetch.add_argument("--output", type=Path, required=True)
    fetch.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES, help="Transfer cap in bytes (default: 100000000)")
    fetch.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    verify = commands.add_parser("verify-snapshot", help="Verify files listed in the repository snapshot")
    verify.add_argument("--snapshot", default=str(DEFAULT_SNAPSHOT), help="Snapshot JSON path (entries are repository-relative)")
    verify.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "verify-snapshot":
            result = verify_snapshot(load_json(args.snapshot))
        else:
            manifest = load_json(args.manifest)
            files = manifest_files(manifest)
            if args.command == "list":
                if args.storage:
                    files = [entry for entry in files if entry["storage"] == args.storage]
                result = {"ok": True, "release": manifest.get("release"), "file_count": len(files), "files": files}
            else:
                result = fetch_file(select_file(files, args.selector), args.output, args.max_bytes)
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        elif args.command == "list":
            print("storage\tbytes\trelease_file_id\tpath")
            for entry in result["files"]:
                print(f"{entry['storage']}\t{entry['bytes']}\t{entry.get('release_file_id') or '-'}\t{entry['path']}")
        elif args.command == "verify-snapshot":
            print(f"Checked {result['checked_files']} files; {len(result['failures'])} verification failures")
            for failure in result["failures"]:
                print(f"{failure['path']}: {failure['error']}")
        else:
            print(f"Verified {result['bytes']} bytes: {result['output']}")
        return 0 if result["ok"] else 1
    except (CaseDataError, OSError, HTTPError, URLError) as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
