# Immunotherapy resistance — 17 November 2026

The [current dated package](2026-11-17/README.txt) provides the reviewed report sources, website findings/rankings snapshot, compact numerical inputs, derived tables and source provenance. Its [release record](../../release/immunotherapy_resistance_2026-11-17.json) pins the separate 58-page PDF and package inventory. The [16 November package](2026-11-16/README.txt) remains unchanged historical provenance. Unrelated clinical tables and root website source remain the historical 1.53 snapshot.

The current addition integrates completed SMAD4 G359E evidence and a 160-gene review of SMAD4-independent TGF-beta signalling, ERK and alternative pathway inputs. Exact published MPAS membership is rescored with explicit research normalization and coding-transcript sensitivities; this is not a clinical MPAS classifier. Total ERK detection does not establish phosphorylation or TGF-beta dependence. G359E remains a clinical variant of uncertain significance despite evidence that it is acquired and transcribed in the primary biopsy. Caris NS means an assay-matched percentile was not supplied, not absent RNA or assay failure. Neither finding upgrades vactosertib efficacy or changes therapeutic priorities.

The separate vactosertib trial RNA analysis is unfinished. No interim pathway scores, association tests or responder/nonresponder inference are included. Its prespecified primary endpoint is durable clinical benefit (5 versus 23); objective response (2 versus 26) is secondary. Screening-labelled tissue is often archival.

```sh
python3 analysis/immunotherapy-resistance/2026-11-17/verify_package.py
python3 -m pip install -r analysis/immunotherapy-resistance/2026-11-17/requirements.txt
python3 analysis/immunotherapy-resistance/2026-11-17/verify_package.py --rerun
```

Integrity verification uses the standard library. The numerical rerun reproduces the retained 24 tables plus the new RNA/protein summaries, peptide and modification counts, allele fractions and structural angles from pinned compact inputs. It does not rerun raw sequencing, full-universe reference preprocessing, spectral searches or clinical variant calling. Full-source provenance and optional upstream algorithms retain these boundaries; original trial workbooks are optional, hash-pinned inputs and only aggregate outputs are redistributed. CI does not fetch third-party source data.

All tumour assays are archival. Provider percentiles, research TPM, full-universe expression ranks, protein groups, gene-specific peptides and actual pathway activation remain separate. Rankings are conditional research priorities, not individual response predictions. The user reports insufficient cryopreserved material for organoid/tissue-culture experiments; no such proposals are made. Publication does not establish treatment administration or clinical access.
