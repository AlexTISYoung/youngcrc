#!/usr/bin/env python3
"""Plan and inspect raw sequencing preparation without modifying input data.

The default checks filesystem metadata only. Header reads require an explicit
flag and skip files marked as nonresident by the filesystem. Nothing is uploaded.
The job file and output report belong outside the public source tree.
"""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import json
from pathlib import Path
import re
import shutil
import stat
import sys

sys.dont_write_bytecode = True
from release_tool import ReleaseError, load_policy, relative_path, scan_text

KINDS = {"bam", "cram", "fastq", "vcf", "index"}
MAX_HEADER_BYTES = 4 * 1024 * 1024


def file_state(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        return {"state": "missing_or_unsupported", "bytes": None}
    st = path.stat()
    if not stat.S_ISREG(st.st_mode):
        return {"state": "unsupported", "bytes": None}
    flags = getattr(st, "st_flags", 0)
    offline = bool(flags & getattr(stat, "SF_DATALESS", 0))
    offline |= bool(getattr(st, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_OFFLINE", 0))
    return {"state": "nonresident" if offline else "locally_available",
            "bytes": st.st_size, "allocated_bytes": getattr(st, "st_blocks", 0) * 512}


def inspect_header(path: Path, kind: str, rules: list) -> dict:
    if kind == "index":
        return {"status": "not_applicable", "note": "Regenerate index after any transformed alignment"}
    if kind in {"bam", "cram"}:
        if not importlib.util.find_spec("pysam"):
            return {"status": "dependency_unavailable", "dependency": "pysam"}
        import pysam
        mode = "rb" if kind == "bam" else "rc"
        with pysam.AlignmentFile(str(path), mode, check_sq=False) as handle:
            text = str(handle.header)
            if len(text.encode()) > MAX_HEADER_BYTES:
                return {"status": "blocked", "reason": "header_size_limit"}
            header = handle.header.to_dict()
            return {"status": "inspected_header_only", "findings": scan_text(text, "header", rules),
                    "read_groups": len(header.get("RG", [])), "program_records": len(header.get("PG", [])),
                    "comment_records": len(header.get("CO", [])),
                    "sequence_dictionary_records": len(header.get("SQ", [])),
                    "record_tags_and_read_names_reviewed": False}
    opener = gzip.open if path.name.endswith(".gz") else open
    lines, total = [], 0
    with opener(path, "rt", encoding="utf-8", errors="strict") as handle:
        for line in handle:
            total += len(line.encode())
            if total > MAX_HEADER_BYTES:
                return {"status": "blocked", "reason": "header_size_limit"}
            if kind == "vcf":
                if not line.startswith("#"):
                    break
                lines.append(line)
                if line.startswith("#CHROM"):
                    break
            else:
                lines.append(line)
                if len(lines) == 4:
                    break
    text = "".join(lines)
    return {"status": "inspected_header_only" if kind == "vcf" else "first_record_only",
            "findings": scan_text(text, "header", rules), "complete_content_reviewed": False}


def preparation_steps(kind: str) -> list[str]:
    common = ["Verify sample identity and specimen/assay provenance",
              "Create a new derivative in separate staging; never overwrite originals",
              "Run the private content policy on all relevant metadata and text fields",
              "Validate format, scientific equivalence and checksum before marking released"]
    specific = {
        "bam": ["Review header RG/SM/LB/PU/PG/CO and SQ metadata; use public sample/read-group identifiers",
                "Review all query names and auxiliary text tags, not just the header",
                "Preserve alignment, sequence, quality, pairing, barcodes and biological tags",
                "Regenerate BAM index; verify record counts and mapped/unmapped/flag statistics"],
        "cram": ["Review alignment metadata and record-level text fields",
                 "Record exact reference assembly, checksums and reference availability",
                 "Regenerate CRAI and validate complete decode with the intended reference"],
        "fastq": ["Review every identifier and plus line; synchronize paired-end identifier replacement if needed",
                  "Preserve sequence and quality bytes; validate equal mate counts and pair identity",
                  "Verify gzip integrity and a sequence/quality digest independent of read identifiers"],
        "vcf": ["Review sample-column names and every metadata/header line, including command/source fields",
                "Review record-level free-text INFO/FORMAT fields against the private policy",
                "Preserve genotype, allele, annotation and filter semantics",
                "Use BGZF and recreate the index when indexable output is required"],
        "index": ["An index alone is not a raw dataset; link it to its complete parent file",
                  "Prefer an index regenerated from the final approved derivative"],
    }
    return common[:2] + specific[kind] + common[2:]


def plan_jobs(jobs: dict, source_tree: Path, policy_path: Path, staging: Path,
              read_headers: bool = False) -> dict:
    if jobs.get("version") != 1 or not isinstance(jobs.get("jobs"), list) or not jobs["jobs"]:
        raise ReleaseError("A nonempty version-1 private job list is required")
    rules = load_policy(policy_path, source_tree.resolve())
    records, paths, ids = [], set(), set()
    for item in jobs["jobs"]:
        job_id, kind = item.get("id"), item.get("kind")
        if not isinstance(job_id, str) or not re.fullmatch(r"[A-Za-z0-9._-]+", job_id) or job_id in ids:
            raise ReleaseError("Invalid or duplicate public job identifier")
        if kind not in KINDS:
            raise ReleaseError("Unsupported raw data format")
        public_path = relative_path(item.get("public_path"))
        if not public_path.startswith("raw/") or public_path in paths:
            raise ReleaseError("Use unique destinations inside the public raw prefix")
        public_metadata = {key: item.get(key) for key in ("id", "sample_id", "assay_id", "public_path")}
        if any(not isinstance(value, str) or not value for value in public_metadata.values()):
            raise ReleaseError("Public sample and assay identifiers are required")
        if scan_text(json.dumps(public_metadata), "job_metadata", rules):
            raise ReleaseError("Public job metadata did not pass the private policy")
        source = Path(item.get("source", ""))
        if not source.is_absolute():
            raise ReleaseError("Private raw jobs require absolute input paths")
        ids.add(job_id)
        paths.add(public_path)
        state = file_state(source)
        record = dict(public_metadata, kind=kind, **state)
        record["release_status"] = "not_released"
        record["public_url"] = None
        record["sha256"] = None
        record["preparation_steps"] = preparation_steps(kind)
        if read_headers and state["state"] == "locally_available":
            try:
                record["header_inspection"] = inspect_header(source, kind, rules)
            except Exception:
                record["header_inspection"] = {"status": "blocked", "reason": "header_parse_error"}
        else:
            record["header_inspection"] = {"status": "not_read"}
        records.append(record)
    probe = staging.absolute()
    while not probe.exists():
        probe = probe.parent
    free = shutil.disk_usage(probe).free
    total = sum(row["bytes"] or 0 for row in records)
    return {"schema_version": "1.0", "mode": "header_inspection" if read_headers else "metadata_only_dry_run",
            "input_data_modified": False, "data_uploaded": False, "raw_files_prepared": 0,
            "logical_input_bytes": total, "available_staging_bytes": free,
            "estimated_full_derivative_space_bytes": int(total * 1.15),
            "full_derivative_space_available": free >= int(total * 1.15),
            "space_note": "Planning allowance only; temporary conversion/indexing/reference needs may be larger",
            "jobs": records}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--source-tree", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--inspect-headers", action="store_true")
    args = parser.parse_args()
    try:
        root = args.source_tree.resolve()
        for private_file in (args.jobs, args.policy, args.report):
            if root == private_file.resolve() or root in private_file.resolve().parents:
                raise ReleaseError("Job, policy and report files must remain outside the public source tree")
        if args.report.exists():
            raise ReleaseError("Use a new report path; existing reports are not overwritten")
        report = plan_jobs(json.loads(args.jobs.read_text()), root, args.policy, args.staging,
                           args.inspect_headers)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": "planned", "jobs": len(report["jobs"]),
                          "raw_files_prepared": 0, "data_uploaded": False,
                          "full_derivative_space_available": report["full_derivative_space_available"]}))
        return 0
    except (ReleaseError, OSError, ValueError):
        print(json.dumps({"status": "blocked", "error": "Review the private job/configuration locally"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
