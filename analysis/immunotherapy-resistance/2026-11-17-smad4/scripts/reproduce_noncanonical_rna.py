#!/usr/bin/env python3
"""Reproduce focused RNA outputs from frozen sufficient statistics.
Full-universe ranks were computed upstream from 19,619 coding genes; the
stored 160-gene subset is not reranked. No private raw reads are required.
"""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,required=True);args=parser.parse_args()
OUT=args.output_dir;OUT.mkdir(parents=True,exist_ok=True)
INP=ROOT/'inputs/noncanonical'
def save(name,df):df.to_csv(OUT/name,index=False,float_format='%.10g')
definitions=json.loads((ROOT/'noncanonical/definitions.json').read_text())
meta=json.loads((ROOT/'noncanonical/computation.json').read_text())
panels=definitions['modules'];genes=meta['genes'];cases=meta['cases']
full=pd.read_csv(INP/'source_values.csv',index_col=0)
mat=pd.read_csv(INP/'total_TPM.csv',index_col=0)
coding=pd.read_csv(INP/'coding_TPM.csv',index_col=0)
ref=mat[meta['references']]
universe=json.loads((ROOT/'definitions/rna_computation.json').read_text())['rank_universe_symbols']
assert len(universe)==meta['rank_universe_n']==19619
stored_ranks={'all_transcript_TPM':pd.read_csv(INP/'total_full_universe_ranks.csv',index_col=0), 'coding_transcript_TPM_same_denominator':pd.read_csv(INP/'coding_full_universe_ranks.csv',index_col=0)}
def selected(frame,requested):return frame.reindex(requested).copy()
panel = selected(full, genes)
panel.insert(0, "gene", panel.index)
panel["panels"] = [";".join(p["id"] for p in panels if gene in p["genes"]) for gene in genes]
for sample in cases:
    panel[sample + "_coding_transcript_TPM_same_denominator"] = selected(coding, genes)[sample]
rv = selected(ref, genes)
for name, values in [("median", rv.median(axis=1)), ("q1", rv.quantile(.25, axis=1)),
                     ("q3", rv.quantile(.75, axis=1)), ("min", rv.min(axis=1)), ("max", rv.max(axis=1))]:
    panel["GSE50760_primary18_TPM_" + name] = values
save("all_source_gene_table.csv", panel)
save("MPAS10_all_source_gene_table.csv", panel.loc[panels[0]["genes"]])
save("reference18_panel_TPM.csv", rv.reset_index(names="gene"))

scores, comparisons, genecomparisons = [], [], []
for measure, frame in [("all_transcript_TPM", mat), ("coding_transcript_TPM_same_denominator", coding.reindex(mat.index))]:
    assert frame[mat.columns].notna().all().all()
    frame = frame[mat.columns]
    log = np.log2(frame + 1)
    ranks = stored_ranks[measure]
    for p in panels:
        if not p["score"]:
            continue
        present = [g for g in p["genes"] if g in universe]
        assert len(present) / len(p["genes"]) >= .8
        l = log.loc[present]
        meanlog = l.mean()
        meanrank = ranks.loc[present].mean()
        means = l[ref.columns].mean(axis=1)
        sds = l[ref.columns].std(axis=1, ddof=1)
        assert sds.gt(0).all()
        z = l.sub(means, axis=0).div(sds, axis=0)
        scorez = z.sum() / np.sqrt(len(present))
        for sample in frame.columns:
            scores.append({"module": p["id"], "measure": measure, "sample": sample,
                           "n_genes": len(present), "rank_universe_n": len(universe),
                           "mean_within_sample_coding_gene_rank": meanrank[sample],
                           "mean_log2_TPM_plus1": meanlog[sample],
                           "reference_log_z_sum_div_sqrt_n": scorez[sample]})
        for sample in cases:
            comp = {"module": p["id"], "measure": measure, "sample": sample,
                    "set_n": len(p["genes"]), "measured_n": len(present), "rank_universe_n": len(universe),
                    "missing_genes": ";".join(g for g in p["genes"] if g not in present),
                    "genes_above_reference_median": int((l[sample] > l[ref.columns].median(axis=1)).sum()),
                    "genes_above_reference_q3": int((l[sample] > l[ref.columns].quantile(.75, axis=1)).sum()),
                    "genes_below_reference_q1": int((l[sample] < l[ref.columns].quantile(.25, axis=1)).sum())}
            for metric, vals in [("rank", meanrank), ("meanlog", meanlog), ("reference_log_z", scorez)]:
                reference = vals[ref.columns]
                comp.update({f"sample_{metric}": vals[sample], f"reference_{metric}_median": reference.median(),
                             f"reference_{metric}_q1": reference.quantile(.25), f"reference_{metric}_q3": reference.quantile(.75),
                             f"reference_{metric}_min": reference.min(), f"reference_{metric}_max": reference.max(),
                             f"reference_n_lower_{metric}": int((reference < vals[sample]).sum()),
                             f"reference_n_equal_{metric}": int((reference == vals[sample]).sum())})
            loo = []
            for omitted in present:
                v = ranks.loc[[g for g in present if g != omitted]].mean()
                loo.append(int((v[ref.columns] < v[sample]).sum()))
            comp["leave_one_gene_out_rank_n_lower_min"] = min(loo)
            comp["leave_one_gene_out_rank_n_lower_max"] = max(loo)
            comparisons.append(comp)
        for gene in present:
            for sample in cases:
                genecomparisons.append({"module": p["id"], "measure": measure, "gene": gene,
                    "sample": sample, "TPM": frame.at[gene, sample],
                    "reference_TPM_median": frame.loc[gene, ref.columns].median(),
                    "reference_TPM_q1": frame.loc[gene, ref.columns].quantile(.25),
                    "reference_TPM_q3": frame.loc[gene, ref.columns].quantile(.75),
                    "reference_gene_log_mean": means[gene], "reference_gene_log_SD": sds[gene],
                    "reference_log_z": z.at[gene, sample]})
save("module_scores_each_sample.csv", pd.DataFrame(scores))
save("module_reference_comparisons.csv", pd.DataFrame(comparisons))
save("module_member_reference_comparisons.csv", pd.DataFrame(genecomparisons))

coverage = []
for p in panels:
    for column in full.columns:
        x = selected(full, p["genes"])[column].dropna()
        rec = {"module": p["id"], "source_metric": column, "set_n": len(p["genes"]),
               "reported_n": len(x), "missing_n": len(p["genes"]) - len(x), "positive_n": int(x.gt(0).sum())}
        if column in ["BostonGene_CRC_percentile", "Caris_clinical_CRC_percentile", "Caris_Nov7_CRC_percentile"]:
            rec.update(median_of_reported_gene_percentiles=x.median(), n_below25=int(x.lt(25).sum()),
                       n_atleast75=int(x.ge(75).sum()), n_atleast90=int(x.ge(90).sum()))
        coverage.append(rec)
save("source_coverage.csv", pd.DataFrame(coverage))
liver = pd.read_csv(INP / "liver_selected.csv")
save("liver_selected_celltypes.csv", liver.loc[liver.gene.isin(genes)])
