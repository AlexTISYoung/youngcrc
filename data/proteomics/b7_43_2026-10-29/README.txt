B7_43 quantitative proteomics — portable public release
29 October 2026

START HERE
Report: ../../../reports/proteomics/quantitative-2026-10-29/index.html
Public URL: https://youngcrc.com/reports/proteomics/quantitative-2026-10-29/index.html
Machine-readable index: index.json
Complete website source package: https://youngcrc.com/downloads/source.zip
Download the website source to preserve the data/ and reports/ directory layout.
The report's target table works locally without a server or remote scripts.
Its three displayed PNG figures are external; all four scientific PNGs are under
reports/proteomics/quantitative-2026-10-29/figures in the website source.

THIS RELEASE
Contains the original processed protein-group and precursor matrices, the
Protein worksheet as a TSV derivative, identifier mapping, prior RNA annotation,
frozen search FASTA, contaminant library, all main numerical analysis outputs,
selected evidence/audit notes and the six analytical/report steps. Original
local files remain untouched. source_transformations.json records original and
published hashes plus changes. Text FASTA files use .fasta.txt and tab-delimited
vendor .xls files use .tsv without changing their bytes. The original workbook
is retained locally; its Protein worksheet export preserves all scientific cells.

LARGE DOWNLOADS AND PACKAGE CHOICE
Four large files are served directly on the website only as .gz downloads:
- analysis/public_ibaq_context.tsv.gz
- analysis/proteins_with_prior_RNA.tsv.gz
- raw/vendor_delivery/Match_result-X202SC26085414_F01_F001_B1_43/report.pr_matrix.tsv.gz
- raw/vendor_delivery/Match_result-X202SC26085414_F01_F001_B1_43/homo_sapiens_uniprot_2025_06_11_Swissprot.fasta.txt.gz
Their uncompressed originals remain in downloads/source.zip. The curated-data
ZIP contains the gzip copies instead; decompress those copies beside themselves,
removing only the final .gz suffix, before running the analytical scripts. The
source ZIP is the simplest option for local analysis and preserves the original
paths and bytes. Website report links intentionally use the compressed download
URLs; source-package readers can use the corresponding uncompressed local files.
Compressed and decoded hashes are recorded in download_manifest.json/index.json.
The input checker also accepts --fetch-inputs (an alias of --fetch-references)
to retrieve a missing PR/FASTA input as well as missing frozen references. It
does not overwrite existing files or automatically fetch derived output tables.

LIMITS ON REPRODUCIBILITY
This is not a complete raw-spectrum release. Instrument .raw files were not
recovered/researched; identification q-values and search version/configuration
were not supplied in the exported matrices. Run 422 is explicitly labelled
B7_43. The separate run 423 remains unidentified. No raw-spectrum re-search was
performed, and no provided vendor script was executed as an instruction.

Thirteen frozen third-party reference inputs are hosted separately as gzip text
downloads; they are excluded from the main source and curated-data ZIPs.
download_manifest.json records exact original paths, bytes, SHA-256 hashes,
source accessions, retrieval sources and the public compressed copies with their
own hashes. This includes the frozen Open Targets custom snapshot and the
supplied CPTAC/other derived exports: current database endpoints need not be
substituted. Reference attribution and source terms are in reference_credits.json.
The input checker can retrieve the exact frozen copies with --fetch-references,
verify compressed and decoded hashes, then restore the expected relative paths.
Existing files are never overwritten. Raw instrument spectra remain unavailable.
The report, numerical outputs, patient-data checks, peptide audit and report
rendering can be reused from the source ZIP. Full numerical reproduction also
requires these separate reference downloads.
The original local package was reproduced with those frozen files: six scripts
succeeded and nine principal tables matched numerically. That historical result
is retained in analysis/reproduction_check.json; it is not a claim that the
source ZIP already contains every input; references are separate downloads. No heavy analysis was rerun during
publication preparation.

REPRODUCTION AND VERIFICATION
Use Python >=3.9 with pandas, numpy, scipy, matplotlib, markdown, beautifulsoup4
and openpyxl (the latter records the original environment; public metadata read
now uses TSV). Original environment versions are in analysis/final_validation.json.
From this data directory:

  python scripts/check_reproduction_inputs.py
  python scripts/validate.py

By default the input checker only verifies local files and reports missing
inputs. Explicitly download and verify the frozen reference copies before
a full rerun:

  python scripts/check_reproduction_inputs.py --fetch-references --require-complete
  python scripts/analyze.py
  python scripts/supplement.py
  python scripts/summarize_public_ibaq_context.py
  python scripts/audit_target_peptide_mapping.py
  python scripts/build_report.py
  python scripts/validate.py

analyze/supplement write scientific figures to this data directory's figures/;
build_report copies generated figures to the report directory and writes the
public report there. With the included outputs/figures, build_report can also
rebuild the report without retrieving the omitted raw reference matrices.
The public validator writes analysis/public_validation.json; original historical
validation and reproduction receipts are preserved. Native patient matrix bytes
are separately verified in source_transformations.json and download_manifest.json.

CONTROL IDENTITIES AND INTERPRETATION
The workbook control equals run 423, whose biological identity is unknown.
The differential-report AO/control independently matches HPA public colon:
all 4,186 positive values equal that table exactly. HPA has three tissue
measurements from one donor, not a matched patient normal or population cohort.
Both are excluded from patient tumour-versus-normal conclusions.
B7 is archival treated rectal resection (22 October 2024); the vendor maps B7_43
to run FZPR260000422-1A. Exact aliquot/section chain and current-node protein
expression are not established by this release.

QUANTITY DEFINITIONS
intensity: native run-422 protein-group signal in arbitrary units, not molecules.
run423_intensity: unknown companion run, never a patient normal or assumed replicate.
n_unique_sequences: distinct stripped sequences labelled Proteotypic=1 in the
supplied precursor data; not independent biological replicates or reconstructed FDR.
unique_top3_mean_signal: average of the three largest unique-sequence signals,
after summing charge AND modification states; missing with fewer than three.
signal_percentile_all_detected: rank within 7,706 measured protein groups, not a
population expression percentile or concentration estimate.
high_support: analysis filter, not clinical validation. Endogenous keratins flagged
by the contaminant library are restored in the inclusive sensitivity outputs.
rank_shift_points: patient common-set rank minus median reference rank; exploratory.
centered_log2_signal_contrast and marker ratios: cross-study/composition-dependent
signal summaries, not validated tumour-normal fold changes or per-cell expression.
No patient missing-value imputation or differential-expression P values are used.
Public paired CPTAC P values/FDR describe 96 public cases only, not this patient.
Public ppb-iBAQ summaries stay separate by dataset/tissue class and are not on the
same quantitative scale as patient DIA signal. Komor normal has 19 run columns;
its paper reports 18 samples, so independent donor/replicate mapping is unresolved.

CLINICAL SCOPE
FAP/LRRC15/ROR1 are target-validation leads; CDH17/PTK7 have strong identification
support without unusual Astral-reference elevation. Bulk signals do not identify
current cancer-cell membrane expression. HLA/B2M/TAP/PTPN1/2 detection does not
prove functional antigen presentation, pathway dependence or combination efficacy.
The full FAP/checkpoint/IL-12/15/vaccine/PTPN-inhibitor combination remains untested.

ATTRIBUTION AND RIGHTS
Patient-owned data and newly authored analysis retain the repository's applicable
terms. Third-party database sequences, annotations, measurements and publications
retain their original source licenses; this release does not relicense them.
The exact delivered Swiss-Prot FASTA is attributed to UniProt, filename dated
2025-06-11; see https://www.uniprot.org/help/license (CC BY 4.0 for UniProt data).
The delivered contaminant library is retained for reproducible membership checks;
see the source named in download_manifest.json. Derived HPA/CPTAC/PRIDE/Open Targets/
SURFY/CSPA summaries must retain those sources and their individual caveats.
The primary pathology reference uses the already-published reviewed copy:
https://youngcrc.com/reports/clinical/clinical_her2_pathology.pdf
