# Young CRC: open case data for research agents

A patient-led, source-linked record of Alexander Young’s early onset metastatic rectal cancer case. This repository provides a small, inspectable checkout of structured clinical and molecular data, website source, and tools for discovering and verifying published files.

**Website:** [youngcrc.com](https://youngcrc.com) · **Base data snapshot:** website 1.53, 29 October 2026 · **Latest analysis addition:** vaccine combination strategy, 18 November 2026 · **Agent instructions:** [AGENTS.md](AGENTS.md)

The record is selective and incomplete. It distinguishes primary report observations, research analyses, clinician summaries and patient reports. Preserve those distinctions in every analysis. This is research material, not individualized treatment advice.

## Start in under a minute

```sh
git clone https://github.com/AlexTISYoung/youngcrc.git
cd youngcrc
python3 scripts/case_data.py verify-snapshot
python3 examples/summarize_case.py
python3 scripts/case_data.py list --json
```

These commands require Python 3.10+ and use only its standard library. The example runs offline, emits aggregate counts and a finding joined to its specimen, assay and sources, and records the SHA-256 of each input. Read [the data guide](docs/DATA_GUIDE.md) before comparing results across specimens, assays or dates.

To retrieve one published file:

```sh
python3 scripts/case_data.py fetch data/clinical/timeline.json --output /tmp/youngcrc-timeline.json
```

`fetch` accepts an exact manifest path or release file ID, checks the published size and SHA-256, and defaults to a 100,000,000-byte transfer cap. Large data require an explicit `--max-bytes` budget and enough local space. It refuses to overwrite an existing output. Inspect `list` and the relevant catalogue before downloading.

## What is here

| Path | Use |
| --- | --- |
| `data/clinical/` | Timeline, pathology, imaging summaries, laboratory results, liquid biopsy observations, treatment evidence and source metadata. |
| `data/molecular/` | Sources, samples, assays, findings, research-audit loci, read evidence and raw/processed file catalogues. |
| `data/catalogue.json`, `data/reports.json` | Discover datasets and prepared reports by provider, specimen, modality and provenance. |
| `data/release_status.json`, `data/gaps.json` | Known availability, preparation status and missing evidence. |
| `release/website-manifest.json` | Published website file inventory captured for this repository release; includes sizes, hashes and external download entries. |
| `release/snapshot.json` | Repository snapshot inventory used by `verify-snapshot`. |
| `site/`, `server/`, `scripts/` | Website, read-only agent service and release tooling source. |
| `reports/` | Selected public HTML/CSV research materials and their supporting assets. |
| `analysis/` | Dated report, ranking and reproducibility sources supplementing the base snapshot; current immunotherapy-resistance and historical immune-evasion analyses. |

Prepared PDF reports and large sequencing, alignment, DICOM and whole-slide image objects are **not included in this Git checkout**. Discover their published URLs in the manifest and catalogues. An inventoried or requested source file is not necessarily released. Do not invent download paths for pending files.

The pinned website manifest describes the base data snapshot, website release 1.53 captured on 29 October 2026. The repository inventory additionally covers the dated analysis package below; unrelated clinical tables are not synchronized with the live website. The former `v1.0.0` tag was deleted during the authorized 2 November history cleanup. Cite the exact current Git commit and file hashes. Individual table labels may retain earlier dates.

## Immunotherapy resistance and vaccine strategy, 18 November 2026

[The current report](https://youngcrc.com/reports/research/immunotherapy_resistance_report_2026-11-18_vaccine_strategy.pdf) and [dated source package](analysis/immunotherapy-resistance/2026-11-18-vaccine/README.md) consolidate the archival case evidence, completed trial RNA comparison and vaccine-combination review. The proposed strategy combines vactosertib, a personalized peptide vaccine, N-803 and checkpoint blockade; its complete safety and efficacy are untested. Human clinical evidence includes both randomized adjuvant benefit and advanced-disease/colorectal counterevidence. Access summaries distinguish enquiries or listed options from confirmed supply and administration.

Five mechanistic research leads are included at discussion priority 5: FLT3 ligand, CD40 agonism, local ipilimumab-supported vaccine priming, MCT1 inhibition and glutamate-cysteine ligase inhibition. Existing candidate priorities and the complete 28-sample trial findings are preserved. The [release record](release/immunotherapy_resistance_2026-11-18_vaccine.json) pins the reviewed 69-page PDF and source package. The underlying clinical/site snapshot remains historical release 1.53.

## Vactosertib trial RNA comparison, 17 November 2026

[The separate trial package](analysis/vactosertib-pathways/README.md) preserves the exact methods, reviewed aggregate results, technical limitations and source hashes. The [consolidated report](https://youngcrc.com/reports/research/immunotherapy_resistance_report_2026-11-17_trial_analysis.pdf) contains 64 pages and is pinned in the release record. This package accompanies website release 1.74; its scoped candidate catalogue preserves the separate FOG-001 addition from website release 1.73.

All 28 available baseline trial RNA samples were quantified with the fixed reference and kit-specific preprocessing. None of four prespecified TGF-beta/fibroblast/ECM mean-rank scores showed a significant association with study-defined clinical benefit after BH4 correction (all q=0.521). Clinical benefit means confirmed CR/PR or stable disease maintained at least six months: five versus 23. The two-versus-26 objective-response comparison has a separate exploratory BH4 family. No prespecified sensitivity has a nominal P<0.05.

The analysis does not validate high archival pathway expression as a vactosertib-selection biomarker and does not rule out benefit. Archival sampling, unknown biopsy organ, clinical confounding, library-quality differences and small event counts limit interpretation. No untreated comparator, treatment-effect interaction or personal response estimate is available. Therapeutic priorities are not upgraded from these results.

The existing case package below, all molecular corrections and the historical root clinical/site snapshot are preserved. Subject-labelled trial expression/clinical rows, raw reads, original workbooks and full papers are not redistributed.

## SMAD4 functional evidence and immunotherapy resistance, 17 November 2026

[The dated SMAD4 analysis package](analysis/immunotherapy-resistance/2026-11-17-smad4/README.txt) and [release record](release/immunotherapy_resistance_2026-11-17_smad4.json) pin the reviewed report and sources.

The current report incorporates investigator-reported, exact-variant functional evidence for SMAD4 G359E (Monash personal communication, 17 November 2026). The investigators report strong damaging functional evidence and PS3 support while retaining an overall VUS assessment. This materially strengthens impairment of the tested SMAD4-dependent TGF-beta response, but does not establish complete or biallelic loss in current disease, ERK activation, somatic oncogenicity or vactosertib sensitivity. Therapeutic priorities remain unchanged.

The [dated molecular snapshot](analysis/immunotherapy-resistance/2026-11-17-smad4/molecular/summary.json) also fills reviewed gaps from the primary reports. SMAD4 G359E is annotated VUS in the provider VCF but omitted from the printed Caris variant tables; Caris reports SMAD4 copy number as indeterminate. Provider-specific classifications, unresolved copy-number calls and investigator interpretation are shown separately. The historical root molecular tables are not overwritten.

The public conference abstract supplies assay context; the attributed communication supplies the G359E result. Original correspondence, attachment, contact identifiers and unpublished raw MAVE values are excluded. The package cannot independently reproduce or calibrate that experimental result. Existing 33 numerical tables, their inputs, and the historical packages remain unchanged. Outcome-linked trial RNA analysis was pending in that case release; the separately dated trial package above now contains the complete reviewed comparison.

```sh
python3 analysis/immunotherapy-resistance/2026-11-17-smad4/verify_package.py
python3 -m pip install -r analysis/immunotherapy-resistance/2026-11-17-smad4/requirements.txt
python3 analysis/immunotherapy-resistance/2026-11-17-smad4/verify_package.py --rerun
```

## Immunotherapy-resistance evidence, 17 November 2026 (historical)

[The earlier 17 November package](analysis/immunotherapy-resistance/2026-11-17/README.txt) published the completed SMAD4 G359E and noncanonical TGF-beta/ERK review alongside the earlier recruitment and stromal analyses. The [release record](release/immunotherapy_resistance_2026-11-17.json) pins the 58-page report and reproducible sources. A 160-gene all-source lookup, exact MPAS gene-set rescoring with normalization sensitivity, protein-specificity audit, derived allele counts and structural analysis are included.

The mutation remains a clinical VUS. Strong resection early-response RNA does not establish TGF-beta-driven ERK activation; total ERK protein is not a phospho readout. Caris NS identifies percentiles not supplied by the provider, not absent expression. These findings do not change therapeutic priorities. The separate outcome-linked vactosertib trial RNA analysis remains pending; no interim pathway results are published.

```sh
python3 analysis/immunotherapy-resistance/2026-11-17/verify_package.py
python3 -m pip install -r analysis/immunotherapy-resistance/2026-11-17/requirements.txt
python3 analysis/immunotherapy-resistance/2026-11-17/verify_package.py --rerun
```

The package supports downstream reproduction from pinned compact inputs. Original private VCF/BAM files, correspondence and unfinished trial outputs are not redistributed. Historical packages and the root clinical/site snapshot remain unchanged.

## Immunotherapy-resistance revision, 16 November 2026 (historical)

[The 16 November analysis package](analysis/immunotherapy-resistance/2026-11-16/README.txt) expanded the review to poor immune recruitment/priming, effector expansion, stromal composition and suppressive mechanisms, with source-linked conditional therapeutic rankings and counterevidence. It includes 37 sets/1,225 targets, a separate 156-gene recruitment lookup, compact reproducible RNA/protein calculations and an aggregate vactosertib biomarker audit. The [release record](release/immunotherapy_resistance_2026-11-16.json) identifies the separately published PDF and package hashes.

The package distinguishes strong archival smooth-muscle/ECM signals from specific stromal dependence, and trial pharmacodynamic activity from objective response. Archival assays do not establish the recent node's mechanism. The user reports insufficient cryopreserved tissue for organoid/tissue-culture experiments; current proposals respect that constraint. The 14 November package remains historical provenance, with its conclusions and proposals superseded where the current report revises them.

```sh
python3 analysis/immunotherapy-resistance/2026-11-16/verify_package.py
python3 -m pip install -r analysis/immunotherapy-resistance/2026-11-16/requirements.txt
python3 analysis/immunotherapy-resistance/2026-11-16/verify_package.py --rerun
```

The integrity check is dependency-free. The numerical rerun uses pinned dependencies and full-universe rank intermediates, not ranks recomputed within the selected panel. Optional upstream recipes require their documented full inputs; raw reads, full reference matrices, original trial workbooks and third-party papers are not bundled.

## Immune-evasion revision, 14 November 2026 (historical)

[The dated analysis package](analysis/immune-evasion/README.md) accompanies the [revised PDF](https://youngcrc.com/reports/research/immune_evasion_report_2026-11-14.pdf) and website release 1.68. It includes portable extraction scripts, selected source inputs, derived RNA/protein tables, 66 citations, report-generation sources, eight ranked immune-evasion axes and ranked therapeutics within each axis. The [release record](release/immune_evasion_2026-11-14.json) pins the PDF and complete analysis inventory.

New assay-matched Caris percentiles weaken the earlier universal-low-antigen-presentation interpretation; low BostonGene RNA in the treated resection remains unresolved. Stromal and adenosine/ENPP1 evidence support focused tests, not proven drug dependence. HLA-G's labelled peptide is not gene-specific. Archival biopsy, treated resection, liver summaries and the recent node remain distinct. Rankings are research/discussion priorities, not response probabilities or validated treatment choices.

```sh
python3 analysis/immune-evasion/2026-11-14/verify_package.py --rerun
```

This offline standard-library check re-extracts the bundled RNA and protein tables. Full peptide-specificity checks use a documented optional database download. No new clinical variant calling or mass-spectrum search is performed.

## Proteomics research release, 29 October 2026

The new B7_43 report and data are discoverable in `data/reports.json` and `data/proteomics/b7_43_2026-10-29/`; readable analysis and methods are under `reports/proteomics/quantitative-2026-10-29/`. The case is archival treated rectal resection collected on 22 October 2024, not the recent nodal biopsy. Processed protein/precursor measurements and research analyses are distinct from raw-spectrum reprocessing, which was not performed. Public reference comparisons are exploratory; AO is HPA colon from one donor and run 423 remains unidentified. Neither is a matched patient normal. See the report and its input/reference manifest for quantity definitions, exact hashes, required external references and reproduction limits.

A Git clone omits the frozen search FASTA and bulk reference matrices. Before running proteomics input checks, obtain the exact FASTA through its direct URL and SHA-256 in `release/source_snapshot_manifest.json`, or use the complete website `downloads/source.zip` (which contains that FASTA). Thirteen frozen reference matrices are separately hosted deterministic gzip downloads; follow the analysis reference manifest and optional `--fetch-references` command, then verify the unpacked input hashes. A clone alone is not a complete analysis environment.

This snapshot also incorporates intervening published website updates through release 1.53, including the nodal tissue-processing record, immune research summaries and reviewed UCLA clinical extracts. Historical clinical records retain their evidence labels and dates; this update does not establish new treatment administration or current target expression.

## Public access and agents

Public HTTPS GET requests require no authentication or agent registration:

- [Case overview](https://youngcrc.com/agents/case.md), [agent entry point](https://youngcrc.com/llms.txt) and [research skill](https://youngcrc.com/.well-known/agent-skills/youngcrc-research-data/SKILL.md).
- [JSON catalogue](https://youngcrc.com/data/catalogue.json), [API documentation](https://youngcrc.com/docs/api.md), [OpenAPI](https://youngcrc.com/openapi.json) and [manifest](https://youngcrc.com/manifest.json).

The optional read-only MCP service uses Sites/OpenAI sign-in and has separate [authentication documentation](https://youngcrc.com/auth.md). Use public JSON directly when your client does not support that authentication. Never send credentials to dataset or download URLs.

## Evidence and reuse

Keep source IDs, sample and assay IDs, collection/report dates, units, reference builds, evidence labels and limitations with a result. `null` means unknown, unsupplied or inapplicable as qualified by the record; it never silently means zero or negative. Plans do not establish administered care. Genome builds differ, and VCF `FILTER=.` does not mean `PASS`.

Cite Alexander Young, *Young CRC: open case data for research agents*, website release 1.53, the repository commit used, the website at [youngcrc.com](https://youngcrc.com), and the dataset path, SHA-256 and relevant source IDs. A machine-readable base-snapshot citation is in [CITATION.cff](CITATION.cff). For the current report, cite [the 18 November release record](release/immunotherapy_resistance_2026-11-18_vaccine.json). For an earlier analysis addition, also cite its date and the corresponding [SMAD4 functional update](release/immunotherapy_resistance_2026-11-17_smad4.json), [earlier 17 November](release/immunotherapy_resistance_2026-11-17.json), [16 November](release/immunotherapy_resistance_2026-11-16.json) or [14 November](release/immune_evasion_2026-11-14.json) release record.

Code uses the [MIT license](LICENSE). Curated factual datasets and new explanatory text use [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Third-party reports, designs, software and other materials retain their own rights; public access does not grant additional rights to them. See [CONTRIBUTING.md](CONTRIBUTING.md) for corrections and research contributions. Do not contact the patient or providers without an explicit request from the user directing your work.
