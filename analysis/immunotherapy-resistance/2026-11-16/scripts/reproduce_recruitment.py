"""Read-only reuse of existing full RNA and peptide-supported proteomic exports.

No alignment, deconvolution, pathway-activation score, or patient-response prediction.
Research gene comparisons use the existing 18 GSE50760 primary CRC samples.
"""
from pathlib import Path
import hashlib, json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
import argparse,gzip
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=ROOT/'recomputed/recruitment');args=parser.parse_args();OUT=args.output_dir;OUT.mkdir(parents=True,exist_ok=True)
INPUT=ROOT/'inputs/recruitment'
RNA=ROOT/'rna'
LIVER=INPUT/'liver_celltype_summary.csv.gz'
PANELS={
 'priming_cDC1_and_other_APC_context':'BATF3 IRF8 CLEC9A XCR1 FLT3 ITGAX ITGAM CD1C FCER1A CLEC10A CD40 CD80 CD86 CD74 CIITA HLA-DRA HLA-DRB1 HLA-DPA1 HLA-DPB1 HLA-DQA1 HLA-DQB1 CCR7 LAMP3 RELB WDFY4 IL12A IL12B',
 'recruitment_chemokines_and_receptors':'CXCL9 CXCL10 CXCL11 CXCR3 CCL5 CCR5 XCL1 XCL2 CCL4 CCL19 CCL21 CXCL13 CXCR5 CXCL12 CXCR4 ACKR3 CCL2 CCR2 CCL22 CCR4 CCL20 CCR6',
 'expansion_IL15_and_memory_context':'IL15 IL15RA IL2RB IL2RG JAK1 JAK3 STAT5A STAT5B BCL2 MKI67 TCF7 IL7R IL7 IL2 IL2RA BCL2L1 BCL2L11',
 'Tcell_NK_presence_effector_context':'CD3D CD3E CD3G TRAC CD247 CD8A CD8B CD4 PTPRC NKG7 KLRD1 NCR1 NCR3 KLRK1 GNLY PRF1 GZMA GZMB FCGR3A TBX21 EOMES TRBC1 TRBC2 ZAP70 LCK CD2 CD69 CD27 CD28',
 'IFN_presentation_recognition':'IFNG IFNGR1 IFNGR2 JAK2 STAT1 IRF1 TAP1 TAP2 TAPBP B2M HLA-A HLA-B HLA-C PSMB8 PSMB9 NLRC5 HLA-E HLA-G PVR NECTIN2 CD274 PDCD1 PDCD1LG2 CTLA4 TIGIT HAVCR2 LAG3 TOX TNFRSF9 TNFRSF4 CD226 KLRC1',
 'entry_and_suppressive_context':'ICAM1 VCAM1 SELE SELP PECAM1 VWF KDR VEGFA ANGPT2 PLVAP FASLG TGFB1 TGFB2 TGFB3 THBS2 FAP CTHRC1 LRRC15 ITGA5 NT5E ENTPD1 ENPP1 ADORA2A ADORA2B PTGS2 PTGER4 AXL SPP1 CD44',
}
genes=sorted(set(' '.join(PANELS.values()).split()))
inputs=[INPUT/'all_genes_by_source.csv.gz',INPUT/'all_genes_GSE50760_primary18_TPM.csv.gz',INPUT/'all_genes_same_denominator_coding_TPM.csv.gz',RNA/'module_comparisons.csv.gz',INPUT/'protein_groups.csv.gz',INPUT/'reference_rank_comparisons.csv.gz',LIVER]
full=pd.read_csv(inputs[0],index_col='gene')
ref=pd.read_csv(inputs[1],index_col='gene')
coding=pd.read_csv(inputs[2],index_col='gene')
pg=pd.read_csv(inputs[4])
pr=pd.read_csv(inputs[5])
out=full.reindex(genes).copy()
out.insert(0,'descriptive_panels',[';'.join(k for k,v in PANELS.items() if g in v.split()) for g in genes])
for sample in ['Caris','Tempus']:
 out[sample+'_coding_TPM_same_denominator']=coding.reindex(genes)[sample+'_research']
for measure,mat in [('total_transcript_TPM',ref),('coding_TPM_same_denominator',coding.filter(regex='^SRR'))]:
 r=mat.reindex(genes)
 for name,q in [('q1',.25),('median',.5),('q3',.75)]:out['GSE50760_'+measure+'_'+name]=r.quantile(q,axis=1)
 for sample in ['Caris','Tempus']:
  vals=out[sample+'_research_TPM'] if measure=='total_transcript_TPM' else out[sample+'_coding_TPM_same_denominator']
  out[sample+'_GSE18_'+measure+'_n_lower']=r.lt(vals,axis=0).sum(axis=1).where(vals.notna() & r.notna().any(axis=1))
  out[sample+'_GSE18_'+measure+'_n_higher']=r.gt(vals,axis=0).sum(axis=1).where(vals.notna() & r.notna().any(axis=1))

# Protein gene assignment requires an exact single-gene group. Ambiguous groups
# are reported separately, never assigned as confirmed detection of each member.
proteinrows=[]
for g in genes:
 exact=pg[pg.gene.eq(g)]
 ambiguous=pg[pg.gene.fillna('').map(lambda x:g in x.split(';')) & ~pg.gene.eq(g)]
 row={'gene':g,'B7_single_gene_groups':len(exact),'B7_ambiguous_groups':len(ambiguous)}
 if len(exact):
  v=exact.sort_values(['high_support','intensity'],ascending=False).iloc[0]
  row.update({'B7_'+c:v[c] for c in ['protein_group','intensity','high_support','vendor_unique_peptides','n_unique_sequences','qc_status','fasta_gene_agrees']})
  row['B7_detection_status']='single_gene_group_present_higher_support' if v.high_support else 'single_gene_group_present_low_support'
 else:row['B7_detection_status']='ambiguous_group_only' if len(ambiguous) else 'not_reported_in_protein_group_export_not_biological_absence'
 for cohort in ['Astral_CRC','Komor_CRC']:
  v=pr[pr.gene.eq(g)&pr.reference_cohort.eq(cohort)]
  if len(v):row.update({'B7_'+cohort+'_'+c:v.iloc[0][c] for c in ['rank_shift_points','query_rank_pct_common_set','reference_median_rank_pct','n_reference_detected']})
 proteinrows.append(row)
out=out.join(pd.DataFrame(proteinrows).set_index('gene'))
out.to_csv(OUT/'recruitment_gene_by_dataset.csv',index_label='gene',float_format='%.8g')
liv=pd.read_csv(LIVER)
liv[liv.gene.isin(genes)].to_csv(OUT/'liver_selected_recruitment_celltypes.csv',index=False)
liv[['cell_type','n_cells']].drop_duplicates().to_csv(OUT/'liver_recovered_cell_inventory.csv',index=False)
mod=pd.read_csv(RNA/'module_comparisons.csv.gz')
mod[mod.module.str.contains('INTERFERON_GAMMA|effector|chemokine|recruit|cxcr3',case=False,regex=True)].to_csv(OUT/'existing_relevant_module_comparisons.csv',index=False)
(OUT/'descriptive_gene_panels.json').write_text(json.dumps({'purpose':'Mechanism-organised lookup lists, not signatures or clinical response scores. No aggregate panel scores calculated.','panels':{k:v.split() for k,v in PANELS.items()}},indent=2))
print('Recomputed156-gene recruitment lookup and selected-liver summaries.')

for p in OUT.glob('*.csv'):
    p.with_name(p.name+'.gz').write_bytes(gzip.compress(p.read_bytes(),9,mtime=0));p.unlink()
