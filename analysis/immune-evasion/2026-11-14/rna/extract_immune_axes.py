#!/usr/bin/env python3
"""Re-extract immune-axis expression from preserved source tables (no new alignment).

Standard library only. Run from any directory; inputs resolve relative to this package. Values keep assay/specimen-specific
units; no cross-platform pooled percentiles or clinical predictions are computed.
"""
import csv, json, hashlib, math, statistics
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
INPUT = ROOT/'inputs/rna'
AXES = {
 'recognition_interferon': 'IFNG IFNGR1 IFNGR2 JAK1 JAK2 STAT1 STAT2 IRF1 IRF2 IRF9 SOCS1 SOCS3 PTPN1 PTPN2 PTPN12 PTPN13 B2M HLA-A HLA-B HLA-C HLA-E HLA-F HLA-G TAP1 TAP2 TAPBP PSMB8 PSMB9 PSMB10 NLRC5 ERAP1 ERAP2 CALR CANX PDIA3 CIITA HLA-DRA HLA-DRB1 HLA-DPA1 HLA-DPB1 HLA-DQA1 HLA-DQB1 CD74 CXCL9 CXCL10 CXCL11',
 'oncogenic_innate_epigenetic': 'APC CTNNB1 AXIN2 MYC PTEN PIK3CA AKT1 MTOR TP53 SMAD4 KRAS NRAS BRAF NFE2L2 KEAP1 NBR1 SQSTM1 SLC7A11 GPX4 NQO1 HMOX1 TRIM28 SETDB1 EZH2 DNMT1 DNMT3A DNMT3B HDAC1 HDAC2 CGAS TMEM173 IFIH1 DDX58 MAVS TBK1 IRF3 IFNB1 ADAR',
 'stroma_TGF_CXCL_ECM': 'TGFB1 TGFB2 TGFB3 TGFBR1 TGFBR2 SMAD2 SMAD3 SMAD4 SMAD7 SERPINE1 CTGF FAP ACTA2 PDGFRA PDGFRB COL1A1 COL1A2 COL3A1 COL5A1 COL6A1 COL11A1 FN1 TNC POSTN CXCL12 CXCR4 ACKR3 IL6 LIF IL11 LIFR IL6R IL6ST JAK2 STAT3 ITGAV ITGB6 ITGB8 LTBP1 LTBP2 THBS1 THBS2 LOX LOXL2 DDR1 DDR2 LAIR1 CD44 SDC1 SDC4',
 'myeloid_phagocytosis': 'CSF1 CSF1R IL34 CD68 CD163 MRC1 MSR1 LYZ SPP1 TREM2 APOE C1QA C1QB C1QC LGALS3 LGALS9 TYROBP FCER1G AXL MERTK TYRO3 GAS6 PROS1 CCL2 CCR2 CCL5 CCR5 CXCL1 CXCL2 CXCL3 CXCL5 CXCL6 CXCL8 CXCR1 CXCR2 S100A8 S100A9 ARG1 ARG2 NOS2 IL1B IL10 IL10RA IL10RB TGFB1 CD47 SIRPA CD24 SIGLEC10 VSIR C10orf54 LILRB1 LILRB2 CLEC4A MARCO',
 'metabolic_vascular': 'ENTPD1 NT5E ADORA2A ADORA2B CD38 ENPP1 ADA ADK IDO1 IDO2 TDO2 KYNU KMO AHR ARNT HIF1A EPAS1 VEGFA VEGFB VEGFC VEGFD KDR FLT1 FLT4 PGF ANGPT1 ANGPT2 TEK PECAM1 VWF PLVAP CA9 SLC2A1 HK2 PFKFB3 LDHA LDHB SLC16A1 SLC16A3 SLC1A5 GLS GLUL FASN CD36 CPT1A ACAT1 PTGS2 PTGER2 PTGER4',
 'effectors_checkpoints_priming': 'CD3D CD3E CD4 CD8A CD8B NKG7 NCR1 KLRD1 KLRK1 KLRC1 KLRC2 FCGR3A GZMA GZMB GZMK PRF1 GNLY TBX21 EOMES TCF7 TOX PDCD1 CD274 PDCD1LG2 CTLA4 TIGIT CD226 PVR NECTIN2 PVRL2 LAG3 FGL1 HAVCR2 CEACAM1 BTLA TNFRSF14 CD160 CD276 VTCN1 HHLA2 TMIGD2 TNFRSF9 TNFRSF4 ICOS ICOSLG IL2 IL2RA IL2RB IL2RG IL7 IL7R IL15 IL15RA IL21 FOXP3 IKZF2 CCR8 CCL22 CCL17 ITGAE ITGA1 CXCR3 CXCR6 BATF3 XCR1 CLEC9A CD1C ITGAX FLT3LG CD80 CD86 CD40 CD40LG CCL19 CCL21 CXCL13 MS4A1 CD79A TNFRSF17',
 'surface_bypass': 'CEACAM5 EGFR ERBB2 MET TACSTD2 EPCAM ROR1 ROR2 B7H6 NCR3LG1 MICA MICB ULBP1 ULBP2 ULBP3 MSLN MUC1 MUC16 FOLR1 CLDN18 CLDN6 CLDN4 PRAME MAGEA4 CTAG1B'
}
ALIASES = {'CTGF':'CCN2','TMEM173':'STING1','C10orf54':'VSIR','PVRL2':'NECTIN2','B7H6':'NCR3LG1'}
AXES = {k:list(dict.fromkeys(ALIASES.get(g,g) for g in v.split())) for k,v in AXES.items()}
AXES['stroma_TGF_CXCL_ECM'].append('TGFBI')
GENES = sorted(set(g for v in AXES.values() for g in v))
MEMBERSHIPS = {g:';'.join(k for k,v in AXES.items() if g in v) for g in GENES}
sources = {}
def read(path, sep=','):
    p=Path(path); sources[str(p.relative_to(ROOT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
    return list(csv.DictReader(p.open(encoding='utf-8-sig'),delimiter=sep))
def num(x):
    try:return float(x)
    except (ValueError,TypeError):return None
def write_csv(name, rows, fields=None):
    fields=fields or list(rows[0]);
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
    return len(rows)
def quantile(a,q):
    a=sorted(a);p=(len(a)-1)*q;i=int(p);return a[i]+(a[min(i+1,len(a)-1)]-a[i])*(p-i)

bg_path=INPUT/'kandinsky_gene_explorer.csv'
bg={r['Gene Symbol']:r for r in read(bg_path)}
sample_data={s:{r['gene_symbol']:r for r in read(INPUT/f'{s}_all_gene_abundance.csv')} for s in ['caris','tempus']}
old_caris={r['gene']:r for r in read(INPUT/'caris_clinical_percentiles.tsv','\t')}
new_caris={r['gene']:r for r in read(INPUT/'gene_percentiles.csv')}
coding={r['gene']:r for r in read(INPUT/'transcript_type_breakdown.csv')}
cell=read(INPUT/'liver_valius_celltype_expression_summary.csv')
tumor={r['gene']:r for r in read(INPUT/'liver_valius_target_expression_summary.csv')}
blood={r['Gene']:r for r in read(INPUT/'caris_assure_cell_free_rna_expression_summary.csv')}
unresolved={r['Gene']:r for r in read(INPUT/'additional_caris_expression_provenance_unresolved.csv')}

wide=[]
for g in GENES:
    b=bg.get(g,{});c=new_caris.get(g,{});old=old_caris.get(g,{});t=tumor.get(g,{})
    row={'gene':g,'axes':MEMBERSHIPS[g],
    'Caris_primary_provider_CRC_percentile':c.get('percentile',old.get('percentile_in_cancer_type','')),
    'Caris_percentile_source':('2026-11-07 supplement' if c else 'primary clinical report' if old else 'not supplied'),
    'Caris_primary_provider_total_TPM':c.get('query_tpm',''),
    'Caris_primary_provider_coding_TPM_share':coding.get(g,{}).get('protein_coding_share',''),
    'Caris_primary_research_total_TPM':sample_data['caris'].get(g,{}).get('TPM',''),
    'Tempus_resection_research_total_TPM':sample_data['tempus'].get(g,{}).get('TPM',''),
    'BostonGene_resection_log2_TPM_plus1':b.get('RNA Expression — BostonGene log2(TPM+1)',''),
    'BostonGene_resection_CRC_percentile':b.get('Percentile: BostonGene Colorectal Adenocarcinoma',''),
    'Valius_liver_malignant_pct_RNA_detected':t.get('tumor_pct',''),
    'Valius_liver_nonmalignant_pct_RNA_detected':t.get('stroma_pct',''),
    'blood_cellfree_RNA_TPM_NOT_TUMOUR':blood.get(g,{}).get('TPM',''),
    'Caris_buffycoat_RNA_TPM_NOT_TUMOUR':unresolved.get(g,{}).get('TPM',''),
    'Valius_pipeline_unresolved_log2_TPM_plus1':b.get('RNA Expression — Valius Pipeline (log2(TPM+1))','')}
    wide.append(row)
write_csv('immune_axis_expression_matrix.csv',wide)
CORE_GENES=['ACTA2', 'ADORA2A', 'ADORA2B', 'AXL', 'B2M', 'CCL2', 'CD163', 'CGAS', 'CSF1', 'CSF1R', 'CTLA4', 'CXCL12', 'CXCL8', 'ENPP1', 'ENTPD1', 'FAP', 'FOXP3', 'GAS6', 'HLA-A', 'HLA-B', 'HLA-C', 'HLA-E', 'HLA-F', 'HLA-G', 'IKZF2', 'IL6', 'IL6R', 'IL6ST', 'IRF1', 'ITGAV', 'ITGB6', 'ITGB8', 'MERTK', 'MRC1', 'NLRC5', 'NT5E', 'PDCD1', 'PSMB8', 'PSMB9', 'PTGER4', 'PTGS2', 'PTPN1', 'PTPN12', 'PTPN13', 'PTPN2', 'SPP1', 'STAT1', 'STAT3', 'STING1', 'TAP1', 'TAP2', 'TCF7', 'TGFB1', 'TGFB2', 'TGFB3', 'TGFBI', 'TGFBR1', 'TGFBR2', 'TIGIT', 'TNC', 'TOX', 'TREM2']
CORE_FIELDS=['gene', 'Caris_primary_provider_CRC_percentile', 'Caris_primary_research_total_TPM', 'Tempus_resection_research_total_TPM', 'BostonGene_resection_log2_TPM_plus1', 'BostonGene_resection_CRC_percentile', 'Valius_liver_malignant_pct_RNA_detected']
write_csv('core_gene_table.csv',[{k:r[k] for k in CORE_FIELDS} for r in wide if r['gene'] in CORE_GENES],CORE_FIELDS)
write_csv('liver_immune_axis_celltypes.csv',[r for r in cell if r['gene'] in GENES])

# Same-computational-pipeline public context is exploratory, not assay matched.
ref_by_gene=defaultdict(list); refrows=[]
id_to_genes=defaultdict(list)
for g in GENES:
    if g in sample_data['caris']:id_to_genes[sample_data['caris'][g]['gene_id']].append(g)
for run in range(975551,975569):
    name=f'SRR{run}'
    for r in read(INPUT/f'gse50760/{name}.tsv','\t'):
        for g in id_to_genes.get(r['Name'],[]):
            val=float(r['TPM']);ref_by_gene[g].append(val);refrows.append({'gene':g,'run':name,'TPM':val})
write_csv('gse50760_18_primary_immune_axis_TPM.csv',refrows)
comparisons=[]
for g,vals in ref_by_gene.items():
    assert len(vals)==18
    for sample in ['caris','tempus']:
        value=float(sample_data[sample][g]['TPM'])
        comparisons.append({'gene':g,'sample':sample,'sample_TPM':value,'reference_n':18,
        'reference_median_TPM':statistics.median(vals),'reference_q1_TPM':quantile(vals,.25),'reference_q3_TPM':quantile(vals,.75),
        'reference_n_lower':sum(v<value for v in vals),'reference_n_equal':sum(v==value for v in vals),
        'reference_n_higher':sum(v>value for v in vals),
        'sample_above_reference_q3':value>quantile(vals,.75),'sample_below_reference_q1':value<quantile(vals,.25),
        'interpretation':'Exploratory cross-assay bulk comparison; not a clinical percentile, tumour-cell value or differential-expression test'})
write_csv('gse50760_exploratory_context.csv',comparisons)

# Preserve the validated five-gene coding/full-transcript comparison, without pooling cohorts.
original5=read(INPUT/'patient_vs_cohort.csv')
assert {int(r['cohort_n']) for r in original5}=={18}
write_csv('five_gene_existing_gse_comparison.csv',original5)
write_csv('caris_new_provider_percentiles.csv',list(new_caris.values()))
write_csv('caris_new_transcript_types.csv',list(coding.values()))

variants=read(INPUT/'variants.csv')
write_csv('selected_immune_axis_variant_candidates_NOT_CLINICAL_VALIDATION.csv',[r for r in variants if any(r['gene_label'].split('_')[0].split(';')[0]==g for g in GENES)])
portal_variants=read(INPUT/'kandinsky_somatic_variants.csv')
write_csv('portal_somatic_candidates_original.csv',portal_variants)

manifest={'date':'2026-11-14','script':str(Path(__file__).resolve().relative_to(ROOT)), 'gene_count':len(GENES),'axes':AXES,'gene_aliases_resolved':ALIASES,'sources':sources,
 'coverage':{'BostonGene_CRC_percentiles':sum(num(r['BostonGene_resection_CRC_percentile']) is not None for r in wide),
 'Caris_provider_percentiles':sum(num(r['Caris_primary_provider_CRC_percentile']) is not None for r in wide),
 'Valius_liver_genes_in_selected_celltype_export':len(set(r['gene'] for r in cell if r['gene'] in GENES)),
 'GSE_context_genes':len(ref_by_gene)},
 'limitations':['Re-extraction from existing quantification and provider data; no new alignment or variant calling.','Exploratory analyst-selected marker panel, not a validated pathway score; no multiple-testing inference.','Bulk RNA conflates malignant, immune and stromal cells. Each assay keeps its own specimen and reference.','Caris primary March2024; Tempus/BostonGene treated resection October2024; Valius single cell liverOctober2024. None establishes October2026 nodal biology.','BostonGene CRC percentiles are vendor ranks; no percentile imputed for blank entries.','Caris new total TPM includes noncoding isoforms; coding fractions lack an assay-matched coding reference.','GSE18 uses same Salmon computational pipeline but different laboratory/library preparation; cohort ratios/ranks are exploratory and do not supersede Caris provider percentiles.','Single-cell summaries cover selected101 targets; absent row is not no expression. RNA-positive fractions are not membrane-protein staining.','Blood cfRNA and buffy-coat RNA (legacy filename additional_caris_expression_provenance_unresolved.csv; provider clarification19October2026) are retained separately and excluded from tissue hypotheses. Valius-pipeline bulk specimen remains unresolved.','Portal mutation/copy-number annotations do not override low-purity source-report caveats. No new candidate validation performed.']}
(OUT/'extraction_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({k:v for k,v in manifest.items() if k in ['gene_count','coverage']},indent=2))
