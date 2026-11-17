#!/usr/bin/env python3
"""Locked pathway-level response analysis; no individual-gene hypothesis tests.

Input matrix: gene symbols in first column, unique sample IDs in remaining columns.
Input metadata: sample_id, subject, timepoint, objective_response, clinical_benefit,
dose_level; optional liver_metastasis. Endpoints are Yes/No, never inferred.
Input universe: one canonical protein-coding gene symbol per line, from the actual
quantification reference. Input values are TPM or counts, as explicitly supplied.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 20261116
EXACT_LIMIT = 200000
MC_DRAWS = 99999
ALIASES = {"CTGF": "CCN2", "FAM101B": "RFLNB", "CYR61": "CCN1"}
EXPECTED_PATHWAYS = {"HALLMARK_TGF_BETA_SIGNALING", "MARIATHASAN_PAN_F_TBRS_19",
                     "DOMINGUEZ_LRRC15_TGF_BETA_CAF_11", "CHAKRAVARTHY_C_ECM_UP_2018"}


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bh(pvalues, family_size=None):
    """BH with untestable prespecified hypotheses retained as P=1 in family."""
    p = np.asarray(pvalues, dtype=float)
    m = family_size or len(p)
    order = np.argsort(p)
    ordered = p[order]
    adjusted = np.minimum.accumulate((ordered * m / np.arange(1, len(p) + 1))[::-1])[::-1]
    result = np.empty(len(p))
    result[order] = np.minimum(adjusted, 1)
    return result


def label_permutation(scores, labels, strata=None, seed=SEED):
    """Two-sided exact/MC rank-sum permutation, preserving labels per stratum.

    Test statistic sums within-stratum centered ranks. Strata containing only one
    outcome contribute zero; they do not create artificial exchangeability.
    """
    x = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=bool)
    if len(x) != len(y) or not np.isfinite(x).all():
        raise ValueError("Finite scores and corresponding labels required")
    if not y.any() or y.all():
        return {"status": "not_estimable_one_outcome_group", "p": None}
    s = np.zeros(len(x), dtype=str) if strata is None else np.asarray(strata, dtype=str)
    groups = []
    observed = 0.0
    total = 1
    for name in sorted(set(s)):
        ii = np.flatnonzero(s == name)
        k = int(y[ii].sum())
        if k == 0 or k == len(ii):
            continue
        r = pd.Series(x[ii]).rank(method="average").to_numpy() - (len(ii) + 1) / 2
        observed += float(r[y[ii]].sum())
        groups.append((name, r, k))
        total *= math.comb(len(ii), k)
    if not groups:
        return {"status": "not_estimable_no_mixed_outcome_stratum", "p": None,
                "n_allocations": 1}
    tol = 1e-10
    extreme = 0
    if total <= EXACT_LIMIT:
        possibilities = []
        for _, r, k in groups:
            possibilities.append([float(r[list(indices)].sum())
                                  for indices in itertools.combinations(range(len(r)), k)])
        for terms in itertools.product(*possibilities):
            extreme += abs(sum(terms)) >= abs(observed) - tol
        pvalue = extreme / total
        method = "exhaustive_label_permutation"
        draws = total
    else:
        rng = np.random.default_rng(seed)
        for _ in range(MC_DRAWS):
            statistic = sum(float(r[rng.choice(len(r), k, replace=False)].sum())
                            for _, r, k in groups)
            extreme += abs(statistic) >= abs(observed) - tol
        pvalue = (extreme + 1) / (MC_DRAWS + 1)
        method = "monte_carlo_label_permutation_plus_one"
        draws = MC_DRAWS
    return {"status": "ok", "p": float(pvalue), "statistic": observed,
            "method": method, "n_allocations": int(total), "draws": draws,
            "informative_strata": [{"stratum": a, "n": len(r), "n_positive": k}
                                   for a, r, k in groups]}


def effects(scores, labels):
    x = np.asarray(scores, dtype=float)
    y = np.asarray(labels, dtype=bool)
    a, b = x[y], x[~y]
    if not len(a) or not len(b):
        return {"n_positive": len(a), "n_negative": len(b)}
    diffs = a[:, None] - b[None, :]
    auc = float(np.mean((diffs > 0) + 0.5 * (diffs == 0)))
    return {
        "n_positive": len(a), "n_negative": len(b),
        "median_positive": float(np.median(a)), "median_negative": float(np.median(b)),
        "q1_positive": float(np.quantile(a, .25)), "q3_positive": float(np.quantile(a, .75)),
        "q1_negative": float(np.quantile(b, .25)), "q3_negative": float(np.quantile(b, .75)),
        "median_difference": float(np.median(a) - np.median(b)),
        "hodges_lehmann_difference": float(np.median(diffs)),
        "auc_positive_higher": auc, "cliffs_delta": 2 * auc - 1,
    }


def binary(values):
    invalid = set(values.dropna()) - {"Yes", "No"}
    if invalid:
        raise ValueError(f"Endpoints must explicitly be Yes/No, found {invalid}")
    return values == "Yes"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--metadata", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--pathways", required=True)
    ap.add_argument("--units", required=True, choices=["TPM", "counts"])
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    matrix = pd.read_csv(args.matrix, sep=None, engine="python", index_col=0)
    matrix.index = [ALIASES.get(str(g), str(g)) for g in matrix.index]
    if matrix.index.duplicated().any() or matrix.columns.duplicated().any():
        raise ValueError("Duplicate gene/sample IDs require source-resolved aggregation")
    matrix = matrix.apply(pd.to_numeric, errors="raise")
    if not np.isfinite(matrix.to_numpy()).all() or (matrix < 0).any().any():
        raise ValueError("Expression matrix must be finite and nonnegative")
    metadata = pd.read_csv(args.metadata, dtype=str)
    required = {"sample_id", "subject", "timepoint", "objective_response", "clinical_benefit", "dose_level"}
    if not required <= set(metadata):
        raise ValueError(f"Missing metadata columns: {required - set(metadata)}")
    if metadata.sample_id.duplicated().any():
        raise ValueError("Duplicate sample IDs")
    if set(matrix.columns) != set(metadata.sample_id):
        raise ValueError("Matrix and metadata sample inventories differ")
    metadata = metadata.set_index("sample_id").loc[matrix.columns]
    metadata.index.name = "sample_id"
    baseline = metadata.index[metadata.timepoint.eq("screening")]
    if len(baseline) < 3 or metadata.loc[baseline, "subject"].duplicated().any():
        raise ValueError("Require at least three subjects with one screening sample each")
    universe = {ALIASES.get(g.strip(), g.strip()) for g in Path(args.universe).read_text().splitlines() if g.strip()}
    measured = sorted(set(matrix.index) & universe)
    if len(measured) < 5000:
        raise ValueError("Fewer than 5000 reference protein-coding genes: resolve gene mapping")
    fixed = [g for g in measured if (matrix.loc[g, baseline] > 0).any()]
    x = matrix.loc[fixed]
    if args.units == "counts":
        normalized = matrix.div(matrix.sum(axis=0), axis=1) * 1e6
    else:
        normalized = matrix
    stricter = [g for g in fixed if (normalized.loc[g, baseline] >= 1).sum() >= math.ceil(.2 * len(baseline))]
    (out / "gene_universe.txt").write_text("\n".join(fixed) + "\n")
    (out / "gene_universe_stricter.txt").write_text("\n".join(stricter) + "\n")
    sets = json.loads(Path(args.pathways).read_text())
    if len(sets) != 4 or {s["id"] for s in sets} != EXPECTED_PATHWAYS:
        raise ValueError("Require exactly the four locked pathway IDs")
    all_scores, coverage = [], []
    for mode, used in [("mean_rank", fixed), ("mean_rank_stricter", stricter), ("mean_log", fixed)]:
        values = normalized.loc[used]
        if mode.startswith("mean_rank"):
            values = (values.rank(axis=0, method="average") - .5) / len(used) * 100
        else:
            values = np.log2(values + 1)
        for pathway in sets:
            members = sorted(set(pathway["genes"]) & set(used))
            n_full = len(set(pathway["genes"]))
            eligible = len(members) >= 5 and len(members) / n_full >= .8
            coverage.append({"pathway": pathway["id"], "scoring": mode,
                             "eligible": eligible, "n_available": len(members), "n_original": n_full,
                             "members": members, "missing": sorted(set(pathway["genes"]) - set(members)),
                             "unmeasured_or_outside_coding_reference": sorted(set(pathway["genes"]) - set(measured)),
                             "measured_zero_in_every_screening_sample": sorted(set(pathway["genes"]) & (set(measured) - set(fixed))),
                             "removed_by_stricter_expression_filter": sorted(set(pathway["genes"]) & (set(fixed) - set(used)))})
            if not eligible:
                continue
            score = values.loc[members].mean(axis=0)
            for sample, val in score.items():
                all_scores.append({"sample_id": sample, "pathway": pathway["id"],
                                   "scoring": mode, "score": float(val)})
    scores = pd.DataFrame(all_scores).merge(metadata.reset_index(), on="sample_id", validate="many_to_one")
    scores.to_csv(out / "pathway_scores_by_sample.csv", index=False)
    (out / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    results = []
    # This run deliberately tests only the requested pretreatment association.
    for (pathway, mode), frame in scores[scores.timepoint.eq("screening")].groupby(["pathway", "scoring"]):
        for endpoint in ["objective_response", "clinical_benefit"]:
            f = frame.dropna(subset=[endpoint])
            y = binary(f[endpoint]).to_numpy()
            result = {"pathway": pathway, "scoring": mode, "endpoint": endpoint,
                      "contrast": "screening_linked_archival", **effects(f.score, y)}
            result.update(label_permutation(f.score, y))
            result["dose_stratified"] = label_permutation(f.score, y, f.dose_level.fillna("unknown"))
            if "liver_metastasis" in f:
                known = f.liver_metastasis.isin(["Yes", "No"])
                ff = f[known]
                result["dose_liver_stratified"] = label_permutation(
                    ff.score, binary(ff[endpoint]), ff.dose_level + "|" + ff.liver_metastasis)
            result["q_primary"] = None
            result["q_secondary"] = None
            results.append(result)
    for endpoint, family_size, qcol in [("clinical_benefit", 4, "q_primary"),
                                        ("objective_response", 4, "q_secondary")]:
        ii = [i for i, r in enumerate(results) if r["scoring"] == "mean_rank" and r["endpoint"] == endpoint and r["p"] is not None]
        qq = bh([results[i]["p"] for i in ii], family_size=family_size)
        for i, q in zip(ii, qq):
            results[i][qcol] = float(q)
    (out / "pathway_response_statistics.json").write_text(json.dumps(results, indent=2) + "\n")
    flattened = [{k: v for k, v in r.items() if not isinstance(v, (dict, list))} for r in results]
    pd.DataFrame(flattened).to_csv(out / "pathway_response_statistics.csv", index=False)
    manifest = {"analysis": "Four locked pathway-level tests; no gene-level tests or classifier fitting",
                "units": args.units, "subjects_at_screening": len(baseline),
                "measured_coding_genes": len(measured), "primary_universe": len(fixed),
                "stricter_universe": len(stricter), "seed": SEED,
                "sources": {key: {"path": str(value), "sha256": file_hash(value)}
                            for key, value in {"matrix": args.matrix, "metadata": args.metadata,
                                               "universe": args.universe, "pathways": args.pathways,
                                               "script": __file__}.items()},
                "plan_version": 2,
                "primary_endpoint": "Durable clinical benefit: confirmed CR/PR or SD >=6months, 5 versus23; four-pathway BH family.",
                "secondary_BH_note": "Objective response only, 2versus26, is an exploratory sensitivity with a separate four-pathway BH family. Endpoint amendment was explicitly user-requested before any trial pathway scores were inspected.",
                "interpretation": "Single-arm exploratory archival-tissue association; no treatment interaction or validated clinical cutoff."}
    (out / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
