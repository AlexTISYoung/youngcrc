"""Check frozen input hashes; optionally retrieve missing pinned reference or source-package inputs."""
from pathlib import Path
import argparse, gzip, hashlib, io, json, sys
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

def checked_reference_bytes(compressed, row):
    asset = row['public_gzip']
    if len(compressed) != asset['bytes'] or hashlib.sha256(compressed).hexdigest() != asset['sha256']:
        raise ValueError('Compressed reference does not match its pinned hash')
    if row['bytes'] > 128 * 1024 * 1024:
        raise ValueError('Decoded reference exceeds the supported limit')
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        decoded = stream.read(row['bytes'] + 1)
    if len(decoded) != row['bytes'] or hashlib.sha256(decoded).hexdigest() != row['sha256']:
        raise ValueError('Decoded reference does not match its pinned hash')
    return decoded

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-complete', action='store_true')
    parser.add_argument('--fetch-references', '--fetch-inputs', dest='fetch_references', action='store_true',
                        help='Download missing pinned inputs from youngcrc.com (13 references plus any missing PR/FASTA source inputs); verify compressed and decoded hashes')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'download_manifest.json').read_text())
    missing, mismatches, verified, fetched = [], [], [], []
    for row in manifest['files']:
        path = root / row['local']
        if root not in path.resolve().parents:
            raise ValueError('Input path escapes the analysis directory')
        if not path.is_file() and args.fetch_references and row.get('public_gzip'):
            asset = row['public_gzip']
            url = urlsplit(asset['url'])
            if (url.scheme != 'https' or url.netloc != 'youngcrc.com' or url.query or url.fragment
                    or not (url.path.startswith('/reports/proteomics/quantitative-2026-10-29/reference-inputs/')
                            or (row['included'] and url.path == '/data/proteomics/b7_43_2026-10-29/' + row['local'] + '.gz'))
                    or asset['bytes'] > 25 * 1024 * 1024):
                raise ValueError('Unexpected pinned input download location or size')
            request = Request(asset['url'], headers={'User-Agent': 'youngcrc-proteomics-reproduction/1.0'})
            with urlopen(request, timeout=90) as response:
                content = response.read(asset['bytes'] + 1)
            decoded = checked_reference_bytes(content, row)
            path.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation preserves an existing input; a mismatched file is never overwritten.
            with path.open('xb') as output:
                output.write(decoded)
            fetched.append(row['local'])
        if not path.is_file():
            missing.append({'path': row['local'], 'separately_hosted': bool(row.get('public_gzip')),
                            'included_in_source_package': row['included']})
        elif path.stat().st_size != row['bytes'] or hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            mismatches.append(row['local'])
        else:
            verified.append(row['local'])
    result = {'verified_inputs': len(verified), 'fetched_inputs': len(fetched), 'missing_inputs': missing,
              'hash_mismatches': mismatches, 'full_reproduction_ready': not missing and not mismatches,
              'included_input_validation_passed': not mismatches and not any(x['included_in_source_package'] for x in missing)}
    print(json.dumps(result, indent=2))
    return 1 if not result['included_input_validation_passed'] else 2 if args.require_complete and missing else 0

if __name__ == '__main__':
    sys.exit(main())
