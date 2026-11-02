# Specimen provenance and prior reference-comparison audit

Reviewed and updated 29 October 2026 after inspection of the delivered vendor report, source tables, supplied analyst tracker and public-reference files. Original source files were not edited. The sample-to-run mapping and the report control's numeric source are now verified; the identity of run 423 and the detailed pathology-to-aliquot chain remain unresolved. This audit preceded public-release preparation; publication derivatives preserve its scientific findings.

## Main findings

1. **The pathology meaning of B7 is established.** UCLA accession SSW-24-27123, part B, is the treated rectal low anterior resection collected 22 October 2024. The B6–B7 pair samples a full cross-section of the lesion in relation to uninvolved mucosa and radial margin. The exact proteomics analytical suffix `_43` and section/aliquot chain were never established by the HTML.
2. **The vendor explicitly maps run FZPR260000422-1A to B7_43.** This appears in the actual vendor HTML sample table, despite `B1_43`/`B1-43` in delivery/report identifiers. B1–B2 are distal-margin pathology blocks, but the folder/report identifier must not be substituted for the sample table's B7_43 label. The meaning of the identifier suffix is not established; the run label itself is no longer unresolved.
3. **There are two different “control” columns.** `Pro_Pep.xlsx` control equals run FZPR260000423-1A throughout the protein matrix. By contrast, every one of the 4,186 positive `all_sample.xls` control values exactly equals HPA public normal-colon intensity by gene. This independently corroborates a supplied analyst note reporting vendor confirmation. The report control is an external one-donor tissue reference; run 423's biological identity remains unknown. Neither is established as a matched patient normal.
4. **Low tumour-versus-tumour AUC is not equivalent to failed sample identity, low purity, or absent malignancy.** Patient versus Astral AUC 0.1953 is low but lies inside the Astral leave-one-out range 0.061–0.8939. Several like-versus-like controls show systematic cohort offsets. These results undermine a clinically calibrated overexpression interpretation, not the existence of protein detections.
5. **A single archived, treated rectal section and external heterogeneous cohorts cannot identify a patient-specific tumour/normal treatment effect.** New quantitative exports can improve identification QC, abundance descriptions, and reference-relative sensitivity analyses, but cannot create biological replication or a matched normal.
6. **Reported identification FDR and differential-expression p-values require different treatment.** The vendor states 1% identification filters, but the delivered matrices lack q-values and the full search output/logs. Its differential report names Significance A, generic methods name a t-test, and its README says no-replicate analyses should use fold-change alone. These p-values do not establish replicated biological differential expression; the HPA comparison also confounds specimen and technical effects.

## Original pathology crosswalk

Primary local report: `https://youngcrc.com/reports/clinical/clinical_her2_pathology.pdf`.

Public prepared copy: [Resection pathology and HER2 add-on](https://youngcrc.com/reports/clinical/clinical_her2_pathology.pdf).

- Page 2 reproduces accession **SSW-24-27123**, collected **22 October 2024, 13:07**, received 23 October. Part B is **rectum, low anterior resection**.
- Page 3 describes residual moderately differentiated adenocarcinoma, extensive mucinous features following neoadjuvant treatment, many acellular mucin pools, and partial response score 2.
- Page 5 cassette key: **B1–B2 distal margin, shave**; **B3 proximal margin, shave**; **B4–B5 lesion cross-sections nearest serosa**; **B6–B7 lesion cross-section in relation to uninvolved mucosa and radial margin**; B8–B17 further lesion cross-section pairs; B18 uninvolved mucosa; B19–B29 regional nodes; B30–39 additional fat. No B43 is listed.
- The B6–B7 description applies to the paired section. It does not enumerate each structure separately in B7 alone.
- Part C is the left lateral liver segment; C4 supplied the prior liver IHC. B4 is associated with prior Tempus/BostonGene work. Their tumour fractions must not be assigned to B7.
- Page 6 original report signature: 28 October 2024.

Independent source: original Signatera report `original Signatera report dated 22 October 2024 (source retained locally)`, pages 1–2, explicitly identifies **SSW-24-27123 (B7)**, tissue collected 22 October 2024, received 3 December 2024, block type slides. The later report at [youngcrc Signatera](https://youngcrc.com/reports/natera/natera_signatera.pdf) gives the same block. This identifies B7 pathology; it does not independently establish which proteomics raw run arose from that block.

Prior detailed source audit: `22 October pathology source audit (retained locally; summarized here)`.

Interpretation: bowel-wall muscle, margin-region stroma and post-treatment changes are plausible contributors to the muscle/stroma-rich proteomic pattern. Their proportional contribution remains unmeasured. FAP detection in this old primary does not establish FAP abundance or target distribution in current metastatic nodes.

## Supplied HTML and what was actually available on 22 October

Files:

- `https://youngcrc.com/reports/proteomics/B7_43_proteomics_explorer.html`
- `second byte-identical supplied B7_43 explorer copy`

Both are 2,942,141 bytes with SHA-256 `9bef2ee589f4f32db211ea21a67b41622f1b9a9ab0e8da58155bc6b804ee0243`.

The HTML was parsed as data without running its JavaScript. Its patient reference row labels B7_43 as FFPE primary colorectal tumour measured by Orbitrap Astral, DIA (300 × 2 Th), library-free DIA-NN. Its prose states that no healthy tissue was usable as a reference and that the FFPE section was cleared by the pathology centre. There is no B1_43 text in the supplied report.

`22 October explorer extraction (retained locally; counts summarized here)` contains:

- 7,706 protein-group rows;
- 186 validation rows;
- 53 selected antibody/surface panel rows;
- 14 reference-source rows.

The patient protein table contains unique-peptide counts and reference-derived annotations/ranks, but no patient signal-intensity column. The 6,468 confident groups are defined by at least two unique peptides, single-gene mapping and absence from the contaminant list. That is an identification-support filter; it is not by itself an independently verified peptide/protein false-discovery-rate threshold. The raw pipeline outputs must establish q-value filtering and protein-inference details.

The 22 October script `analyze_report.py` copied these annotations and made exact gene-symbol joins to separate RNA assays. It did not recompute the reference AUCs from primary intensity matrices. Thus all AUCs below are transcribed/reaggregated source results, not independently reproduced calculations.

## Reference design and AUC interpretation

The source defines each protein's score as its within-sample percentile in the query minus its median percentile in the reference. AUC tests whether proteins labelled tumour-up by external CPTAC tend to have higher scores than proteins labelled tumour-down. It is a descriptive rank-separation statistic. It is not a sample-level cancer diagnostic probability, a tumour-purity measurement, a calibrated patient-expression percentile, or an estimate of response to a targeted drug.

| Comparison | Query count | Source expectation | Median AUC | Observed range |
|---|---:|---|---:|---|
| Komor cancer vs Komor normal | 30 | >0.5 | 0.89455 | 0.6676–0.9257 |
| Komor normal vs other Komor normals | 19 | 0.5 | 0.5159 | 0.2502–0.8726 |
| Astral tumour vs other Astral tumours | 27 | 0.5 | 0.5323 | 0.0610–0.8939 |
| Astral tumour vs Komor normal | 27 | >0.5 | 0.7605 | 0.3842–0.8612 |
| Astral tumour vs HPA colon | 27 | >0.5 | 0.8216 | 0.4799–0.8929 |
| HPA colon vs Komor normal | 3 | 0.5 | 0.4082 | 0.3887–0.4164 |
| Komor normal vs HPA colon | 19 | 0.5 | 0.6050 | 0.4538–0.7619 |
| Komor cancer vs Astral tumour | 30 | 0.5 | 0.64435 | 0.3253–0.7107 |
| B7_43 vs Komor normal | 1 | >0.5 | 0.4249 | — |
| B7_43 vs HPA colon | 1 | >0.5 | 0.5567 | — |
| B7_43 vs Astral tumour | 1 | 0.5 | 0.1953 | — |
| B7_43 vs Komor cancer | 1 | 0.5 | 0.1825 | — |

The tumour-versus-tumour expectation differs from the tumour-versus-normal expectation: an AUC of 0.5 in a like-versus-like comparison is not a failed test. Conversely, 0.1953/0.1825 means an inverse tendency of these external gene-set scores relative to those references. The cause could include specimen composition, treatment state, protein detection/filtering, rank-universe differences or technical effects. These numbers do not identify the cause.

The patient-versus-Astral statistic is **within** the very broad Astral leave-one-out range: 6 of 27 reference tumours have a lower AUC than 0.1953. It must not be described as uniquely outside the reference distribution. Those controls also should not be used as a formal null distribution without checking that gene overlap, ranking, reference membership and missing-data handling are identical; 6/27 is a descriptive count, not a calibrated patient percentile or p-value. The patient-versus-Komor value cannot simply be compared to Komor-versus-Astral controls as though they were the same experiment.

Like-versus-like cohort medians away from 0.5 (especially Komor cancer vs Astral tumour 0.64435) demonstrate residual systematic differences under the supplied scoring approach. Tumour-versus-normal positive controls show that some general colorectal contrast transfers between studies; they do not validate individual-patient expression differences for every protein.

### Concrete cohort differences already documented in the report

- Astral PXD073413: 27 CRC tumours (13 KRAS-mutant, 14 wild type), 4 pooled QC runs excluded; SDRF cell-type label epithelial cell, but tissue preparation not stated in the report. Same instrument family does not mean the same batch, protocol or cellular composition. The epithelial label should not be silently converted into proof of purified malignant epithelium.
- Komor PXD012254: Q Exactive HF DIA, Spectronaut protein groups, fresh-frozen tissue; 30 cancer runs and 19 normal-mucosa runs (paper reports 18 normal samples). Runs must not be assumed to represent independent people until sample identities/replicates are resolved.
- HPA colon: 3 FFPE tissue measurements from **one healthy female donor**, Astral Zoom DIA, DIA-NN 1.9.2 and directLFQ. The [official detailed methods](https://www.proteinatlas.org/humanproteome/tissue/method/MS%2Bbased) establish the donor count; these are not three independent healthy people. The report control uses the tissue-level summary, not a matched patient sample or a healthy-population reference distribution.
- CPTAC labels: external colon TMT proteomics, 97 tumours, 100 normals and 96 pairs. They are population labels learned in another cohort, not measurements of this patient's tumour or adjacent tissue.

### Reanalysis checks before ranking patient overexpression

1. Resolve project label, acquired run name, raw-file metadata, DIA-NN output sample columns and provider specimen sheet. Compare new patient unique-peptide identities/counts against the old 7,706 groups to test whether the new export is actually the source of the old report. An exact numeric match supports analytical continuity, not an independent pathology chain.
2. Separate biological samples, repeat injections, pooled QC, blanks and attempted normal material. Do not inflate sample size using runs or peptide observations as patient replicates.
3. Establish peptide/protein q-value thresholds, precursor filtering, library-free versus refined-library stage, interference treatment, protein-group-to-gene mapping and duplicate-group handling.
4. Inspect quantitative distributions, missingness, zero encoding, shared-gene/peptide overlap, technical reproducibility and sample loading. Confirm whether values are raw quantity, normalized quantity, MaxLFQ-like estimates or arbitrary rank scores before combining data.
5. For external comparisons, evaluate common-gene rank universes, identical filtering, treatment/fixation/platform differences and sensitivity to stromal/epithelial composition. Report multiple reasonable normalizations if their conclusions differ.
6. Do not apply batch correction as though batch and patient identity were separable when the only patient specimen is in its own batch. Such correction can remove true biology or force agreement with the reference.
7. Present target ranks and reference-relative values descriptively with assay/specimen caveats. Neither an extreme rank nor a nominal gene-wise comparison establishes a clinical biomarker without appropriate controls and tumour-compartment validation.

## Verified vendor delivery and control provenance

Source root: `raw/vendor_delivery/` under this review directory. The first version of this audit preceded delivery; the following findings supersede its unresolved run-label/control questions.

### Sample/run identity

- `Report-X202SC26085414-F01-F001-B1-43/report.html`, lines 341–342, explicitly gives **FZPR260000422-1A / B7_43 / B7_43** and **AO / control / control** in its sample table. Its report date is 12 October 2026, distinct from a tissue collection or instrument acquisition date. The report number is `X202SC26085414-Z01-F001-B1-43`.
- `Match_result-X202SC26085414_F01_F001_B1_43/report.pg_matrix.tsv` has two quantity columns: `FZPR260000422-1A.raw` and `FZPR260000423-1A.raw`.
- `Result-X202SC26085414_F01_F001_B1_43/3.ProtExprQuantification/Pro_Pep.xlsx`, Protein sheet, has 7,755 rows. After matching the first accession of each matrix protein group, its `B7_43` and `control` values each match the corresponding run 422 and 423 matrix columns across **all 7,755 rows, including missingness**. Run 422 has 7,706 positive values; run 423 has 7,688.
- The `B7_43` values in `all_sample.xls` equal workbook/run-422 values multiplied by **1.052755024634099** across all 7,706 shared positive entries. This verifies quantitative continuity, with a constant rescaling, rather than a separate patient measurement. The factor's procedural rationale is not documented by this numeric match.
- Neither vendor table includes UCLA accession SSW-24-27123, collection date, section number, `_43` definition, tumor cellularity or block-to-extraction custody. The prior pathology and Signatera crosswalk establishes what B7 means in that accession; it does not independently fill these laboratory chain details.

### AO/report control is public HPA normal colon; run 423 remains unknown

The supplied `Target_analysis_plan_tracker.docx`, extracted to `analysis/shared_tracker_text.txt` (lines 21 and 332), states that on 20 October Novogene confirmed `all_sample.xls` control came from HPA `ms_tissue.tsv`; it separately leaves run 423 unexplained. This is an analyst's supplied record of a vendor conversation, not the conversation itself.

Independent numeric check against `raw/shared/analysis/refs/ms_tissue.tsv`, `Tissue = colon`:

- `all_sample.xls` has 7,709 rows and **4,186 positive control values**.
- All 4,186 join to HPA by gene symbol and **all 4,186 equal the HPA intensity exactly** (all ratios 1.0; no positive vendor controls left unexplained).
- The HPA gene-symbol duplicates TBCE and NOX5 have identical quantities/missingness across their Ensembl IDs; they were collapsed only for this validation join. Original files remain intact.
- Conversely, the report control differs from workbook/run 423: 4,177 shared positive values, no exact matches, and widely varying ratios. It cannot be treated as a rescaled copy of run 423.

The audit result is saved in `analysis/control_provenance_check.json`. The “AO” label itself is not explained, but the numeric source of its report quantities is established. The user's lack of knowledge about the control is consistent with this supplied external-reference provenance. **Exclude the vendor report's fold-changes, differential labels and downstream enrichment as patient-specific tumour-versus-normal findings.** Run 423 must also be excluded from normal, replicate, purity or treatment-effect interpretations until its identity is independently resolved.

### Vendor methods: stated settings versus independently checkable evidence

The project HTML identifies Vanquish Neo–Astral, DIA-NN, **Fragment Quantification**, trypsin, two missed cleavages, C carbamidomethylation and N-terminal methionine excision. The supplied FASTA contains **20,422 sequences**, matching the stated `homo_sapiens_uniprot_2025_06_11_Swissprot.fasta` database. The generic methods text describes 200 ng injection, 380–980 m/z, 300 ×2-Th DIA windows and 3 ms maximum injection time. These are vendor-reported settings, not independently recovered instrument metadata.

The project HTML says `Global.Q.Value < 0.01` and `PG.Q.Value < 0.01` and calls the latter global. The generic methods instead name `Lib.Q.Value ≤ 0.01` and `Lib.PG.Q.Value ≤ 0.01`, and retain a `*** protein database` placeholder. These are not interchangeable q-value fields in current DIA-NN documentation. The delivery contains no original per-observation q-values, complete DIA-NN long report/parquet, software/version log or command/configuration. Accordingly, describe the filtering as **vendor-reported nominal 1% identification FDR**, not independently verified run/global FDR or a 99% probability for every target.

The delivered vendor directory contains **no `.raw` instrument files**. Its raw-data README says those are supplied separately as `Raw_file-*.zip`; that archive is absent from this local delivery. It contains protein/precursor matrices and derived results. The `report.pg_matrix.tsv` headers do not themselves identify the algorithmic quantity as `PG.MaxLFQ`, TopN or iBAQ. Preserve it as the vendor protein-group quantity unless the original processing metadata settles that field.

### Differential statistics and internal report inconsistencies

The actual HTML section 4.1 says **Significance A** generated the p-values. Its generic methods text says **t-test**, while `4.DiffExprAnalysis_README.txt` says analyses without biological replicates use **fold-change only**. With one patient specimen, an external HPA summary and no matched/replicated experimental design, the reported p-values cannot quantify patient-level biological variance or establish patient-specific differential expression. A distribution-based Significance A score can be computed mathematically; it must not be represented as a valid replicated tumour–normal test. Multiple-testing and model details are not established by the exported table.

There is also a threshold/count discrepancy. The 4,183-row comparison table contains 486 rows with p<0.05, labelled 215 up and 271 down. Applying the report's stated additional cutoffs (FC>2 or FC<0.5) gives **187 up +271 down =458**, not 486. Thus 28 “up” rows fail the stated FC>2 rule. These are source-report inconsistencies, not a corrected patient differential analysis; none of these calls is used for therapeutic inference.

## Komor run count versus independent samples

The actual shared `PXD012254/ProteinGroups_Normal_Adenoma_Cancer_Search.xls` is tab-delimited text with `R.Condition`, `R.FileName`, `R.Replicate`, protein fields and `PG.Quantity`. Deduplication of its run annotation gives **79 distinct file names: 19 normal, 30 cancer and 30 adenoma**. `R.Replicate` is an ordinal within each condition (1–19, 1–30 and 1–30); it does not repeat within a condition, but it provides no donor identifier, pairing or proof of biological independence. The 79 annotation rows are preserved in `analysis/komor_run_metadata.tsv`.

The original report's 18-normal-sample versus 19-normal-run discrepancy is not resolved by these ordinal labels. Report **19 normal reference runs and 30 CRC reference runs**, without claiming 19/30 independently verified donors. The nearby file `WRONG_copy_of_PXD073413_sdrf.tsv` is indeed Astral/KRAS metadata (its first source is `P01-M24359769a-KRAS/G12D(Tumor)`), and must not be used as Komor donor metadata. Obtain the correct source sample sheet/publication supplement to resolve independence and the extra normal run; do not guess which run to remove.
