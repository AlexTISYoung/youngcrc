#!/usr/bin/env python3
"""Assemble all 28 successful baseline Salmon outputs before any outcome scoring.

Raw-transfer/MD5 and run-completion admission is performed by the quantification
runner; this script additionally requires the approved run IDs in --admitted-runs.
That text file must contain only fully validated run IDs, one per line.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

ALIASES = {"CTGF": "CCN2", "FAM101B": "RFLNB", "CYR61": "CCN1"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline-manifest", required=True)
    p.add_argument("--subject-map", required=True)
    p.add_argument("--annotation", required=True)
    p.add_argument("--quant-root", required=True)
    p.add_argument("--admitted-runs", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(Path(args.baseline_manifest).read_text())
    if len(manifest) != 28 or len({r["subject"] for r in manifest}) != 28:
        raise ValueError("Require the complete verified 28-subject baseline manifest")
    required = {r["run_accession"] for r in manifest}
    admitted = set(Path(args.admitted_runs).read_text().splitlines())
    if admitted != required:
        raise ValueError(f"Incomplete or unexpected admitted runs: missing={required-admitted}, extra={admitted-required}")
    subjects = pd.read_csv(args.subject_map, dtype=str).set_index("subject")
    annotation = pd.read_csv(args.annotation, dtype=str)
    if annotation.transcript_id.duplicated().any():
        raise ValueError("Duplicate transcript annotation rows")
    annotation["gene"] = annotation.gene_name.replace(ALIASES)
    coding = sorted(set(annotation.loc[annotation.transcript_type.eq("protein_coding"), "gene"]))
    (out / "reference_coding_gene_universe.txt").write_text("\n".join(coding) + "\n")
    annotated_names = annotation.groupby("gene").gene_id.nunique()
    ambiguous_names = annotated_names[annotated_names > 1].to_dict()
    matrices = {k: [] for k in ["TPM", "NumReads", "coding_transcript_TPM_same_denominator"]}
    metadata, qc, biotype_qc = [], [], []
    for row in sorted(manifest, key=lambda r: r["run_accession"]):
        run, subject = row["run_accession"], str(row["subject"])
        folder = Path(args.quant_root) / run
        quant_path = folder / "quant.sf"
        meta_path = folder / "aux_info/meta_info.json"
        quant = pd.read_csv(quant_path, sep="\t")
        if quant.Name.duplicated().any():
            raise ValueError(f"Duplicate transcript IDs in {run}")
        joined = quant.merge(annotation, left_on="Name", right_on="transcript_id", how="left", validate="one_to_one")
        if joined.gene.isna().any():
            raise ValueError(f"Unmapped quantified transcripts in {run}")
        total_tpm = float(joined.TPM.sum())
        if abs(total_tpm - 1e6) > 10:
            raise ValueError(f"Unexpected TPM sum for {run}: {total_tpm}")
        for column in ["TPM", "NumReads"]:
            matrices[column].append(joined.groupby("gene")[column].sum().rename(run))
        coding_tpm = joined.loc[joined.transcript_type.eq("protein_coding")].groupby("gene").TPM.sum()
        matrices["coding_transcript_TPM_same_denominator"].append(coding_tpm.rename(run))
        coding_reads = joined.loc[joined.transcript_type.eq("protein_coding")].groupby("gene").NumReads.sum()
        for biotype, value in joined.groupby("transcript_type").NumReads.sum().items():
            biotype_qc.append({"run_accession": run, "transcript_type": biotype,
                               "estimated_assigned_fragments": float(value)})
        meta = json.loads(meta_path.read_text())
        run_manifest = json.loads((Path(args.quant_root) / f"{run}_run_manifest.json").read_text())
        prep = run_manifest["preprocessing"]
        lib = json.loads((folder / "lib_format_counts.json").read_text())
        qc.append({"run_accession": run, "quant_sha256": sha(quant_path), "meta_info_sha256": sha(meta_path),
                   "TPM_sum": total_tpm, "n_transcripts": len(joined),
                   "n_mapped_gene_symbols": joined.gene.nunique(),
                   "num_processed": meta.get("num_processed"), "num_mapped": meta.get("num_mapped"),
                   "percent_mapped": meta.get("percent_mapped"), "library_types": meta.get("library_types"),
                   "raw_pairs": prep["raw_pairs"], "retained_pairs": prep["retained_pairs"],
                   "short_pairs_removed": prep["short_pairs_removed"],
                   "retained_fraction": prep["retained_pairs"] / prep["raw_pairs"],
                   "percent_mapped_of_original_pairs": 100 * meta["num_mapped"] / prep["raw_pairs"],
                   "R1_adapter_fraction": prep["read_counts"]["read1_with_adapter"] / prep["raw_pairs"],
                   "R2_adapter_fraction": prep["read_counts"]["read2_with_adapter"] / prep["raw_pairs"],
                   "compatible_fragment_ratio": lib.get("compatible_fragment_ratio"),
                   "coding_transcript_estimated_fragments": float(coding_reads.sum()),
                   "coding_genes_with_at_least_1_estimated_fragment": int((coding_reads >= 1).sum()),
                   "coding_genes_with_at_least_10_estimated_fragments": int((coding_reads >= 10).sum()),
                   "preprocessing_config_sha256": run_manifest["preprocessing_config_sha256"]})
        sr = subjects.loc[subject]
        metadata.append({"sample_id": run, "subject": subject, "timepoint": "screening",
                         "objective_response": row["objective_response"], "clinical_benefit": row["clinical_benefit"],
                         "dose_level": str(row["nominal_dose_mg_from_alias"]),
                         "liver_metastasis": "Yes" if row["active_liver_metastasis_from_clinical_list"] else "No",
                         "collection_date": row["collection_date"],
                         "collection_interval_days_to_post": sr["collection_interval_days"],
                         "biopsy_organ": row.get("biopsy_organ"), "age": row["age"], "sex": row["sex"],
                         "primary_site": row["primary_site"], "TMB_as_reported": row["TMB"]})
    for name, parts in matrices.items():
        pd.concat(parts, axis=1).fillna(0).sort_index().to_csv(out / f"gene_{name}_28screening.csv")
    pd.DataFrame(metadata).to_csv(out / "metadata_28screening.csv", index=False)
    pd.DataFrame(qc).to_csv(out / "quantification_QC.csv", index=False)
    pd.DataFrame(biotype_qc).to_csv(out / "quantification_biotype_QC.csv", index=False)
    receipt = {"status": "complete_28_sample_matrix", "method": "Sum quantified transcripts by canonical gene symbol; retain all transcript contributions in primary gene TPM. Coding-transcript contribution is saved separately using the same whole-transcriptome denominator.",
               "duplicate_symbol_policy": "Reference entries with shared gene symbols, including PAR copies, are summed; source gene IDs retained in annotation and duplicate-symbol inventory.",
               "reference_coding_universe_definition": "Gene symbols with at least one transcript annotated protein_coding in the actual GENCODE37 transcript annotation.",
               "n_reference_coding_genes": len(coding), "multi_gene_id_symbols": ambiguous_names,
               "technical_QC": "Raw/retained/mapped counts, adapter fractions, strand compatibility, coding-fragment depth and coverage are reported for all 28. They are diagnostic summaries, not outcome-based exclusion rules. Protein-coding transcript assignments are model estimates and may share ambiguous fragments.",
               "public_boundary": "Patient-level labelled matrices and sample-to-clinical joins remain local; public reporting is aggregate only, per parent instruction.",
               "sources": {key: {"path": value, "sha256": sha(value)} for key, value in {
                   "baseline_manifest": args.baseline_manifest, "subject_map": args.subject_map,
                   "annotation": args.annotation, "admitted_runs": args.admitted_runs, "script": __file__}.items()},
               "runs": qc}
    (out / "matrix_assembly_manifest.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
