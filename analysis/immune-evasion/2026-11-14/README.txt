Immune-evasion analysis and report — 14 November 2026

Purpose
Reproducible sources for the revised case report, including its one-page executive summary, eight ranked immune-evasion axes, therapeutics ranked within each axis, cross-dataset evidence and experiments that discriminate between hypotheses. The rankings are research/discussion priorities, not response probabilities or treatment recommendations. The final ranking tables in rankings.json supersede preliminary working drafts.

Scope and specimen identity
Caris: March2024 rectal biopsy. Tempus and BostonGene: treated October2024 rectal resection, with separate assays/blocks. Valius: selected October2024 liver-metastasis single-cell summaries. B7 protein data: October2024 rectal resection, not the October2026 node. Blood cell-free and buffy-coat RNA are kept separately and cannot establish lesion expression. No newly generated current-node sequencing or proteome is included.

Key revisions
The November Caris assay-matched percentiles place IRF1, TAP1 and HLA-A/B near the cohort median, weakening the previous universal-low-expression interpretation. BostonGene's low resection RNA remains a genuine assay observation with cell-composition and treatment confounding. The old Caris TGFBI percentile is not a TGFB1 ligand percentile. CD39/CD73/ENPP1 protein identification strengthens a testable nucleotide-metabolism hypothesis. The sole source-labelled HLA-G peptide is not gene-specific when leucine/isoleucine ambiguity is allowed. Current-node localisation and functional rescue remain necessary to establish a therapeutic dependency.

Files
- rankings.json: exact final report ranking tables, rationale, counterevidence, access and tests.
- rna/: 337-gene expression matrix, 18-primary GSE50760 context, provider tables, selected research variants, source-linked findings, portable re-extraction script.
- proteomics/: 279-gene panel, 168 source quantity/sequence checks, sequence-specificity audits and portable scripts.
- inputs/: minimal selected rows/columns sufficient to recreate the derived tables. These are source subsets, not new assays. Full source hashes, subset hashes, transformations and public source/provenance URLs are in source_manifest.json.
- literature/: dated ClinicalTrials.gov protocol/status snapshots, with contacts/locations directories omitted. URLs and original snapshot hashes are retained. Full journal articles and superseded working rankings are not redistributed.
- report/: portable Python report content/builder and 66 source citations. Only an unnecessary pathology accession is removed from the public report source; clinical content is retained. The existing authorized Tempus correspondence paraphrases remain, without emails, addresses or links to private correspondence.
- provenance/: prior quantification settings/run provenance and publication validation. The previous whole-transcriptome Salmon calculation is distinct from this revision's table re-extraction.
- package_manifest.json: hash inventory of the finished package.

Reproduction (Python3 standard library)
  python3 verify_package.py
  python3 verify_package.py --rerun
The second command runs the RNA and protein extraction scripts in a temporary copy and compares all generated CSV rows/values with the bundled results. It does not alter the original package.

Optional sequence-specificity rerun
  python3 fetch_optional_database.py
  python3 verify_package.py --rerun
The helper retrieves the already-published 7.2MB frozen Swiss-Prot database and verifies its exact SHA-256 before use. When that file is present, the verifier also re-runs both peptide audits. It searches the entire database, not merely the target proteins. No mass-spectrum search or identification-FDR reconstruction is performed.

Editable report generation (python-docx required)
  python3 -m pip install python-docx
  python3 report/build_revision.py
This produces report/immune_evasion_report_2026-11-14.docx. PDF rendering requires a compatible Word/LibreOffice renderer and full visual review; pagination can depend on fonts and renderer. The deployed PDF is a separately reviewed artifact, with its checksum recorded by the website release. Sources use relative paths; no private workspace is required.

Computational and interpretation limits
Patient and GSE50760 gene estimates were computed with Salmon2.8.0, GENCODE37/GRCh38.p13, k31, automatic per-library orientation, selective alignment, sequence/GC bias correction, allowDovetail and 30 bootstraps. All transcriptome genes were quantified before target selection. No genomic decoys, personalised HLA alleles, UMI correction or PCR duplicate removal were used. Matching software does not match library chemistry, tissue preservation, purity or treatment. The selected 18-primary cohort is exploratory and must not be interpreted as assay-matched clinical percentiles.
Protein-group intensity is an arbitrary bulk signal; source-labelled proteotypic peptide counts are not automatically gene-specific. Reference ranks are descriptive, not clinical percentiles or replicated differential expression. No surface, phospho, spatial or functional assay is supplied. No new clinical mutation calling, methylation analysis, pathway activity score or individual response prediction is performed.

Publication boundaries
The package contains participant-authorized case-derived analysis. It omits private correspondence, internal patient/accession identifiers, local filesystem paths, withdrawn third-party vaccine-renderer material and full journal-article working copies. Original public sources retain their own terms; publication of a URL or a checksum does not transfer third-party rights. Trial status is dated14November2026 and does not establish individual eligibility or supply. No clinical intervention is performed by these scripts.
