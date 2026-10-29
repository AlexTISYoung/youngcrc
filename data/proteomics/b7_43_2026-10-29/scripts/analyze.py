"""Independent descriptive reanalysis. No patient differential-expression p values.
Run from any directory with Python, pandas, scipy, numpy, openpyxl and matplotlib.
"""
from pathlib import Path
import json, re, hashlib, sys
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'raw/vendor_delivery'; SH=ROOT/'raw/shared/analysis'; OUT=ROOT/'analysis'
OUT.mkdir(exist_ok=True)
PG=pd.read_csv(next(RAW.rglob('report.pg_matrix.tsv')),sep='\t')
PR=pd.read_csv(next(RAW.rglob('report.pr_matrix.tsv')),sep='\t')
T,C=PG.columns[1:]
PP=pd.read_csv(next(RAW.rglob('Pro_Pep.protein.tsv')),sep='\t')
assert PG['Protein.Group'].is_unique
MP=pd.read_csv(SH/'out/id_mapping.tsv',sep='\t').set_index('protein_group')
# Verify the supplied mapping keys and abundances, then use its HPA symbol/Ensembl
# fields only. Independently check mapped genes against the actual search FASTA.
assert set(PG['Protein.Group'])==set(MP.index)
FA={}; gene=None; accession=None
for line in next(RAW.rglob('*.fasta.txt')).read_text().splitlines():
    if line.startswith('>'):
        accession=line.split('|')[1]; m=re.search(r' GN=(\S+)',line)
        FA[accession]={'gene':m.group(1) if m else None,'seq':''}
    elif accession: FA[accession]['seq']+=line.strip()
CONT={line.split('|')[1].replace('Cont_','').split('-')[0] for line in (SH/'refs/Universal_Contaminants_0602.fasta.txt').read_text().splitlines() if line.startswith('>')}
base=PG.rename(columns={T:'intensity',C:'run423_intensity','Protein.Group':'protein_group'}).set_index('protein_group')
assert np.allclose(base.intensity,MP.loc[base.index,'intensity_422'],equal_nan=True)
for col in ['leading_accession','gene_hpa','ensembl','map_status']:
    base[col]=MP.loc[base.index,col]
base['gene']=base.gene_hpa
base['multi_gene']=base.gene.fillna('').str.contains(';')|base.gene.isna()
base['fasta_genes']=[';'.join(sorted({FA[a]['gene'] for a in g.split(';') if a in FA and FA[a]['gene']})) for g in base.index]
base['fasta_gene_agrees']=[g in fg.split(';') if pd.notna(g) and ';' not in g else False for g,fg in zip(base.gene,base.fasta_genes)]
base['contaminant_library_flag']=[any(a.split('-')[0] in CONT for a in g.split(';')) for g in base.index]
pp=PP.set_index('Protein')
for dest,source in [('vendor_unique_peptides','B7_43_uniqCount'),('vendor_peptides','B7_43_pepCount'),('coverage_pct','Coverage [%]'),('protein_length','AAs'),('description','Description')]:
    base[dest]=base.leading_accession.map(pp[source])
present=PR[PR[T].notna()&(PR[T]>0)].copy()
seq=present.groupby(['Protein.Group','Stripped.Sequence'])[T].sum().reset_index()
unique=present[present.Proteotypic==1].groupby(['Protein.Group','Stripped.Sequence'])[T].sum().reset_index()
base['n_peptide_sequences']=seq.groupby('Protein.Group').size()
base['n_unique_sequences']=unique.groupby('Protein.Group').size()
base[['n_peptide_sequences','n_unique_sequences']]=base[['n_peptide_sequences','n_unique_sequences']].fillna(0).astype(int)
top3=unique.sort_values(T,ascending=False).groupby('Protein.Group').head(3).groupby('Protein.Group')[T].mean()
base['unique_top3_mean_signal']=top3.where(unique.groupby('Protein.Group').size()>=3)
base['detected']=base.intensity.notna()&(base.intensity>0)
base['high_support']=base.detected&~base.multi_gene&~base.contaminant_library_flag&(base.n_unique_sequences>=2)
base['signal_percentile_all_detected']=base.intensity.where(base.detected).rank(pct=True)*100
base['signal_percentile_high_support']=base.intensity.where(base.high_support).rank(pct=True)*100
base['top3_signal_percentile']=base.unique_top3_mean_signal.where(base.high_support).rank(pct=True)*100
base['rank_high_to_low']=base.intensity.where(base.detected).rank(ascending=False,method='min')
base['qc_status']=np.select([~base.detected,base.multi_gene,base.contaminant_library_flag,base.n_unique_sequences==0,base.n_unique_sequences==1],['not quantified','ambiguous gene assignment','contaminant-library flag (may be biological)','shared peptides only','single unique sequence'],default='higher support: >=2 unique sequences')
base.to_csv(OUT/'protein_groups.tsv',sep='\t',index=True)
unique.rename(columns={T:'summed_charge_and_modification_state_signal'}).to_csv(OUT/'unique_peptide_sequences.tsv',sep='\t',index=False)
# Do not combine ambiguous groups across different genes. If multiple qualifying
# groups map to the same gene, retain the largest signal and report multiplicity.
valid=base[base.high_support].sort_values('intensity',ascending=False).copy()
valid['qualifying_groups_for_gene']=valid.groupby('gene').gene.transform('size')
genes=valid.drop_duplicates('gene').set_index('gene')
genes.to_csv(OUT/'high_support_gene_quantification.tsv',sep='\t')
q=genes.intensity

def single(df,gcol,cols):
    d=df[df[gcol].notna()&~df[gcol].astype(str).str.contains(';')]
    return d.groupby(gcol)[cols].max().replace(0,np.nan)

ast=pd.read_csv(SH/'refs/external/PXD073413/report1.pg_matrix.tsv',sep='\t')
acols=[c for c in ast if '/' in c and 'sQC' not in c]
AST=single(ast,'Genes',acols); AST.columns=[c.split('/')[-1].split('_')[0] for c in acols]
k=pd.read_csv(SH/'refs/external/PXD012254/ProteinGroups_Normal_Adenoma_Cancer_Search.tsv',sep='\t')
k=k[k['PG.Genes'].notna()&~k['PG.Genes'].fillna('').str.contains(';')]
kw=k.pivot_table(index='PG.Genes',columns=['R.Condition','R.FileName'],values='PG.Quantity',aggfunc='max').replace(0,np.nan)
ms=pd.read_csv(SH/'refs/ms_tissue_sample_data.tsv',sep='\t'); colon=ms[ms.Tissue=='colon']
HPA=colon.pivot_table(index='Gene name',columns='sample_name',values='Intensity',aggfunc='max').replace(0,np.nan)
cohorts={'Astral_CRC':AST,'Komor_CRC':kw['cancer'],'Komor_normal':kw['normal'],'HPA_colon_one_donor':HPA}
bench=[]; QC=[]; COHORT_INFO=[]; centered={}
for name,ref in cohorts.items():
    # Fixed anchor set within a comparison: query high-support genes measured in
    # >=80% of reference samples; missing values remain missing.
    anchors=q.index.intersection(ref.index[(ref.notna()&(ref>0)).mean(axis=1)>=.8])
    rq=q.loc[anchors].rank(pct=True)*100; rr=ref.loc[anchors].rank(pct=True)*100
    lq=np.log2(q); lr=np.log2(ref)
    cq=lq-lq.loc[anchors].median(); cr=lr-lr.loc[anchors].median(axis=0)
    centered[name]=(cq,cr)
    rec=pd.DataFrame(index=anchors)
    rec['query_rank_pct_common_set']=rq
    rec['reference_median_rank_pct']=rr.median(axis=1)
    rec['rank_shift_points']=rq-rr.median(axis=1)
    rec['reference_rank_q25']=rr.quantile(.25,axis=1)
    rec['reference_rank_q75']=rr.quantile(.75,axis=1)
    rec['fraction_reference_ranks_below_query']=(rr.lt(rq,axis=0).sum(axis=1)/rr.notna().sum(axis=1))
    rec['centered_log2_signal_contrast']=cq-cr.median(axis=1)
    rec['n_reference_detected']=ref.loc[anchors].notna().sum(axis=1)
    rec['reference_cohort']=name; rec.index.name='gene';bench.append(rec.reset_index())
    for sample in ref:
        mask=ref[sample].reindex(anchors).notna()
        corr=spearmanr(q.loc[anchors[mask]],ref.loc[anchors[mask],sample]).correlation
        QC.append({'cohort':name,'sample':sample,'shared_genes':int(mask.sum()),'spearman':float(corr)})
    COHORT_INFO.append({'cohort':name,'samples':ref.shape[1],'genes_any':int(ref.notna().any(axis=1).sum()),'anchor_genes':len(anchors),'median_detected':float(ref.notna().sum().median()),'median_query_correlation':float(np.median([r['spearman'] for r in QC if r['cohort']==name]))})
B=pd.concat(bench,ignore_index=True);B.to_csv(OUT/'reference_rank_comparisons.tsv',sep='\t',index=False)
pd.DataFrame(QC).to_csv(OUT/'reference_sample_qc.tsv',sep='\t',index=False)
pd.DataFrame(COHORT_INFO).to_csv(OUT/'reference_cohorts.tsv',sep='\t',index=False)
AST.to_csv(OUT/'astral_reference_gene_matrix.tsv',sep='\t')

# Hand-selected descriptive marker panels; these are not deconvolution or purity.
panels={'epithelial':['EPCAM','CDH1','KRT8','KRT18','KRT19','KRT20','VIL1','LGALS4','CDH17','CEACAM5','TSPAN8'],
 'fibroblast_ECM':['FAP','LRRC15','COL1A1','COL1A2','COL3A1','DCN','LUM','PDGFRA','PDGFRB','FN1','POSTN','THY1'],
 'smooth_muscle':['ACTA2','ACTG2','DES','CNN1','MYH11','TAGLN'],
 'immune':['PTPRC','CD3D','CD3E','CD8A','CD8B','CD4','CD68','LST1','TYROBP','CD163','MS4A1','NKG7','GNLY','GZMB','PRF1'],
 'antigen_presentation':['HLA-A','HLA-B','HLA-C','B2M','TAP1','TAP2','TAPBP','ERAP1','ERAP2','NLRC5','IRF1','STAT1','PSMB8','PSMB9','PSMB10','CALR','CANX'],
 'immune_regulation':['PTPN1','PTPN2','PTPN12','PTPN13','CD274','PDCD1LG2','PDCD1','CTLA4','LAG3','TIGIT','HAVCR2','TGFB1','TGFBR1','TGFBR2','JAK1','JAK2'],
 'surface_targets':['CDH17','PTK7','FAP','LRRC15','CEACAM5','CEACAM6','TACSTD2','MET','ERBB2','EGFR','CD276','GUCY2C','EPCAM','GPA33','EPHA2','EPHA3','EPHB2','EPHB3','MUC1','MUC16','FOLR1','NECTIN4','CLDN18','CLDN6','MSLN','ROR1','AXL','DLL3','VTCN1','ITGB6','ITGA5','ENG','NT5E','ENTPD1','CD200','NCAM1','FGFR2','FGFR3','TNFRSF10B'],
 'drug_mechanisms':['TOP1','TOP2A','TUBB','TYMS','DPYD','RRM1','RRM2','PARP1','BRCA1','BRCA2','ATM','ATR','WEE1','CHEK1','SMARCA2','SMARCA4','MTAP','PRMT5','BCL2','BCL2L1','MCL1','BRAF','KRAS','NRAS','PIK3CA','PTEN','AKT1','MTOR','MAP2K1','MAP2K2','VEGFA','KDR','FLT1','FGFR1','SLC7A11','GPX4']}
alltargets=list(dict.fromkeys(g for gs in panels.values() for g in gs))
tb=base[~base.multi_gene].sort_values('intensity',ascending=False).drop_duplicates('gene').reset_index().set_index('gene').reindex(alltargets)
tb['panels']=[';'.join(n for n,gs in panels.items() if g in gs) for g in tb.index]
for name in cohorts:
    br=B[B.reference_cohort==name].set_index('gene')
    for col in ['rank_shift_points','fraction_reference_ranks_below_query','centered_log2_signal_contrast','n_reference_detected']:
        tb[name+'_'+col]=br[col]
    tb[name+'_measured_samples_all']=cohorts[name].notna().sum(axis=1).reindex(tb.index).fillna(0).astype(int)
    tb[name+'_total_sample_columns']=cohorts[name].shape[1]
    tb[name+'_eligible_for_rank_comparison']=tb.index.isin(br.index)
    tb[name+'_coverage_reason']=np.where(tb.index.isin(br.index),'eligible',np.where(tb[name+'_measured_samples_all']==0,'no mapped positive reference measurement',np.where(tb[name+'_measured_samples_all']/cohorts[name].shape[1]<.8,'reference detection below 80%','query excluded from strict set')))
tb.index.name='gene';tb.to_csv(OUT/'therapeutic_targets.tsv',sep='\t')
PM=[]
for pn,gs in panels.items():
    if pn in ['surface_targets','drug_mechanisms']:continue
    for cn in cohorts:
        z=B[(B.reference_cohort==cn)&B.gene.isin(gs)]
        PM.append({'panel':pn,'reference':cn,'n_markers':len(z),'markers':';'.join(z.gene),'median_rank_shift_points':z.rank_shift_points.median(),'median_centered_log2_signal_contrast':z.centered_log2_signal_contrast.median()})
pd.DataFrame(PM).to_csv(OUT/'marker_panel_summary.tsv',sep='\t',index=False)

# Context only: matched tumour-normal differences WITHIN CPTAC, never subtract
# patient LFQ values from TMT reference-channel-normalized intensities.
hpa=pd.read_csv(SH/'refs/proteinatlas.tsv',sep='\t',usecols=['Gene','Ensembl','Uniprot'])
emap=hpa.drop_duplicates('Ensembl').set_index('Ensembl').Gene.to_dict()
ct=pd.read_csv(SH/'refs/cptac_coad/COAD_proteomics_gene_abundance_log2_reference_intensity_normalized_Tumor.txt',sep='\t',index_col=0)
cn=pd.read_csv(SH/'refs/cptac_coad/COAD_proteomics_gene_abundance_log2_reference_intensity_normalized_Normal.txt',sep='\t',index_col=0)
ct.index=[s.split('.')[0] for s in ct.index];cn.index=[s.split('.')[0] for s in cn.index]
ct=ct.groupby(level=0).median();cn=cn.groupby(level=0).median();pairs=ct.columns.intersection(cn.columns)
stats=[]
for gid in ct.index.intersection(cn.index):
    diff=(ct.loc[gid,pairs]-cn.loc[gid,pairs]).dropna()
    if len(diff)<10:continue
    p=wilcoxon(diff).pvalue if np.any(diff!=0) else 1.0
    stats.append({'ensembl':gid,'gene':emap.get(gid,''),'n_pairs':len(diff),'median_log2_tumour_minus_normal':diff.median(),'fraction_pairs_positive':(diff>0).mean(),'wilcoxon_p':p})
st=pd.DataFrame(stats).sort_values('wilcoxon_p');m=len(st);st['BH_FDR']=np.minimum(1,np.minimum.accumulate((st.wilcoxon_p.values*m/np.arange(1,m+1))[::-1])[::-1]);st.to_csv(OUT/'cptac_within_cohort_context.tsv',sep='\t',index=False)

# Normal-tissue IHC context uses supported/enhanced/approved rows only.
ihc=pd.read_csv(SH/'refs/normal_ihc_data.tsv',sep='\t')
ihc=ihc[ihc['Gene name'].isin(alltargets)&ihc.Reliability.isin(['Supported','Enhanced','Approved'])]
ihc.to_csv(OUT/'target_normal_tissue_IHC.tsv',sep='\t',index=False)
hist=base[base.detected]
qc={'protein_groups_total':len(base),'tumour_detected_groups':int(base.detected.sum()),'high_support_groups':int(base.high_support.sum()),'high_support_genes':len(genes),'precursor_rows':len(PR),'tumour_quantified_precursors':len(present),'unique_unmodified_sequences':present['Stripped.Sequence'].nunique(),'qc_counts':hist.qc_status.value_counts().to_dict(),'protein_signal_dynamic_range_log10':float(np.log10(hist.intensity.max()/hist.intensity.min())),'run423_log2_pearson':float(np.log2(base[['intensity','run423_intensity']]).corr().iloc[0,1]),'unique_count_disagreements':int((hist.n_unique_sequences!=hist.vendor_unique_peptides.fillna(0)).sum()),'fasta_gene_disagreement_high_support':int((~genes.fasta_gene_agrees).sum()),'top3_available':int(genes.unique_top3_mean_signal.notna().sum()),'top3_vs_protein_signal_spearman':float(genes[['intensity','unique_top3_mean_signal']].corr('spearman').iloc[0,1]),'CPTAC_matched_sample_ids':len(pairs),'CPTAC_genes_tested':len(st),'reference_cohorts':COHORT_INFO,'versions':{'python':sys.version.split()[0],'pandas':pd.__version__,'numpy':np.__version__},'no_differential_expression_test_for_patient':True}
(OUT/'qc_summary.json').write_text(json.dumps(qc,indent=2))

plt.rcParams.update({'font.size':10,'figure.dpi':150,'axes.spines.top':False,'axes.spines.right':False})
fig,axs=plt.subplots(1,2,figsize=(11,4))
axs[0].hist(np.log10(hist.intensity),bins=55,color='#286878');axs[0].set(xlabel='log10 protein-group signal (arbitrary units)',ylabel='Protein groups',title='B7_43: measured signal distribution')
z=genes[['intensity','unique_top3_mean_signal']].dropna();axs[1].scatter(np.log10(z.intensity),np.log10(z.unique_top3_mean_signal),s=3,alpha=.25,color='#286878');axs[1].set(xlabel='log10 delivered protein-group signal',ylabel='log10 mean of top 3 unique peptide signals',title='Peptide aggregation sensitivity check')
fig.tight_layout();fig.savefig(ROOT/'figures/qc.png');plt.close(fig)
show=['CDH17','PTK7','FAP','LRRC15','CEACAM5','TACSTD2','CD276','EGFR','ERBB2','PTPN1','PTPN2','B2M','TAP1','TAP2','SMARCA4']
z=tb.reindex(show);fig,ax=plt.subplots(figsize=(8,6));ax.barh(np.arange(len(z)),z.signal_percentile_all_detected,color='#286878');ax.set_yticks(np.arange(len(z)));ax.set_yticklabels(z.index);ax.invert_yaxis();ax.set(xlim=(0,105),xlabel='Within-sample protein signal percentile (not a patient-population percentile)',title='Therapeutic targets: detection strength and relative signal')
for i,(g,row) in enumerate(z.iterrows()):
    n=row.n_unique_sequences
    ax.text(min((row.signal_percentile_all_detected if pd.notna(row.signal_percentile_all_detected) else 0)+1,98),i,('ND' if pd.isna(n) else str(int(n))+' peptides'),va='center',fontsize=8)
fig.tight_layout();fig.savefig(ROOT/'figures/target_signal.png');plt.close(fig)
piv=B[B.gene.isin(show)].pivot(index='gene',columns='reference_cohort',values='rank_shift_points').reindex(show)
fig,ax=plt.subplots(figsize=(8,6));im=ax.imshow(piv.to_numpy(),aspect='auto',vmin=-50,vmax=50,cmap='RdBu_r');ax.set_yticks(range(len(piv)));ax.set_yticklabels(piv.index);ax.set_xticks(range(len(piv.columns)));ax.set_xticklabels(piv.columns,rotation=25,ha='right');ax.set_title('Exploratory rank shifts across separate references\nMissing comparison cells are blank; these are not fold changes');fig.colorbar(im,ax=ax,label='Query minus reference median rank (percentage points)');fig.tight_layout();fig.savefig(ROOT/'figures/reference_sensitivity.png');plt.close(fig)
print(json.dumps(qc,indent=2))
