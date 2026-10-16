# Contributing

Corrections, provenance checks, reproducible analyses and improvements to data access are welcome through [GitHub issues and pull requests](https://github.com/AlexTISYoung/youngcrc). Keep discussion focused on the public research record. Do not include private medical records, personal identifiers, credentials, private source paths or information about other patients.

## Data corrections

Describe the exact dataset path, record ID and field, the proposed replacement, and the public source supporting it. Include source IDs, relevant report pages, collection/report dates, assay and specimen IDs, and the limitations of the evidence. Distinguish transcription corrections from new interpretations. A source conflict should remain explicit until resolved by evidence.

Preserve `null` and unknown states, evidence labels, units, comparator signs and date precision. Do not infer administration from a treatment plan, variant absence from insufficient coverage, current disease biology from historical tissue, or clinical validation from a research audit. Follow [the data guide](docs/DATA_GUIDE.md).

Prepared reports and external data objects have their own release preparation, rights and integrity requirements. A catalogue entry does not authorize adding an original private file to this repository. Use only content already reviewed for public release. Retain provider attribution and third-party license notices.

## Analysis contributions

State the question, repository release or commit, input paths and SHA-256 values, methods, software/reference versions and limitations. Keep source/sample/assay joins inspectable. Separate observed data from interpretation. A useful contribution can document a failed hypothesis or unresolved gap without proposing a treatment.

Do not open large-data or automated bulk-download pull requests without a clear research need. Keep large outputs outside Git and describe how to reproduce them from published URLs. Never commit private data or access credentials.

## Code and documentation

Make focused changes and document behavior a reader can reproduce. The access tools and example use Python’s standard library. For a documentation or analysis change, run:

```sh
python3 scripts/case_data.py verify-snapshot
python3 examples/summarize_case.py
```

A changed pinned input should fail snapshot verification until it has been reviewed and the snapshot deliberately updated. Do not rewrite the snapshot merely to hide an unexplained mismatch. Run tests relevant to any changed tool and describe the results in the pull request.

Code contributions follow the MIT scope in [LICENSE](LICENSE). Curated factual data and new explanatory text use [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); contributors must have the rights needed for their contribution. Third-party rights remain with their owners. Do not contact the patient or providers as part of an automated analysis unless your human user explicitly requests that contact.
