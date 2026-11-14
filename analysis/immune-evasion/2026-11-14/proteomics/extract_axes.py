#!/usr/bin/env python3
"""Extract targeted immune-axis evidence, retaining measured group identity and limitations.
No raw-spectrum re-search, imputation, fold changes or clinical threshold inference.
Run from any directory: python3 proteomics/extract_axes.py
"""
import csv, json, hashlib, gzip
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'inputs/proteomics'
OUT = Path(__file__).resolve().parent
ALIASES = {'CTGF':'CCN2','CYR61':'CCN1','TMEM173':'STING1','cGAS':'MB21D1'}
AXES = {
 'antigen_IFN': 'B2M HLA-A HLA-B HLA-C HLA-E HLA-F HLA-G TAP1 TAP2 TAPBP CALR CANX ERAP1 ERAP2 PSMB8 PSMB9 PSMB10 NLRC5 IRF1 IRF2 IFNGR1 IFNGR2 JAK1 JAK2 STAT1 STAT2 IRF9 IFNG CXCL9 CXCL10 CXCL11 HLA-DRA HLA-DRB1 CD74 CIITA',
 'PTPN_APC_WNT': 'PTPN1 PTPN2 PTPN12 PTPN13 APC CTNNB1 AXIN1 AXIN2 DVL1 GSK3B PTEN NBR1 SDC4 PRKCA',
 'CAF_TGF_ECM': 'FAP LRRC15 PDGFRA PDGFRB ACTA2 TAGLN CNN1 MYH11 DES DCN LUM COL1A1 COL1A2 COL3A1 COL11A1 COL12A1 FN1 POSTN CTHRC1 THBS1 THBS2 TNC TGFBI TGFB1 TGFB2 TGFB3 TGFBR1 TGFBR2 SMAD2 SMAD3 SMAD4 SERPINE1 LOX LOXL2 ITGA5 ITGB1 MMP2 MMP9 MMP14 DPP4 YAP1 CTGF CYR61',
 'myeloid_state_recruitment': 'SPP1 TREM2 TYROBP LST1 AIF1 CD68 CD163 MRC1 CSF1 CSF1R CCL2 CCR2 CXCL8 CXCR2 S100A8 S100A9 ARG1 NOS2 IL10 IL10RA IL6 IL6R IL6ST STAT3 SLPI C3 C3AR1 C5 C5AR1 MIF CD36 LILRB1 LILRB2 SIGLEC10',
 'phagocytosis_checkpoints': 'CD47 SIRPA CD24 CALR CD274 PDCD1LG2 VSIR PVR NECTIN2 LGALS1 LGALS3 LGALS9 HAVCR2 LAG3 TIGIT PDCD1 CTLA4 CD276 VTCN1 HHLA2 CD80 CD86 CD40 CD40LG CD70 TNFRSF9',
 'adenosine_metabolism_hypoxia': 'NT5E ENTPD1 ENPP1 ADORA2A ADORA2B ADA ADK HIF1A EPAS1 CA9 CA12 SLC2A1 SLC2A3 LDHA LDHB SLC16A1 SLC16A3 HK2 PKM PDK1 IDO1 IDO2 TDO2 AHR SLC7A11 GPX4 NFE2L2 KEAP1 NQO1 HMOX1',
 'cGAS_STING': 'MB21D1 STING1 TBK1 IRF3 IKBKE TREX1 IFNB1 CCL5',
 'PGE2_integrin': 'PTGS1 PTGS2 PTGES PTGER2 PTGER4 ITGB8 ITGAV',
 'vascular': 'VEGFA VEGFB VEGFC FLT1 KDR FLT4 ANGPT1 ANGPT2 TEK ENG PECAM1 VWF EMCN PLVAP ICAM1 VCAM1',
 'effector_priming': 'PTPRC CD3D CD3E CD3G CD4 CD8A CD8B NKG7 GNLY GZMA GZMB PRF1 NCR1 KLRD1 KLRK1 KLRC1 FCGR3A FCGR2A FCGR2B FCER1G ZAP70 LCK CD247 TRAC CD19 MS4A1 FOXP3 IL2RA IL7R TCF7 BATF3 CLEC9A XCR1 FLT3 CD1C FCER1A CCL19 CCL21 CXCL13',
 'target_bypass': 'AXL MERTK GAS6 ROR1 CDH17 PTK7 EGFR MET CEACAM5 TACSTD2 EPCAM ERBB2 FOLR1 CLDN18',
 'composition': 'KRT8 KRT18 KRT19 KRT20 CDH1 VIL1 LGALS4 TSPAN8 ALB HBB ACTG2 ACTA1 ACTB ACTG1'
}
def readtsv(rel):
 with (SOURCE/rel).open() as f: return list(csv.DictReader(f,delimiter='\t'))
groups=readtsv('protein_groups.tsv')
raw=readtsv('report.pg_matrix.tsv')
raw_map={r['Protein.Group']:r for r in raw}
refs=readtsv('reference_rank_comparisons.tsv')
refmap={(r['gene'],r['reference_cohort']):r for r in refs}
precursor_path='report.pr_matrix.tsv.gz'
unique_by_group={}
with gzip.open(SOURCE/precursor_path,'rt') as f:
 for p in csv.DictReader(f,delimiter='\t'):
  if p['Proteotypic']=='1' and p['FZPR260000422-1A.raw'] and float(p['FZPR260000422-1A.raw'])>0:
   unique_by_group.setdefault(p['Protein.Group'],set()).add(p['Stripped.Sequence'])
gene_axes={}
for axis,text in AXES.items():
 for gene in text.split(): gene_axes.setdefault(gene,[]).append(axis)
rows=[]
raw_checks=[]
for gene,axes in gene_axes.items():
 lookup_gene=ALIASES.get(gene,gene)
 matches=[r for r in groups if lookup_gene in r['gene'].split(';') or lookup_gene in r['fasta_genes'].split(';')]
 if not matches:
  rows.append({'query_gene':gene,'axes':';'.join(axes),'measurement_status':'not detected in delivered protein-group table; not biological absence'})
 for r in matches:
  x={'query_gene':gene,'lookup_gene':lookup_gene,'axes':';'.join(axes),'measurement_status':('detected' if r['detected']=='True' else 'group listed but patient signal missing'),**r}
  # Preserve HPA and FASTA disagreement rather than silently renaming genes.
  x['exact_single_gene_match'] = r['gene']==lookup_gene and r['multi_gene']=='False'
  x['raw_run422_agrees']=r['intensity']==raw_map[r['protein_group']]['FZPR260000422-1A.raw']
  x['recounted_unique_sequences']=len(unique_by_group.get(r['protein_group'],set()))
  x['unique_count_agrees']=x['recounted_unique_sequences']==int(r['n_unique_sequences'])
  raw_checks.append(x['raw_run422_agrees'])
  for ref in ['Astral_CRC','Komor_CRC','Komor_normal','HPA_colon_one_donor']:
   rr=refmap.get((lookup_gene,ref),{}) if x['exact_single_gene_match'] else {}
   for key in ['rank_shift_points','n_reference_detected','query_rank_pct_common_set','reference_median_rank_pct']:
    x[ref+'_'+key]=rr.get(key,'')
  rows.append(x)
fields=list(dict.fromkeys(k for r in rows for k in r))
with (OUT/'immune_axes_proteomics.csv').open('w') as f:
 w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
sources=['protein_groups.tsv','reference_rank_comparisons.tsv','report.pg_matrix.tsv',precursor_path]
manifest={
 'analysis_date':'2026-11-14','specimen':'B7_43; archival treated rectal low anterior resection 22 October 2024; Block B7. Exact analytical aliquot chain unresolved. Not recent node.',
 'raw_patient_run':'FZPR260000422-1A.raw','unknown_run_excluded':'FZPR260000423-1A.raw',
 'requested_gene_count':len(gene_axes),'output_rows':len(rows),'raw_signal_checks':len(raw_checks),'raw_signal_checks_all_pass':all(raw_checks),'unique_sequence_recounts_all_pass':all(r.get('unique_count_agrees',True) for r in rows),'explicit_gene_aliases':ALIASES,
 'sources':[{'path':str((SOURCE/p).relative_to(ROOT)),'sha256':hashlib.sha256((SOURCE/p).read_bytes()).hexdigest()} for p in sources],
 'limits':['Single archival patient biological sample; no raw-spectrum re-search or reconstructed identification FDR.', 'Arbitrary protein-group signal is not molecule count, surface density or per-cell expression.', 'Within-proteome ranks and cross-study rank shifts are not assay-matched CRC population percentiles.', 'No phosphoproteomics: STAT/TGF-beta pathway activation cannot be established from total protein.', 'No surface assay or immunopeptidomics: functional HLA presentation is not established.', 'Non-detection cannot establish protein or cell-type absence.', 'Unknown run423 and public HPA one-donor control are not matched patient normals.']}
(OUT/'extraction_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k not in ['sources','limits']},indent=2))
