#!/usr/bin/env python3
"""Summarize the local public snapshot without network access or dependencies.

Run from the repository root: python3 examples/summarize_case.py
This is a schema/join example, not a clinical interpretation.
"""

import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUTS = (
    "data/clinical/timeline.json",
    "data/clinical/sources.json",
    "data/clinical/pathology.json",
    "data/clinical/laboratory_observations.json",
    "data/clinical/ctdna.json",
    "data/molecular/samples.json",
    "data/molecular/assays.json",
    "data/molecular/sources.json",
    "data/molecular/findings.json",
    "data/molecular/variants.json",
    "data/molecular/sample_links.json",
    "data/release_status.json",
    "release/website-manifest.json",
)


def read_inputs():
    """Hash the exact bytes parsed, so every result has reproducible inputs."""
    documents = {}
    provenance = []
    for name in INPUTS:
        raw = (ROOT / name).read_bytes()
        documents[name] = json.loads(raw)
        provenance.append(
            {"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        )
    return documents, provenance


def records(document):
    """The checked-in tables use either an array or an object with records."""
    rows = document if isinstance(document, list) else document.get("records")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("Expected an array of objects or an object with a records array")
    return rows


def index_by(rows, key):
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate identifiers in " + key)
    return result


def join_finding(finding, samples, assays, molecular_sources, clinical_sources, links, pathology):
    """Keep raw records and all linked provenance rather than flattening evidence."""
    sample = samples[finding["sample_id"]]
    assay = assays[finding["assay_id"]]
    specimen_links = [
        link for link in links if link["molecular_sample_id"] == sample["sample_id"]
    ]
    specimen_ids = {link["clinical_specimen_id"] for link in specimen_links}
    clinical_records = [row for row in pathology if row["specimen_id"] in specimen_ids]
    context = [finding, sample, assay] + specimen_links + clinical_records
    source_ids = sorted({source_id for row in context for source_id in row.get("source_ids", [])})
    sources = {**molecular_sources, **clinical_sources}
    # A dangling source is a data problem, so fail instead of silently dropping it.
    return {
        "finding": finding,
        "sample": sample,
        "assay": assay,
        "clinical_specimen_links": specimen_links,
        "clinical_pathology": clinical_records,
        "sources": [sources[source_id] for source_id in source_ids],
    }


def main():
    documents, provenance = read_inputs()
    table_names = [name for name in INPUTS if name not in (
        "data/release_status.json", "release/website-manifest.json"
    )]
    tables = {name: records(documents[name]) for name in table_names}
    timeline = tables["data/clinical/timeline.json"]
    samples = index_by(tables["data/molecular/samples.json"], "sample_id")
    assays = index_by(tables["data/molecular/assays.json"], "assay_id")
    molecular_sources = index_by(tables["data/molecular/sources.json"], "source_id")
    clinical_sources = index_by(tables["data/clinical/sources.json"], "id")
    findings = index_by(tables["data/molecular/findings.json"], "finding_id")
    manifest = documents["release/website-manifest.json"]
    availability = documents["data/release_status.json"]
    result = {
        "purpose": "Offline inventory and provenance join; no clinical interpretation",
        "website_release": manifest["release"],
        "counts": {name: len(tables[name]) for name in table_names},
        "timeline_status_counts": dict(sorted(Counter(row["status"] for row in timeline).items())),
        "availability": {
            "checked_date": availability["checked_date"],
            "all_available_data_public": availability["all_available_data_public"],
            "verified_external_objects": availability["verified_external_objects"],
            "verified_external_bytes": availability["verified_external_bytes"],
            "integrity_holds": availability.get("integrity_holds", []),
            "note": "Counts describe the source release's availability checks; large objects are not in Git",
        },
        "joined_finding_example": join_finding(
            findings["M-FINDING-001"], samples, assays, molecular_sources,
            clinical_sources, tables["data/molecular/sample_links.json"],
            tables["data/clinical/pathology.json"],
        ),
        "inputs": provenance,
        "interpretation_limits": [
            "Keep evidence labels, dates, units, sample/assay/source IDs and limitations with results.",
            "Missing or null values are not negative findings; plans do not establish administered care.",
            "Historical tissue findings do not establish current metastatic biology.",
        ],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
