#!/usr/bin/env python3
"""Fetch the optional frozen Swiss-Prot input and verify the published SHA-256."""
from pathlib import Path
import hashlib,json,urllib.request
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'source_manifest.json').read_text())
for entry in manifest['sources']:
    if entry.get('bundled') is not False:
        continue
    target=ROOT/entry['package_path']
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==entry['original_source_sha256']:
        print('Verified existing',entry['package_path']);continue
    target.parent.mkdir(parents=True,exist_ok=True)
    temp=target.with_name(target.name+'.download')
    urllib.request.urlretrieve(entry['public_source_url'],temp)
    if hashlib.sha256(temp.read_bytes()).hexdigest()!=entry['original_source_sha256']:
        temp.unlink();raise RuntimeError('Database SHA-256 mismatch; no input accepted')
    temp.replace(target);print('Verified download',entry['package_path'])
