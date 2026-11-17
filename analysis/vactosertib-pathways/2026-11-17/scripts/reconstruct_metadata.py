#!/usr/bin/env python3
"""Reconstruct the original 28 baseline clinical joins locally from public sources.

Outputs contain trial subject labels and are not public-package deliverables.
This script does not read expression, score pathways, or publish subject rows.
"""
import argparse
import csv
import datetime
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import openpyxl

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sources", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    out = a.out.resolve()
    if out == ROOT or ROOT in out.parents:
        p.error("Clinical joins must be generated outside the public package")
    if out.exists() and any(out.iterdir()):
        p.error("Require a new or empty output directory")
    sources = {s["id"]: s for s in json.loads((ROOT / "provenance/external_sources.json").read_text())}
    paths = {}
    for key in ["clinical_source_workbook", "ena_runs", "ena_run_checksums", "ncbi_sra_fullxml"]:
        s = sources[key]
        path = a.sources / s["local_name"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != s["sha256"]:
            raise ValueError(f"Original source hash mismatch: {key}")
        paths[key] = path
    workbook = openpyxl.load_workbook(paths["clinical_source_workbook"], read_only=True, data_only=True)
    iterator = workbook["Suppl Dataset2"].iter_rows(values_only=True)
    next(iterator)
    header = list(next(iterator))
    clinical = {}
    for row in iterator:
        if not isinstance(row[0], (int, float)):
            continue
        subject = str(int(row[0]))
        record = dict(zip(header, row))
        if subject in clinical:
            if any(clinical[subject][key] != record[key] for key in header[:14] + header[17:]):
                raise ValueError("Conflicting static clinical fields in repeated treatment-history rows")
        else:
            clinical[subject] = record
    workbook.close()
    assert len(clinical) == 103
    assert sum(c["RESPONDER"] == "Yes" for c in clinical.values()) == 13
    assert sum(c["CLINICAL BENEFIT"] == "Yes" for c in clinical.values()) == 16
    ena = list(csv.DictReader(paths["ena_runs"].open(), delimiter="\t"))
    checks = {r["run_accession"]: r for r in csv.DictReader(paths["ena_run_checksums"].open(), delimiter="\t")}
    ncbi = {}
    for package in ET.parse(paths["ncbi_sra_fullxml"]).getroot().findall("EXPERIMENT_PACKAGE"):
        attrs = {e.findtext("TAG"): e.findtext("VALUE") for e in package.findall(".//SAMPLE_ATTRIBUTE")}
        for run in package.findall(".//RUN_SET/RUN"):
            ncbi[run.get("accession")] = {"alias": package.find("SAMPLE").get("alias"), "attrs": attrs}
    assert len(ena) == len(ncbi) == 56
    baseline, grouped = [], {}
    for source in ena:
        dose, subject, visit = re.fullmatch(r"(200|300)_(\d+)_(Screening|Cycle\d+)_T_R1.fastq.gz", source["sample_alias"]).groups()
        c, n = clinical[subject], ncbi[source["run_accession"]]
        assert n["alias"] == source["sample_alias"]
        assert c["TUMOR TYPE"] == "Colorectal Cancer"
        assert n["attrs"]["disease"] == "metastatic colorectal cancer"
        assert str(c["AGE"]) == n["attrs"]["age"] and c["SEX"].lower() == n["attrs"]["sex"]
        assert c["DOSE"] == dose + " mg BID"
        for field in ["fastq_ftp", "fastq_bytes"]:
            assert source[field] == checks[source["run_accession"]][field]
        grouped.setdefault(subject, []).append((visit, n["attrs"]["collection_date"]))
        if visit != "Screening":
            continue
        baseline.append({"run_accession": source["run_accession"], "subject": subject,
                         "objective_response": c["RESPONDER"], "clinical_benefit": c["CLINICAL BENEFIT"],
                         "nominal_dose_mg_from_alias": int(dose),
                         "active_liver_metastasis_from_clinical_list": "LIVER" in c["SITES OF METASTASIS"],
                         "collection_date": n["attrs"]["collection_date"], "biopsy_organ": None,
                         "age": c["AGE"], "sex": c["SEX"], "primary_site": c["PRIMARY SITE"], "TMB": c["TMB"]})
    approved = {r["run_accession"] for r in json.loads((ROOT / "inputs/baseline_runs_technical.json").read_text())}
    assert len(baseline) == len(grouped) == len(approved) == 28
    assert {r["run_accession"] for r in baseline} == approved
    assert sum(r["clinical_benefit"] == "Yes" for r in baseline) == 5
    assert sum(r["objective_response"] == "Yes" for r in baseline) == 2
    subject_map = []
    for subject, visits in sorted(grouped.items()):
        assert len(visits) == 2
        before = [date for visit, date in visits if visit == "Screening"]
        after = [date for visit, date in visits if visit != "Screening"]
        assert len(before) == len(after) == 1
        gap = (datetime.date.fromisoformat(after[0]) - datetime.date.fromisoformat(before[0])).days
        subject_map.append({"subject": subject, "collection_interval_days": gap})
    out.mkdir(parents=True, exist_ok=True)
    (out / "baseline_28_manifest.json").write_text(json.dumps(sorted(baseline, key=lambda r: r["run_accession"]), indent=2) + "\n")
    with (out / "subject_sample_map.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["subject", "collection_interval_days"])
        writer.writeheader()
        writer.writerows(subject_map)
    print("Reconstructed all28 baseline joins locally; no expression or pathway statistics read.")


if __name__ == "__main__":
    main()
