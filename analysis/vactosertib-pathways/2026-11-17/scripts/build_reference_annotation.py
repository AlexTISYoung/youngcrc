#!/usr/bin/env python3
"""Recreate and hash-check the GENCODE37 annotation and transcript-to-gene map."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fasta", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    reference = json.loads((ROOT / "provenance/reference.json").read_text())
    assert sha(a.fasta) == reference["fasta"]["sha256"], "Reference FASTA hash mismatch"
    a.out.mkdir(parents=True, exist_ok=True)
    annotation = a.out / "transcript_annotation.csv"
    mapping = a.out / "transcript_to_gene.tsv"
    if annotation.exists() or mapping.exists():
        p.error("Refusing to overwrite existing reference annotations")
    with gzip.open(a.fasta, "rt") as fasta, annotation.open("x", newline="") as ann, mapping.open("x") as tx:
        writer = csv.writer(ann)
        writer.writerow(["transcript_id", "gene_id", "gene_name", "transcript_length", "transcript_type"])
        for line in fasta:
            if not line.startswith(">"):
                continue
            fields = line[1:].strip().split("|")
            assert len(fields) >= 8
            writer.writerow([fields[0], fields[1], fields[5], fields[6], fields[7]])
            tx.write(fields[0] + "\t" + fields[1] + "\n")
    results = {"annotation": sha(annotation), "transcript_to_gene": sha(mapping)}
    for key, actual in results.items():
        assert actual == reference[key]["sha256"], f"Generated {key} differs from original; stop and investigate"
    print(json.dumps({"status": "exact_original_reference_annotations", "sha256": results}))


if __name__ == "__main__":
    main()
