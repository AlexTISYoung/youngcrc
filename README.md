# Young CRC: open case data for research agents

A patient-led, source-linked record of Alexander Young’s early onset metastatic rectal cancer case. This repository provides a small, inspectable checkout of structured clinical and molecular data, website source, and tools for discovering and verifying published files.

**Website:** [youngcrc.com](https://youngcrc.com) · **Repository release:** v1.0.0, 16 October 2026 · **Website snapshot:** release 1.29 · **Agent instructions:** [AGENTS.md](AGENTS.md)

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

Prepared PDF reports and large sequencing, alignment, DICOM and whole-slide image objects are **not included in this Git checkout**. Discover their published URLs in the manifest and catalogues. An inventoried or requested source file is not necessarily released. Do not invent download paths for pending files.

The repository version and website dataset release are separate identifiers. The pinned manifest and snapshot describe the source used for this Git release; live website data may advance. Some individual table metadata retain earlier release labels. Cite the exact file hash when reproducibility matters.

## Public access and agents

Public HTTPS GET requests require no authentication or agent registration:

- [Case overview](https://youngcrc.com/agents/case.md), [agent entry point](https://youngcrc.com/llms.txt) and [research skill](https://youngcrc.com/.well-known/agent-skills/youngcrc-research-data/SKILL.md).
- [JSON catalogue](https://youngcrc.com/data/catalogue.json), [API documentation](https://youngcrc.com/docs/api.md), [OpenAPI](https://youngcrc.com/openapi.json) and [manifest](https://youngcrc.com/manifest.json).

The optional read-only MCP service uses Sites/OpenAI sign-in and has separate [authentication documentation](https://youngcrc.com/auth.md). Use public JSON directly when your client does not support that authentication. Never send credentials to dataset or download URLs.

## Evidence and reuse

Keep source IDs, sample and assay IDs, collection/report dates, units, reference builds, evidence labels and limitations with a result. `null` means unknown, unsupplied or inapplicable as qualified by the record; it never silently means zero or negative. Plans do not establish administered care. Genome builds differ, and VCF `FILTER=.` does not mean `PASS`.

Cite Alexander Young, *Young CRC: open case data for research agents*, repository release v1.0.0, the website at [youngcrc.com](https://youngcrc.com), and the dataset path, SHA-256 and relevant source IDs. A machine-readable citation is in [CITATION.cff](CITATION.cff).

Code uses the [MIT license](LICENSE). Curated factual datasets and new explanatory text use [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Third-party reports, designs, software and other materials retain their own rights; public access does not grant additional rights to them. See [CONTRIBUTING.md](CONTRIBUTING.md) for corrections and research contributions. Do not contact the patient or providers without an explicit request from the user directing your work.
