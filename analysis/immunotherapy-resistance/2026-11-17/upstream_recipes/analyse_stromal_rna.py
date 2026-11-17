#!/usr/bin/env python3
"""Optional full-matrix RNA recipe; requiredfull_inputs are NOT bundled.
See provenance/upstream_sources.json and README.txt for reproduction boundaries. No new read alignment.

Official gene sets and mechanistic/context panels are intentionally distinct.
No module statistic is a validated pathway activity or treatment-response score.
"""
from pathlib import Path
import hashlib, io, json, time
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'full_run/rna'
OUT.mkdir(parents=True,exist_ok=True)
BASE=ROOT/'full_inputs/rna_quantification'
DATA=ROOT/'full_inputs/public_data'
SOURCES={}
aliases={'CYR61':'CCN1','CTGF':'CCN2','WISP1':'CCN4','WISP2':'CCN5','WISP3':'CCN6','FAM101B':'RFLNB','MARCH1':'MARCHF1','MARCH2':'MARCHF2','C9ORF16':'C9orf16','LRRC33':'NRROS','TMEM2':'CEMIP2','HACL2':'ILVBL','RIGI':'DDX58','TMT1B':'METTL7B','MYL11':'MYLPF'}
def panel_reindex(df,genes):
    out=df.reindex(genes).copy()
    for g in genes:
        alternatives=[aliases.get(g)]+[a for a,b in aliases.items() if b==g]
        for a in alternatives:
            if a in df.index:out.loc[g]=out.loc[g].combine_first(df.loc[a])
    return out
def readbytes(p):
    p=Path(p)
    for _ in range(3):
        b=p.read_bytes()
        if b and len(b)==p.stat().st_size: break
        time.sleep(.2)
    assert b and len(b)==p.stat().st_size,p
    SOURCES[str(p.relative_to(ROOT))]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
    return b
def read(p,sep=','):
    return pd.read_csv(io.BytesIO(readbytes(p)),sep=sep,encoding='utf-8-sig')
def save(name,df):
    df.to_csv(OUT/name,index=True,index_label=df.index.name or 'gene',float_format='%.8g')
def jsave(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n')
def numer(df):
    return df.apply(pd.to_numeric,errors='coerce')

# Memberships are the reviewed exact37 sets; no classifier training is repeated.
sets=json.loads((ROOT/'definitions/module_definitions.json').read_text())['modules']
panelgenes=json.loads((ROOT/'definitions/rna_computation.json').read_text())['panelgenes']
caris=read(BASE/'results/caris_all_gene_abundance.csv')
tempus=read(BASE/'results/tempus_all_gene_abundance.csv')
annot=read(BASE/'reference/transcript_annotation.csv')
gid_symbol=caris.set_index('gene_id')['gene_symbol']
assert caris.gene_id.is_unique and tempus.gene_id.is_unique
coding_symbols=set(annot.loc[annot.transcript_type.eq('protein_coding'),'gene_name'])
q=pd.concat({s:d.groupby('gene_symbol').TPM.sum() for s,d in [('Caris_research',caris),('Tempus_research',tempus)]},axis=1)
counts=pd.concat({s:d.groupby('gene_symbol').estimated_fragments.sum() for s,d in [('Caris',caris),('Tempus',tempus)]},axis=1)
bg=read(DATA/'valius/kandinsky_gene_explorer.csv').set_index('Gene Symbol')
assert bg.index.is_unique
bgcols={
 'RNA Expression — BostonGene log2(TPM+1)':'BostonGene_log2_TPM_plus1',
 'RNA Expression — Valius Pipeline (log2(TPM+1))':'Valius_bulk_UNRESOLVED_log2_TPM_plus1',
 'Percentile: BostonGene Colorectal Adenocarcinoma':'BostonGene_CRC_percentile',
 'Percentile: BostonGene Pan-Solid':'BostonGene_pansolid_percentile',
 'Percentile: Valius Patients':'Valius_patients_percentile_UNRESOLVED',
 'Percentile: TCGA Pan-Cancer':'TCGA_pancancer_percentile_UNRESOLVED'}
bgnum=numer(bg[list(bgcols)].rename(columns=bgcols))
old=read(ROOT/'full_inputs/caris_clinical_percentiles.tsv','\t').set_index('gene')
new=read(DATA/'expression/caris-primary-rna-context-2026-11-07/gene_percentiles.csv').set_index('gene')
oldpct=pd.to_numeric(old.percentile_in_cancer_type).rename('Caris_clinical_CRC_percentile')
newpct=pd.to_numeric(new.percentile).rename('Caris_Nov7_CRC_percentile')
newtpm=pd.to_numeric(new.query_tpm).rename('Caris_Nov7_provider_TPM')
assert old.index.is_unique and new.index.is_unique
cf=read(DATA/'expression/caris_assure_cell_free_rna_expression_summary.csv')
buffy=read(DATA/'expression/additional_caris_expression_provenance_unresolved.csv')
blood=pd.concat({'Blood_cfRNA_TPM_NOT_TUMOUR':cf.groupby('Gene').TPM.sum(),'Buffycoat_TPM_NOT_TUMOUR':buffy.groupby('Gene').TPM.sum()},axis=1)
liver=read(DATA/'expression/liver_valius_celltype_expression_summary.csv')
livet=read(DATA/'expression/liver_valius_target_expression_summary.csv').set_index('gene')
livnum=livet[['tumor_mean','tumor_pct','stroma_mean','stroma_pct']].rename(columns=lambda c:'Liver_selected_'+c)
full=pd.concat([q.rename(columns=lambda c:c+'_TPM'),counts.rename(columns=lambda c:c+'_estimated_fragments'),bgnum,oldpct,newpct,newtpm,blood,livnum],axis=1)
full.index.name='gene'
save('all_genes_by_source.csv',full)
save('panel_genes_by_source.csv',panel_reindex(full,panelgenes))
save('caris_original_clinical_percentiles.csv',old)
liver.loc[liver.gene.isin(panelgenes)].to_csv(OUT/'liver_selected_celltypes_panel.csv',index=False)

ref={};coding={};source_metadata={}
for run in ['Caris_research','Tempus_research']+[f'SRR{i}' for i in range(975551,975569)]:
    folder=BASE/f'results/{run.split("_")[0].lower()}_salmon' if not run.startswith('SRR') else BASE/f'reference/gse50760/quantification/{run}'
    meta=json.loads(readbytes(folder/'aux_info/meta_info.json'));source_metadata[run]=meta
    assert meta['num_bootstraps']==30 and meta['meta_info_complete'] and meta['em_converged'] and not meta['quant_errors']
    if run.startswith('SRR'):
        df=read(folder/'quant.genes.sf','\t');assert abs(df.TPM.sum()-1e6)<1
        symbol=df.Name.map(gid_symbol);assert symbol.notna().all()
        ref[run]=df.assign(gene=symbol).groupby('gene').TPM.sum()
    # Coding-only sensitivity retains the original whole-transcriptome denominator.
    tx=read(folder/'quant.sf','\t')
    tx=tx.merge(annot,left_on='Name',right_on='transcript_id',validate='one_to_one')
    assert len(tx)==233652 and abs(tx.TPM.sum()-1e6)<1
    coding[run]=tx.loc[tx.transcript_type.eq('protein_coding')].groupby('gene_name').TPM.sum()
    print('loaded',run,flush=True)
assert len({m['index_seq_hash'] for m in source_metadata.values()})==1
assert len({m['index_name_hash'] for m in source_metadata.values()})==1
for metadata_path in [BASE/'reference/gse50760/metadata/primary_18_manifest.json',BASE/'results/caris_run_manifest.json',BASE/'results/tempus_run_manifest.json',DATA/'expression/caris-primary-rna-context-2026-11-07/context.json']:
    readbytes(metadata_path)
ref=pd.DataFrame(ref);matrix=pd.concat([q,ref],axis=1)
coding=pd.DataFrame(coding).reindex(matrix.index,fill_value=0).fillna(0)
save('all_genes_GSE50760_primary18_TPM.csv',ref)
save('all_genes_same_denominator_coding_TPM.csv',coding)
save('panel_GSE50760_primary18_TPM.csv',panel_reindex(ref,panelgenes))
save('panel_same_denominator_coding_TPM.csv',panel_reindex(coding,panelgenes))
save('panel_coding_fraction.csv',panel_reindex(coding/matrix.replace(0,np.nan),panelgenes))

# A fixed transcriptome universe avoids ranks inflated by selective panels.
universe=sorted(set(matrix.index)&coding_symbols)
assert len(universe)>19000
statrows=[];scores=[];comparisons=[];coding_comparisons=[];coverage=[]
refcols=list(ref.columns)
for measure,mat in [('all_transcript_TPM',matrix),('coding_transcript_TPM_same_denominator',coding)]:
    logs=np.log2(mat+1)
    ranks=mat.loc[universe].rank(axis=0,method='average',pct=True)*100
    for s in sets:
        mapped={g:g if g in mat.index else aliases.get(g,g) for g in s['genes']}
        genes=list(dict.fromkeys(g for g in mapped.values() if g in mat.index))
        rankgenes=[g for g in genes if g in universe]
        means=logs.loc[genes].mean();rankmeans=ranks.loc[rankgenes].mean()
        refmedian=logs.loc[genes,refcols].median(axis=1)
        median_shifts=logs.loc[genes].sub(refmedian,axis=0).median()
        for sample in mat.columns:
            scores.append({'module':s['id'],'measure':measure,'sample':sample,'n_genes':len(genes),'mean_log2_TPM_plus1':means[sample],'median_gene_log2_difference_from_reference':median_shifts[sample],'mean_within_sample_coding_gene_rank':rankmeans[sample]})
        for sample in q.columns:
            a=logs.loc[genes,sample];r=logs.loc[genes,refcols]
            loo=[]
            for removed in genes:
                keep=[g for g in genes if g!=removed]
                if not keep:continue
                loomean=logs.loc[keep].mean()
                loo.append(int((loomean[refcols]<loomean[sample]).sum()))
            ref_mean=means[refcols];ref_rank=rankmeans[refcols]
            st={'module':s['id'],'definition_type':s['definition_type'],'measure':measure,'sample':sample,'set_n':len(s['genes']),'measured_n':len(genes),'rank_universe_n':len(universe),'rank_gene_n':len(rankgenes),'missing_genes':';'.join(g for g,v in mapped.items() if v not in mat.index),'alias_mappings':';'.join(f'{g}->{v}' for g,v in mapped.items() if g!=v),
            'sample_mean_log2_TPM_plus1':means[sample],'reference_meanlog_q1':ref_mean.quantile(.25),'reference_meanlog_median':ref_mean.median(),'reference_meanlog_q3':ref_mean.quantile(.75),'reference_meanlog_min':ref_mean.min(),'reference_meanlog_max':ref_mean.max(),
            'reference_n_lower_meanlog':int((ref_mean<means[sample]).sum()),'reference_n_equal_meanlog':int((ref_mean==means[sample]).sum()),'reference_n_higher_meanlog':int((ref_mean>means[sample]).sum()),
            'median_gene_log2_difference_from_reference':median_shifts[sample],
            'sample_mean_within_sample_gene_rank':rankmeans[sample],'reference_median_mean_within_sample_gene_rank':ref_rank.median(),'reference_n_lower_rankscore':int((ref_rank<rankmeans[sample]).sum()),
            'genes_above_reference_q3':int((a>r.quantile(.75,axis=1)).sum()),'genes_below_reference_q1':int((a<r.quantile(.25,axis=1)).sum()),'genes_above_reference_median':int((a>r.median(axis=1)).sum()),
            'leave_one_gene_out_n_lower_min':min(loo),'leave_one_gene_out_n_lower_max':max(loo)}
            statrows.append(st)
    for gene in panelgenes:
        mapped_gene=gene if gene in mat.index else aliases.get(gene,gene)
        if mapped_gene not in mat.index:continue
        vals=mat.loc[mapped_gene,refcols]
        for sample in q.columns:
            value=mat.at[mapped_gene,sample]
            rec={'gene':gene,'source_gene_symbol':mapped_gene,'sample':sample,'TPM':value,'reference_q1':vals.quantile(.25),'reference_median':vals.median(),'reference_q3':vals.quantile(.75),'reference_min':vals.min(),'reference_max':vals.max(),'reference_n_lower':int((vals<value).sum()),'reference_n_higher':int((vals>value).sum()),'log2_TPMplus1_difference_from_reference_median':np.log2(value+1)-np.log2(vals+1).median()}
            (comparisons if measure=='all_transcript_TPM' else coding_comparisons).append(rec)
pd.DataFrame(statrows).to_csv(OUT/'module_comparisons.csv',index=False,float_format='%.8g')
pd.DataFrame(scores).to_csv(OUT/'module_scores_each_sample.csv',index=False,float_format='%.8g')
pd.DataFrame(comparisons).to_csv(OUT/'gene_GSE50760_comparisons.csv',index=False,float_format='%.8g')
pd.DataFrame(coding_comparisons).to_csv(OUT/'coding_gene_GSE50760_comparisons.csv',index=False,float_format='%.8g')
for s in sets:
    for col in full.columns:
        a=pd.to_numeric(panel_reindex(full,s['genes'])[col],errors='coerce').dropna()
        rec={'module':s['id'],'source_metric':col,'set_n':len(s['genes']),'reported_n':len(a),'missing_n':len(s['genes'])-len(a),'positive_n':int(a.gt(0).sum())}
        if col in ['BostonGene_CRC_percentile','Caris_clinical_CRC_percentile','Caris_Nov7_CRC_percentile']:
            rec.update({'median_reported_provider_percentile':a.median() if len(a) else np.nan,'n_atleast90th':int(a.ge(90).sum()),'n_below25th':int(a.lt(25).sum())})
        coverage.append(rec)
pd.DataFrame(coverage).to_csv(OUT/'module_coverage_and_provider_percentiles.csv',index=False,float_format='%.8g')
overlap=[]
for s in sets:
    a={aliases.get(g,g) for g in s['genes']}
    for t in sets:
        b={aliases.get(g,g) for g in t['genes']}
        overlap.append({'module1':s['id'],'module2':t['id'],'intersection_n':len(a&b),'union_n':len(a|b),'Jaccard':len(a&b)/len(a|b)})
pd.DataFrame(overlap).to_csv(OUT/'module_gene_overlap.csv',index=False,float_format='%.8g')
dimensions={'all_source_union_genes':len(full),'Caris_research_gene_rows':len(caris),'Caris_research_unique_symbols':caris.gene_symbol.nunique(),'Tempus_research_gene_rows':len(tempus),'BostonGene_reported_values':int(bgnum.BostonGene_log2_TPM_plus1.notna().sum()),'BostonGene_reported_CRC_percentiles':int(bgnum.BostonGene_CRC_percentile.notna().sum()),'Valius_bulk_reported_values':int(bgnum.Valius_bulk_UNRESOLVED_log2_TPM_plus1.notna().sum()),'Caris_original_clinical_percentile_genes':len(old),'Caris_Nov7_provider_genes':len(new),'blood_cfRNA_rows':len(cf),'blood_cfRNA_unique_symbols':cf.Gene.nunique(),'buffycoat_rows':len(buffy),'buffycoat_unique_symbols':buffy.Gene.nunique(),'liver_selected_genes':liver.gene.nunique(),'liver_celltype_rows':len(liver),'liver_celltypes':liver.cell_type.nunique(),'liver_recovered_cells':int(liver.drop_duplicates('cell_type').n_cells.sum())}
jsave('source_dimensions.json',dimensions)
inventory={
 'Caris_native_tissue':'Original paired FASTQs/BAM available in the original Caris tumour-RNA source; no full provider tissue gene-TPM file located. Full native-read independent Salmon quantification used.',
 'Caris_provider':'Original selected clinical WTS percentiles plus November7 five-gene tissue supplement. Five-gene supplement is archival biopsy, not new biopsy. Table cohort58610 vs narrative59608 remains unresolved. No CTHRC1 or broader stromal vendor percentile supplement.',
 'Tempus_native':'Original archival tumour RNA reads available; The separate Tempus fusion CSV contains fusions, not expression. Full native-read independent Salmon used. No vendor full tissue TPM matrix located.',
 'BostonGene':'Full rounded log2(TPM+1) and CRC percentiles retained from merged gene explorer; rectal resection October22,2024 blockB4. Same block as Tempus, separate assays/extractions, not independent tissue time points.',
 'Valius_bulk':'Merged Valius-pipeline column specimen/pipeline linkage unresolved; retain separately, do not call it liver or another independent tissue assay.',
 'Liver_singlecell':'Selected101-gene aggregates only; no full cell-by-gene matrix located. Missing genes are not zero. Full sets cannot be scored. Cell mean normalisation insufficiently documented.',
 'Blood':'January27,2026 Caris Assure cfRNA and gDNA/buffy-coat-associated RNA; retained as separate non-tumour sources, not evidence of lesion stroma. No gene-TPM counts processing revalidation here.',
 'Current_node':'No current October2026 node RNA matrix located; archival sources do not establish current lesion mechanism.',
 'New_additions':'November7 provider five-gene data included; no additional complete tissue expression assay identified in local inventory or root current catalogue review.'}
methods={
 'analysis':'Re-extraction of entire completed quantification matrices. No new alignment, differential expression, deconvolution or clinical classifier.',
 'reference':'18 GSE50760 primary stageIV colorectal tumours; identical Salmon2.8.0/GENCODEv37/k31 index, separately prepared public libraries. Different laboratory/library preparation/treatment/site/purity remain confounding. Reference18 counts are not clinical percentiles.',
 'primary_statistic':'Unweighted arithmetic mean of gene log2(TPM+1), so no single high collagen TPM dominates a sum. Equal-weight median gene-wise log difference from18 reference medians reported as complementary robust effect.',
 'rank_sensitivity':'Mean within-sample average-tie expression ranks among a fixed GENCODEv37 coding-gene universe, compared with the same reference samples. Does not remove gene-length/library or cell-composition differences.',
 'coding_sensitivity':'Repeat using only protein_coding transcript TPM contributions while retaining each original whole-transcriptome normalisation denominator; no renormalisation or vendor matched coding percentile. Comparing total vs coding flags transcript allocation dependence.',
 'leave_one_gene_out':'Recompute mean-log ordering versus18 reference samples after dropping each individual set member. Range of counts lower reported. Not a sampling confidence interval.',
 'gene_concordance':'Count genes above reference75th/below25th, plus median gene differences. No t-tests/p-values or claims of pathway activation.',
 'provider_summary':'Within-set medians/counts of separately supplied BostonGene/Caris CRC percentiles are descriptive summaries, not a validated combined percentile or activity score. Caris selected panel has sparse coverage and cannot represent full modules.',
 'bulk_limit':'RNA conflates tumour, fibroblast, muscle, vascular and immune abundance. Myogenesis/smooth-muscle/epithelial/pericyte controls explore alternative composition; they do not estimate cell fractions.',
 'no_Gut_classifier':'The Gut CTHRC1CAF classifier is not reconstructed; published11-gene Dominguez set is distinct.',
 'overlap':'Modules overlap in genes and are not independent confirmations; full pairwise overlap table retained. Multiple displayed summaries do not multiply independent sample evidence.'}
readbytes(Path(__file__))
readbytes(ROOT/'definitions/symbol_alias_provenance.json')
jsave('analysis_manifest.json',{'date':'2026-11-16','full_gene_rows':len(full),'panel_genes':len(panelgenes),'reference_n':18,'module_n':len(sets),'rank_universe_n':len(universe),'sources':SOURCES,'inventory':inventory,'methods':methods,'aliases':aliases,'limits':['All summaries exploratory, not validated clinical selection tests.','No direct measurement of collagen geometry, stiffness, activated ligand, phospho-SMAD/FAK/STAT, YAP localisation, chemokine gradients or spatial CD8 entry.','No current-node molecular inference.']})
print(json.dumps({'full_genes':len(full),'panel_genes':len(panelgenes),'modules':len(sets),'rank_universe':len(universe),'sources':len(SOURCES)},indent=2))
