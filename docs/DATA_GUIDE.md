# Data guide

This checkout is a reproducible research entry point to [youngcrc.com](https://youngcrc.com). It contains curated structured data and source code. Prepared PDF reports and large externally hosted data remain separate downloads. Coverage is selective and is not a complete longitudinal medical record.

## Choose a table

| Question | Entry point | Shape |
| --- | --- | --- |
| What happened, and with what evidence? | `data/clinical/timeline.json` | Array of events; `id`, `date`, `status`, `source_ids`, `limitations`. |
| Which clinical source supports a record? | `data/clinical/sources.json` | Array keyed by `id` (`CL-SRC-*`). |
| What specimen was reviewed? | `data/clinical/pathology.json` | Array; `specimen_id`, collection/report dates, `findings`, `source_ids`. |
| What was measured over time? | `data/clinical/laboratory_observations.json`, `ctdna.json`, `liquid_biopsy_observations.json` | Objects containing `records`; inspect the individual unit/date/evidence fields. |
| What did plasma profiling report? | `data/clinical/plasma_profiling_assays.json` | Object containing assay `records` with nested `findings`. |
| Which molecular specimen, assay or source? | `data/molecular/samples.json`, `assays.json`, `sources.json` | Objects containing `records`; keys `sample_id`, `assay_id`, `source_id`. |
| What was reported or audited? | `data/molecular/findings.json`, `variants.json`, `target_read_evidence.json` | Objects containing `records`; clinical extraction and research evidence remain distinct. |
| How do clinical and molecular specimens link? | `data/molecular/sample_links.json` | Object containing `records`, with explicit link level and aliquot uncertainty. |
| What can I download? | `data/catalogue.json`, `data/reports.json`, modality release catalogues and `release/website-manifest.json` | Catalogue objects containing records, or the published manifest schema. |
| What is missing or pending? | `data/release_status.json`, `data/gaps.json`, `data/molecular/raw_file_inventory.json` | Availability metadata; inventory is not proof of a public release. |

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

## Snapshot-specific limits (website release 1.28)

The release status checked on 16 October 2026 records two withheld primary Caris DNA FASTQs: R1 failed source gzip validation; R2 is on a pair-completeness hold, with no established independent R2 failure. The separately validated primary Caris DNA BAM remains available. Do not describe both FASTQs as corrupt or treat their hold as withdrawal of the BAM.

BostonGene rectal-resection bulk WES/WTS and matched-normal saliva reads are public. These are separate from the missing liver 10x Flex reads and per-cell matrices. Provider roles and report context do not resolve every file-to-library or aliquot link. Likewise, additional Caris material has unresolved specimen provenance, and a Natera tumour-file association with the Signatera design specimen remains inferred.

Exact custom Caris and Natera reference FASTAs/checksums remain requested. The Tempus tumour DNA alignment remains missing. Native April 2026 PET/CT release covers selected series; June and September scan images are missing. Read the full release status and record notes before interpreting a gap or grouping files into a cohort.

## Reproducibility and citation

Run `python3 scripts/case_data.py verify-snapshot` to compare local pinned inputs with `release/snapshot.json`. The captured website manifest is `release/website-manifest.json`; the live manifest is <https://youngcrc.com/manifest.json>. Git release v1.0.0 and the website release are separate version identifiers; individual table labels may be older. Record the repository tag or commit and each input’s actual SHA-256. Do not silently replace pinned inputs with live data during an analysis.

A useful result includes the question and methods; input paths, hashes and release/commit; source/sample/assay IDs; dates, original units and evidence labels; unresolved gaps and limitations. Attribute the dataset to Alexander Young and link [youngcrc.com](https://youngcrc.com); use [CITATION.cff](../CITATION.cff) for the repository citation. Preserve report providers’ attribution and third-party rights.

Public JSON GET needs no authentication. Optional MCP access uses Sites/OpenAI sign-in, as described in [the API documentation](https://youngcrc.com/docs/api.md) and [authentication documentation](https://youngcrc.com/auth.md). Do not send credentials to public dataset URLs. Do not use this record for individualized treatment advice or contact the patient or providers without an explicit human request.
