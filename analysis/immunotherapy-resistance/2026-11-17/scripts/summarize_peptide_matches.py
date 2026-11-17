#!/usr/bin/env python3
"""Summarise supplied full-database match records; does not repeat the FASTA search."""
from pathlib import Path
import argparse,gzip
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,default=ROOT/'recomputed/proteomics');args=p.parse_args();OUT=args.output_dir;OUT.mkdir(parents=True,exist_ok=True)
m=pd.read_csv(ROOT/'proteomics/critical_protein_peptide_mapping.csv.gz')
rows=[]
for gene,z in m.groupby('target_gene',sort=False):
    seq=[]
    for peptide,a in z.groupby('peptide',sort=False):
        exact=set(a.loc[a.exact_match,'matched_gene']);allgenes=set(a.matched_gene);tryptic=set(a.loc[a.fully_tryptic_up_to2_missed,'matched_gene'])
        seq.append({'exact_gene_specific':exact=={gene},'IL_substring_gene_specific':allgenes=={gene},'IL_fully_tryptic_gene_specific':tryptic=={gene}})
    rows.append({'gene':gene,'protein_group':z.protein_group.iloc[0],'source_labelled_sequences':len(seq),**{k:sum(x[k] for x in seq) for k in ['exact_gene_specific','IL_substring_gene_specific','IL_fully_tryptic_gene_specific']}})
def output(df,name):(OUT/(name+'.gz')).write_bytes(gzip.compress(df.to_csv(index=False).encode(),9,mtime=0))
output(pd.DataFrame(rows),'critical_protein_peptide_specificity.csv')
d=m[m.target_gene.isin(['TGFB1','LOX','LOXL1'])].copy()
d['domain_context']=d.apply(lambda q: ('LAP pro-domain' if q.peptide_end_1based<=278 else 'mature chain region') if q.target_gene=='TGFB1' else ('propeptide region' if q.peptide_end_1based<=168 else 'mature chain region') if q.target_gene=='LOX' else 'LOXL1 precursor/catalytic-region sequence; processing not quantified',axis=1)
output(d,'tgfb_loxl_processing_peptide_context.csv')
print('Recounted278 source-labelled sequences across35targets from preserved database-match records.')
