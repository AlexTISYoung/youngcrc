# Target peptide sequence-mapping audit

Audited 2026-10-29. This checks sequence specificity; it does not reprocess instrument spectra, estimate FDR, verify peptide identification, or alter patient quantities.

## Inputs and scope

- `unique_peptide_sequences.tsv`: 151 distinct stripped sequences assigned to the 18 requested targets, originally selected from quantified run422 precursors with vendor `Proteotypic=1`. Charge and modification states have already been collapsed by the main analysis.
- `protein_groups.tsv`: target/gene and protein-group assignments. Every requested target is represented by one single-accession group. The target-specific peptide row counts reconcile exactly to the main table's `n_unique_sequences`.
- Delivered `homo_sapiens_uniprot_2025_06_11_Swissprot.fasta`: 20,422 proteins, 11,413,722 amino acids; 126 entries lack a `GN=` gene annotation. File SHA256: `bf2255e4f2c68aebd4fca5bc6d541606981ffce547fdf4b0ee1ecdd3bf210f95`.

The primary audit finds every full-protein substring occurrence, using a non-amino-acid separator between proteins to prevent boundary matches. It repeats the search after replacing I with L in both peptides and proteins. This tests conservative specificity under leucine/isoleucine equivalence. All matches are mapped to FASTA accessions and `GN=` genes, retaining unknown-gene accessions explicitly.

## Results

All 151 sequences exactly match their assigned target protein. Of these, 150 are gene-specific by literal sequence and 148 remain gene-specific after I/L equivalence, without imposing digestion assumptions.

| Target | Vendor-unique sequences audited | Exact gene-specific | I/L-equivalent gene-specific |
|---|---:|---:|---:|
| CDH17 | 22 | 22 | 22 |
| PTK7 | 19 | 19 | 19 |
| FAP | 14 | 14 | 14 |
| LRRC15 | 8 | 8 | 8 |
| ROR1 | 6 | 6 | 6 |
| CEACAM5 | 3 | 3 | 3 |
| EGFR | 13 | 13 | 13 |
| ERBB2 | 7 | 7 | 7 |
| CD276 | 5 | 5 | 5 |
| PTPN1 | 11 | 11 | 11 |
| PTPN2 | 3 | 3 | 3 |
| B2M | 3 | 3 | 3 |
| HLA-A | 5 | 5 | 5 |
| HLA-B | 5 | 5 | 5 |
| HLA-C | 4 | 4 | 3 |
| TAP1 | 8 | 8 | 7 |
| TAP2 | 11 | 11 | 11 |
| SMARCA4 | 4 | 3 | 3 |

The three exceptions require different interpretations:

1. **HLA-C `THVTHHPLSDHEATLR`**: exact match to HLA-C P10321 at 211. Its I/L-equivalent sequence `THVTHHPISDHEATLR` occurs in HLA-B P01889 at 211 and HLA-E P13747 at 208. All are flanked `K.<peptide>.C` and are fully tryptic. This is the clearest practical sequence-specificity limitation. Three other audited HLA-C peptides remain gene-specific in this reference under I/L equivalence.
2. **TAP1 `IFEYLDR`**: exact match to TAP1 Q03518 at 478, `K.IFEYLDR.T`. I/L-equivalent `IFEYIDR` occurs in XRN2 Q9H0D6 at 81, `A.IFEYIDR.L`. The XRN2 match lacks a conventional tryptic N terminus. Seven of eight are unconditionally sequence-specific; the eighth can still be digestion-specific to TAP1 under fully tryptic assumptions.
3. **SMARCA4 `GLDPVEILQER`**: exact match to SMARCA4 P51532 at 360, `R.GLDPVEILQER.E`, and SMARCA2 P51531 at 336, `Q.GLDPVEILQER.E`. The SMARCA2 match lacks a conventional tryptic N terminus. Three of four are unconditionally sequence-specific; the fourth can still be digestion-specific to SMARCA4. This alone does not demonstrate that the vendor's proteotypic flag is incorrect.

The primary therapeutic-target conclusions retain multiple gene-specific sequences under this conservative test. No target falls below two such sequences. No quantities or main-analysis support flags were changed.

## Digestion-aware comparator and validation

The audit table also includes an explicitly specified comparator: trypsin with no cleavage before proline, at most two missed cleavages, protein termini, and optional initiator-methionine removal. It is a sensitivity check, not a reconstruction of the actual vendor search settings. The table preserves full flanking sequences so the assumptions remain inspectable.

Four target peptides are incompatible with this strict no-cleavage-before-P comparator because they begin or end at an R/K–P boundary: PTK7 `PTYQWFR`, CD276 `DFGSAAVSLQVAAPYSK`, HLA-A `YFFTSVSR`, and HLA-B `YFYTSVSR`. They remain exact and I/L gene-specific; a trypsin/P or permissive cleavage rule would admit them. Do not interpret their comparator flags as failed identifications or subtract them from the primary substring-specificity counts.

An independent second implementation searched each original protein sequence separately, rather than the concatenated sequence. It reproduced every exact and I/L-equivalent accession set for all 151 peptides. The three exception flank contexts were independently inspected.

## Limits

- “Gene-specific” means within this supplied FASTA. It is not a claim of uniqueness across every human isoform, variant, HLA allele, contaminant, or non-human sequence. The HLA reference is particularly limited; this does not establish patient HLA genotype, allele retention, antigen presentation, or T-cell recognition.
- The strict substring audit intentionally does not require that every alternative match be a predicted tryptic peptide. Sequence-level and digestion-aware specificity must not be conflated.
- Sequence matching does not independently establish the correctness of the spectra, chromatographic evidence, library assignment, q-values, or FDR. The delivered instrument raw files and detailed per-identification reports are absent.
- Peptide identity does not establish intact surface localization, accessible therapeutic epitopes, tumour-cell origin rather than stroma/immune cells, or present-day metastatic expression.
- This is a targeted audit of 151 sequences, not a full-dataset reassignment or reanalysis of all 65,000+ observed sequences.

## Files

- Reproducible script: `../scripts/audit_target_peptide_mapping.py`
- Per-peptide full accession/gene mappings and flanks: `target_peptide_mapping_audit.tsv`
- Per-target counts: `target_peptide_mapping_summary.tsv`
- Input hashes and method parameters: `target_peptide_mapping_metadata.json`
