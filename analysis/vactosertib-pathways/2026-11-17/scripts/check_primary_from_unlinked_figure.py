#!/usr/bin/env python3
"""Reproduce the four primary unstratified results from public plot distributions.

Each pathway/group is independently sorted and has no subject identifiers or
cross-pathway linkage. This cannot reproduce stratified tests, transcript
assembly, sample-level gene ranks or other scoring modes.
"""
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    spec = importlib.util.spec_from_file_location("frozen_core", ROOT / "analysis/pathway_response.py")
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    figure = json.loads((ROOT / "report/trial_figure_data.json").read_text())
    assert set(figure) == {"scope", "panels"}
    assert len(figure["panels"]) == 4
    assert {p["pathway"] for p in figure["panels"]} == core.EXPECTED_PATHWAYS
    published = json.loads((ROOT / "results/pathway_response_statistics.json").read_text())
    checked = []
    for panel in figure["panels"]:
        assert set(panel) == {"pathway", "label", "p", "benefit", "nonbenefit"}
        positive, negative = panel["benefit"], panel["nonbenefit"]
        assert len(positive) == 5 and len(negative) == 23
        assert positive == sorted(positive) and negative == sorted(negative)
        values, labels = positive + negative, [True] * 5 + [False] * 23
        assert all(isinstance(x, (float, int)) and math.isfinite(x) and 0 <= x <= 100 for x in values)
        saved = next(r for r in published if r["pathway"] == panel["pathway"] and
                     r["scoring"] == "mean_rank" and r["endpoint"] == "clinical_benefit")
        test = core.label_permutation(values, labels)
        assert test["n_allocations"] == 98280
        assert math.isclose(test["p"], saved["p"], abs_tol=1e-12)
        assert math.isclose(float(panel["p"]), saved["p"], abs_tol=.0005)
        for name, value in core.effects(values, labels).items():
            assert math.isclose(value, saved[name], abs_tol=1e-10), (panel["pathway"], name)
        checked.append({"pathway": panel["pathway"], "p": test["p"], "q_primary": saved["q_primary"]})
    assert all(math.isclose(q, row["q_primary"], abs_tol=1e-12)
               for q, row in zip(core.bh([r["p"] for r in checked], 4), checked))
    print(json.dumps({"status": "PASS", "primary_unstratified_tests_reproduced": 4,
                      "all_effect_sizes_and_BH4_match": True,
                      "boundary": "Public unlinked plot values only; no stratified or upstream reconstruction."}))


if __name__ == "__main__":
    main()
