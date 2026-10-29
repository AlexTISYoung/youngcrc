#!/usr/bin/env python3
"""Build a public export from an exact, externally reviewed allowlist.

Uses only Python's standard library. The content policy is supplied from a
private file outside this source tree. No network or publication operations.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import html
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import zipfile
import zlib
from urllib.parse import unquote, urlsplit

sys.dont_write_bytecode = True

TEXT_SUFFIXES = {".html", ".css", ".js", ".mjs", ".json", ".csv", ".tsv", ".txt", ".md",
                 ".py", ".yaml", ".yml", ".svg", ".xml", ".toml", ".cff", ".sh", ".vcf", ".bed"}
TEXT_NAMES = {"LICENSE", "NOTICE", ".gitignore", "api-catalog", "server-card"}
RESERVED = {"manifest.json", "checksums.sha256", "external-checksums.sha256", "downloads/curated-data.json",
            "downloads/curated-data.zip", "downloads/source.zip"}
PRIVATE_PARTS = {".git", ".codex", ".agents", ".aws", ".ssh", "node_modules",
                 "__pycache__", "private", "originals", ".openai"}
MAX_TEXT_BYTES = 25 * 1024 * 1024
MAX_DECODED_BYTES = 128 * 1024 * 1024
BUILTIN_RULES = [
    ("local_path", re.compile(r"(?:/(?:Users|home|private|tmp)/[^\s\"<>]+|[A-Z]:[\\/](?:Users|Documents)[\\/])")),
    ("credential", re.compile(r"(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)")),
    ("signed_url", re.compile(r'''(?:X-Amz-(?:Signature|Credential)|[?&](?:access_token|api_key)=[^\s"'`&<>]+)''', re.I)),
    ("opaque_embedded_data", re.compile(r"data:[^,\s]*;base64,", re.I)),
]


class ReleaseError(ValueError):
    pass


def relative_path(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ReleaseError("Paths must be nonempty, relative POSIX paths")
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in {"", ".", ".."} for x in value.split("/")):
        raise ReleaseError("Unsafe relative path")
    if any(x in PRIVATE_PARTS for x in p.parts):
        raise ReleaseError("A private or generated directory cannot be released")
    return str(p)


def checked_file(root: Path, rel: str) -> Path:
    root = root.resolve()
    path = root / relative_path(rel)
    current = root
    for component in PurePosixPath(rel).parts:
        current = current / component
        if current.is_symlink():
            raise ReleaseError("Symlinks are not valid release inputs")
    if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
        raise ReleaseError("An allowlisted source is missing or is not a regular file")
    if root not in path.resolve().parents:
        raise ReleaseError("Input escapes the source root")
    flags = getattr(path.stat(), "st_flags", 0)
    if flags & getattr(stat, "SF_DATALESS", 0):
        raise ReleaseError("An allowlisted source is not locally available")
    return path


def load_policy(path: Path, source_root: Path) -> list[tuple[str, re.Pattern]]:
    source_root = source_root.resolve()
    resolved = path.resolve()
    if resolved == source_root or source_root in resolved.parents:
        raise ReleaseError("The content policy must remain outside the public source tree")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("version") != 1 or not isinstance(doc.get("rules"), list) or not doc["rules"]:
        raise ReleaseError("A nonempty version-1 private content policy is required")
    rules = list(BUILTIN_RULES)
    for i, item in enumerate(doc["rules"]):
        if not isinstance(item, dict) or not isinstance(item.get("pattern"), str):
            raise ReleaseError("Malformed private content rule")
        # Reports use ordinal rule IDs; never echo the expression or matched text.
        flags = re.I if item.get("ignore_case", True) else 0
        try:
            rules.append(("private_rule_" + str(i + 1), re.compile(item["pattern"], flags)))
        except re.error as exc:
            raise ReleaseError("Invalid private content rule at position " + str(i + 1)) from exc
    return rules


def scan_text(text: str, label: str, rules: list) -> list[dict]:
    findings = []
    layers = [text]
    decoded = html.unescape(unquote(text))
    if decoded != text:
        layers.append(decoded)
    for layer_number, layer in enumerate(layers):
        for rule_id, pattern in rules:
            for match in pattern.finditer(layer):
                # In FASTA, an AWS-key-shaped substring can occur naturally
                # inside a longer amino-acid sequence. Only that structural
                # false positive is excluded; headers, standalone tokens and
                # every non-FASTA input retain normal credential checking.
                if (rule_id == 'credential' and label.endswith(('.fasta.txt', '.fasta.txt.gz'))
                        and re.fullmatch(r'AKIA[0-9A-Z]{16}', match.group())):
                    left = layer.rfind('\n', 0, match.start()) + 1
                    right = layer.find('\n', match.end())
                    line = layer[left:right if right >= 0 else len(layer)]
                    if len(line) > 20 and re.fullmatch(r'[ACDEFGHIKLMNPQRSTVWYBXZJUO*]+', line):
                        continue
                findings.append({"file": label, "rule": rule_id, "decoded_layer": layer_number,
                                 "line": layer.count("\n", 0, match.start()) + 1})
                if len(findings) >= 100:
                    return findings
    return findings


def decode_payload(content: bytes, rel: str) -> tuple[str, str]:
    path = PurePosixPath(rel)
    decoded_path = path.with_suffix("") if path.suffix.lower() == ".gz" else path
    if decoded_path.suffix.lower() not in TEXT_SUFFIXES and decoded_path.name not in TEXT_NAMES:
        raise ReleaseError("Unsupported input format; use a separate reviewed binary workflow")
    if path.suffix.lower() == ".gz":
        chunks, total, remaining = [], 0, content
        while remaining:
            if len(remaining) < 10 or remaining[:3] != b"\x1f\x8b\x08":
                raise ReleaseError("Malformed gzip member")
            flags = remaining[3]
            if flags & (8 | 16 | 0xE0):
                raise ReleaseError("Gzip names/comments or unsupported header flags require separate review")
            if flags & 4:
                extra_size = int.from_bytes(remaining[10:12], "little")
                extra = remaining[12:12 + extra_size]
                if len(extra) != 6 or extra[:4] != b"BC\x02\x00":
                    raise ReleaseError("Only standard BGZF extra metadata is accepted")
            decoder = zlib.decompressobj(31)
            try:
                decoded = decoder.decompress(remaining, MAX_DECODED_BYTES - total + 1)
            except zlib.error as exc:
                raise ReleaseError("Malformed gzip stream") from exc
            total += len(decoded)
            if total > MAX_DECODED_BYTES or not decoder.eof:
                raise ReleaseError("Compressed input exceeds its limit or is incomplete")
            chunks.append(decoded)
            remaining = decoder.unused_data
        content = b"".join(chunks)
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ReleaseError("Release text must be valid UTF-8") from exc
    if "\x00" in text:
        raise ReleaseError("Binary content found in a declared text file")
    return text, decoded_path.suffix.lower()


def read_text_input(path: Path, rel: str, rules: list) -> tuple[bytes, list]:
    if path.stat().st_size > MAX_TEXT_BYTES:
        raise ReleaseError("Text input exceeds the bounded export size")
    content = path.read_bytes()
    text, suffix = decode_payload(content, rel)
    findings = scan_text(rel + "\n" + text, rel, rules)
    if suffix == ".json" or Path(rel).name in {"api-catalog", "server-card"}:
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ReleaseError("Invalid JSON input: " + rel) from exc
        # Also inspect decoded escape sequences, which can otherwise hide a value.
        findings.extend(scan_text(json.dumps(parsed, ensure_ascii=False), rel, rules))
    return content, findings


def load_binary_reviews(path: Path | None, root: Path, policy_path: Path) -> dict:
    """Pin separately reviewed documents to their exact bytes and policy."""
    if path is None:
        return {}
    if root.resolve() in path.resolve().parents:
        raise ReleaseError("Binary review evidence must remain outside the source tree")
    doc = json.loads(path.read_text())
    if doc.get("version") != 1 or not isinstance(doc.get("files"), list):
        raise ReleaseError("Malformed binary review evidence")
    policy_hash = hashlib.sha256(policy_path.read_bytes()).hexdigest()
    result = {}
    for row in doc["files"]:
        rel = relative_path(row.get("source"))
        if (rel in result or not rel.startswith("reports/")
                or PurePosixPath(rel).suffix.lower() not in {".pdf", ".png", ".jpg", ".jpeg", ".js"}
                or (rel.endswith('.js') and (row.get('kind') != 'reviewed_javascript_library'
                    or row.get('allowed_rule_ids') != ['opaque_embedded_data']))
                or row.get("status") != "approved_for_publication"
                or row.get("policy_sha256") != policy_hash
                or any(row.get(k) != "passed" for k in ("text_review", "visual_review", "metadata_review"))
                or not isinstance(row.get("bytes"), int) or isinstance(row["bytes"], bool)
                or row["bytes"] <= 0
                or not re.fullmatch(r"[0-9a-f]{64}", row.get("sha256", ""))):
            raise ReleaseError("Binary review is incomplete, duplicated or uses a different policy")
        result[rel] = row
    return result


def validate_binary(content: bytes, rel: str, review: dict) -> None:
    if len(content) != review["bytes"] or hashlib.sha256(content).hexdigest() != review["sha256"]:
        raise ReleaseError("Reviewed binary content has changed")
    suffix = PurePosixPath(rel).suffix.lower()
    if ((suffix == ".pdf" and not content.startswith(b"%PDF-"))
            or (suffix == ".png" and not content.startswith(b"\x89PNG\r\n\x1a\n"))
            or (suffix in {".jpg", ".jpeg"} and not content.startswith(b"\xff\xd8\xff"))):
        raise ReleaseError("Reviewed binary format does not match its extension")


def reviewed_findings(content: bytes, rel: str, review: dict, rules: list) -> list:
    validate_binary(content, rel, review)
    if rel.endswith('.js'):
        text, _ = decode_payload(content, rel)
        # Exact-hash library review covers its bundled icons and format-detection
        # constants only. Every other policy rule still applies to all code.
        selected = [(name, pattern) for name, pattern in rules if name != 'opaque_embedded_data']
        return scan_text(rel + '\n' + text, rel, selected)
    return scan_text(rel, rel, rules)


def check_allowlist(root: Path, doc: dict) -> list[dict]:
    if doc.get("version") != 1 or not isinstance(doc.get("entries"), list):
        raise ReleaseError("Expected a version-1 allowlist with entries")
    if not doc["entries"] or not isinstance(doc.get("scan_roots"), list) or not doc["scan_roots"]:
        raise ReleaseError("Allowlist and scan roots must be nonempty")
    sources, destinations, entries = set(), set(), []
    for item in doc["entries"]:
        if not isinstance(item, dict) or set(item) - {"source", "destination", "archive"}:
            raise ReleaseError("Malformed allowlist entry")
        source = relative_path(item.get("source"))
        dest = item.get("destination")
        dest = relative_path(dest) if dest is not None else None
        if source in sources or (dest and dest in destinations):
            raise ReleaseError("Duplicate input or destination")
        if dest in RESERVED:
            raise ReleaseError("Input collides with a generated release file")
        if dest and any(dest.startswith(x + "/") or x.startswith(dest + "/") for x in destinations):
            raise ReleaseError("Destination file/directory collision")
        sources.add(source)
        if dest:
            destinations.add(dest)
        entries.append({"source": source, "destination": dest,
                        "archive": bool(item.get("archive", True))})
    observed = set()
    for value in doc["scan_roots"]:
        rel_root = relative_path(value)
        base = root / rel_root
        if not base.is_dir() or base.is_symlink():
            raise ReleaseError("Scan root is missing or is a symlink")
        for directory, subdirs, names in os.walk(base, followlinks=False):
            for name in subdirs:
                if (Path(directory) / name).is_symlink():
                    raise ReleaseError("Symlink found in a scan root")
            for name in names:
                observed.add((Path(directory) / name).relative_to(root).as_posix())
    unexpected = observed - sources
    if unexpected:
        # Avoid exposing private filenames if an unexpected input is confidential.
        raise ReleaseError(str(len(unexpected)) + " unexpected file(s) in scan roots; revise the private inventory")
    return entries


def archive_bytes(inputs: dict[str, bytes], entries: list[dict]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in sorted(entries, key=lambda row: row["source"]):
            if item["archive"]:
                info = zipfile.ZipInfo(item["source"], date_time=(2000, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, inputs[item["source"]])
    return buffer.getvalue()


def audit_archive(content: bytes, rules: list, binary_reviews: dict | None = None) -> list[dict]:
    """Independently inspect the names and decoded contents of a generated ZIP."""
    findings = []
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for info in archive.infolist():
            rel = relative_path(info.filename)
            if rel in (binary_reviews or {}):
                if info.flag_bits & 1:
                    raise ReleaseError("Encrypted archive member")
                findings.extend(reviewed_findings(archive.read(info), rel, binary_reviews[rel], rules))
                continue
            if info.file_size > MAX_TEXT_BYTES or info.flag_bits & 1:
                raise ReleaseError("Unsupported archive member")
            decoded, suffix = decode_payload(archive.read(info), rel)
            findings.extend(scan_text(rel + "\n" + decoded, rel, rules))
            if suffix == ".json":
                findings.extend(scan_text(json.dumps(json.loads(decoded), ensure_ascii=False), rel, rules))
    return findings


def external_files_from_outputs(outputs: dict[str, bytes]) -> list[dict]:
    """Reference separately verified objects without bundling or fetching them."""
    records = []
    for catalogue_path in (
            "data/molecular/raw_release_catalog.json", "data/imaging_release_catalog.json",
            "data/pathology_release_catalog.json", "data/molecular/processed_release_catalog.json"):
        payload = outputs.get(catalogue_path)
        if payload is None:
            continue
        rows = json.loads(payload.decode("utf-8")).get("records")
        if not isinstance(rows, list):
            raise ReleaseError("Malformed external object catalogue")
        if catalogue_path.endswith("processed_release_catalog.json"):
            rows = [row for row in rows if row.get("storage") == "external"]
        records.extend(rows)
    result, ids, urls, names = [], set(), set(), set()
    for row in records:
        identifier, filename = row.get("release_file_id"), row.get("filename")
        url, digest, size = row.get("download_url"), row.get("sha256"), row.get("bytes")
        if not isinstance(url, str):
            raise ReleaseError("An external object has no verified URL")
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                or parsed.query or parsed.fragment or any(c.isspace() for c in url)):
            raise ReleaseError("External object URL must be unsigned public HTTPS")
        if (row.get("availability") != "verified_public_download"
                or row.get("included_in_release") is not True
                or row.get("public_read_without_credentials") is not True
                or row.get("storage") != "external"
                or not isinstance(identifier, str) or not re.fullmatch(r"(?:M-RAW|M-RELEASE|I-RAW|IHC-WSI)-[0-9]{3}", identifier)
                or not isinstance(filename, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]+", filename)
                or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
                or not isinstance(size, int) or isinstance(size, bool) or size <= 0):
            raise ReleaseError("External object metadata is incomplete or unverified")
        if identifier in ids or url in urls or filename in names:
            raise ReleaseError("Duplicate external object metadata")
        ids.add(identifier); urls.add(url); names.add(filename)
        result.append({key: row[key] for key in (
            "release_file_id", "source_file_id", "assay_id", "sample_ids", "filename",
            "format", "reference_build", "bytes", "sha256", "download_url",
            "storage", "availability", "companion_file_id", "verified_at")})
    return sorted(result, key=lambda row: row["release_file_id"])


def create_export(root: Path, allowlist_path: Path, policy_path: Path, destination: Path,
                  release_id: str, execute: bool = False, binary_review_path: Path | None = None) -> dict:
    root = root.resolve()
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", release_id):
        raise ReleaseError("Use a short public release identifier")
    if destination.exists():
        raise ReleaseError("Destination must be new; build a fresh release directory")
    destination = destination.absolute()
    if destination == root or destination in root.parents:
        raise ReleaseError("Destination may not replace the source tree")
    doc = json.loads(allowlist_path.read_text(encoding="utf-8"))
    if root in allowlist_path.resolve().parents:
        raise ReleaseError("The reviewed allowlist must remain outside the public source tree")
    rules = load_policy(policy_path, root)
    binary_reviews = load_binary_reviews(binary_review_path, root, policy_path)
    entries = check_allowlist(root, doc)
    if set(binary_reviews) - {row["source"] for row in entries}:
        raise ReleaseError("Binary review names an unlisted source")
    inputs, outputs, findings = {}, {}, []
    for item in entries:
        path = checked_file(root, item["source"])
        if item["source"] in binary_reviews:
            content = path.read_bytes()
            hits = reviewed_findings(content, item["source"], binary_reviews[item["source"]], rules)
        else:
            content, hits = read_text_input(path, item["source"], rules)
        findings.extend(hits)
        if item["destination"]:
            findings.extend(scan_text(item["destination"], item["source"], rules))
            outputs[item["destination"]] = content
        inputs[item["source"]] = content
    if findings:
        return {"status": "blocked", "executed": False, "findings": findings}
    datasets = {}
    for rel, content in outputs.items():
        if rel.startswith("data/") and rel.endswith(".json"):
            datasets[rel] = json.loads(content.decode("utf-8-sig"))
    outputs["downloads/curated-data.json"] = (json.dumps({"release": release_id, "datasets": datasets},
                                                         indent=2, ensure_ascii=False) + "\n").encode()
    outputs["downloads/source.zip"] = archive_bytes(inputs, entries)
    data_entries = [{"source": rel, "archive": True} for rel in outputs if rel.startswith("data/")]
    outputs["downloads/curated-data.zip"] = archive_bytes(outputs, data_entries)
    generated_findings = scan_text(release_id, "release_identifier", rules)
    for rel in ("downloads/source.zip", "downloads/curated-data.zip"):
        generated_findings.extend(audit_archive(outputs[rel], rules, binary_reviews))
    generated_findings.extend(scan_text(outputs["downloads/curated-data.json"].decode(),
                                       "downloads/curated-data.json", rules))
    if generated_findings:
        return {"status": "blocked", "executed": False, "findings": generated_findings}
    external_files = external_files_from_outputs(outputs)
    if external_files:
        outputs["external-checksums.sha256"] = "".join(
            row["sha256"] + "  " + row["filename"] + "\n" for row in external_files).encode()
    manifest = {"schema_version": "1.1", "release": release_id,
                "scope": "Approved public website and curated data; verified external objects are referenced separately and not bundled",
                "external_files": external_files,
                "checksum_note": "manifest.json is covered by checksums.sha256; the checksum file cannot hash itself",
                "files": [{"path": rel, "bytes": len(content),
                           "sha256": hashlib.sha256(content).hexdigest()}
                          for rel, content in sorted(outputs.items())]}
    outputs["manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    outputs["checksums.sha256"] = "".join(hashlib.sha256(content).hexdigest() + "  " + rel + "\n"
                                         for rel, content in sorted(outputs.items())).encode()
    report = {"status": "passed", "executed": execute, "release": release_id,
              "source_files": len(inputs), "export_files": len(outputs),
              "bytes": sum(map(len, outputs.values())), "findings": []}
    if execute:
        destination.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".release-stage-", dir=destination.parent))
        try:
            for rel, content in outputs.items():
                target = staging / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            # Files are complete before making the output directory available.
            staging.rename(destination)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["build"])
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--allowlist", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--release", required=True)
    parser.add_argument("--execute", action="store_true", help="Write the reviewed export; default is dry run")
    parser.add_argument("--binary-review", type=Path, help="Private, exact-hash evidence from separate document review")
    args = parser.parse_args()
    try:
        report = create_export(args.root, args.allowlist, args.policy, args.output,
                               args.release, args.execute, args.binary_review)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "passed" else 2
    except (ReleaseError, OSError, ValueError) as exc:
        # Avoid exception strings from parsers/OS that could contain source values.
        message = str(exc) if isinstance(exc, ReleaseError) else "Input/read error; inspect private inputs locally"
        print(json.dumps({"status": "blocked", "executed": False, "error": message}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
