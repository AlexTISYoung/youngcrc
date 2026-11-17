#!/usr/bin/env python3
"""Reproduce bounded derived protein summaries and SMAD4 arithmetic.

Sequence-search flags and full-universe rank vectors are frozen upstream
inputs, not independently re-searched spectra or a new whole-proteome rank.
"""
from pathlib import Path
import argparse, collections, csv, json, re
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);args=p.parse_args()
OUT=args.output_dir;OUT.mkdir(parents=True,exist_ok=True)
def get(rel):return json.loads((ROOT/rel).read_text())
def read(rel):return pd.read_csv(ROOT/rel)
panels=get('noncanonical/protein/panels.json')
refs=read('noncanonical/protein/selected_reference_ranks.csv')
summary=[]
for panel,genes in panels.items():
    for cohort in sorted(refs.reference_cohort.unique()):
        rr=refs[refs.gene.isin(genes)&refs.reference_cohort.eq(cohort)]
        values=rr.rank_shift_points;n=len(values)
        eligible=n>=3 and n/len(genes)>=.5
        summary.append({'panel':panel,'reference':cohort,'panel_gene_count':len(genes),'rank_eligible_genes':n,'genes_ranked':';'.join(rr.gene),'median_rank_shift_points':values.median() if eligible else None,'positive_rank_shifts':int(values.gt(0).sum()),'status':'descriptive total-protein abundance; not a pathway activation score' if eligible else 'insufficient protein coverage for a panel-level abundance summary; no activity score'})
pd.DataFrame(summary).to_csv(OUT/'descriptive_panel_reference_summary.csv',index=False)
flags=read('inputs/noncanonical/peptide_specificity_flags.csv')
specificity={}
for gene,rows in flags.groupby('gene',sort=True):
    specificity[gene]={'source_labelled_sequences':len(rows),'exact_gene_specific_sequences':int(rows.exact_gene_specific.sum()),'IL_gene_specific_sequences':int(rows.IL_gene_specific.sum())}
assert specificity==get('noncanonical/protein/peptide_specificity_summary.json')['summary']
seq=read('inputs/noncanonical/protein_unique_sequence_hashes.csv')
unique=seq.groupby('protein_group').sequence_sha256.nunique()
groups=read('noncanonical/protein/selected_protein_groups.csv')
checked=0
for _,row in groups.dropna(subset=['protein_group']).iterrows():
    assert int(row.confirmed_source_unique_sequence_count)==unique.get(row.protein_group,0),row.query_gene
    checked+=1
hist=read('inputs/noncanonical/modification_state_histogram.csv')
tokens=collections.Counter();phospho=0
for _,row in hist.iterrows():
    if row.modification_tokens=='unmodified':continue
    for token in row.modification_tokens.split(';'):tokens[token]+=int(row.positive_precursor_rows)
    if re.search(r'phosph|unimod:21\b|\+79\.9',row.modification_tokens,re.I):phospho+=int(row.positive_precursor_rows)
inventory=get('noncanonical/protein/modification_inventory.json')
assert int(hist.positive_precursor_rows.sum())==inventory['positive_patient_precursor_rows']
assert dict(tokens)==inventory['modified_sequence_tokens_in_positive_patient_precursors']
assert phospho==inventory['phosphorylation_annotation_rows']==0
alleles=read('smad4/case_allele_counts.csv')
assert (alleles.ref+alleles.alt).equals(alleles.denominator)
np.testing.assert_allclose(alleles.alt/alleles.denominator,alleles.VAF,rtol=1e-12,atol=1e-12)
structures=get('smad4/structure_audit.json')['structures']
expected={(s['pdb'],r['chain']):r['phi_degrees'] for s in structures for r in s['residues'] if r['residue']==359}
angles=[]
for row in get('inputs/noncanonical/smad4_phi_coordinates.json'):
    a,b,c,d=np.array(row['coordinates_A'],dtype=float);b0=-(b-a);b1=c-b;b2=d-c;b1/=np.linalg.norm(b1)
    v=b0-np.dot(b0,b1)*b1;w=b2-np.dot(b2,b1)*b1
    angle=float(np.degrees(np.arctan2(np.dot(np.cross(b1,v),w),np.dot(v,w))))
    assert abs(angle-expected[(row['pdb'],row['chain'])])<.0001
    angles.append({'pdb':row['pdb'],'chain':row['chain'],'phi_degrees':round(angle,4)})
result={'status':'pass','assigned_protein_group_rows_count_verified':checked,'specificity_counts':specificity,'positive_precursor_rows':int(hist.positive_precursor_rows.sum()),'modification_tokens':dict(tokens),'phosphorylation_annotation_rows':phospho,'allele_fraction_rows_verified':len(alleles),'SMAD4_G359_phi':angles,'limitations':'Counts from frozen sequence-search flags are verified; full FASTA search, raw spectra and read-level variant calling are upstream and are not rerun. No activation or pathogenicity classification is inferred.'}
(OUT/'bounded_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':'pass','protein_groups':checked,'allele_rows':len(alleles),'structural_angles':len(angles)}))
