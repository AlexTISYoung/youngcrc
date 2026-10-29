# Download and structure audit: Robles public CRC reference

Downloaded 29 October 2026 from the [EMBL-EBI repository](https://ftp.ebi.ac.uk/pub/databases/pride/resources/colorectalcancer/). `download_manifest.json` records URLs, UTC retrieval timestamps, byte counts and SHA-256 hashes. Original files are unchanged. `reference_structure_qc.json` contains reproducible counts and metadata discrepancies. No patient-data comparison was performed.

## Files available

- `CPTAC-PDC000111/`: original gene matrix, SDRF, analysis methods, IDF, MaxQuant XML and README. Matrix size 4,644,494 bytes.
- `Solid_samples/Solid_samples.rar`: 75,582,485 bytes, downloaded successfully.
- Extracted from the archive: `proteinGroups_ppb_final.txt` (23.5 MB), `proteinGroups_ppb_final_binning.txt` (6.4 MB), `Sample_classification.txt` (12 KB).
- The original 486.8 MB MaxQuant `proteinGroups.txt` remains available inside the archive; its header was inspected without extracting the full file.

## Unit and processing verification

The downloaded methods and MaxQuant configuration confirm label-free MaxQuant 2.1.0.0, iBAQ enabled, match-between-runs enabled, protein and peptide FDR 1%, human UniProt September 2020 one-protein-per-gene database, followed by removal of contaminants/decoys and ambiguous or absent gene mappings. The normalized matrix headers specify **ppb.iBAQ**, fraction-of-total iBAQ expressed in parts per billion. It is neither TMT reference ratios nor patient LFQ intensity, concentration or copies/cell.

Column sums are below 1 billion after the documented mapping/filtering: approximately 0.557–0.832 billion in the standalone PDC matrix and 0.372–0.882 billion in the combined sample matrix. Preserve these provided values; renormalizing the surviving mapped subset to 1 billion changes the quantity. There are no numeric zeros or negative quantities in either matrix. Missing values must remain missing.

## Standalone PDC000111 matrix

6,089 unique Ensembl gene IDs and unique gene symbols ×90 sample columns. There are 322,462 observed numeric values and 225,548 missing cells. Per-sample coverage ranges from 2,397 to 4,418 genes. SDRF labels 60 colon and 30 rectal samples, all tumors, with 42 female/48 male samples. Eleven rows are stage IV; the rest are mainly stage I–III, with three unspecified.

Two metadata defects prevent an unqualified donor-level reference interpretation:

1. After consistently replacing matrix-header hyphens with periods, 89/90 columns join to SDRF. Matrix column `ppb.iBAQ.Tumour-ColonAdenocarcinoma_1_Zhang_READ` is unmatched; the unmatched SDRF row is `ppb.iBAQ.Tumour.RectalAdenocarcinoma_1_Zhang_READ-1`. This is a plausible naming error, but the link has **not** been assumed or repaired.
2. Two distinct columns, `...ColonAdenocarcinoma_27_Zhang_COAD` and `...ColonAdenocarcinoma_28_Zhang_COAD`, share `individual 28` in SDRF but have different stages (IIIC and IIA). This could be a clerical error rather than a true repeated donor. Do not silently collapse them or call the matrix 89 confirmed donors. The public source describes 90 people; the anonymized individual labels need reconciliation.

The original source study had 95 aliquots from 90 people, whereas this reanalysis matrix has 90 columns. Do not carry the original 95-aliquot denominator into this matrix.

## Combined solid-tissue matrix

8,949 unique genes ×274 annotated samples, with 1,139,209 observed numeric values. Every annotated sample name matches a matrix column exactly. Metadata contains only sample name, dataset, tissue class and organ; donor, stage, sex and pairing are not present.

| Dataset | Tumor | Mucosa | Adenoma | Measured genes per sample: minimum / median / maximum |
|---|---:|---:|---:|---|
| CPTAC | 90 | 0 | 0 | 2,435 / 3,752 / 4,639 |
| PXD001676 | 8 | 8 | 0 | 863 / 1,093.5 / 1,396 |
| PXD002137 | 8 | 8 | 16 | 5,414 / 6,871 / 7,556 |
| PXD014511 | 0 | 17 | 45 | 169 / 4,768 / 5,789 |
| PXD019504 | 37 | 37 | 0 | 2,209 / 3,860 / 4,826 |
| Total | 143 | 70 | 61 | 169 / — / 7,556 |

**Exclude `ppb.iBAQ.peptides`:** this is an additional numeric column without sample metadata. The original MaxQuant header contains `iBAQ peptides`, which is peptide-count metadata. Its processed version is not a biological observation. The 274-sample counts above exclude it.

The 90 CPTAC columns use distinct original-style TCGA identifiers, for example `ppb.iBAQ.TCGA.AG.A036`. This subset is preferable for tracking source cases to the standalone anonymous matrix. However, the two matrices come from separate reanalyses with different protein coverage and quantities; they overlap biologically and must not be pooled as independent samples.

The adenoma `ppb.iBAQ.S5E6_` (PXD014511) has only 169 measured genes. PXD001676 has very shallow coverage throughout. These samples/studies need explicit QC consideration rather than automatic inclusion in pooled percentile calculations. No source rows were removed or repaired in this audit.

## Credible comparison use

Use this resource as independent, approximate protein-abundance and detection context, keeping studies and tissue classes separate. The combined CPTAC subset supplies 90 labeled tumor samples; PXD019504 and PXD002137 provide within-study tumor/mucosa sets once original donor/pairing metadata is verified. Do not treat all 143 tumors and 70 mucosa samples as a single matched or uniformly measured population.

For patient comparisons, a ppb-iBAQ-versus-LFQ quotient is not a fold-change. Rank comparisons remain exploratory and require sensitivity to common protein coverage and sample composition. Public tumor–normal differences should be calculated within each study and reported as public biology, separate from the patient's measured signal. Low coverage, missingness, different acquisition/preparation and bulk-tissue composition materially limit a calibrated patient percentile.
