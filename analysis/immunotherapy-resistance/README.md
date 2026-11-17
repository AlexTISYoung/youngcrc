# Immunotherapy resistance — SMAD4 functional evidence, 17 November 2026

The [current dated package](2026-11-17-smad4/README.txt) contains the report sources, website findings/rankings, selected numerical inputs and provenance. Its [release record](../../release/immunotherapy_resistance_2026-11-17_smad4.json) pins the separately reviewed PDF and inventory. The earlier [17 November](2026-11-17/README.txt), [16 November](2026-11-16/README.txt) and [14 November](../immune-evasion/2026-11-14/README.txt) packages remain historical provenance. Unrelated clinical tables and root website source retain the historical 1.53 snapshot.

The current report incorporates investigator-reported, exact-variant functional evidence for SMAD4 G359E (Monash personal communication, 17 November 2026). The investigators report strong damaging functional evidence and PS3 support while retaining an overall VUS assessment. This materially strengthens impairment of the tested SMAD4-dependent TGF-beta response, but does not establish complete or biallelic loss in current disease, ERK activation, somatic oncogenicity or vactosertib sensitivity. Therapeutic priorities remain unchanged.

The [dated molecular snapshot](2026-11-17-smad4/molecular/summary.json) also fills reviewed gaps from the primary reports. SMAD4 G359E is annotated VUS in the provider VCF but omitted from the printed Caris variant tables; Caris reports SMAD4 copy number as indeterminate. Provider-specific classifications, unresolved copy-number calls and investigator interpretation are shown separately. The historical root molecular tables are not overwritten.

The public conference abstract supplies assay context; the attributed communication supplies the G359E result. Original correspondence, attachment, contact identifiers and unpublished raw MAVE values are excluded. The package cannot independently reproduce or calibrate that experimental result. Existing 33 numerical tables, their inputs, and the historical packages remain unchanged. Outcome-linked vactosertib trial RNA analysis remains pending; no interim pathway results are included.

```sh
python3 analysis/immunotherapy-resistance/2026-11-17-smad4/verify_package.py
python3 -m pip install -r analysis/immunotherapy-resistance/2026-11-17-smad4/requirements.txt
python3 analysis/immunotherapy-resistance/2026-11-17-smad4/verify_package.py --rerun
```

Integrity verification is dependency-free. The numerical rerun reproduces compact downstream outputs, including original-universe rank summaries, protein/peptide counts, six allele fractions and five structural angles. It does not rerun raw sequencing, full-universe reference construction, spectral searches or clinical variant calling. Optional original-workbook clinical checks are hash-pinned and produce aggregate outputs only; CI does not fetch third-party data.

All tumour assays remain archival. Provider percentiles, research TPM/ranks, protein abundance and activation are distinct measurements. No current-node pathway state or treatment response is established. The patient reports insufficient cryopreserved material for tissue-culture experiments; no such proposals are made.
