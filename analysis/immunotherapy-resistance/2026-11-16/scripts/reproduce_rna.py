#!/usr/bin/env python3
"""Recompute downstream RNA summaries from compact full-precision intermediates.
Rank vectors retain the complete19619-gene universe; they are not reranked here.
Raw reads, transcript aggregation and upstream rank construction are outside this rerun.
"""
from pathlib import Path
import argparse,json,gzip
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=ROOT/'recomputed/rna');args=parser.parse_args();OUT=args.output_dir;OUT.mkdir(parents=True,exist_ok=True)
config=json.loads((ROOT/'definitions/rna_computation.json').read_text())
sets=json.loads((ROOT/'definitions/module_definitions.json').read_text())['modules']
aliases=config['aliases'];panelgenes=config['panelgenes'];universe=config['rank_universe_symbols']
def load(name):return pd.read_csv(ROOT/'inputs/rna'/name,index_col=0,float_precision='round_trip')
def output(df,name,index=False):
    raw=df.to_csv(index=index,index_label=df.index.name or 'gene' if index else None,float_format='%.8g').encode()
    (OUT/(name+'.gz')).write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
matrix=load('total_TPM.csv.gz');coding=load('coding_TPM.csv.gz')
full=load('provider_and_case_source_values.csv.gz')
ref=matrix[config['reference_columns']];q=matrix[config['case_columns']]
rank_inputs={m:load(f'{kind}_full_universe_ranks.csv.gz') for m,kind in [('all_transcript_TPM','total'),('coding_transcript_TPM_same_denominator','coding')]}
def panel_reindex(df, genes):
    out = df.reindex(genes).copy()
    for g in genes:
        alternatives = [aliases.get(g)] + [a for a, b in aliases.items() if b == g]
        for a in alternatives:
            if a in df.index:
                out.loc[g] = out.loc[g].combine_first(df.loc[a])
    return out
statrows = []
scores = []
comparisons = []
coding_comparisons = []
coverage = []
refcols = list(ref.columns)
for measure, mat in [('all_transcript_TPM', matrix), ('coding_transcript_TPM_same_denominator', coding)]:
    logs = np.log2(mat + 1)
    ranks = rank_inputs[measure]
    for s in sets:
        mapped = {g: g if g in mat.index else aliases.get(g, g) for g in s['genes']}
        genes = list(dict.fromkeys((g for g in mapped.values() if g in mat.index)))
        rankgenes = [g for g in genes if g in universe]
        means = logs.loc[genes].mean()
        rankmeans = ranks.loc[rankgenes].mean()
        refmedian = logs.loc[genes, refcols].median(axis=1)
        median_shifts = logs.loc[genes].sub(refmedian, axis=0).median()
        for sample in mat.columns:
            scores.append({'module': s['id'], 'measure': measure, 'sample': sample, 'n_genes': len(genes), 'mean_log2_TPM_plus1': means[sample], 'median_gene_log2_difference_from_reference': median_shifts[sample], 'mean_within_sample_coding_gene_rank': rankmeans[sample]})
        for sample in q.columns:
            a = logs.loc[genes, sample]
            r = logs.loc[genes, refcols]
            loo = []
            for removed in genes:
                keep = [g for g in genes if g != removed]
                if not keep:
                    continue
                loomean = logs.loc[keep].mean()
                loo.append(int((loomean[refcols] < loomean[sample]).sum()))
            ref_mean = means[refcols]
            ref_rank = rankmeans[refcols]
            st = {'module': s['id'], 'definition_type': s['definition_type'], 'measure': measure, 'sample': sample, 'set_n': len(s['genes']), 'measured_n': len(genes), 'rank_universe_n': len(universe), 'rank_gene_n': len(rankgenes), 'missing_genes': ';'.join((g for g, v in mapped.items() if v not in mat.index)), 'alias_mappings': ';'.join((f'{g}->{v}' for g, v in mapped.items() if g != v)), 'sample_mean_log2_TPM_plus1': means[sample], 'reference_meanlog_q1': ref_mean.quantile(0.25), 'reference_meanlog_median': ref_mean.median(), 'reference_meanlog_q3': ref_mean.quantile(0.75), 'reference_meanlog_min': ref_mean.min(), 'reference_meanlog_max': ref_mean.max(), 'reference_n_lower_meanlog': int((ref_mean < means[sample]).sum()), 'reference_n_equal_meanlog': int((ref_mean == means[sample]).sum()), 'reference_n_higher_meanlog': int((ref_mean > means[sample]).sum()), 'median_gene_log2_difference_from_reference': median_shifts[sample], 'sample_mean_within_sample_gene_rank': rankmeans[sample], 'reference_median_mean_within_sample_gene_rank': ref_rank.median(), 'reference_n_lower_rankscore': int((ref_rank < rankmeans[sample]).sum()), 'genes_above_reference_q3': int((a > r.quantile(0.75, axis=1)).sum()), 'genes_below_reference_q1': int((a < r.quantile(0.25, axis=1)).sum()), 'genes_above_reference_median': int((a > r.median(axis=1)).sum()), 'leave_one_gene_out_n_lower_min': min(loo), 'leave_one_gene_out_n_lower_max': max(loo)}
            statrows.append(st)
    for gene in panelgenes:
        mapped_gene = gene if gene in mat.index else aliases.get(gene, gene)
        if mapped_gene not in mat.index:
            continue
        vals = mat.loc[mapped_gene, refcols]
        for sample in q.columns:
            value = mat.at[mapped_gene, sample]
            rec = {'gene': gene, 'source_gene_symbol': mapped_gene, 'sample': sample, 'TPM': value, 'reference_q1': vals.quantile(0.25), 'reference_median': vals.median(), 'reference_q3': vals.quantile(0.75), 'reference_min': vals.min(), 'reference_max': vals.max(), 'reference_n_lower': int((vals < value).sum()), 'reference_n_higher': int((vals > value).sum()), 'log2_TPMplus1_difference_from_reference_median': np.log2(value + 1) - np.log2(vals + 1).median()}
            (comparisons if measure == 'all_transcript_TPM' else coding_comparisons).append(rec)
output(pd.DataFrame(statrows), 'module_comparisons.csv')
output(pd.DataFrame(scores), 'module_scores_each_sample.csv')
output(pd.DataFrame(comparisons), 'gene_GSE50760_comparisons.csv')
output(pd.DataFrame(coding_comparisons), 'coding_gene_GSE50760_comparisons.csv')
for s in sets:
    for col in full.columns:
        a = pd.to_numeric(panel_reindex(full, s['genes'])[col], errors='coerce').dropna()
        rec = {'module': s['id'], 'source_metric': col, 'set_n': len(s['genes']), 'reported_n': len(a), 'missing_n': len(s['genes']) - len(a), 'positive_n': int(a.gt(0).sum())}
        if col in ['BostonGene_CRC_percentile', 'Caris_clinical_CRC_percentile', 'Caris_Nov7_CRC_percentile']:
            rec.update({'median_reported_provider_percentile': a.median() if len(a) else np.nan, 'n_atleast90th': int(a.ge(90).sum()), 'n_below25th': int(a.lt(25).sum())})
        coverage.append(rec)
output(pd.DataFrame(coverage), 'module_coverage_and_provider_percentiles.csv')
overlap = []
for s in sets:
    a = {aliases.get(g, g) for g in s['genes']}
    for t in sets:
        b = {aliases.get(g, g) for g in t['genes']}
        overlap.append({'module1': s['id'], 'module2': t['id'], 'intersection_n': len(a & b), 'union_n': len(a | b), 'Jaccard': len(a & b) / len(a | b)})
output(pd.DataFrame(overlap), 'module_gene_overlap.csv')
output(panel_reindex(full,panelgenes),'panel_genes_by_source.csv',True)
output(panel_reindex(ref,panelgenes),'panel_GSE50760_primary18_TPM.csv',True)
output(panel_reindex(coding,panelgenes),'panel_same_denominator_coding_TPM.csv',True)
output(panel_reindex(coding/matrix.replace(0,np.nan),panelgenes),'panel_coding_fraction.csv',True)
print('Recomputed RNA modules and sensitivity outputs from compact intermediates.')

mods=pd.read_csv(OUT/'module_comparisons.csv.gz')
summary_rows=[]
for definition in sets:
    for sample in config['case_columns']:
        a=mods[(mods.module==definition['id'])&(mods['sample']==sample)]
        t=a[a.measure.eq('all_transcript_TPM')].iloc[0]
        c=a[a.measure.eq('coding_transcript_TPM_same_denominator')].iloc[0]
        summary_rows.append({'module':definition['id'],'sample':sample,'genes':t.measured_n,'total_meanlog_refs_lower':t.reference_n_lower_meanlog,'total_rank_refs_lower':t.reference_n_lower_rankscore,'coding_meanlog_refs_lower':c.reference_n_lower_meanlog,'coding_rank_refs_lower':c.reference_n_lower_rankscore,'total_genes_above_refQ3':t.genes_above_reference_q3,'total_genes_below_refQ1':t.genes_below_reference_q1,'median_gene_log2_difference':t.median_gene_log2_difference_from_reference})
output(pd.DataFrame(summary_rows),'report_module_summary.csv')
