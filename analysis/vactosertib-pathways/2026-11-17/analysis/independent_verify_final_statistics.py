#!/usr/bin/env python3
"""Independent full-cohort verification. Never imports the production scorer.

The real-data branch requires all three completed gates and an explicit flag.
The self-test branch uses only synthetic arrays.
"""
from __future__ import annotations
import argparse
import collections
import csv
import datetime
import hashlib
import itertools
import json
import math
from pathlib import Path
import numpy as np
import pandas as pd

ALIASES = {"CTGF": "CCN2", "FAM101B": "RFLNB", "CYR61": "CCN1"}


def rankdata(values, method="average", axis=None):
    """Stable sorting and explicit tie blocks, independent of pandas ranking."""
    assert method == "average"
    a = np.asarray(values)
    if axis == 0:
        return np.column_stack([rankdata(a[:, j]) for j in range(a.shape[1])])
    assert axis is None and a.ndim == 1
    order = np.argsort(a, kind="stable")
    sorted_values = a[order]
    boundaries = np.r_[0, np.flatnonzero(sorted_values[1:] != sorted_values[:-1]) + 1, len(a)]
    ranks = np.empty(len(a), dtype=float)
    for start, stop in zip(boundaries[:-1], boundaries[1:]):
        ranks[order[start:stop]] = (start + 1 + stop) / 2
    return ranks


def sha(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def exact_rank_test(values, outcome, strata=None):
    """Convolve integer twice-centered-rank frequencies, including tie multiplicity."""
    values, outcome = np.asarray(values), np.asarray(outcome, dtype=bool)
    strata = np.zeros(len(values), dtype=int) if strata is None else np.asarray(strata)
    distribution, observed, informative = collections.Counter({0: 1}), 0, []
    for name in np.unique(strata):
        chosen = strata == name
        v, y = values[chosen], outcome[chosen]
        n, k = len(v), int(outcome[chosen].sum())
        if k in (0, n):
            continue
        r2 = np.rint(2 * rankdata(v, method="average") - (n + 1)).astype(int)
        assert np.allclose(r2, 2 * rankdata(v, method="average") - (n + 1))
        observed += int(r2[y].sum())
        local = collections.Counter(sum(int(r2[i]) for i in ii)
                                    for ii in itertools.combinations(range(n), k))
        combined = collections.Counter()
        for a, ca in distribution.items():
            for b, cb in local.items():
                combined[a + b] += ca * cb
        distribution = combined
        informative.append({"n": n, "positive": k})
    if not informative:
        return {"p": None, "n_allocations": 1, "statistic": None}
    total = sum(distribution.values())
    extreme = sum(count for value, count in distribution.items() if abs(value) >= abs(observed))
    return {"p": extreme / total, "n_allocations": total,
            "statistic": observed / 2, "informative_strata": informative}


def independent_bh(values, size=4):
    padded = list(values) + [1.] * (size - len(values))
    order = sorted(range(size), key=padded.__getitem__)
    q = [None] * size
    for pos, index in enumerate(order):
        q[index] = min(1., min(size * padded[order[j]] / (j + 1) for j in range(pos, size)))
    return q[:len(values)]


def self_test():
    assert exact_rank_test([1, 2, 3, 4], [0, 0, 1, 1])["p"] == 2 / 6
    assert exact_rank_test([0, 0, 1, 1], [1, 1, 0, 0])["p"] == 2 / 6
    assert exact_rank_test([1, 1, 1, 1], [1, 1, 0, 0])["p"] == 1
    x = exact_rank_test([1, 2, 8, 9], [0, 1, 0, 1], [0, 0, 1, 1])
    assert x["p"] == .5 and x["n_allocations"] == 4
    assert exact_rank_test([1, 2, 8, 9], [0, 0, 1, 1], [0, 0, 1, 1])["p"] is None
    assert np.allclose(independent_bh([.001, .01, .02, .9]), [.004, .02, .08 / 3, .9])
    assert np.allclose(independent_bh([.01, .04]), [.04, .08])
    assert np.allclose(rankdata([0, 0, 3, 5]), [1.5, 1.5, 3, 4])
    print("8 independent synthetic checks passed; no real input was opened")


def main(args):
    root = Path(args.task_root).resolve()
    out = root / "analysis/final_independent_review"
    out.mkdir(exist_ok=True)
    analysis = root / "analysis"
    status = json.loads((analysis / "completion_controller_status.json").read_text())
    admission = json.loads((analysis / "complete_cohort_admission.json").read_text())
    identifiers = json.loads((analysis / "independent_transcript_coverage_QC.json").read_text())
    assert args.permit_full_cohort and status["phase"] == "complete"
    assert admission["n_runs"] == 28
    assert identifiers["n_completed_runs"] == 28
    assert identifiers["all_completed_sets_identical"] and identifiers["no_duplicate_transcripts"]

    inputs, results = analysis / "assembled_inputs", analysis / "results"
    matrix_path = inputs / "gene_TPM_28screening.csv"
    matrix = pd.read_csv(matrix_path, index_col=0)
    matrix.index = [ALIASES.get(x, x) for x in matrix.index]
    assert not matrix.index.duplicated().any() and matrix.shape[1] == 28
    metadata = pd.read_csv(inputs / "metadata_28screening.csv", dtype=str).set_index("sample_id").loc[matrix.columns]
    assert metadata.subject.nunique() == 28 and metadata.timepoint.eq("screening").all()
    assert metadata.clinical_benefit.value_counts().to_dict() == {"No": 23, "Yes": 5}
    assert metadata.objective_response.value_counts().to_dict() == {"No": 26, "Yes": 2}
    assert np.isfinite(matrix.to_numpy()).all() and (matrix.to_numpy() >= 0).all()

    # Independently reconstruct every gene TPM using CSV parsing and math.fsum,
    # rather than the production pandas merge/groupby implementation.
    annotation = Path(args.annotation)
    assert sha(annotation) == "741e0625c79aa984fbcdb61ccc5da3d316cdf01c50e28f79ab4adb35df7a298b"
    tx = {}
    coding = set()
    with annotation.open() as f:
        for row in csv.DictReader(f):
            gene = ALIASES.get(row["gene_name"], row["gene_name"])
            assert row["transcript_id"] not in tx
            tx[row["transcript_id"]] = gene
            if row["transcript_type"] == "protein_coding":
                coding.add(gene)
    reconstruction = []
    for run in matrix.columns:
        totals = collections.defaultdict(list)
        with (root / "quantification" / run / "quant.sf").open() as f:
            for row in csv.DictReader(f, delimiter="\t"):
                totals[tx[row["Name"]]].append(float(row["TPM"]))
        assert set(totals) == set(matrix.index)
        expected = np.array([math.fsum(totals[g]) for g in matrix.index])
        observed = matrix[run].to_numpy()
        assert np.allclose(expected, observed, rtol=1e-11, atol=1e-8), run
        reconstruction.append({"run_accession": run,
                               "maximum_absolute_TPM_difference": float(np.max(abs(expected - observed)))})
    declared = {ALIASES.get(x, x) for x in (inputs / "reference_coding_gene_universe.txt").read_text().splitlines()}
    assert coding == declared
    measured = sorted(coding.intersection(matrix.index))
    fixed = [g for g in measured if np.any(matrix.loc[g].to_numpy() > 0)]
    strict = [g for g in fixed if np.count_nonzero(matrix.loc[g].to_numpy() >= 1) >= 6]
    assert fixed == (results / "gene_universe.txt").read_text().splitlines()
    assert strict == (results / "gene_universe_stricter.txt").read_text().splitlines()
    pathways = json.loads((root / "methodology/locked_pathways.json").read_text())
    coverage = json.loads((results / "coverage.json").read_text())
    scores_out = pd.read_csv(results / "pathway_scores_by_sample.csv")
    stats_out = json.loads((results / "pathway_response_statistics.json").read_text())
    verified = []
    for mode, universe in [("mean_rank", fixed), ("mean_rank_stricter", strict), ("mean_log", fixed)]:
        a = matrix.loc[universe].to_numpy()
        scaled = ((rankdata(a, method="average", axis=0) - .5) / len(universe) * 100
                  if mode.startswith("mean_rank") else np.log2(a + 1))
        positions = {g: i for i, g in enumerate(universe)}
        for pathway in pathways:
            members = sorted(set(pathway["genes"]) & set(universe))
            eligible = len(members) >= 5 and len(members) >= .8 * len(set(pathway["genes"]))
            cov = next(x for x in coverage if x["pathway"] == pathway["id"] and x["scoring"] == mode)
            assert cov["eligible"] == eligible and cov["members"] == members
            if not eligible:
                continue
            scores = np.array([math.fsum(scaled[positions[g], j] for g in members) / len(members)
                               for j in range(matrix.shape[1])])
            exported = scores_out[(scores_out.pathway == pathway["id"]) & (scores_out.scoring == mode)].set_index("sample_id").loc[matrix.columns]
            assert np.allclose(scores, exported.score.to_numpy(), rtol=1e-12, atol=1e-11)
            for endpoint in ["clinical_benefit", "objective_response"]:
                y = metadata[endpoint].eq("Yes").to_numpy()
                saved = next(x for x in stats_out if x["pathway"] == pathway["id"] and x["scoring"] == mode and x["endpoint"] == endpoint)
                p = exact_rank_test(scores, y)
                assert math.isclose(p["p"], saved["p"], abs_tol=1e-12)
                assert p["n_allocations"] == saved["n_allocations"]
                assert math.isclose(p["statistic"], saved["statistic"], abs_tol=1e-10)
                positive, negative = scores[y], scores[~y]
                pairs = np.subtract.outer(positive, negative).ravel()
                effect = {"n_positive": len(positive), "n_negative": len(negative),
                          "median_positive": np.median(positive), "median_negative": np.median(negative),
                          "q1_positive": np.quantile(positive, .25), "q3_positive": np.quantile(positive, .75),
                          "q1_negative": np.quantile(negative, .25), "q3_negative": np.quantile(negative, .75),
                          "median_difference": np.median(positive) - np.median(negative),
                          "hodges_lehmann_difference": np.median(pairs),
                          "auc_positive_higher": (np.count_nonzero(pairs > 0) + .5 * np.count_nonzero(pairs == 0)) / len(pairs)}
                effect["cliffs_delta"] = 2 * effect["auc_positive_higher"] - 1
                for key, value in effect.items():
                    assert math.isclose(float(value), saved[key], abs_tol=1e-10), (pathway["id"], mode, endpoint, key)
                for key, strata in [("dose_stratified", metadata.dose_level.to_numpy()),
                                    ("dose_liver_stratified", (metadata.dose_level + "|" + metadata.liver_metastasis).to_numpy())]:
                    sensitivity = exact_rank_test(scores, y, strata)
                    assert sensitivity["p"] == saved[key]["p"]
                    assert sensitivity["n_allocations"] == saved[key]["n_allocations"]
                verified.append({"pathway": pathway["id"], "scoring": mode, "endpoint": endpoint,
                                 "p": p["p"], "n_allocations": p["n_allocations"],
                                 "all_score_effect_and_stratified_comparisons_match": True})
    for endpoint, column in [("clinical_benefit", "q_primary"), ("objective_response", "q_secondary")]:
        family = [x for x in stats_out if x["endpoint"] == endpoint and x["scoring"] == "mean_rank"]
        for row, q in zip(family, independent_bh([x["p"] for x in family])):
            assert math.isclose(row[column], q, abs_tol=1e-12)
    receipt = {"reviewed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "status": "PASS", "independent_source_sha256": sha(__file__),
               "n_subjects": 28, "reference_coding_symbols": len(coding),
               "measured_coding_symbols": len(measured), "primary_universe": len(fixed),
               "stricter_universe": len(strict), "reconstructed_all_gene_TPM_columns": reconstruction,
               "matrix_reconstruction_tolerance": {"relative": 1e-11, "absolute": 1e-8},
               "verified_aggregate_results": verified, "primary_and_secondary_BH4_match": True,
               "method": "Independent CSV/math.fsum gene assembly, stable-sort explicit tie-block average ranks, exact integer rank-frequency convolution and independently padded BH4. Production scorer was not imported.",
               "limitation": "Numerical equivalence verifies implementation, not a predictive biomarker or causal inference. No confidence intervals are implemented in the frozen analysis.",
               "input_hashes": {str(p.relative_to(root)): sha(p) for p in [matrix_path, inputs / "metadata_28screening.csv", results / "pathway_response_statistics.json", root / "methodology/locked_pathways.json"]}}
    (out / "numeric_verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": "PASS", "verified_result_rows": len(verified), "full_gene_matrix_columns": 28}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--permit-full-cohort", action="store_true")
    parser.add_argument("--task-root")
    parser.add_argument("--annotation")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        if not (args.permit_full_cohort and args.task_root and args.annotation):
            parser.error("Real-data review requires explicit all-cohort flag, task root and annotation")
        main(args)
