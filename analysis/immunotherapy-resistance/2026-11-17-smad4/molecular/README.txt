Reviewed molecular summary — 17 November 2026

The dated summary preserves provider-specific clinical calls and explicitly separates raw provider-VCF annotations, clinical-report omissions, and research interpretation. Primary-report audits and hashes document additions. Original clinical PDFs/OCR, raw patient VCFs and private correspondence are not redistributed here.

Run: python3 molecular/reproduce_summary.py --output-dir ./molecular-summary-check

The scripts apply reviewed annotations to the historical public summary, then compare the resulting JSON with summary.json. This reproduces curation, not clinical assay analysis or independent variant classification. Source report URLs and SHA-256 values permit audit against the prepared public reports.
