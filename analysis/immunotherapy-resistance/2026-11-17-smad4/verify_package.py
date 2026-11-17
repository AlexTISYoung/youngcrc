#!/usr/bin/env python3
"""Check integrity and optionally reproduce the compact numerical analysis."""
from pathlib import Path
import argparse,hashlib,json,tempfile,subprocess,sys,gzip
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--rerun',action='store_true');p.add_argument('--vactosertib-source',type=Path);p.add_argument('--fetch-vactosertib',action='store_true');args=p.parse_args()
m=json.loads((ROOT/'package_manifest.json').read_text())
listed={entry['path'] for entry in m['files']}
actual={f.relative_to(ROOT).as_posix() for f in ROOT.rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.name!='package_manifest.json'}
assert actual==listed,{'unlisted':sorted(actual-listed),'missing':sorted(listed-actual)}
for entry in m['files']:
    f=ROOT/entry['path'];assert f.is_file(),entry['path']
    assert f.stat().st_size==entry['bytes'],entry['path']
    assert hashlib.sha256(f.read_bytes()).hexdigest()==entry['sha256'],entry['path']
    if f.suffix=='.gz':
        b=f.read_bytes();assert b[3]&8==0 and b[4:8]==b'\0\0\0\0','Non-deterministic gzip header'
        assert hashlib.sha256(gzip.decompress(b)).hexdigest()==entry['decoded_sha256'],entry['path']
print('Verified',len(m['files']),'package files.')
def run(script,out,more=()):
    r=subprocess.run([sys.executable,str(ROOT/'scripts'/script),'--output-dir',str(out),*more],capture_output=True,text=True)
    if r.returncode:raise RuntimeError(r.stderr or r.stdout)
if args.rerun or args.vactosertib_source or args.fetch_vactosertib:
    import pandas as pd
    with tempfile.TemporaryDirectory(prefix='immunotherapy-resistance-') as tmp:
        temp=Path(tmp).resolve()
        if args.rerun:
            for script,folder in [('reproduce_rna.py','rna'),('reproduce_proteomics.py','proteomics'),('summarize_peptide_matches.py','proteomics'),('reproduce_recruitment.py','recruitment')]:run(script,temp/folder)
            n=0
            for folder in ['rna','proteomics','recruitment']:
                for f in (temp/folder).glob('*.csv.gz'):
                    pd.testing.assert_frame_equal(pd.read_csv(ROOT/folder/f.name),pd.read_csv(f),check_dtype=False,rtol=1e-7,atol=1e-7);n+=1
            assert n==24,n
            print('Reproduced all 24 numerical CSV tables within declared tolerance.')
            run('reproduce_noncanonical_rna.py',temp/'noncanonical-rna')
            nnew=0
            for f in (temp/'noncanonical-rna').glob('*.csv'):
                pd.testing.assert_frame_equal(pd.read_csv(ROOT/'noncanonical/rna'/f.name),pd.read_csv(f),check_dtype=False,rtol=1e-7,atol=1e-7);nnew+=1
            assert nnew==8,nnew
            run('reproduce_noncanonical_protein_smad4.py',temp/'noncanonical-protein-smad4')
            name='descriptive_panel_reference_summary.csv'
            pd.testing.assert_frame_equal(pd.read_csv(ROOT/'noncanonical/protein'/name),pd.read_csv(temp/'noncanonical-protein-smad4'/name),check_dtype=False,rtol=1e-7,atol=1e-7)
            expected=json.loads((ROOT/'provenance/noncanonical_portable_equivalence.json').read_text())['bounded_checks']
            assert json.loads((temp/'noncanonical-protein-smad4/bounded_checks.json').read_text())==expected
            print('Reproduced 8 additional RNA tables, 1 protein summary, peptide/modification counts, 6 allele fractions and 5 structural angles.')
            if (ROOT/'molecular/reproduce_summary.py').exists():
                subprocess.run([sys.executable,str(ROOT/'molecular/reproduce_summary.py'),'--output-dir',str(temp/'molecular-curation')],check=True)
        if args.vactosertib_source or args.fetch_vactosertib:
            more=['--source',str(args.vactosertib_source.resolve())] if args.vactosertib_source else ['--fetch']
            run('audit_vactosertib_aggregate.py',temp/'literature',more)
            for name in ['vactosertib_source_data_audit.json','vactosertib_pd_vs_benefit_counts.json']:
                assert json.loads((ROOT/'literature'/name).read_text())==json.loads((temp/'literature'/name).read_text()),name
            pd.testing.assert_frame_equal(pd.read_csv(ROOT/'literature/vactosertib_baseline_ihc_summary.csv'),pd.read_csv(temp/'literature/vactosertib_baseline_ihc_summary.csv'))
            print('Reproduced all 3 aggregate clinical-audit outputs; no subject rows saved.')
