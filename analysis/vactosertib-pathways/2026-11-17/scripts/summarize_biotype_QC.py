#!/usr/bin/env python3
"""Reproduce aggregate biotype QC from the local complete-cohort QC table.

No outcome labels, individual gene values or hypothesis tests are used.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path
import statistics


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    rows = list(csv.DictReader(a.input.open()))
    assert len({r["run_accession"] for r in rows}) == 28
    assert len({(r["run_accession"], r["transcript_type"]) for r in rows}) == len(rows)
    groups = collections.defaultdict(list)
    for row in rows:
        groups[row["transcript_type"]].append(float(row["estimated_assigned_fragments"]))
    assert all(len(v) == 28 for v in groups.values())
    result = {
        "scope": "Aggregate descriptive transcript-biotype QC across all28 runs; no outcome comparison, new hypothesis test or filtering.",
        "units": "Salmon-estimated assigned fragments, not unique molecules.",
        "n_runs": 28,
        "source_relative_path": "analysis/assembled_inputs/quantification_biotype_QC.csv",
        "source_sha256": hashlib.sha256(a.input.read_bytes()).hexdigest(),
        "types": [{"transcript_type": k, "n_runs": len(v), "minimum": min(v), "median": statistics.median(v),
                   "maximum": max(v), "sum_across_runs": sum(v)} for k, v in sorted(groups.items())]}
    if a.out.exists():
        p.error("Refusing to overwrite an existing aggregate")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
