# Methods and public-reference review for B7_43 quantitative proteomics

Reviewed 29 October 2026. This is a methods/reference note, not a new analysis of the patient's raw spectra. Linked files were located through primary repositories; where a binary/API could not be fetched with the web reader, that limitation is stated. The recommended analyses below are methodological judgments based on the cited evidence.

**Subsequent local verification:** the Robles/PDC000111 files and solid-sample archive were successfully downloaded and inspected. See [download/structure audit](robles_crc/README_INSPECTION.md) and `robles_crc/reference_structure_qc.json`. Material issues include an extra non-sample `ppb.iBAQ.peptides` column, highly variable study coverage, and two standalone SDRF annotation discrepancies. The standalone matrix has 90 sample columns, not the original source study's 95 aliquots.

## What can be quantified defensibly

| Quantity | Interpretation | Requirement / main limitation |
|---|---|---|
| Unique peptide count | Identification support and sequence coverage | Not protein abundance; depends on sequence length, digestion, detectability, search database and thresholds. |
| Precursor/peptide intensity | Instrument signal for a specified analyte | Keep units and intensity field explicit; do not mix MS1 and fragment intensities, raw and normalized fields, or different charge/modification aggregation rules. |
| PG.MaxLFQ / directLFQ protein intensity | Relative protein-group signal, principally useful for the same protein across comparable samples | Not molarity. Different proteins' ionization/digestion/observable-peptide responses differ. |
| Within-sample intensity rank | Where this protein's signal lies among the measured proteins | Useful descriptive signal ranking; not a cancer percentile or molecules-per-cell rank. The quantified universe affects the rank. |
| iBAQ / relative iBAQ | Approximate abundance estimator correcting summed peptide signal for theoretically observable peptides | Requires peptide-intensity sum, declared FASTA and in-silico digestion rules. Relative iBAQ additionally divides by the sample's total iBAQ. Not calibrated concentration. |
| Top3 | Mean/sum, explicitly specified, of three highest-signal distinct peptides | Require three qualifying peptide sequences and declare charge/modification aggregation. Fewer than three is missing for strict Top3, or a differently named TopN measure. |
| Reference-cohort percentile | Position for the same protein in a defined cohort measured on a comparable scale | Needs compatible quantification/calibration, biological sample metadata, nonmissing denominator and uncertainty. Cross-study rank alignment alone does not establish it. |

The original MaxLFQ method reconstructs protein profiles using shared peptide ratios and scales them to overall peptide signal. It was designed and benchmarked for relative changes across samples; its arbitrary scale is not a concentration measurement. [Cox et al., 2014](https://pubmed.ncbi.nlm.nih.gov/24942700/)

iBAQ is the sum of peptide intensities divided by the number of theoretically observable peptides. This is not equivalent to dividing MaxLFQ by amino-acid length. A reproducible implementation must declare enzyme, peptide length/mass limits, missed-cleavage handling, sequence release and ambiguous-group treatment. OpenMS explicitly implements the theoretical-peptide denominator. [OpenMS quantifier documentation](https://archive.openms.de/openms/Documentation/release/latest/html/classOpenMS_1_1PeptideAndProteinQuant.html) The original Top3 calibration used the three most intense tryptic peptides and an internal standard; uncalibrated Top3 in this patient should be described as an approximate abundance proxy. [Silva et al., 2006](https://pubmed.ncbi.nlm.nih.gov/16219938/)

## DIA-NN-specific audit

Record exact software version, command/configuration, FASTA/library, precursor and protein inference, normalization and match-between-runs settings. Current DIA-NN documentation distinguishes run-level and global precursor/group q-values; a main long report contains rows that need filtering before downstream aggregation. A global protein identification does not establish confident presence in every run. `PG.TopN` defaults to N=1 in current documentation: never rename it Top3 without the actual settings. `Genes.MaxLFQ.Unique` uses gene-proteotypic evidence; this is different from total protein-group signal. Version-specific documentation must govern the actual run. [Official DIA-NN documentation](https://vdemichev.github.io/DiaNN/)

Recommended patient export: preserve the full protein-group identifier and all mapped genes; include run/global q-values, peptide/precursor support, the original quantity field, a clearly named signal rank, and ambiguity flags. Do not duplicate one ambiguous group's entire intensity into each gene. Do not silently sum multiple groups mapped to one gene. Inspect proteotypic peptide evidence for therapeutic targets individually. FDR controls an expected identification error proportion; it does not measure quantitative accuracy or establish intact cell-surface localization.

## Normalization, reference comparison and uncertainty

directLFQ aligns ion/sample traces on a log scale and assumes most proteins are unchanged for between-sample normalization. Its authors discuss extracellular-matrix shifts as a situation where a selected normalization subset can help. It preserves relative peptide relationships but cannot correct every nonlinear acquisition effect. [Ammar et al., 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10315922/)

For B7_43, the primary quantitative output should therefore be **the measured patient signal and its support**. Public comparisons can be layered on as follows:

1. **Best:** patient and reference tissues prepared/acquired together, including bridge samples/standards, with common sequence search and quantification. Reprocessing raw spectra together harmonizes software but cannot erase extraction, instrument, fixation or tissue-selection differences.
2. **Exploratory:** compare matched peptide sets, or clearly labelled within-sample signal ranks, within a specified public cohort. Show sensitivity to the common quantified-protein universe and to alternative normalization. Report disagreement between references instead of selecting whichever gives the strongest increase.
3. **Independent biological context:** use public paired tumor–normal changes calculated within that study. A public tumor–normal fold-change supports general CRC biology, not the patient's own tumor–normal fold-change.

With one patient run and no contemporaneous normal, do not manufacture differential-expression P values or treat peptides as patient biological replicates. A z-score against a public reference includes both biology and batch differences. Batch and patient status are perfectly confounded when the only patient sample is its own batch; ComBat or quantile normalization cannot identify a unique correction from this design.

If exploratory percentiles are retained, use the same protein in a predeclared reference set, report `number below / number measured`, ties, detection prevalence and independent-donor count. Keep missing values separate. Distinguish an empirical reference rank from a clinically calibrated percentile; 27 independent tumors have only approximately 3.7-percentage-point empirical resolution. Three repeat tissue measurements from one donor are not three independent people. Do not translate a percentile or rank difference into a fold-change.

## Missingness and tissue composition

Missing values can arise at any intensity because of interference, identification thresholds or stochastic/technical effects, in addition to low abundance. Imputing a low number can create apparent patient overexpression or false absence. Preserve missingness in the patient target table and report reference detection rates. Imputation, if used for exploratory clustering, must be separately labelled and must not become observed target evidence. Comparative benchmarks find that imputation can impair downstream inference; its benefit is dataset-dependent. [Evaluating Proteomics Imputation Methods with Improved Criteria](https://pmc.ncbi.nlm.nih.gov/articles/PMC10949645/)

Bulk CRC tissue contains epithelial, fibroblast, smooth-muscle, vascular and immune components. Spatial/LCM proteomics demonstrates distinct epithelial versus stromal abundance patterns. Consequently FAP, collagens or smooth-muscle proteins can reflect compartment abundance; lower epithelial markers can reflect dilution. Neither observation alone establishes tumor-cell regulation. Review matched H&E/tumor cellularity and retain compartment signatures as QC/context, not an unvalidated numerical purity correction. [CRC stromal proteomics study](https://pmc.ncbi.nlm.nih.gov/articles/PMC9010820/), [spatial CRC proteomics study](https://pubmed.ncbi.nlm.nih.gov/39026393/)

## Public datasets and actionable downloads

### 1. HPA normal-tissue bulk MS: useful FFPE/DIA technical context, not a healthy-population cohort

- [Individual sample matrix ZIP](https://www.proteinatlas.org/download/tsv/ms_tissue_sample_data.tsv.zip)
- [Tissue summary matrix ZIP](https://www.proteinatlas.org/download/tsv/ms_tissue.tsv.zip)
- [Tissue metadata ZIP](https://www.proteinatlas.org/download/tsv/ms_tissue_tissues.tsv.zip)
- [Download definitions](https://www.proteinatlas.org/humanproteome/tissue/data)

HPA v25.1/Ensembl109 describes 60 samples across 20 tissues, including colon. The individual table contains gene, gene name, sample, cell type, replicate and intensity. Download targets resolve, but the web text reader cannot render ZIP contents; inspect headers after download.

**Critical metadata:** official detailed methods say all 20 tissues come from **one healthy female donor**, with three tissue replicates each. They are FFPE, measured by Orbitrap Astral Zoom DIA, processed with DIA-NN 1.9.2 and directLFQ 0.2.19 without imputation. Tissue summaries are replicate medians with a missingness rule. These are relative normalized intensities, not iBAQ or molecules/cell. A patient-versus-colon comparison is an exploratory comparison to one donor's tissue. [HPA detailed MS methods](https://www.proteinatlas.org/humanproteome/tissue/method/MS%2Bbased)

HPA's cell-resolved DVP resource can help interpret the compartment of a signal; it uses laser-microdissected cells and should not be treated as the same bulk quantitative scale. [DVP methods](https://www.proteinatlas.org/humanproteome/single%2Bcell/dvp/method)

### 2. Harmonized public CRC label-free DDA reanalysis: useful approximate abundance reference

- [Repository root, individual datasets and metadata](https://ftp.ebi.ac.uk/pub/databases/pride/resources/colorectalcancer/)
- [Solid-tissue archive, 72 MB](https://ftp.ebi.ac.uk/pub/databases/pride/resources/colorectalcancer/Solid_samples/Solid_samples.rar)
- [Archive file definitions](https://ftp.ebi.ac.uk/pub/databases/pride/resources/colorectalcancer/Solid_samples/Readme.txt)
- [TCGA/CPTAC PDC000111 gene-level abundance matrix, 4.4 MB](https://ftp.ebi.ac.uk/pub/databases/pride/resources/colorectalcancer/CPTAC-PDC000111/CPTAC-PDC000111-MappedToGeneID.txt)
- [PDC000111 sample/run metadata](https://ftp.ebi.ac.uk/pub/databases/pride/resources/colorectalcancer/CPTAC-PDC000111/CPTAC-PDC000111.sdrf.txt)
- [PDC000111 processing methods](https://ftp.ebi.ac.uk/pub/databases/pride/resources/colorectalcancer/CPTAC-PDC000111/CPTAC-PDC000111-analysis-methods.tsv)
- [PDC000111 quantification settings](https://ftp.ebi.ac.uk/pub/databases/pride/resources/colorectalcancer/CPTAC-PDC000111/CPTAC-PDC000111.mqpar.xml)

Robles et al. reprocessed public label-free DDA studies with MaxQuant 2.1.0.0. The abundance unit is fraction-of-total iBAQ in parts per billion, not TMT ratios. Mixed tissues/secretions were analyzed separately; use **Solid_samples**, then filter normal mucosa, adenoma and carcinoma by metadata. Different acquisition depths still bias fractional abundance; the paper explicitly observes this. The collection is useful for approximate abundance/distribution context, but its iBAQ scale cannot be equated to patient MaxLFQ. [Primary study and methods](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1011828)

The solid archive contains `proteinGroups_ppb_final.txt` (ppb-iBAQ), `proteinGroups_ppb_final_binning.txt` (five abundance bins), `Sample_classification.txt` (sample, dataset, condition, source) and raw MaxQuant `proteinGroups.txt`. The individual PDC000111 download is also explicitly documented as ppb abundances mapped to Ensembl genes. [Repository README](https://ftp.ebi.ac.uk/pub/databases/pride/resources/colorectalcancer/CPTAC-PDC000111/Readme.txt) Resolve donor duplicates before calculating a cohort distribution: the source PDC study has 95 tumor aliquots from 90 people, including five repeat tumor portions. [PDC000111](https://pdc.cancer.gov/pdc/study/PDC000111)

### 3. PRIDE DIA cohorts already relevant to the original explorer

**PXD073413 (Astral CRC):** [ProteomeXchange record](https://proteomecentral.proteomexchange.org/cgi/GetDataset?ID=PXD073413) describes 13 KRAS-mutant and 14 wild-type CRC cases, plus matched adjacent tissue in the study description. The original repository FTP path is `ftp://ftp.pride.ebi.ac.uk/pride/data/archive/2026/02/PXD073413`. Verify actual matrix columns and sample metadata; a description of matched normals does not prove normals are included in the specific available tumor matrix. Exclude pooled QC and do not mix it with patients. Check library, software version, unit and preparation before comparing with B7_43. A paper now explicitly cites this accession: [Extracellular CD44 lactylation impairs CD8+ T cell function in KRAS-mutant colorectal cancer](https://www.nature.com/articles/s42255-026-01482-3). Its publication date/methods should be incorporated before retaining an older “unpublished” label. The archive listing was not fetchable through the web tool in this pass; no unverified specific matrix URL is supplied.

**PXD012254 (Komor normal/adenoma/CRC):** [Primary paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC7027554/) and [PRIDE accession](https://www.ebi.ac.uk/pride/archive/projects/PXD012254). Useful exports are `ProteinGroups_Normal_Adenoma_Cancer_Search.xls` and `FragmentLevelExport_Normal_Adenoma_Cancer_Search.zip`; there is a separate low-risk/high-risk adenoma search, which must not be confused with the tumor/normal comparison. Fetch file URLs through the [PRIDE API](https://www.ebi.ac.uk/pride/ws/archive/v2/docs/api-guide.html) or repository download panel, preserve the original Spectronaut quantity definition, and verify sample/run-to-donor mapping. This pass verified the accession and export names but did not download/revalidate their numeric headers.

### 4. CPTAC/PDC: separate label-free abundance from TMT relative quantities

[PDC000109](https://pdc.cancer.gov/pdc/study/PDC000109) is the prospective Vanderbilt label-free CRC arm; [PDC000116](https://proteomic.datacommons.cancer.gov/pdc/study/PDC000116) is the prospective PNNL **TMT10** arm. The latter describes 97 tumor and 100 normal tissues, with 96 matched pairs in that assay; publication-derived data are linked from [LinkedOmics](http://linkedomics.org/cptac-colon/). PDC000111 above is another explicitly label-free source.

The [PDC public API](https://pdc.cancer.gov/pdc/publicapi-documentation) exposes `quantDataMatrix` with `data_type` such as `log2_ratio` or `unshared_log2_ratio`, plus biospecimen and workflow metadata. A pooled-reference TMT ratio describes each protein relative to its own reference abundance; ranks across different proteins are not absolute-abundance ranks. Use the TMT cohort for internally estimated tumor–normal effects or within-protein distributions, **not direct subtraction from patient LFQ**. Preserve the specific data release and reference-channel definition.

### 5. ProteomicsDB: normal-tissue iBAQ/Top3 context with sample-level metadata

The [official API](https://www.proteomicsdb.org/api) supports `proteinexpression.xsodata`, `proteinspertissue.xsodata` and `tissuelist.xsodata`. `CALCULATION_METHOD=0` selects iBAQ and `1` Top3; `GROUP_BY_TISSUE=0` retains samples rather than tissue aggregation. Available fields include experiment/project IDs, source, raw intensity, total-sum-normalized intensity and number of samples. Use the tissue list to resolve the actual colon ontology ID; do not reuse the documentation's example tissue ID as colon.

An actionable documented path template, appended to `https://www.proteomicsdb.org`, is:

```text
/proteomicsdb/logic/api/proteinexpression.xsodata/InputParams(PROTEINFILTER='P00533',MS_LEVEL=1,TISSUE_ID_SELECTION='',TISSUE_CATEGORY_SELECTION='tissue;fluid',SCOPE_SELECTION=1,GROUP_BY_TISSUE=0,CALCULATION_METHOD=0,EXP_ID=-1)/Results?$format=json
```

The endpoint is documented, not download-tested in this review; the [v2 API](https://www.proteomicsdb.org/apiv2) is also available. Do not compare aggregated tissue minima/maxima to B7_43 as patient percentiles. Total-sum-normalized iBAQ is compositional and does not remove study/platform effects.

## Recommended implementation order

1. Audit and preserve native patient quantities, confidence fields and protein-group mapping; produce descriptive patient signal ranks with no overexpression claim.
2. Retrieve HPA individual FFPE/DIA data and the Robles solid CRC ppb-iBAQ matrix plus metadata. Keep their units separate; treat the HPA donor as one person.
3. Revalidate the actual PXD073413/PXD012254 files and their sample annotations, excluding QC and duplicate biological units.
4. Present reference detection, public within-study tumor–normal direction, and exploratory rank comparisons as separate fields. Label all missing observations and technical incompatibilities.
5. Reserve clinical target-expression conclusions for convergent evidence: confidently assigned peptides, patient IHC/spatial localization, reproducibility and modality-specific eligibility criteria. Abundance alone does not establish dependency, surface accessibility, drug sensitivity or trial eligibility.
