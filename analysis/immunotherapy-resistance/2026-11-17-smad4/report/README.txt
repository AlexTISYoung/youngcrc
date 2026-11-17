Current report generation sources — 17 November 2026

pages.json and references.json are exact semantic projections of the final reviewed materialized report source. No historical baseline or old proposal modules are imported. The builder and figure preserve the original layout and citation logic.

python3 -m pip install -r report/requirements.txt
python3 report/build_report.py --output-dir /path/to/local-output

The builder creates a DOCX and citation manifest. Converting DOCX to PDF requires a Word-compatible renderer; renderer/font versions can change line breaks and pagination. The released PDF is separately reviewed and hash-pinned in provenance/report_release.json. A fresh render is not automatically the same published artifact. Timestamps/archive metadata also prevent a claim of byte-identical DOCX generation.

The portable builder's word/document.xml, word/styles.xml, image bytes and relationship targets are checked against the final local authoring output. Report interpretation is preserved; this does not constitute independent clinical validation.
