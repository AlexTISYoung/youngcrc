#!/usr/bin/env python3
"""Fetch one pinned external source into a user-selected local directory.

This does not fetch FASTQ reads, publish files, or silently accept changed bytes.
Metadata/workbooks fetched here can contain published trial subject rows and
must remain outside the public package.
"""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_id")
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    sources = json.loads((ROOT / "provenance/external_sources.json").read_text())
    source = next((s for s in sources if s["id"] == a.source_id), None)
    if not source or not source.get("sha256") or source.get("direct_download") is False:
        p.error("Require an existing direct-download source with pinned SHA256")
    destination = a.out.resolve()
    if destination == ROOT or ROOT in destination.parents:
        p.error("External sources must be downloaded outside the public package")
    destination.mkdir(parents=True, exist_ok=True)
    final = destination / source["local_name"]
    temporary = final.with_suffix(final.suffix + ".partial")
    if final.exists() or temporary.exists():
        p.error("Refusing to overwrite an existing external source or partial file")
    digest = hashlib.sha256()
    size = 0
    request = urllib.request.Request(source["url"], headers={"User-Agent": "ReproducibleResearch/1.0"})
    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("xb") as out:
        while block := response.read(1024 * 1024):
            size += len(block)
            digest.update(block)
            out.write(block)
    if digest.hexdigest() != source["sha256"] or (source.get("bytes") and size != source["bytes"]):
        raise ValueError("Source changed or download incomplete; partial file retained for review")
    temporary.rename(final)
    print(json.dumps({"source_id": a.source_id, "bytes": size, "sha256": digest.hexdigest()}))


if __name__ == "__main__":
    main()
