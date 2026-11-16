# Immunotherapy resistance — 16 November 2026

The [revised 51-page PDF](https://youngcrc.com/reports/research/immunotherapy_resistance_report_2026-11-16.pdf) is accompanied by the [dated package](2026-11-16/README.txt). The package provides the reviewed report sources, website findings/rankings snapshot, compact numerical inputs, derived tables, method definitions and source provenance. Its [release record](../../release/immunotherapy_resistance_2026-11-16.json) pins the separate public PDF and package inventory. Unrelated clinical/evidence tables and website source remain the historical 1.53 snapshot.

The analysis covers 37 RNA/protein sets, 1,225 targets, a separate 156-gene recruitment lookup, protein assignment/peptide checks, and a source-workbook audit of vactosertib trial biomarkers. The package reproduces downstream calculations from selected full-precision intermediates and full-universe rank vectors. It does not redo raw-read quantification, full-reference preprocessing or spectral analysis. Published source hashes and optional upstream algorithms retain those boundaries explicitly.

```sh
python3 analysis/immunotherapy-resistance/2026-11-16/verify_package.py
python3 -m pip install -r analysis/immunotherapy-resistance/2026-11-16/requirements.txt
python3 analysis/immunotherapy-resistance/2026-11-16/verify_package.py --rerun
```

Integrity verification uses the standard library; the 24-table numerical rerun uses the pinned dependencies. The optional clinical-workbook audit requires the original public workbook and verifies its hash; it publishes aggregate outputs only. See the package README for its source/fetch commands. CI does not fetch third-party source data.

All tumour assays are archival. Provider percentiles, research TPM, full-universe expression ranks, protein group signals, gene-specific peptides and actual pathway activation remain separate. Strong smooth-muscle/ECM signals do not measure tumour fraction or prove a drug-sensitive stromal mechanism. Clinical trial pharmacodynamic change, durable stable disease and objective response are different endpoints. Rankings are conditional research priorities, not personal response estimates.

The user reports insufficient cryopreserved material for organoid or tissue-culture experiments; current report proposals respect that constraint. Historical report sources remain provenance, not current experimental recommendations. No treatment change or clinical access is effected by this publication.
