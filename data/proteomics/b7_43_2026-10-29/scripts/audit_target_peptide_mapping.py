#!/usr/bin/env python3
"""Audit target-associated vendor Proteotypic=1 sequences against delivered FASTA.

No patient intensity is re-estimated. Substring matching is deliberately
independent of digestion assumptions and is restricted to the supplied database.
"""
from __future__ import annotations

import bisect
import csv
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "analysis"
FASTA = ROOT / "raw/vendor_delivery/Match_result-X202SC26085414_F01_F001_B1_43/homo_sapiens_uniprot_2025_06_11_Swissprot.fasta.txt"
PEPTIDES = ANALYSIS / "unique_peptide_sequences.tsv"
GROUPS = ANALYSIS / "protein_groups.tsv"
TARGETS = ["CDH17", "PTK7", "FAP", "LRRC15", "ROR1", "CEACAM5", "EGFR", "ERBB2", "CD276", "PTPN1", "PTPN2", "B2M", "HLA-A", "HLA-B", "HLA-C", "TAP1", "TAP2", "SMARCA4"]


def read_tsv(path):
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path, rows):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def read_fasta(path):
    records = []
    header, sequence = None, []
    for line in path.read_text().splitlines() + [">"]:
        if line.startswith(">"):
            if header:
                accession = header.split("|")[1]
                gene_match = re.search(r"(?:^|\s)GN=(\S+)", header)
                sequence_text = "".join(sequence).upper()
                assert re.fullmatch("[A-Z]+", sequence_text), accession
                records.append({"accession": accession, "gene": gene_match.group(1) if gene_match else "", "sequence": sequence_text})
            header, sequence = line[1:], []
        else:
            sequence.append(line.strip())
    assert len({r["accession"] for r in records}) == len(records)
    return records


records = read_fasta(FASTA)
starts, position = [], 0
for record in records:
    starts.append(position)
    position += len(record["sequence"]) + 1
joined = "|".join(r["sequence"] for r in records)  # Cannot match across proteins.
joined_il = joined.replace("I", "L")


def match_sequence(sequence, collapse_il=False):
    query = sequence.replace("I", "L") if collapse_il else sequence
    subject = joined_il if collapse_il else joined
    hits = defaultdict(list)
    position = subject.find(query)
    while position >= 0:
        index = bisect.bisect_right(starts, position) - 1
        local_position = position - starts[index]
        assert local_position + len(sequence) <= len(records[index]["sequence"])
        hits[index].append(local_position + 1)  # 1-based protein position.
        position = subject.find(query, position + 1)
    return hits


def tryptic_compatible(record, start_1based, length):
    """Specified comparator: trypsin (no cleavage before P), <=2 missed cuts,
    protein termini allowed, and optional initiator-methionine removal.
    This comparator does not establish the vendor's exact digestion settings.
    """
    sequence = record["sequence"]
    start, end = start_1based - 1, start_1based - 1 + length
    n_ok = start == 0 or (start == 1 and sequence[0] == "M") or (sequence[start - 1] in "KR" and sequence[start] != "P")
    c_ok = end == len(sequence) or (sequence[end - 1] in "KR" and sequence[end] != "P")
    missed = sum(sequence[index] in "KR" and sequence[index + 1] != "P" for index in range(start, end - 1))
    return n_ok and c_ok and missed <= 2


group_rows = read_tsv(GROUPS)
group_targets = {}
for row in group_rows:
    genes = set(row["gene"].split(";"))
    overlap = [target for target in TARGETS if target in genes]
    if overlap:
        group_targets[row["protein_group"]] = (row, overlap)

audit = []
for peptide in read_tsv(PEPTIDES):
    group = peptide["Protein.Group"]
    if group not in group_targets:
        continue
    source, assigned_targets = group_targets[group]
    sequence = peptide["Stripped.Sequence"]
    assert re.fullmatch("[A-Z]+", sequence), sequence
    exact, il = match_sequence(sequence), match_sequence(sequence, True)
    assert set(exact) <= set(il)
    for target in assigned_targets:
        row = {
            "target_gene": target,
            "assigned_protein_group": group,
            "assigned_group_genes": source["gene"],
            "sequence": sequence,
            "sequence_length": len(sequence),
            "summed_charge_and_modification_state_signal": peptide["summed_charge_and_modification_state_signal"],
            "source_vendor_proteotypic_flag": 1,
        }
        for label, hits in [("exact", exact), ("il_equivalent", il)]:
            accessions = sorted(records[i]["accession"] for i in hits)
            genes = sorted({records[i]["gene"] for i in hits if records[i]["gene"]})
            unknown = sorted(records[i]["accession"] for i in hits if not records[i]["gene"])
            compatible = {i: positions for i, positions in hits.items() if any(tryptic_compatible(records[i], pos, len(sequence)) for pos in positions)}
            compatible_genes = sorted({records[i]["gene"] for i in compatible if records[i]["gene"]})
            flanks = []
            for i, positions in sorted(hits.items()):
                protein_sequence = records[i]["sequence"]
                for pos in positions:
                    start, end = pos - 1, pos - 1 + len(sequence)
                    before = protein_sequence[start - 1] if start else "-"
                    after = protein_sequence[end] if end < len(protein_sequence) else "-"
                    flanks.append(f"{records[i]['accession']}:{pos}:{before}.{protein_sequence[start:end]}.{after}")
            row.update({
                f"{label}_protein_count": len(hits),
                f"{label}_gene_count": len(genes),
                f"{label}_accessions": ";".join(accessions),
                f"{label}_genes": ";".join(genes),
                f"{label}_accessions_without_gene": ";".join(unknown),
                f"{label}_positions_1based": ";".join(f"{records[i]['accession']}:{','.join(map(str, hits[i]))}" for i in sorted(hits)),
                f"{label}_assigned_gene_present": target in genes,
                f"{label}_assigned_group_accession_present": bool(set(group.split(";")) & set(accessions)),
                f"{label}_gene_unique_to_target": genes == [target] and not unknown,
                f"{label}_match_flanks": ";".join(flanks),
                f"{label}_trypsin_2mc_compatible_accessions": ";".join(sorted(records[i]["accession"] for i in compatible)),
                f"{label}_trypsin_2mc_compatible_genes": ";".join(compatible_genes),
                f"{label}_trypsin_2mc_gene_unique_to_target": compatible_genes == [target] and all(records[i]["gene"] for i in compatible),
            })
        row["il_additional_genes"] = ";".join(sorted({records[i]["gene"] for i in il} - {records[i]["gene"] for i in exact}))
        audit.append(row)

audit.sort(key=lambda row: (TARGETS.index(row["target_gene"]), row["sequence"]))
assert audit, "No target peptides found"
summary = []
for target in TARGETS:
    rows = [row for row in audit if row["target_gene"] == target]
    groups = [row for row in group_rows if target in row["gene"].split(";")]
    summary.append({
        "target_gene": target,
        "protein_groups": ";".join(row["protein_group"] for row in groups),
        "source_n_unique_sequences_sum": sum(int(row["n_unique_sequences"]) for row in groups),
        "audited_peptide_rows": len(rows),
        "audited_distinct_sequences": len({row["sequence"] for row in rows}),
        "exact_assigned_gene_present": sum(row["exact_assigned_gene_present"] for row in rows),
        "exact_gene_unique_to_target": sum(row["exact_gene_unique_to_target"] for row in rows),
        "il_equivalent_gene_unique_to_target": sum(row["il_equivalent_gene_unique_to_target"] for row in rows),
        "exact_trypsin_2mc_gene_unique_to_target": sum(row["exact_trypsin_2mc_gene_unique_to_target"] for row in rows),
        "il_equivalent_trypsin_2mc_gene_unique_to_target": sum(row["il_equivalent_trypsin_2mc_gene_unique_to_target"] for row in rows),
        "exact_shared_with_other_genes": sum(row["exact_gene_count"] > 1 for row in rows),
        "il_equivalent_shared_with_other_genes": sum(row["il_equivalent_gene_count"] > 1 for row in rows),
        "no_exact_match": sum(row["exact_protein_count"] == 0 for row in rows),
    })
    assert summary[-1]["source_n_unique_sequences_sum"] == len(rows), target

write_tsv(ANALYSIS / "target_peptide_mapping_audit.tsv", audit)
write_tsv(ANALYSIS / "target_peptide_mapping_summary.tsv", summary)
metadata = {
    "executed_utc": datetime.now(timezone.utc).isoformat(),
    "inputs": [{"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()} for path in [FASTA, PEPTIDES, GROUPS]],
    "database_proteins": len(records),
    "database_amino_acids": sum(len(row["sequence"]) for row in records),
    "database_proteins_without_gene": sum(not row["gene"] for row in records),
    "target_count": len(TARGETS),
    "audited_peptide_rows": len(audit),
    "audited_distinct_sequences": len({row["sequence"] for row in audit}),
    "exact_gene_unique_to_target": sum(row["exact_gene_unique_to_target"] for row in audit),
    "il_equivalent_gene_unique_to_target": sum(row["il_equivalent_gene_unique_to_target"] for row in audit),
    "exact_trypsin_2mc_gene_unique_to_target": sum(row["exact_trypsin_2mc_gene_unique_to_target"] for row in audit),
    "il_equivalent_trypsin_2mc_gene_unique_to_target": sum(row["il_equivalent_trypsin_2mc_gene_unique_to_target"] for row in audit),
    "method": "All full-protein substring matches, with | protein separators; repeat after substituting I with L in peptides and proteins. Main uniqueness fields do not filter by digestion. Separate trypsin-compatible fields allow protein termini, initiator methionine removal, <=2 missed cuts, and no cleavage before proline. No external isoform or HLA allele augmentation; no spectral reanalysis.",
}
(ANALYSIS / "target_peptide_mapping_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
print(json.dumps(metadata, indent=2))
for row in summary:
    print(row)
for row in audit:
    if not row["il_equivalent_gene_unique_to_target"]:
        print("NONUNIQUE", row["target_gene"], row["sequence"], row["exact_genes"], row["il_equivalent_genes"])
