#!/usr/bin/env python3
"""Wrap an exact reviewed release in a Worker without rebundling large binaries."""
import argparse
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('release', type=Path)
args = parser.parse_args()
export = args.release.resolve()
if not (export / 'index.html').is_file() or not (export / 'manifest.json').is_file():
    raise SystemExit('A complete reviewed release is required before preparing the Worker.')
dist = ROOT / 'dist'
if dist.exists():
    shutil.rmtree(dist)
shutil.copytree(export, dist / 'client')
(dist / 'server').mkdir()
content = {}
paths = []
for p in export.rglob('*'):
    if not p.is_file():
        continue
    rel = str(p.relative_to(export))
    if rel.startswith('data/') and p.suffix == '.json':
        paths.append('/' + rel)
    if (rel.startswith('data/') and p.suffix == '.json') or rel in {'index.html', 'manifest.json', 'checksums.sha256', 'external-checksums.sha256'} or rel.startswith(('agents/', '.well-known/', 'mcp/')) or rel in {'robots.txt', 'sitemap.xml', 'openapi.json', 'llms.txt', 'auth.md', 'docs/api.md'}:
        media = 'application/json' if p.suffix == '.json' or rel.endswith('server-card') else 'text/markdown' if p.suffix == '.md' else 'text/html' if p.suffix == '.html' else 'application/xml' if p.suffix == '.xml' else 'text/plain'
        if rel == '.well-known/api-catalog':
            media = 'application/linkset+json'
        if rel == 'mcp/server-card':
            media = 'application/mcp-server-card+json'
        content['/' + rel] = {'type': media + '; charset=utf-8', 'body': p.read_text()}
        (dist / 'client' / rel).unlink()
content['/agents/datasets.json'] = {'type': 'application/json; charset=utf-8', 'body': json.dumps({'paths': sorted(paths)})}
(dist / 'server/public-content.mjs').write_text('export const publicContent = ' + json.dumps(content, ensure_ascii=False) + ';\nexport const datasetPaths = ' + json.dumps(sorted(paths)) + ';\n')
shutil.copy2(ROOT / 'server/index.mjs', dist / 'server/index.js')
shutil.copy2(ROOT / 'site/agent-tools.mjs', dist / 'server/agent-tools.mjs')
(dist / '.openai').mkdir()
shutil.copy2(ROOT / '.openai/hosting.json', dist / '.openai/hosting.json')
(dist / 'client/_headers').write_text('/*\n  Access-Control-Allow-Origin: *\n  Content-Signal: search=yes, ai-input=yes, ai-train=yes\n  X-Content-Type-Options: nosniff\n')
print(json.dumps({'embedded_files': len(content), 'dataset_paths': len(paths), 'worker_content_bytes': (dist / 'server/public-content.mjs').stat().st_size, 'static_files': len([p for p in (dist / 'client').rglob('*') if p.is_file()])}))
