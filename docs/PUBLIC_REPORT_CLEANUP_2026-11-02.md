# Public vaccine report cleanup — 2 November 2026

This focused change removes the original internal report renderer, score-calibration explanation, method-description tooltips and analysis-provider branding from the public vaccine target report. It keeps the candidate tables, sequences, scores and figure data and adds an independently written public viewer for navigation, filtering and plots.

The underlying dataset remains the historical website release 1.53 snapshot. Clinical JSON/CSV records, treatment plans, the agent-readable case summary and unrelated display labels are unchanged. Stable report/source identifiers and paths are retained. This is not a synchronization with subsequent website clinical or therapeutic updates.

Both 250-row candidate table bodies are identical after excluding title attributes. Figure numeric values are unchanged; ten axis-label text fields are neutralized. The retired report.js file is removed from the current tree.

The data/reports.json catalogue remains unchanged because updating its full payload was blocked by automatic approval review. Its vaccine entry still has historical provider labels, the retired script dependency and earlier report hash/size. Use the cleaned HTML and release inventories for the current report files.

Subsequent authorized history cleanup on 2 November replaced `main` with the reviewed cleaned snapshot, retaining only the initial README commit as parent, and deleted the former `v1.0.0` tag/release. Do not restore pre-cleanup history. Copies or objects addressed by older exact identifiers may remain outside the current tree; no server-side purge is asserted.
