#!/usr/bin/env python3
"""Optional full-matrix protein recipe; requiredfull_inputs are NOT bundled.
See provenance/upstream_sources.json and README.txt.
Descriptive stromal protein audit; no activity score or patient DE testing.

Input matrices retain their native units and biological independence. Common-set
ranks and marker ratios are sensitivity descriptions, not clinical percentiles.
"""
from pathlib import Path
import bisect, csv, gzip, hashlib, json, re
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'full_run/proteomics'
OUT.mkdir(parents=True,exist_ok=True)
SITE=ROOT/'full_inputs/public_site'
OLD=ROOT/'full_inputs/protein_reference'
SOURCE=SITE/'data/proteomics/b7_43_2026-10-29'
RAW=SOURCE/'raw/vendor_delivery/Match_result-X202SC26085414_F01_F001_B1_43'
SH=OLD/'raw/shared/analysis/refs'
T='FZPR260000422-1A.raw'
panel_definitions=json.loads((ROOT/'definitions/protein_module_definitions.json').read_text())
panels=panel_definitions['modules']
targets=sorted({g for p in panels for g in p['genes']} | set(panel_definitions.get('extra_target_genes',[])))
ALIASES={'CYR61':'CCN1','CTGF':'CCN2'}
used=[Path(__file__).resolve(),ROOT/'definitions/protein_module_definitions.json',ROOT/'definitions/curated_panels.json']
def read(path,**kwargs):
    used.append(path);return pd.read_csv(path,sep='\t',**kwargs)
def record_json(name,j): (OUT/name).write_text(json.dumps(j,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def safe(x):
    if isinstance(x,dict):return {str(k):safe(v) for k,v in x.items()}
    if isinstance(x,list):return [safe(v) for v in x]
    if isinstance(x,(np.integer,)):return int(x)
    if isinstance(x,(np.floating,)):return float(x) if np.isfinite(x) else None
    if isinstance(x,(np.bool_,)):return bool(x)
    return x
b=read(SOURCE/'analysis/protein_groups.tsv')
pg=read(RAW/'report.pg_matrix.tsv').set_index('Protein.Group')
pr=read(RAW/'report.pr_matrix.tsv.gz')
assert len(b)==7755 and len(pg)==7755
assert np.allclose(b.set_index('protein_group').intensity,pg[T].reindex(b.protein_group),equal_nan=True)
positive=pr[pr[T].notna()&(pr[T]>0)&(pr.Proteotypic==1)]
seq=positive.groupby(['Protein.Group','Stripped.Sequence'])[T].sum().reset_index()
counts=seq.groupby('Protein.Group').size()
assert all(int(r.n_unique_sequences)==int(counts.get(r.protein_group,0)) for _,r in b.iterrows())
strict=b[b.high_support].sort_values('intensity',ascending=False).drop_duplicates('gene').set_index('gene')
inclusive=b[b.detected&~b.multi_gene&(b.n_unique_sequences>=2)].sort_values('intensity',ascending=False).drop_duplicates('gene').set_index('gene')
assert len(strict)==6465 and len(inclusive)==6487
ast_raw=read(SH/'external/PXD073413/report1.pg_matrix.tsv')
acols=[c for c in ast_raw if '/' in c and 'sQC' not in c]
ast=ast_raw[ast_raw.Genes.notna()&~ast_raw.Genes.str.contains(';',na=False)].groupby('Genes')[acols].max().replace(0,np.nan)
ast.columns=[c.split('/')[-1].split('_')[0] for c in acols]
k=read(SH/'external/PXD012254/ProteinGroups_Normal_Adenoma_Cancer_Search.xls')
k=k[k['PG.Genes'].notna()&~k['PG.Genes'].str.contains(';',na=False)]
kw=k.pivot_table(index='PG.Genes',columns=['R.Condition','R.FileName'],values='PG.Quantity',aggfunc='max').replace(0,np.nan)
h=read(SH/'ms_tissue_sample_data.tsv');h=h[h.Tissue=='colon'].pivot_table(index='Gene name',columns='sample_name',values='Intensity',aggfunc='max').replace(0,np.nan)
refs={'Astral_CRC':ast,'Komor_CRC':kw['cancer'],'Komor_normal':kw['normal'],'HPA_colon_one_donor':h}
assert {n:v.shape[1] for n,v in refs.items()}=={'Astral_CRC':27,'Komor_CRC':30,'Komor_normal':19,'HPA_colon_one_donor':3}
baseline=read(SOURCE/'analysis/reference_rank_comparisons.tsv')
comparisons=[]; sensitivities=[]; reference_coverage=[]
for rn,ref in refs.items():
    for g in targets:
        reference_coverage.append({'gene':g,'reference':rn,'reference_sample_columns':ref.shape[1],
            'mapped_positive_reference_columns':int(ref.loc[g].notna().sum()) if g in ref.index else 0,
            'status':'mapped reference gene' if g in ref.index else 'no mapped gene in reference matrix'})
    for un,q in [('strict',strict),('inclusive_flagged_endogenous',inclusive)]:
        for threshold in [.5,.8,1.]:
            anchors=q.index.intersection(ref.index[ref.notna().mean(axis=1)>=threshold])
            qr=q.intensity.loc[anchors].rank(pct=True)*100
            rr=ref.loc[anchors].rank(pct=True)*100
            br=pd.DataFrame({'query_rank_pct':qr,'reference_median_rank_pct':rr.median(axis=1),'rank_shift_points':qr-rr.median(axis=1),
                'reference_q25_rank_pct':rr.quantile(.25,axis=1),'reference_q75_rank_pct':rr.quantile(.75,axis=1),
                'n_reference_detected':ref.loc[anchors].notna().sum(axis=1)})
            if un=='strict' and threshold==.8:
                old=baseline[baseline.reference_cohort==rn].set_index('gene')
                assert len(br)==len(old)
                assert np.allclose(br.rank_shift_points,old.rank_shift_points.reindex(br.index),atol=1e-8,equal_nan=True)
                for g in targets:
                    reason='eligible common-set rank' if g in br.index else ('not in strict patient support set' if g not in q.index else 'reference coverage below80% or gene unmapped')
                    row={'gene':g,'reference':rn,'status':reason,'anchors':len(anchors),'total_reference_columns':ref.shape[1]}
                    if g in br.index:row.update(br.loc[g].to_dict())
                    comparisons.append(row)
            for p in panels:
                z=br.reindex(p['genes']).dropna(subset=['rank_shift_points'])
                sensitivities.append({'panel':p['id'],'reference':rn,'universe':un,'minimum_reference_detection_fraction':threshold,'anchor_genes':len(anchors),
                    'panel_genes':len(p['genes']),'eligible_panel_genes':len(z),'genes_used':';'.join(z.index),
                    'median_rank_shift_points':z.rank_shift_points.median(),'q25_rank_shift':z.rank_shift_points.quantile(.25),
                    'q75_rank_shift':z.rank_shift_points.quantile(.75),'positive_rank_shifts':int((z.rank_shift_points>0).sum()),
                    'large_positive_shifts_gt25points':int((z.rank_shift_points>25).sum()),'large_negative_shifts_ltminus25points':int((z.rank_shift_points< -25).sum())})
pd.DataFrame(comparisons).to_csv(OUT/'gene_reference_comparisons.csv',index=False)
pd.DataFrame(reference_coverage).to_csv(OUT/'reference_gene_coverage.csv',index=False)
pd.DataFrame(sensitivities).to_csv(OUT/'pathway_rank_sensitivity.csv',index=False)
main_summary=pd.DataFrame(sensitivities).query("universe=='strict' and minimum_reference_detection_fraction==0.8").copy()
status_by_gene={}
target_rows=[]
for g in targets:
    hits=b[(b.gene.fillna('').apply(lambda v:g in v.split(';')))|(b.fasta_genes.fillna('').apply(lambda v:g in v.split(';') or any(a in v.split(';') for a,c in ALIASES.items() if c==g)))]
    if hits.empty:
        status='not assigned in delivered protein-group table; biological absence not established'
        target_rows.append({'query_gene':g,'status':status,'panels':';'.join(p['id'] for p in panels if g in p['genes'])})
    else:
        statuses=[]
        for _,r in hits.iterrows():
            status=('group listed but no positive patient quantity' if not r.detected else
                'detected ambiguous multi-gene assignment' if r.multi_gene else
                'detected with shared sequences only' if r.n_unique_sequences==0 else
                'detected single source-labelled sequence' if r.n_unique_sequences==1 else
                'detected >=2 sequences; contaminant-library flag retained' if r.contaminant_library_flag else
                'detected higher-support single-gene group')
            statuses.append(status)
            row={'query_gene':g,'status':status,'panels':';'.join(p['id'] for p in panels if g in p['genes']),**r.to_dict()}
            for rn in refs:
                z=next(x for x in comparisons if x['gene']==g and x['reference']==rn)
                row.update({rn+'_'+key:val for key,val in z.items() if key not in {'gene','reference'}})
            target_rows.append(row)
        status='; '.join(sorted(set(statuses)))
    status_by_gene[g]=status
pd.DataFrame(target_rows).to_csv(OUT/'stromal_gene_by_assay_protein.csv',index=False)
for i,row in main_summary.iterrows():
    p=next(x for x in panels if x['id']==row.panel); sub=b[b.gene.isin(p['genes'])]
    panel_rows=[r for r in target_rows if r['query_gene'] in p['genes']]
    main_summary.at[i,'patient_genes_any_assigned']=len({r['query_gene'] for r in panel_rows if not r['status'].startswith('not assigned')})
    main_summary.at[i,'patient_genes_positive_quantity']=len({r['query_gene'] for r in panel_rows if r.get('detected',False)})
    main_summary.at[i,'patient_genes_higher_support']=len(set(p['genes'])&set(strict.index))
    main_summary.at[i,'patient_genes_ambiguous_assignment']=len({r['query_gene'] for r in panel_rows if r.get('multi_gene',False)})
    main_summary.at[i,'patient_genes_only_single_source_peptide']=len({r['query_gene'] for r in panel_rows if r.get('n_unique_sequences')==1})
    main_summary.at[i,'patient_unassigned_genes']=';'.join(g for g in p['genes'] if status_by_gene[g].startswith('not assigned'))
main_summary.to_csv(OUT/'pathway_summary.csv',index=False)

# Descriptive scale-invariant marker ratios; not purity adjustment or activity.
denominators={'broad_ECM':['DCN','LUM','COL1A1','COL1A2','COL3A1','FN1','POSTN'],
    'epithelial':['EPCAM','CDH1','KRT8','KRT18','KRT19','KRT20','VIL1','LGALS4'],
    'smooth_muscle':['DES','CNN1','MYH11','TAGLN']}
ratio_targets='CTHRC1 FAP LRRC15 THBS2 SULF1 AEBP1 COL11A1 ITGA11 TGFB1 LTBP1 LTBP4 LRRC32 ITGAV ITGA5 ITGB1 DDR1 DDR2 LOX LOXL1 PLOD2 P4HA1 PTK2 YAP1 CCN1 CCN2 CXCL12 CD44 SPP1 LAIR1 ENTPD1 NT5E ENPP1'.split()
ratio_rows=[]
for rn,ref in refs.items():
    for pn,members in denominators.items():
        markers=[g for g in members if g in inclusive.index and g in ref.index and ref.loc[g].notna().mean()>=.8]
        if len(markers)<3:continue
        qm=np.log2(inclusive.loc[markers,'intensity']).mean()
        rm=np.log2(ref.loc[markers]).mean(axis=0).where(ref.loc[markers].notna().all(axis=0))
        for g in ratio_targets:
            if g not in inclusive.index or g not in ref.index or g in markers:continue
            rr=(np.log2(ref.loc[g])-rm).dropna()
            if len(rr)<2:continue
            qr=float(np.log2(inclusive.loc[g,'intensity'])-qm)
            ratio_rows.append({'gene':g,'reference':rn,'denominator':pn,'denominator_genes':';'.join(markers),'n_complete_reference_columns':len(rr),
                'query_log2_target_to_marker_geomean':qr,'reference_median_log2_ratio':rr.median(),
                'query_minus_reference_log2_ratio':qr-rr.median(),'fraction_reference_ratios_below_query':(rr<qr).mean()})
pd.DataFrame(ratio_rows).to_csv(OUT/'target_to_composition_marker_sensitivity.csv',index=False)
cptac=read(OLD/'analysis/cptac_within_cohort_context.tsv')
cptac[cptac.gene.isin(targets)].to_csv(OUT/'external_CPTAC_paired_context_NOT_patient_DE.csv',index=False)
ibaq=read(OLD/'analysis/public_ibaq_context.tsv')
ibaq[ibaq.gene_symbol.isin(targets)].to_csv(OUT/'external_public_iBAQ_NOT_comparable_patient_AU.csv',index=False)

# Expanded reference specificity for proteins carrying key mechanistic claims.
audit_targets='CTHRC1 FAP LRRC15 THBS2 SULF1 AEBP1 COL11A1 COL10A1 C1QTNF3 ITGA11 TGFB1 TGFB3 TGFBR2 LTBP1 LTBP4 LRRC32 ITGAV ITGA5 DDR1 DDR2 LOX LOXL1 LOXL3 LOXL4 PLOD2 P4HA1 PTK2 YAP1 CCN1 CCN2 CXCL12 CD44 LAIR1 SPP1 PDGFRB PDGFRA'.split()
fa=ROOT/'full_inputs/human_reviewed_isoforms_2026-11-16.fasta'
used.append(fa); records=[];header=None;s=[]
for line in fa.read_text().splitlines():
    if line.startswith('>'):
        if header is not None:records.append((header,''.join(s)))
        header=line;s=[]
    else:s.append(line.strip())
if header is not None:records.append((header,''.join(s)))
parsed=[];starts=[];parts=[];offset=0
for h,s in records:
    accession=h.split('|')[1];m=re.search(r'\bGN=(\S+)',h);gene=m.group(1) if m else 'UNKNOWN:'+accession
    gene=ALIASES.get(gene,gene);parsed.append((accession,gene,s));starts.append(offset);parts.append(s+'|');offset+=len(s)+1
joined=''.join(parts);il_joined=joined.replace('I','L')
mapping=[];audit_summary=[]
for g in audit_targets:
    hits=b[(b.gene==g)&~b.multi_gene]
    if hits.empty:continue
    row=hits.sort_values('intensity',ascending=False).iloc[0];peptides=seq[seq['Protein.Group']==row.protein_group]
    seq_results=[]
    for _,prrow in peptides.iterrows():
        peptide=prrow['Stripped.Sequence'];start=0;matches=[];q=peptide.replace('I','L')
        while (found:=il_joined.find(q,start))>=0:
            index=bisect.bisect_right(starts,found)-1;accession,gene,protein=parsed[index]
            pos=found-starts[index];end=pos+len(peptide);native=protein[pos:end]
            assert len(native)==len(peptide)
            nterm=(pos==0 or (pos==1 and protein[0]=='M') or (protein[pos-1] in 'KR' and protein[pos]!='P'))
            cterm=(end==len(protein) or (protein[end-1] in 'KR' and protein[end]!='P'))
            missed=sum(native[i] in 'KR' and native[i+1]!='P' for i in range(len(native)-1))
            match={'target_gene':g,'protein_group':row.protein_group,'peptide':peptide,'patient_summed_precursor_signal_AU':prrow[T],
                'matched_accession':accession,'matched_gene':gene,'exact_match':native==peptide,
                'peptide_start_1based':pos+1,'peptide_end_1based':end,
                'fully_tryptic_up_to2_missed':nterm and cterm and missed<=2,'flanks':protein[max(0,pos-2):pos]+'.'+native+'.'+protein[end:end+2]}
            matches.append(match);mapping.append(match);start=found+1
        exact={x['matched_gene'] for x in matches if x['exact_match']};allgenes={x['matched_gene'] for x in matches};tryptic={x['matched_gene'] for x in matches if x['fully_tryptic_up_to2_missed']}
        seq_results.append({'exact_gene_specific':exact=={g},'IL_substring_gene_specific':allgenes=={g},'IL_fully_tryptic_gene_specific':tryptic=={g}})
    audit_summary.append({'gene':g,'protein_group':row.protein_group,'source_labelled_sequences':len(peptides),
        **{k:sum(x[k] for x in seq_results) for k in ['exact_gene_specific','IL_substring_gene_specific','IL_fully_tryptic_gene_specific']}})
pd.DataFrame(mapping).to_csv(OUT/'critical_protein_peptide_mapping.csv',index=False)
pd.DataFrame(audit_summary).to_csv(OUT/'critical_protein_peptide_specificity.csv',index=False)
summary={'date':'2026-11-16','patient_biological_samples':1,'specimen':'B7 archival treated rectal resection, 22 October 2024; exact aliquot and tumour fraction unresolved; not current node',
    'genes_queried':len(targets),'panels':len(panels),'positive_patient_groups':int(b.detected.sum()),'all_raw_pg_quantities_agree':True,'all_source_proteotypic_counts_agree':True,
    'baseline_reference_rank_reproduction':'all four cohorts agree with prior analysis at strict 80% coverage',
    'reference_columns':{k:v.shape[1] for k,v in refs.items()},'specificity_database_records':len(records),'critical_targets_audited':len(audit_summary),'critical_sequences_audited':sum(x['source_labelled_sequences'] for x in audit_summary),
    'limits':['One historical mixed patient specimen, no biological replication or matched normal.','No raw-spectrum re-search, q-value reconstruction, clinical protein percentile, pSMAD/pFAK or spatial activity readout.','Curated panels are descriptive and include overlapping/opposing components; not validated pathway activation scores.','Komor reference runs are not independently verified donors; HPA3measurements represent one donor.','Non-detection and absence from a selected export do not establish biological absence.','Peptide specificity is scoped to the reviewed human reference; proteoforms, variants and raw spectral correctness remain unestablished.'],
    'sources':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(set(used))]}
record_json('analysis_manifest.json',safe(summary))
print(json.dumps({k:v for k,v in summary.items() if k not in ['sources','limits']},indent=2))
