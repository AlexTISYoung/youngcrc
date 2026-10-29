# Descriptive public iBAQ reference context

`public_ibaq_context.tsv` summarizes every one of the 8,949 genes in the downloaded Robles combined solid-tissue matrix separately for each dataset and tissue class: 10 groups and 89,490 gene/group rows. Tumor, mucosa and adenoma are never pooled. Values remain on the source's **fraction-of-total iBAQ, parts-per-billion (ppb.iBAQ)** scale. No normalization, imputation, patient comparison, percentile, fold-change or statistical test was performed.

For each gene/group, the table reports sample-column count, detected/missing counts, detection fraction, positive-value median, positive-value 25th/75th percentiles and their difference (IQR). Quantiles use linear interpolation. Numeric values were positive or missing; there were no numeric zeros. The median and IQR are conditional on detection, so interpret them with the detection fraction. Blank abundance statistics mean no measurements. With one detected value, both quartiles equal that value and IQR is zero; that does not establish reproducibility.

`public_ibaq_sample_metadata.tsv` preserves source sample IDs, dataset, tissue class and organ and adds measured-gene coverage. For the 90 distinct CPTAC samples, the source TCGA participant barcodes are preserved as donor IDs (for example TCGA-AG-A036). The remaining datasets lack explicit donor/pairing fields in the combined metadata; their donor count is blank rather than equated to sample count. The CPTAC tumor group contains both colon and rectal samples; organ is retained in sample metadata and the group has `Colon|Rectum` in `organs_in_group`.

| Dataset | Tumor samples | Mucosa samples | Adenoma samples |
|---|---:|---:|---:|
| CPTAC | 90 | 0 | 0 |
| PXD001676 | 8 | 8 | 0 |
| PXD002137 | 8 | 8 | 16 |
| PXD014511 | 0 | 17 | 45 |
| PXD019504 | 37 | 37 | 0 |

The unannotated `ppb.iBAQ.peptides` field was excluded because it is processed peptide-count metadata, not a sample. All 274 annotated source samples were retained. PXD001676 has shallow coverage (863–1,396 genes/sample), and PXD014511 contains an adenoma with only 169 measured genes. These are descriptive summaries of the supplied data, not a filtered clinical reference cohort. Coverage is supplied so subsequent analyses can predeclare justified quality filters.

The gene-mapped column totals do not sum to one billion after upstream filtering. They were preserved without renormalization. The separate standalone PDC000111 matrix was **not** combined with this matrix: it represents overlapping people reprocessed separately and has sample-annotation discrepancies. Detailed provenance, checksums and inspection findings are in `../reference/robles_crc/download_manifest.json`, `reference_structure_qc.json` and `README_INSPECTION.md`.

Use these distributions as independent public abundance/detection context. A quotient of patient DIA fragment/MaxLFQ signal and these ppb-iBAQ values is not a biological fold-change. A high median among measured samples is not tumor-specific expression. Within-study tumor/mucosa comparisons need the original pairing/donor metadata and appropriate handling of missingness, coverage and tissue composition before inference.

Sources: [EMBL-EBI solid-tissue matrix archive and README](https://ftp.ebi.ac.uk/pub/databases/pride/resources/colorectalcancer/Solid_samples/), [Robles et al., primary methods](https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1011828).
