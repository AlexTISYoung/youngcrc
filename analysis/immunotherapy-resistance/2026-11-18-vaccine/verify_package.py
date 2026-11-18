#!/usr/bin/env python3
"""Offline integrity and source-reproduction checks for the reviewed report."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--require-final", action="store_true")
    ap.add_argument("--require-repository-dependencies", action="store_true")
    ap.add_argument("--rerun", action="store_true")
    args = ap.parse_args()
    manifest = json_read(ROOT / "package_manifest.json")
    expected = {r["path"]: r for r in manifest["files"]}
    actual = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
              if p.is_file() and "__pycache__" not in p.parts
              and p.name != ".DS_Store" and p.relative_to(ROOT).as_posix() != "package_manifest.json"}
    assert actual == set(expected), {"missing": sorted(set(expected) - actual),
                                     "unlisted": sorted(actual - set(expected))}
    for name, row in expected.items():
        path = ROOT / name
        assert not Path(name).is_absolute() and ".." not in Path(name).parts, name
        assert path.suffix.lower() not in {".pdf", ".docx", ".bam", ".cram", ".vcf", ".fastq", ".fq", ".eml"}, "Excluded original/binary type: " + name
        assert path.stat().st_size == row["bytes"] and digest(path) == row["sha256"], name
        if path.suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=name)
        if path.suffix in {".json", ".md", ".txt", ".py"}:
            content = path.read_text(encoding="utf-8")
            forbidden = ["/" + "Users" + r"/[^\s]+", "/" + "private" + r"/(?:tmp|var)/[^\s]+",
                         "file" + "://", r"https?://mail\.google\.com/",
                         r"(?i)gmail[_ -]?(?:message|thread|draft)[_ -]?id",
                         r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"]
            assert not any(re.search(pattern, content) for pattern in forbidden), "Private path/identifier: " + name
    content = json_read(ROOT / "report/materialized_content.json")
    assert isinstance(content["PAGES"], list) and isinstance(content["REFS"], dict)
    assert content["PAGES"] and content["REFS"]
    citations = json_read(ROOT / "report/citation_manifest.json")
    assert all(key in content["REFS"] and value == content["REFS"][key] for key, value in citations.items())
    report_sources = json_read(ROOT / "report/source_manifest.json")
    for row in report_sources["source_files"]:
        assert digest(ROOT / "report" / row["path"]) == row["sha256"], "Report source manifest: " + row["path"]
    baseline = json_read(ROOT / "report/baseline_content.json")
    baseline_receipt = json_read(ROOT / "report/baseline_receipt.json")
    assert digest(ROOT / "report/baseline_content.json") == baseline_receipt["content_sha256"]
    current_pages = {page["title"]: page for page in content["PAGES"]}
    for page in baseline["PAGES"][11:15]:
        assert current_pages[page["title"]] == page, "Changed inherited trial analysis: " + page["title"]
    evidence = json_read(ROOT / "report/evidence_snapshot.json")
    expected_leads = {"flt3l-cdx301", "cd40-cdx1140", "local-ipilimumab-vaccine-priming",
                      "mct1-dc-metabolism", "gcl-bso-dc-metabolism"}
    assert {row["id"] for row in evidence["research_leads"]} == expected_leads
    assert all(row["priority"]["rank"] == 5 for row in evidence["research_leads"])
    publication = json_read(ROOT / "publication.json")
    if args.require_final:
        assert publication["status"] == "FINAL_REVIEWED_PUBLIC_REPORT"
        assert publication["all_pages_visually_inspected"] is True
        assert publication["pages_visually_inspected"] == list(range(1, publication["pages"] + 1))
        assert publication["pdf_url"] == "https://youngcrc.com/reports/research/immunotherapy_resistance_report_2026-11-18_vaccine_strategy.pdf"
        assert re.fullmatch(r"[0-9a-f]{64}", publication["pdf_sha256"])
        assert publication["pdf_bytes"] > 0
        assert publication["materialized_content_sha256"] == digest(ROOT / "report/materialized_content.json")
    dependencies = json_read(ROOT / "provenance/inherited_dependencies.json")
    verified_dependencies = 0
    if args.require_repository_dependencies:
        repo = ROOT.parents[2]
        assert (repo / "release/snapshot.json").is_file(), "Run this check from the complete repository package"
        for item in dependencies["files"]:
            target = repo / item["repository_path"]
            assert target.is_file() and digest(target) == item["sha256"], item["repository_path"]
            verified_dependencies += 1
    if args.rerun:
        with tempfile.TemporaryDirectory(prefix="vaccine-report-reproduction-") as work:
            dest = Path(work) / "report"
            shutil.copytree(ROOT / "report", dest)
            target = dest / "materialized_content.json"
            target.unlink()
            subprocess.run([sys.executable, str(dest / "assemble_vaccine_revision.py")], check=True,
                           cwd=dest, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            assert target.is_file() and digest(target) == digest(ROOT / "report/materialized_content.json"), "Report source assembly differs"
    print(json.dumps({"status": "passed", "files_verified": len(expected),
                      "designed_pages": len(content["PAGES"]), "references_used": len(citations),
                      "repository_dependencies_verified": verified_dependencies,
                      "inherited_trial_pages_unchanged": 4,
                      "research_leads_at_priority_5": len(expected_leads),
                      "source_assembly_rerun": args.rerun, "final_publication_checked": args.require_final}))


if __name__ == "__main__":
    main()
