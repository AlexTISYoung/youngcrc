#!/usr/bin/env python3
"""Recompute a deterministic file/hash manifest after a reviewed package change."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
files = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or "__pycache__" in path.parts or path.name == "package_manifest.json":
        continue
    data = path.read_bytes()
    files.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
manifest = {"schema_version": 1, "package": "analysis/vactosertib-pathways/2026-11-17", "files": files,
            "file_count_excluding_manifest": len(files), "bytes_excluding_manifest": sum(f["bytes"] for f in files)}
(ROOT / "package_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({k: v for k, v in manifest.items() if k != "files"}))
