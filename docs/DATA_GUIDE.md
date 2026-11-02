# Data guide

This checkout is a reproducible research entry point to [youngcrc.com](https://youngcrc.com). It contains curated structured data and source code. Prepared PDF reports and large externally hosted data remain separate downloads. Coverage is selective and is not a complete longitudinal medical record.

Current `main` captures website release 1.53 on 29 October 2026. Use the exact repository commit and input hashes to identify this snapshot.

## Choose a table

| Question | Entry point | Shape |
| --- | --- | --- |
| What happened, and with what evidence? | `data/clinical/timeline.json` | Array of events; `id`, `date`, `status`, `source_ids`, `limitations`. |
| Which clinical source supports a record? | `data/clinical/sources.json` | Array keyed by `id` (`CL-SRC-*`). |
| What specimen was reviewed? | `data/clinical/pathology.json` | Array; `specimen_id`, collection/report dates, `findings`, `source_ids`. |
| Which imaging reports were reviewed or remain missing? | `data/clinical/imaging_report_coverage.json` | Coverage records distinguish report copies, summaries and missing images. |
| What was measured over time? | `data/clinical/laboratory_observations.json`, `ctdna.json`, `liquid_biopsy_observations.json` | Objects containing `records`; inspect the individual unit/date/evidence fields. |
| What did plasma profiling report? | `data/clinical/plasma_profiling_assays.json` | Object containing assay `records` with nested `findings`. |
| Which molecular specimen, assay or source? | `data/molecular/samples.json`, `assays.json`, `sources.json` | Objects containing `records`; keys `sample_id`, `assay_id`, `source_id`. |
| What was reported or audited? | `data/molecular/findings.json`, `variants.json`, `target_read_evidence.json` | Objects containing `records`; clinical extraction and research evidence remain distinct. |
| What molecular evidence is summarized on the website? | `data/molecular/summary.json` | Specimen- and assay-specific summaries with source links and research limitations. |
| How do clinical and molecular specimens link? | `data/molecular/sample_links.json` | Object containing `records`, with explicit link level and aliquot uncertainty. |
| What can I download? | `data/catalogue.json`, `data/reports.json`, modality release catalogues and `release/website-manifest.json` | Catalogue objects containing records, or the published manifest schema. |
| What is missing or pending? | `data/release_status.json`, `data/gaps.json`, `data/molecular/raw_file_inventory.json`, `data/molecular/caris_delivery_status.json` | Availability metadata; inventory or a provider announcement is not proof of a public release. |

Start with `data/clinical/dataset_info.json` and `data/molecular/data_dictionary.json` for the original evidence definitions and conventions. `data/molecular/index.json` describes its tables. Do not assume all JSON has the same top-level structure or that all tables share the same update date.

## Join provenance before interpreting

For a molecular finding:

1. Resolve `finding.sample_id` in `samples.records` using `sample_id`.
2. Resolve `finding.assay_id` in `assays.records` using `assay_id`. An assay may use `sample_id` or `sample_ids`, and may identify a separate matched-normal specimen.
3. Resolve the finding, sample and assay `source_ids` in `sources.records` using `source_id`. A finding’s immediate source list alone may omit contextual specimen or assay provenance.
4. Preserve `evidence_class`, `current_node_status`, notes and dates alongside the value. An old specimen and a later molecular report are different points in time.
5. For clinical context, join `sample_links.records.molecular_sample_id` to the sample and its `clinical_specimen_id` to `pathology[].specimen_id`. Keep `link_level`, `linkage_evidence` and `aliquot_linkage_status`. A specimen association does not prove an exact block, aliquot or extraction match.

For clinical records, `source_ids` is usually an array, while ctDNA and liquid biopsy observations use singular `source_id`. Clinical IDs resolve through `clinical/sources.json[].id`. Some bridging records include both `M-SOURCE-*` and `CL-SRC-*`; use the matching namespace. A source label records provenance and does not imply that an original document is public. Check `public_prepared_report_available` and its URL separately from original availability.

The dependency-free [example](../examples/summarize_case.py) performs a finding/sample/assay/source join and records exact input hashes.

## Preserve measurement meaning

- **Missingness:** `null` means unknown, not supplied or not applicable as described by notes/status. Missing records, missing dates and unmeasured loci are not negative results. Do not convert them to zero.
- **Evidence:** preserve `status`, `evidence_type` and `evidence_class`. A clinical report extraction, primary report observation, research audit and patient report have different support. Treatment options, recommendations, research candidates and plans do not establish administered care, dose, response or efficacy.
- **Time:** dates are ISO calendar dates when known; `YYYY-MM` has month precision. Collection dates, report dates, result issue times and source dates have different meanings. Do not sort an unknown date into an invented position or use a report date as a specimen date.
- **Units:** retain original units, comparator signs, assay and method. Signatera MTM/mL and NeXT Personal PPM are not interchangeable. A value preceded by `<` is not an exact measurement. Keep plasma tumour fraction distinct from a variant allele fraction.
- **Coordinates:** audit loci use 1-based positions with explicit reference build and reference/alternate alleles. GRCh37, hg38/GRCh38 and hs37d5 files must retain their reference identity and sequence dictionary. A build label alone does not establish an exact reference FASTA. Any liftover, transcript annotation or variant normalization is a new analysis and must be documented.
- **Variant filters:** VCF `FILTER=.` is unset and is not standardized `PASS`. Preserve vendor `FILTER`, `INFO` and `FORMAT` definitions. Vendor callsets are not automatically a paired-normal somatic catalogue.
- **Read evidence:** preserve `count_unit`, `coverage_status` and assay. `alternate_count / reference_plus_alternate_count` is method-specific; `0/0` means no informative coverage. Zero alternate reads at limited depth do not prove absence. Fragment proxies, read counts, RNA evidence and caller counts are not interchangeable.
- **Biological scope:** historical tissue results do not establish present metastatic biology. RNA expression, amplification, IHC staining, peptide prediction, protein presentation and immune recognition are separate questions. Research candidate sequences do not establish a validated treatment or manufacturing plan.

## Availability, sizes and integrity

`M-FILE-*` identifies an inventoried or requested source file. `M-RAW-*` identifies a released read/alignment/index object, and `M-RELEASE-*` identifies a prepared processed file. They are different identifiers. One source archive can yield several public objects.

Read `data/molecular/raw_release_catalog.json`, `processed_release_catalog.json`, `data/imaging_release_catalog.json` and `data/pathology_release_catalog.json` for actual public objects. Preserve `release_file_id`, `source_file_id`, sample/assay IDs, `download_url`, `bytes`, `sha256`, reference build, preparation status and transformation notes. Original logical input sizes differ from released object sizes. A historical verification timestamp describes the check performed then, not a promise of future server availability.

Use published download URLs only. Relative website paths resolve against `https://youngcrc.com/`; externally hosted objects retain their published URL. Match a BAM and index through their companion/generated-from IDs rather than filenames. Check bytes and full-file SHA-256 after transfer. Hash agreement establishes file identity, not scientific validity or completeness.

```sh
python3 scripts/case_data.py list --storage external --json
python3 scripts/case_data.py fetch M-RAW-002 --output /tmp/youngcrc-rna.bam.bai
```

The second command illustrates an individually selected companion index, not a complete alignment dataset. The tool enforces a default 100,000,000-byte budget; larger objects require an explicit `--max-bytes`. No PDF reports or large external data objects are bundled in Git. Do not bulk-fetch data without a research need and an explicit storage/transfer budget.

## Snapshot-specific limits (website release 1.53)

The release status checked on 19 October 2026 records 90 verified external sequencing and imaging objects and two withheld primary Caris DNA FASTQs: R1 failed source gzip validation; R2 is on a pair-completeness hold, with no established independent R2 failure. The separately validated primary Caris DNA BAM remains available. Do not describe both FASTQs as corrupt or treat their hold as withdrawal of the BAM.

BostonGene rectal-resection bulk WES/WTS and matched-normal saliva reads are public. These are separate from the missing liver 10x Flex reads and per-cell matrices. Provider roles and report context do not resolve every file-to-library or aliquot link. A Natera tumour-file association with the Signatera design specimen remains inferred.

The additional Caris material (`M-SAMPLE-007`, assays `M-ASSAY-007` through `M-ASSAY-009` and `M-ASSAY-021`) is linked to the Assure peripheral-blood case collected 27 January 2026 and reported 6 February 2026, distinct from the March 2024 rectal biopsy. This is a blood-draw case across separate fractions, not a single physical aliquot. Caris confirmed that gDNA-labelled DNA/RNA files come from buffy coat and cfTNA-labelled files from cell-free nucleic acid (`M-SOURCE-014`). These filename-family assignments do not establish an exact file-to-tube, extraction or library link, or clinical germline classification. Do not treat buffy-coat or cell-free RNA/expression tables as rectal-tumour expression, or compare raw TPM directly with tumour-report percentiles.

The recovered cell-free DNA R2 and existing R1 passed complete mate-identifier/order validation. Cell-free DNA and RNA read pairs, both alignments with regenerated indexes, and cell-free DNA variant calls with a regenerated index are verified public downloads. The cell-free RNA expression table (`M-RELEASE-013`) preserves the received table bytes and contains 59,960 unique gene rows. Exact tube/aliquot, extraction, library/read structure, annotation and reference FASTA/checksum links remain unresolved; BAM and VCF allele fractions are not assumed interchangeable. Fifteen announced Caris metadata/report files were not visible or retrievable through the current connection on 19 October 2026; this does not distinguish absence from access restrictions. Local SHA-256 checks do not substitute for the missing vendor checksum manifests. See `data/molecular/caris_delivery_status.json`, the release catalogues and `M-SOURCE-015` for the checked scope.

The molecular summary distinguishes archived rectal bulk RNA from liver single-cell RNA and liver protein staining. The source liver “stroma” aggregate includes all non-malignant cells. RNA detection percentages, reference-cohort expression labels and IHC scores are not interchangeable, and these historical specimens do not establish expression in current metastases. The TAP2 review covers three exact vendor-called alleles and public classifications; it is not a clinical germline diagnosis or a functional antigen-presentation test and does not establish TAP2 deficiency.

CTDNA-013 retains a patient-reported 100 MTM/mL result and a patient-reported blood draw date of 16 September 2026, clarified on 16 October 2026. The original September report remains unavailable; do not promote this record to a report-verified result.

Exact custom Caris and Natera reference FASTAs/checksums remain requested. The Tempus tumour DNA alignment remains missing. Native April 2026 PET/CT release covers selected series; June and September scan images are missing. Read the full release status and record notes before interpreting a gap or grouping files into a cohort.

## Proteomics and newer source extracts

The 29 October 2026 proteomics analysis is a research derivative of the B7_43 processed delivery. Resolve the report/data entry to its source, assay and archived rectal specimen. Preserve full protein groups, peptide support, ambiguous mappings, missing values and signal units. Within-run signal ranks and cross-study rank shifts are not clinical expression percentiles, concentrations or validated patient tumour/normal fold changes. HPA colon represents one donor; the AO comparator matches those public data and is not patient matched normal. Run 423 is unidentified. No raw spectra were re-searched, and detected HLA/B2M/TAP/PTPN1/PTPN2 do not prove functional tumour antigen presentation or response to an immune combination.

The portable report is under `reports/proteomics/quantitative-2026-10-29/`; processed inputs, analysis tables and reproducibility metadata are under `data/proteomics/b7_43_2026-10-29/`. Use the published catalogue and input/reference manifest to discover exact files rather than guessing download paths. The frozen search FASTA is intentionally omitted from Git and is available by the exact URL/hash in `release/source_snapshot_manifest.json` or in the complete website `downloads/source.zip`. Thirteen frozen third-party reference matrices remain external prerequisites, with deterministic gzip URLs/hashes and the analysis retrieval command documented in the reference manifest. Preserve their release versions, hashes and rights; retrieving a current reference does not reproduce an older frozen input automatically.

The current clinical extract also includes `ucla_ehi_import.json`, `ucla_medication_administrations.json` and `ucla_oncology_notes.json`. Those separately scoped source extracts do not imply a complete longitudinal record. Recent nodal processing and patient-confirmed date records are distinct from post-thaw viability, histology or new expression testing.

## Reproducibility and citation

Run `python3 scripts/case_data.py verify-snapshot` to compare local pinned inputs with `release/snapshot.json`. The captured website manifest is `release/website-manifest.json`; the live manifest is <https://youngcrc.com/manifest.json>. Current `main` captures website release 1.53 on 29 October 2026; identify it by its exact repository commit, not by a new release tag. Historical repository tag `v1.0.0` captures website release 1.29 from 16 October 2026. Repository and website versions are separate identifiers, and individual table labels may be older. Record the commit and each input’s actual SHA-256; use a historical tag only when analyzing that tagged snapshot. Do not silently replace pinned inputs with live data during an analysis.

A useful result includes the question and methods; input paths, hashes and release/commit; source/sample/assay IDs; dates, original units and evidence labels; unresolved gaps and limitations. Attribute the dataset to Alexander Young and link [youngcrc.com](https://youngcrc.com); use [CITATION.cff](../CITATION.cff) for the repository citation. Preserve report providers’ attribution and third-party rights.

Public JSON GET needs no authentication. Optional MCP access uses Sites/OpenAI sign-in, as described in [the API documentation](https://youngcrc.com/docs/api.md) and [authentication documentation](https://youngcrc.com/auth.md). Do not send credentials to public dataset URLs. Do not use this record for individualized treatment advice or contact the patient or providers without an explicit human request.
