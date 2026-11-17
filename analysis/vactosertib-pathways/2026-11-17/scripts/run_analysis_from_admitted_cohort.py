#!/usr/bin/env python3
"""Run unchanged numerical scripts only on an independently admitted complete cohort.

This is a portable entry point, not a replacement for raw-read checksum/native
pipeline QC. It verifies the supplied admission receipt, complete fixed run list,
endpoint counts, annotation hash, quant fingerprints and identical transcript IDs.
All generated subject-level outputs must remain outside this public package.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ["baseline-manifest", "subject-map", "annotation", "quant-root", "admission", "out"]:
        p.add_argument("--" + flag, type=Path, required=True)
    a = p.parse_args()
    out = a.out.resolve()
    if out == ROOT or ROOT in out.parents:
        p.error("Subject-level analysis outputs must be generated outside the public package")
    if out.exists() and any(out.iterdir()):
        p.error("Require a new or empty output directory")
    reference = json.loads((ROOT / "provenance/reference.json").read_text())
    assert sha(a.annotation) == reference["annotation"]["sha256"]
    manifest = json.loads(a.baseline_manifest.read_text())
    required = {r["run_accession"] for r in json.loads((ROOT / "inputs/baseline_runs_technical.json").read_text())}
    assert len(manifest) == len(required) == 28
    assert {r["run_accession"] for r in manifest} == required
    assert len({r["subject"] for r in manifest}) == 28
    for endpoint, n in [("clinical_benefit", 5), ("objective_response", 2)]:
        assert all(r[endpoint] in ["Yes", "No"] for r in manifest)
        assert sum(r[endpoint] == "Yes" for r in manifest) == n
    admission = json.loads(a.admission.read_text())
    assert admission["status"] == "complete_28_independently_admitted"
    assert admission["raw_checksums_preprocessing_native_QC_verified"] is True
    assert admission["endpoint_and_metadata_join_verified"] is True
    assert admission["preprocessing_config_sha256"] == sha(ROOT / "analysis/preprocessing_config.json")
    for name, path in [("baseline_manifest", a.baseline_manifest), ("subject_map", a.subject_map), ("annotation", a.annotation)]:
        assert admission["sources_sha256"][name] == sha(path), "Admitted source and supplied input differ"
    assert len(admission["runs"]) == 28 and {r["run_accession"] for r in admission["runs"]} == required
    expected_ids = None
    for row in admission["runs"]:
        run = row["run_accession"]
        for relative, digest in row["files_sha256"].items():
            path = Path(relative)
            assert not path.is_absolute() and ".." not in path.parts
            assert sha(a.quant_root / path) == digest
        assert f"{run}/quant.sf" in row["files_sha256"]
        assert f"{run}/aux_info/meta_info.json" in row["files_sha256"]
        assert f"{run}/lib_format_counts.json" in row["files_sha256"]
        assert f"{run}_run_manifest.json" in row["files_sha256"]
        with (a.quant_root / run / "quant.sf").open() as handle:
            names = [r["Name"] for r in csv.DictReader(handle, delimiter="\t")]
        assert len(names) == len(set(names)) == reference["index_info"]["num_refs"]
        ids = set(names)
        if expected_ids is None:
            expected_ids = ids
        assert ids == expected_ids, "Sample-specific missing transcript rows; never fill as biological zero"
    out.mkdir(parents=True, exist_ok=True)
    admitted = out / "admitted_runs.txt"
    admitted.write_text("\n".join(sorted(required)) + "\n")
    assembled = out / "inputs"
    subprocess.run([sys.executable, str(ROOT / "analysis/prepare_inputs.py"),
                    "--baseline-manifest", str(a.baseline_manifest), "--subject-map", str(a.subject_map),
                    "--annotation", str(a.annotation), "--quant-root", str(a.quant_root),
                    "--admitted-runs", str(admitted), "--out", str(assembled)], check=True)
    subprocess.run([sys.executable, str(ROOT / "analysis/pathway_response.py"),
                    "--matrix", str(assembled / "gene_TPM_28screening.csv"),
                    "--metadata", str(assembled / "metadata_28screening.csv"),
                    "--universe", str(assembled / "reference_coding_gene_universe.txt"),
                    "--pathways", str(ROOT / "methodology/locked_pathways.json"),
                    "--units", "TPM", "--out", str(out / "statistics")], check=True)


if __name__ == "__main__":
    main()
