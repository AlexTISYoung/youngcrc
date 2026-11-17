# Vactosertib trial pathway analysis — 28 baseline samples

**Final all-28 scientific results have passed independent numerical, metadata and quality review.** None of the four prespecified primary pathway scores showed a significant association with study-defined clinical benefit after four-test correction (all q = 0.521). This does not establish equivalence or absence of benefit. Report/PDF integration has its own readiness gate, separate from the completed scientific results.

The question is whether four prespecified TGF-beta/fibroblast/ECM pathway scores in screening-linked tissue are associated with later benefit in the published vactosertib plus pembrolizumab colorectal cohort. Primary analysis is study-defined clinical benefit—confirmed complete/partial response or stable disease maintained at least six months (five versus 23); objective response alone (two versus 26) is a separately labelled secondary sensitivity. The six-month condition applies to stable disease, not every responder. Frozen source labels using “durable clinical benefit” must be read with this explicit definition. This is a single-arm exploratory association, not a treatment-effect interaction, clinical selection assay or personal response probability.

## Included sources

- `analysis/pathway_response.py` and `analysis/prepare_inputs.py` are byte-identical to the frozen analysis sources. The first performs the four pathway tests; the second aggregates every quantified transcript contribution by canonical gene symbol.
- `methodology/locked_pathways.json` preserves all four exact memberships and published definition sources. `analysis_plan.json` removes a published subject identifier and local source references but preserves the scientific plan. Original source hashes and the full execution-lock5 hash inventory are retained in `provenance/`.
- `inputs/` contains only public ENA run accessions, technical sequencing fields and FASTQ URLs/bytes/MD5. It excludes sample aliases, subject identifiers, collection dates and outcomes.
- `scripts/` provides external-source retrieval with hash checks, local clinical-join reconstruction, exact reference-annotation regeneration, and a complete-cohort entry point for independently admitted native outputs.
- `results/` contains aggregate results, shared gene universes, coverage, technical/biotype summaries and independent verification. It contains no subject-labelled expression or clinical rows. The 24 endpoint/scoring rows, all 72 unstratified/stratified exact tests, effect sizes and both BH4 families were independently reproduced.
- `analysis/independent_verify_final_statistics.py` preserves the independent verification algorithm without importing the production scorer. Its actual full-cohort audit is recorded in `results/independent_numeric_verification.json`.
- `tests/` exercises the statistical implementation using generated data only. `validation/` preserves historical scaffold checks, distinctly dated. Test reruns print findings without overwriting those receipts.

The original source article is [Nature Communications, DOI 10.1038/s41467-026-75595-4](https://www.nature.com/articles/s41467-026-75595-4). RNA reads are under [PRJNA1337917](https://www.ncbi.nlm.nih.gov/bioproject/PRJNA1337917). This package complements the separately published [case report incorporating the Monash SMAD4 update](https://youngcrc.com/reports/research/immunotherapy_resistance_report_2026-11-17_smad4.pdf); that historical report predates this completed trial comparison. The reviewed [64-page consolidated report](https://youngcrc.com/reports/research/immunotherapy_resistance_report_2026-11-17_trial_analysis.pdf) has its own public metadata and distinct immutable PDF filename.

## Reproduction boundary

This small package does **not** redistribute FASTQ reads (161.0 GB compressed for baseline alone), the 594.5 MB index, full papers, supplemental workbooks, subject-labelled expression/clinical matrices, or private execution logs. Reproducing the full analysis requires retrieving original public sources, quantifying all 28 baseline runs, reconstructing joins locally, and independently admitting the native outputs. The package alone cannot recreate numerical results without those external inputs.

The portable numerical scripts reproduce the locked calculation once these inputs are available. The original machine-specific scratch-space scheduler, process supervision and recovery automation are not redistributed. The quantification recipe and pinned reference/software provenance below specify the scientific computation; a new operator must implement and audit transfer/preprocessing/native-output integrity. The portable admission wrapper is an additional guard, not a substitute for that review. It cannot independently prove a reviewer assertion that raw downloads were checked when the raw files are absent.

Public trial-source metadata can change. `fetch_source.py` refuses changed hashes rather than silently replacing the analyzed inputs. If a repository no longer serves the pinned representation, retrieve the archived representation or document a source-equivalence review. Do not substitute a dose-group DESeq2 summary for the individual expression matrix.

## Reproduction steps

Use a separate local working directory, denoted `WORK` below; do not put subject-labelled outputs back into this public package. Install the pinned numerical requirements in an isolated environment. The original numerical runtime was Python 3.12.14, NumPy 2.3.5 and pandas 2.2.3. `software/` records preprocessing versions and original wheel hashes.

```sh
python -m pip install -r requirements.txt
python scripts/fetch_source.py ena_runs --out WORK/sources
python scripts/fetch_source.py ena_run_checksums --out WORK/sources
python scripts/fetch_source.py ncbi_sra_fullxml --out WORK/sources
python scripts/fetch_source.py clinical_source_workbook --out WORK/sources
python scripts/fetch_source.py gencode37_fasta --out WORK/reference
python scripts/build_reference_annotation.py --fasta WORK/reference/gencode.v37.transcripts.fa.gz --out WORK/reference
python scripts/reconstruct_metadata.py --sources WORK/sources --out WORK/metadata
```

Build a Salmon 2.8.0 transcript index from the pinned GENCODE37 FASTA with `--gencode`, k31, default duplicate collapse and no genomic decoys. Match sequence/name hashes and index configuration in `provenance/reference.json`. The original binary hashes are retained for audit; binary identity across platform/rebuild is not assumed.

Retrieve both mates for each run in `inputs/baseline_fastq_technical.json`. Verify exact compressed byte counts and ENA MD5 before use, retaining SHA256 receipts. Baseline selection is fixed by the 28-run inventory, never by pathway score or outcome. Raw data management and disk requirements are the reproducer's responsibility.

The locked SMARTer Pico v2 preprocessing uses Cutadapt 5.2:

```sh
cutadapt -j 6 -a NNNAGATCGGAAGAGCACACGTCTGAACTCCAGTCA -A AGATCGGAAGAGCGTCGTGTAGGGAAAGAGTGT -U 3 -O 10 -e 0.1 -m 31:31 --pair-filter any --compression-level 6 --json CUTADAPT_JSON -o CLEAN_R1 -p CLEAN_R2 RAW_R1 RAW_R2
salmon quant -i INDEX -l A -1 CLEAN_R1 -2 CLEAN_R2 -g TRANSCRIPT_TO_GENE -p 10 --seqBias --gcBias --allowDovetail --sigDigits 8 --no-progress -o OUTPUT
```

No quality/polyG/rRNA filter, deduplication or inferential bootstraps are added. The R1 leading wildcard triplet is removed only when adapter read-through is detected; R2 first-three-base trimming is unconditional. Lossless pigz compression was independently checked for identical decoded FASTQ output; it changes runtime, not sequence content. Automatic library detection remains `-l A`; independently reviewed ISR and weak-directionality IU results require explicit reporting. Read the execution summary before interpreting strand compatibility or low transcript mapping. Final strand summaries must use native `detected_library_type` from the complete-cohort admission receipt plus per-run `library_orientation_qc`; the unchanged assembler's ancillary `library_types` CSV field can be empty and is not a scoring input. An initial kit-only pilot was superseded before outcome scoring and is not part of the final cohort.

Retain the full native outputs, Cutadapt JSON, per-run fingerprints and run receipts. `docs/admission_contract.json` describes the portable admission contract. The unchanged `prepare_inputs.py` also needs each `RUN_run_manifest.json` to contain the preprocessing count fields specified there. The review must verify all 28 native results and exact endpoint joins before producing that receipt.

```sh
python scripts/run_analysis_from_admitted_cohort.py --baseline-manifest WORK/metadata/baseline_28_manifest.json --subject-map WORK/metadata/subject_sample_map.csv --annotation WORK/reference/transcript_annotation.csv --quant-root WORK/quantification --admission WORK/admission.json --out WORK/analysis
```

The wrapper confirms all fixed runs and endpoint counts, supplied input hashes, quantification fingerprints and identical transcript identifiers before running the unchanged aggregation/statistical sources. All generated expression matrices, metadata and subject-labelled per-sample scores remain local. The report plot uses independently sorted within-group values for each pathway, with no subject identifiers or cross-pathway linkage; these distributions reproduce the plot and four primary unstratified tests, but cannot recreate stratified tests or upstream quantification. Reviewed aggregate outputs are in `results/`.

## Interpretation that must accompany final results

The four memberships receive a new uniform unweighted mean-rank score; this does not reproduce each original signature author's scoring method. The primary universe consists of reference protein-coding symbols measured in the identical reference and nonzero in at least one baseline sample. Individual measured zeros are retained; missing transcripts must not be silently treated as biological zero. At least 80% and five members are required. A stricter expression universe and mean-log score are descriptive sensitivities; they do not replace the primary analysis or shrink its four-test BH family.

Screening-labelled tissue is often archival: 23/28 specimens were collected more than 90 days before their on-treatment specimen; median interval 834 days. Exact biopsy organ is unknown. Dose, liver involvement, TMB, sampling and total-RNA library quality complicate inference. Five benefit cases and two objective responses provide limited precision. No multivariable response classifier, cutoff search or cross-platform patient percentile is supported. Nonsignificance does not establish equivalence or absence of biological relevance. The public raw subset has 28 subjects; the peer-review-only population of 34 remains unreconciled.

## Reviewed findings and limitations

The four primary mean-rank scores have lower median point estimates in the clinical-benefit group, with adjusted q = 0.521 for every pathway. No secondary or prespecified scoring/stratification sensitivity gives a nominal P < 0.05. The two objective responders' lower CAF/ECM point estimates do not establish a low-stroma response rule. The analysis does not validate high archival pathway expression as a positive vactosertib-selection biomarker and does not rule out benefit.

All primary signatures are fully covered. The stricter universe retains 52/54 Hallmark genes (LEFTY2 and NOG fail the fixed expression threshold) and all members of the other sets. Thirty-seven reference coding symbols are consistently unmeasured; 62 measured coding symbols are zero across all 28. Neither category affects the locked primary pathway memberships. No sample-specific missing transcript rows were filled as biological zero.

Native admission identifies 24 ISR and four weak-directionality IU libraries. Retained-pair transcript mapping ranges from 4.70% to 39.23%; 11/28 are below 20%. Clinical-benefit samples have lower median mapping/coding depth, a descriptive technical imbalance. These quality limitations were reported without outcome-based exclusions. An IU compatibility ratio of one reflects unstranded acceptance and is not evidence of superior quality. Raw FASTQs were checksum-verified before task-only cleanup; final admission independently rehashed retained native outputs and checked receipts, and could not rehash deleted raw files again.

The interval of 834 days is the median screening-specimen to on-treatment-specimen collection interval, not specimen age at first drug dose. The 28-person paired-RNA subset is not the full trial efficacy population; its 2/28 response count must not replace the published full-trial response rate. No effect confidence intervals, comparator-arm interaction, case-to-trial calibration, SMAD4 subgroup efficacy test or external validation is supplied. Read `results/independent_final_review.json` for all interpretive limits.

## Verification

```sh
python scripts/verify_package.py --require-results
python tests/test_statistics_synthetic.py
python analysis/independent_verify_final_statistics.py --self-test
python scripts/check_primary_from_unlinked_figure.py
python scripts/verify_package.py --require-final
```

The scientific-results gate checks the reviewed all-28 aggregates, coverage, endpoint counts and hashes. The included report plot inputs allow `check_primary_from_unlinked_figure.py` to check their privacy schema and reproduces the four primary unstratified P values, effects and BH4 results through the unchanged numerical core. The final gate additionally requires the reviewed report sources, PDF metadata and source fingerprints; it blocks while `report/FINAL_REPORT_PENDING.json` exists. Neither integrity checks nor synthetic fixtures reproduce trial statistics without external quantifications and clinical joins.

The independent full-cohort verifier accepts `--permit-full-cohort --task-root WORK --annotation ANNOTATION` and expects the original relative layout: `quantification/RUN/quant.sf`, `analysis/assembled_inputs/`, `analysis/results/`, `methodology/locked_pathways.json` and complete controller/admission/identifier-coverage receipts. This is distinct from the convenience wrapper's `WORK/analysis/inputs` and `WORK/analysis/statistics` output layout; arrange inputs deliberately, and never fabricate admission files. The historical independent numeric receipt records the actual run, not a claim that this package redistributes those inputs.

To reproduce the published cohort-level biotype summary from the locally retained QC table, run `scripts/summarize_biotype_QC.py --input LOCAL_QC.csv --out NEW_AGGREGATE.json`; this does not require outcome labels or individual-gene expression. Full source/aggregate hash transformations are in `provenance/source_transformations.json`. `docs/final_insertion_checklist.json` tracks report insertion separately from the now-complete science.

## Website provenance boundary

`website/research_section.json` contains only trial aggregate findings, not the full case-specific website synthesis. `website/therapeutic_rankings.json` retains axis labels/order and option names/order only. The full current website source is linked and pinned by source and canonical JSON hashes in `website/source_provenance.json`. The 30-candidate catalogue preserves the separate website-only FOG-001 addition. This narrowed projection avoids duplicating clinical evidence/history; the explicitly reviewed report remains a separate artifact.
