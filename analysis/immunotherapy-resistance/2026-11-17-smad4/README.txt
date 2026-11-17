Immunotherapy-resistance analysis — 17 November 2026

Purpose
Sources and numerical provenance for the revised immunotherapy-resistance report, including the17November SMAD4 functional-evidence update. The package separates poor immune recruitment/priming, limited effector expansion, antigen presentation, stromal composition and extracellular suppressive mechanisms. These descriptive analyses do not establish the current node's mechanism or predict response to a particular drug. The user reports insufficient cryopreserved tissue for organoid/tissue-culture experiments; no such experimental proposal is included here.

What is reproducible in this compact package
- RNA: 37 published/mechanistic/composition sets and 1,225 targets; both patient research samples and 18 GSE50760 primary CRC references; total versus same-denominator protein-coding contributions; mean-log expression, median gene differences, leave-one-gene-out ordering, gene concordance, provider-percentile coverage, overlap and rank summaries.
- Proteins: 37 sets and 1,225 targets; common-set rank summaries across four references, two patient-support definitions and 50/80/100% reference coverage; marker-ratio sensitivity to broad ECM, epithelial and smooth-muscle denominators; preserved support/assignment status.
- Recruitment: 156-gene lookup, independent assay columns, reference quantiles, protein support and the available selected liver cell summaries. No new panel activity score is calculated.
- Peptide summaries: counts of exact, leucine/isoleucine-equivalent and fully tryptic gene-specific matches from the preserved full-database match records; 35 targets/278 source-labelled sequences.
- Noncanonical signalling: 160 selected RNA genes across all available sources; the exact published MPAS10 and a separate immediate-early context panel, total/coding/rank/z-score sensitivities, full-universe frozen ranks and 18 CRC references. Eight additional RNA tables are reproduced.
- Protein/SMAD4 audit: 89 selected protein targets; 71 assigned rows; selected common-set reference ranks, peptide-specificity counts, aggregate modification inventory, six derived allele fractions and five WT Gly359 backbone angles. No phospho measurement is inferred. Separately, investigator-reported G359E functional evidence is summarized with explicit assay/classification boundaries.
- Vactosertib: optional re-audit of the original public Source Data workbook, joined internally by subject to outcome, writing only aggregate counts and medians. No subject-level arrays or workbook are redistributed.

Reproduction boundary
This is a compact downstream reproduction, not another raw-read or spectral analysis. It includes full-precision selected RNA TPM values and rank vectors originally calculated against the full 19,619-gene coding universe. Protein rank vectors were calculated against the full eligible common-gene universe for each setting. The scripts DO NOT rerank the selected targets as though they were the complete universe.
The Monash result is an attributed personal-communication paraphrase with public assay-method context. The original email/plot and raw MAVE scores are not bundled; this package cannot independently reproduce that new experimental result or calibrate PS3 strength. Existing33 numerical tables remain unchanged.
Raw-read Salmon quantification, transcript-to-gene aggregation, full-matrix rank construction, public reference preprocessing and the full reviewed-proteome FASTA search are upstream operations. Their source hashes, methods and URLs are retained in provenance/. Optional upstream_recipes/ preserve the numerical algorithms with generic relative paths, but require the unbundled full_inputs layout shown in those scripts. They are not claimed to run from this compact bundle alone. The frozen 42,545-record reviewed human canonical/isoform FASTA is identified by SHA-256; a changing live UniProt query is not an exact replacement.

Data and files
- definitions/: exact set memberships, source attribution, aliases, fixed rank-universe membership, sample columns and composition-marker definitions. Published signatures and analyst-curated panels are distinguished.
- inputs/: selected, full-precision sufficient intermediates for the compact calculations; deterministic gzip CSVs, with no filename header or timestamp. Inputs are NOT independent biological assays.
- rna/, proteomics/, recruitment/: reviewed numerical tables, retained with their original decoded bytes. Each assay keeps its own units, reference and specimen. Selected external CPTAC/iBAQ context tables remain external population observations, not patient differential expression or patient iBAQ.
- noncanonical/ and smad4/: reviewed case evidence, exact panel definitions and selected counts/ranks; inputs/noncanonical/ holds compact sufficient inputs. No raw patient variant files or new peptide sequences are redistributed.
- scripts/: portable downstream reproductions and optional aggregate vactosertib audit.
- literature/: concise source-linked clinical review, human trial evidence and aggregate audit; original journal text, figures, PDFs, workbooks and subject arrays are omitted.
- report/: final materialized pages, references, figure and portable DOCX builder; excludes historical baseline modules. The separately reviewed 59-page PDF is pinned in provenance/report_release.json.
- rankings.json and website/: reviewed current website findings and therapeutic rankings; relative links resolve against https://youngcrc.com/.
- recruitment/assessment.json and primary_literature.json: source-linked priming, expansion and recruitment interpretation, with evidence and counterevidence.
- provenance/upstream_sources.json: original full-source hashes, source/provenance URLs and explicit availability boundaries. A compressed public mirror may require decompression before comparison to an original uncompressed hash.
- provenance/portable_equivalence.json: 27 passed numerical/aggregate checks against the reviewed local analyses. Floats use rtol=1e-7 and atol=1e-7; missingness, row/column order and categorical values are preserved. Count differences cannot pass this tolerance.
- package_manifest.json: exact package file hashes.

Run
Use Python 3.12 (tested 3.12.14) and install requirements.txt:
  python3 -m pip install -r requirements.txt
  python3 verify_package.py
  python3 verify_package.py --rerun
The rerun uses a temporary directory and compares 33 regenerated numerical CSVs plus bounded protein/variant/structure checks to the reviewed tables, without overwriting the package.

Optional original-workbook audit
  python3 verify_package.py --vactosertib-source /path/to/41467_2026_75595_MOESM6_ESM.xlsx
or
  python3 verify_package.py --fetch-vactosertib
The exact SHA-256 is checked before acceptance. A download is stored temporarily and removed afterwards. The script deduplicates repeated treatment-history rows, joins IHC to RECIST/clinical-benefit labels and computes aggregate summaries. It does not calculate a personal response probability, a validated biomarker cutoff or raw baseline RNA similarity. The deposited dose-group DESeq2 summary is not an individual baseline TPM matrix. Full-cohort trial RNA pathway-response reanalysis remains pending. No partial trial RNA scores, significance claims or response classifications are included in this release; response plus durable stable disease is the planned primary benefit category.

Interpretation
All tumour assays are archival: Caris rectal biopsy March 2024; Tempus/BostonGene resection October 2024; B7 protein block from that resection; selected Valius liver October 2024. Blood cfRNA and buffy-coat RNA are separate non-tumour sources. A rounded merged Valius bulk column has unresolved provenance. The current node lacks these molecular measurements.
Identical software does not remove differences in laboratory chemistry, treatment, anatomy, purity or cell mixture. Within-sample ranks, external reference ordering, module averages, provider-percentile medians and protein marker ratios are not calibrated clinical percentiles or pathway-activation tests. Strong smooth-muscle signals are not a measured tumour fraction. Modules overlap and do not provide independent biological replication. Protein presence does not establish active TGF-beta, phospho-signalling, surface display, chemokine gradients or immune killing; nondetection is not biological absence.
Clinical conclusions and therapeutic rankings belong to the current revised report. Earlier November 14 analysis remains available for historical provenance; its experimental suggestions and rankings are not automatically current. Vactosertib pharmacodynamic change, durable stable disease and objective response are different endpoints. Prior BOT/BAL exposure limits extrapolation from checkpoint-naive trials.

Publication
The package contains participant-authorized case-derived analysis and source-linked aggregate research. Private correspondence, internal pathology/case identifiers, local workspace paths, pathology images, withdrawn third-party material, full papers and trial subject arrays are excluded. Existing public inputs are referenced rather than duplicated wholesale. Original third-party sources retain their own terms. No tissue allocation, treatment change or clinical access is effected by these scripts.

Source boundary: SMAD4 G359E has CI=VUS in the provider VCF but is omitted from the printed Caris clinical variant tables. Caris explicitly reports SMAD4 copy number as indeterminate. See smad4/provider_annotation.json and molecular/caris_primary_audit.json. The dated molecular snapshot retains provider-specific calls and separately labelled research interpretation.
