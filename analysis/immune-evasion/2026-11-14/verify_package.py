#!/usr/bin/env python3
"""Verify packaged hashes and optionally recompute analysis outputs in a temporary copy."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys,tempfile,shutil,csv
ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--rerun',action='store_true');args=parser.parse_args()
manifest=json.loads((ROOT/'package_manifest.json').read_text())
for entry in manifest['files']:
    p=ROOT/entry['path']
    assert p.is_file(),entry['path']
    assert hashlib.sha256(p.read_bytes()).hexdigest()==entry['sha256'],entry['path']
print('All',len(manifest['files']),'packaged file hashes match.')
if args.rerun:
    with tempfile.TemporaryDirectory(prefix='immune-evasion-') as tmp:
        copy=Path(tmp).resolve()/'analysis';shutil.copytree(ROOT,copy)
        for script in ['rna/extract_immune_axes.py','proteomics/extract_axes.py']:
            subprocess.run([sys.executable,str(copy/script)],check=True,capture_output=True,text=True)
        checked=[]
        for folder in ['rna','proteomics']:
            for p in (ROOT/folder).glob('*.csv'):
                if p.name in ['new_target_peptide_specificity.csv','hla_specificity_supplement.csv']:
                    continue
                assert list(csv.DictReader(p.open()))==list(csv.DictReader((copy/folder/p.name).open())),str(p)
                checked.append(str(p.relative_to(ROOT)))
        print('Recomputed',len(checked),'CSV outputs exactly by values and order; no original files overwritten.')
        fasta=copy/'inputs/proteomics/homo_sapiens_uniprot_2025_06_11_Swissprot.fasta.txt.gz'
        if fasta.exists():
            for options in [[],['--targets','HLA-E,HLA-G','--out-stem','hla_specificity_supplement']]:
                subprocess.run([sys.executable,str(copy/'proteomics/audit_new_target_peptides.py'),*options],check=True,capture_output=True,text=True)
            for name in ['new_target_peptide_specificity.csv','hla_specificity_supplement.csv']:
                assert list(csv.DictReader((ROOT/'proteomics'/name).open()))==list(csv.DictReader((copy/'proteomics'/name).open())),name
            print('Both independent peptide-specificity tables also reproduce.')
        else:
            print('Peptide-specificity rerun skipped: fetch_optional_database.py supplies the pinned full database.')
