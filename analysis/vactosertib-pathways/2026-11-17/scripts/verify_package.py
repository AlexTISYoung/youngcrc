#!/usr/bin/env python3
"""Verify exact file hashes, public technical scope, and optional final-result gate."""
import argparse
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-results", action="store_true", help="Require reviewed complete-cohort scientific aggregates")
    parser.add_argument("--require-final", action="store_true")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "package_manifest.json").read_text())
    declared = {r["path"] for r in manifest["files"]}
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file()
              and "__pycache__" not in p.parts and p.name != "package_manifest.json"}
    assert declared == actual, "File inventory changed; review and reseal"
    forbidden_names = {"pathway_scores_by_sample.csv", "metadata_28screening.csv", "subject_sample_map.csv",
                       "run_sample_clinical_join.csv", "run_sample_clinical_join.json", "source_data.xlsx"}
    forbidden_prefixes = ["/" + "Users/", "/" + "Volumes/", "/" + "private/", "/" + "home/"]
    for row in manifest["files"]:
        path = ROOT / row["path"]
        assert path.name not in forbidden_names
        assert not path.name.startswith("gene_TPM_")
        data = path.read_bytes()
        assert len(data) == row["bytes"] and hashlib.sha256(data).hexdigest() == row["sha256"], row["path"]
        if path.suffix in {".py", ".json", ".md", ".txt", ".csv", ".tsv"}:
            text = data.decode("utf-8")
            assert not any(token in text for token in forbidden_prefixes), f"Private path marker in {row['path']}"
    runs = json.loads((ROOT / "inputs/baseline_runs_technical.json").read_text())
    fastq = json.loads((ROOT / "inputs/baseline_fastq_technical.json").read_text())
    allowed = {"run_accession", "study_accession", "secondary_study_accession", "sample_accession", "experiment_accession",
               "library_strategy", "library_source", "library_selection", "library_layout", "instrument_platform",
               "instrument_model", "read_count", "base_count"}
    assert len(runs) == len({r["run_accession"] for r in runs}) == 28
    assert all(set(r) <= allowed for r in runs)
    assert all(re.fullmatch(r"SRR\d+", r["run_accession"]) for r in runs)
    assert len(fastq) == 56 and all(set(r) == {"run_accession", "read", "https_url", "bytes", "md5"} for r in fastq)
    assert {r["run_accession"] for r in fastq} == {r["run_accession"] for r in runs}
    assert all(sorted(r["read"] for r in fastq if r["run_accession"] == run["run_accession"]) == [1, 2] for run in runs)
    pathways = json.loads((ROOT / "methodology/locked_pathways.json").read_text())
    assert len(pathways) == 4 and sorted(len(p["genes"]) for p in pathways) == [11, 19, 30, 54]
    lock = json.loads((ROOT / "provenance/original_execution_lock5.json").read_text())
    for name in ["analysis/pathway_response.py", "analysis/prepare_inputs.py", "analysis/preprocessing_config.json", "methodology/locked_pathways.json"]:
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == lock["hashes"][name]
    status = "package_integrity_verified"
    if args.require_results or args.require_final:
        assert not (ROOT / "results/FINAL_RESULTS_PENDING.json").exists(), "Final cohort/results have not been inserted and reviewed"
        final = json.loads((ROOT / "results/publication_status.json").read_text())
        assert final["status"] == "FINAL_REVIEWED_ALL_28"
        assert final["n_samples"] == 28 and final["primary_groups"] == [5, 23] and final["secondary_groups"] == [2, 26]
        assert final["independent_review_passed"] is True and final["no_subject_labelled_trial_data_in_public_package"] is True
        for name, digest in final["aggregate_files_sha256"].items():
            path = Path(name)
            assert not path.is_absolute() and ".." not in path.parts
            assert hashlib.sha256((ROOT / "results" / path).read_bytes()).hexdigest() == digest
        required = {"pathway_response_statistics.json", "pathway_response_statistics.csv", "coverage.json",
                    "gene_universe.txt", "gene_universe_stricter.txt", "reference_coding_gene_universe.txt",
                    "aggregate_quantification_QC.json", "aggregate_biotype_QC.json", "analysis_provenance.json", "independent_final_review.json"}
        assert required <= set(final["aggregate_files_sha256"])
        stats = json.loads((ROOT / "results/pathway_response_statistics.json").read_text())
        coverage = json.loads((ROOT / "results/coverage.json").read_text())
        primary_coverage = [r for r in coverage if r["scoring"] == "mean_rank"]
        assert len(primary_coverage) == 4 and {r["pathway"] for r in primary_coverage} == {r["id"] for r in pathways}
        eligible = {r["pathway"] for r in primary_coverage if r["eligible"]}
        for endpoint, positive, negative, qfield in [("clinical_benefit", 5, 23, "q_primary"), ("objective_response", 2, 26, "q_secondary")]:
            main = [r for r in stats if r["endpoint"] == endpoint and r["scoring"] == "mean_rank"]
            assert {r["pathway"] for r in main} == eligible and len(main) == len(eligible)
            assert all(r["n_positive"] == positive and r["n_negative"] == negative for r in main)
            assert all(r[qfield] is not None for r in main if r.get("p") is not None)
        status = "final_all28_scientific_results_verified"
    if args.require_final:
        assert not (ROOT / "report/FINAL_REPORT_PENDING.json").exists(), "Final report sources/metadata have not been inserted and reviewed"
        report = json.loads((ROOT / "report/publication_metadata.json").read_text())
        assert report["status"] == "FINAL_REVIEWED_PUBLIC_REPORT"
        assert report["pdf_url"].startswith("https://youngcrc.com/reports/research/")
        assert re.fullmatch(r"[a-f0-9]{64}", report["pdf_sha256"])
        assert report["pdf_bytes"] > 0 and report["pages"] > 0
        assert report["source_files_sha256"]
        for name, digest in report["source_files_sha256"].items():
            path = Path(name)
            assert not path.is_absolute() and ".." not in path.parts
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest
        assert final["report_publication_ready"] is True
        status = "final_reviewed_package_and_report_verified"
    print(json.dumps({"status": status, "files": len(declared), "bytes": manifest["bytes_excluding_manifest"]}))


if __name__ == "__main__":
    main()
