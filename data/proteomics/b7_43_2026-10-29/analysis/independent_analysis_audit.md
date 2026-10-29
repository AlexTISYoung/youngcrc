# Independent audit of quantitative proteomics analysis

Reviewed 29 October 2026. Scope: `scripts/analyze.py`, its exported tables and the source matrices. This review did not edit the analysis script or publish the website. Audited script SHA-256: `e47fa185e9249491e84b6555b9a925408c993b36ad93e1772d31e29a2f7118b8`. Line references below refer to that version. Later supplementary analyses may resolve individual findings; they should be reported alongside this frozen audit.

## Overall assessment

The script correctly preserves native arbitrary-unit signals, collapses charge/modification states to distinct peptide sequences, avoids patient differential-expression P values, leaves missing observations unimputed, and keeps CPTAC tumour–normal calculations separate from patient LFQ. The three newly emphasized targets have convincing identification support **within the delivered matrix/search database**: FAP 14, LRRC15 8 and ROR1 6 distinct proteotypic sequences. They are not contaminant-library matches and have unambiguous single-gene mapping. Independently searching those 28 sequences across the delivered Swiss-Prot FASTA found each only in its corresponding protein, including when isoleucine/leucine were treated as indistinguishable. This verifies database specificity, not raw-spectrum quality or cell-surface localisation.

The numerical outputs do **not** establish patient-specific overexpression, tumour purity, cell-surface target density or treatment sensitivity. Their strongest defensible use is descriptive measured-signal support, target-validation prioritisation, and separately labelled public-cohort context.

## Required corrections or qualifications before interpreting the results

### 1. Separate endogenous keratins from the contaminant-library exclusion

Lines 31, 40 and 53 treat membership in the universal contaminant library as an exclusion from every high-support/reference comparison. That library contains legitimate human epithelial proteins. In this sample:

| Protein | Distinct unique sequences | All-detected signal percentile | Included in current epithelial reference panel? |
|---|---:|---:|---|
| KRT8 | 32 | 99.0 | No |
| KRT18 | 26 | 97.7 | No |
| KRT19 | 23 | 99.1 | No |
| KRT20 | 20 | 88.6 | No |

Consequently the apparent epithelial panel contains only six or seven of its eleven declared markers. Preserve the library flag, but restore plausible endogenous keratins in a sensitivity analysis, with clearly separated interpretation of common skin/hair contaminants. Do not describe these abundant KRT8/18/19/20 measurements as demonstrated contamination or infer globally low epithelial content from the filtered panel. Restoring these four keratins changed the Astral median epithelial rank shift from −18.27 to −16.03 points in my independent check; the shift remains negative, but keratin-specific shifts are much smaller (KRT8 −0.97, KRT18 −2.32, KRT19 −0.84, KRT20 −10.08). Compartment heterogeneity is therefore more informative than one panel average.

Parent reports a supplementary restoration analysis is underway. Retain both versions rather than silently replacing the original filter.

### 2. Keep cross-platform rank shifts descriptive; do not turn them into population percentiles or fold-changes

Lines 84–99 produce within-proteome ranks, then compare ranks across platforms and preparations. The values combine biological composition, acquisition/search effects, protein-specific response factors and gene-universe selection. Median centring removes one sample-wide location difference, not protein-specific bias. Exponentiating `centered_log2_signal_contrast` would therefore not produce a validated patient tumour/reference fold-change.

The percentages in `fraction_reference_ranks_below_query` count reference **within-proteome ranks** below the patient's within-proteome rank. They do not place the patient's concentration into a calibrated same-protein concentration distribution. LRRC15's 1.0 means 26/26 measured reference ranks were lower, and ROR1's 1.0 means 25/25; neither justifies “100th percentile expression,” “highest among CRC patients,” or an individual response prediction.

There is also a smaller implementation inconsistency: an anchor may be detected in only ≥80% of reference samples, while `rank(pct=True)` uses each sample's own nonmissing denominator. The nominal 6,282-gene Astral anchor set has 6,195–6,278 measured genes per sample. Re-ranking query and reference on a common pairwise measured-gene set gives:

| Target | Current Astral rank shift | Median pairwise matched-gene shift | Reference detections |
|---|---:|---:|---:|
| FAP | +38.41 | +38.04 | 27/27 |
| LRRC15 | +52.37 | +51.95 | 26/27 |
| ROR1 | +43.87 | +43.69 | 25/27 |
| CDH17 | −16.04 | −15.88 | 27/27 |
| PTK7 | +0.91 | +0.84 | 27/27 |

Thus the three large shifts are not created by this denominator inconsistency. The common-set correction still improves methodological clarity. A strict 100%-measured anchor set has 5,989 genes; LRRC15/ROR1 are then excluded, so missing target results under that rule must not be presented as contradicting their measured signal.

Required reporting: native signal and peptide support first; reference detection denominator and cohort preparation second; rank shift explicitly exploratory. Show sensitivity to anchor thresholds and meaningful compartment denominators. A stromal denominator asks a different biological question from a smooth-muscle denominator; disagreement cannot be solved by selecting whichever gives the largest increase. Do not use empirical P values or bootstrap intervals to imply cross-batch calibration that the design lacks.

Panel medians also condition on patient detection and reference coverage. The Astral “immune” panel reduces to **PTPRC, CD163 and CD4**; the other reference panels retain only PTPRC and CD163. These summaries cannot stand in for CD8/NK effector infiltration or establish an immune-cold state. Show which markers were measured, low-support, ambiguous or missing, and reserve cellular/spatial conclusions for tissue examination. Detectability filtering is not a neutral missing-at-random sample of the declared panel.

### 3. Export reference coverage before the ≥80% filter

Lines 99 and 125 attach detection counts only for retained anchors. A blank target/reference cell currently conflates absence, low detection prevalence and exclusion by the anchor rule:

| Target | Astral CRC | Komor CRC | Komor normal | HPA colon |
|---|---:|---:|---:|---:|
| FAP | 27/27 | **21/30** | 0/19 | 0/3 |
| LRRC15 | 26/27 | 0/30 | 0/19 | **1/3** |
| ROR1 | 25/27 | **1/30** | **2/19** | 0/3 |

For example, FAP was measured in most Komor CRC runs, but its current comparison and count fields are blank because 70% is below the anchor threshold. Export all-target detection count, total reference samples/runs, detection fraction, gene-mapping availability and explicit exclusion reason separately from the rank comparison. Zero detection is not proof of biological absence. Sparse positives should not be imputed or used to claim a stable reference distribution.

### 4. Maintain the distinction between controls, technical repeats and biological samples

The script does not reuse the vendor's 486 significant B7/control changes, which is appropriate. Two run columns with a log2 Pearson correlation of 0.9898 cannot identify the second specimen or establish technical reproducibility. A replicate-versus-control label requires the provider specimen/run key. Do not infer that an unknown comparator is normal colon, or that a highly correlated run is a repeat injection, from the correlation alone. The reanalysis correctly calls it `run423_intensity`.

There is only one patient biological sample in these computations. Peptides, precursor rows, technical runs and HPA's three measurements from one donor are not additional independent patients. The Komor table has 19 normal run names whereas the paper describes 18 normal samples; retain “runs” until that discrepancy is resolved. Public matrices are useful contextual controls, not a matched-normal estimate for this patient.

The original report's like-versus-like offsets and broad Astral leave-one-out variability already undermine calibrated patient overexpression claims. If reporting fresh pseudo-query/leave-one-out checks, apply exactly the same gene universe, target availability rules and reference exclusion to all comparisons. Do not compare unlike AUC experiments as though they were a single reference distribution. Parent reports additional control-identity checking and sensitivity work; incorporate verified results without converting assay correlation into pathology provenance.

### 5. State the identification-confidence limit and rename the Top3 check precisely

Lines 44–51 correctly count distinct unmodified sequences; there are no duplicate `(Protein.Group, Modified.Sequence, Precursor.Charge)` records in the precursor matrix. Delivered precursor-derived counts agree with vendor unique counts for every detected group. For the three lead targets, the independently checked sequence counts are sound.

However, the matrix has no run/global q-value columns or raw fragment/retention-time evidence. The vendor's report and methods use different confidence-field descriptions. A ≥2-sequence rule is identification support, not an independently reconstructed FDR or target-level validation. Request the exact DIA-NN version/configuration and long report for a deeper confidence audit; meanwhile state that confidence filtering was inherited from the delivered matrices. Overlapping missed-cleavage peptides are distinct sequences, not fully independent experimental confirmations.

`unique_top3_mean_signal` sums all measured charge **and modification** states for each stripped sequence before choosing the top three. Rename the exported `summed_charge_state_signal` accordingly, and describe Top3 as a “peptide aggregation sensitivity check.” The figure's “Independent peptide-level sensitivity check” could imply independent data: these quantities and the delivered protein signal share the same underlying measurement. Their global Spearman correlation 0.969 largely reflects common signal dynamic range; it does not establish per-target precision or surface abundance. The target-specific Top3 percentiles are FAP 74.82, LRRC15 55.76 and ROR1 43.47, versus all-detected protein signal percentiles 78.89, 65.11 and 52.04. Different rank universes contribute, so those differences are not calibration errors or confidence intervals.

### 6. Preserve mapping and selection provenance in the target export

There are 25 high-support HPA-symbol/FASTA-symbol disagreements. Most visibly resemble gene renaming/alias changes (for example SLC9A3R1/NHERF1), not 25 proven misidentifications. Reconcile by stable accession/Ensembl IDs and record aliases; do not silently drop them or treat exact string agreement as the sole biological validity criterion. None affects FAP/LRRC15/ROR1.

Lines 61–65 choose the highest-signal qualifying protein group for genes with multiple groups, which is a reasonable explicitly declared convention. Reference `groupby(...).max()` likewise can choose different groups in different samples. This is not a summed gene abundance; retain multiplicity/accessions and check important targets individually. The therapeutic target table currently drops the full protein-group identifier when resetting to gene, retaining only the leading accession. Add the full group ID for traceability, especially for HLA-related/isoform-sensitive interpretations.

Normal-tissue IHC filtering at line 154 uses `Reliability != 'Uncertain'` even though the comment promises only supported/enhanced/approved rows. Use an explicit allowed-value list to avoid retaining missing or unexpected categories in a future source release. This is a robustness fix, not a demonstrated change to the current target conclusions.

## CPTAC pairing and statistics: no numerical pairing error found

The 97 tumour and 100 normal columns share 96 unique case IDs. All 96 occur in the clinical case metadata. No duplicate sample IDs or duplicate unversioned Ensembl identifiers were found. The sole unpaired tumour is `14CO003`; four normal-only IDs are appropriately excluded. Pandas subtraction aligns names rather than positions, so differences are correctly paired even though column orders differ.

The Wilcoxon signed-rank calculation and monotone Benjamini–Hochberg adjustment are implemented correctly for the 5,807 retained genes. They test the public paired cohort, not this patient. Interpretation should acknowledge complete-pair selection, tissue composition, and the signed-rank distribution assumptions. For FAP, the independently confirmed table result is 96 pairs, median tumour-minus-normal log2 signal 1.3069 and 82/96 positive pairs (85.4%). PTK7 is +0.3863; CDH17 −0.3799. LRRC15 and ROR1 do not have retained paired results in this output and must not inherit FAP's validation.

Keep this assay distinct from the separate Robles/PDC000111 ppb-iBAQ reanalysis. Those are different quantities/cohorts with possible public-study overlap; combining them is not extra independent replication. Public tumour–normal changes support general CRC biology, not the patient's individual tumour–normal effect.

## ROR1 therapeutic assessment

The ROR1 observation is a credible **exploratory target-validation lead**, but currently weaker therapeutically than CDH17 or MET's human CRC evidence. Six canonical-sequence peptides include two in the annotated extracellular region and four intracellularly. They span both sides of the predicted transmembrane segment, but bulk digestion cannot demonstrate that all arose from one intact surface receptor on malignant cells. The topology record is saved in `ror1_uniprot_Q01973.json`.

No approved ROR1-directed CRC therapy, validated predictive CRC IHC cutoff or human CRC response evidence was identified in the current primary-source review. [IM-1021, NCT06823167](https://clinicaltrials.gov/study/NCT06823167), is recruiting with a possible sponsor-approved route for unlisted histologies; CRC acceptance is conditional, not confirmed. Prior TOP1 ADC and prior grade ≥3 irinotecan gastrointestinal toxicity are exclusions—the latter is not an exclusion of all irinotecan exposure. [NEOK001, NCT07612176](https://clinicaltrials.gov/study/NCT07612176), is a recruiting B7-H3×ROR1 study, but CRC inclusion remains unverified. CS5001 is suspended for benefit–risk/dose review; NBE-002 and LYL797 are terminated, so they should not appear as currently enrolling options.

The solid-tumour zilovertamab vedotin experience yielded one response among 102 participants, with no CRC patients enrolled; only 3/17 evaluable tissue samples were ROR1-positive and none of those patients responded. This neither establishes CRC efficacy nor proves that a genuinely ROR1-positive CRC cannot benefit. Full citations and current registry details are in [ROR1 therapeutic assessment](ror1_therapeutic_evidence.md).

Given limited nodal FFPE material, consider qualified tumour-membrane ROR1 IHC after confirming a plausible trial route, scoring percentage, intensity and malignant versus stromal localisation. A research antibody's positive signal alone need not match a sponsor assay. ROR1 should not displace higher-priority tests solely because its cross-platform rank shift is large.

## Additional immune and stromal leads from the broad surface screen

CD73/NT5E (13 unique peptides) deserves an adenosine-pathway discussion, but the assay does not measure its enzymatic activity or extracellular adenosine. Direct CRC CD73-inhibitor evidence is weak: oleclumab/durvalumab had one complete response in 42 MSS/pMMR CRC patients despite study-assay CD73 selection; randomised COLUMBIA-1 did not improve PFS or OS. The positive ARC-9 CRC regimen used **etrumadenant A2A/A2B receptor blockade**, not quemliclustat/CD73 inhibition, and combined it with checkpoint blockade, FOLFOX and bevacizumab. That multiagent result cannot isolate the adenosine drug's contribution or validate NT5E abundance; prior checkpoint treatment was excluded. Published quemliclustat ARC-8 efficacy is pancreatic, not CRC. See [CD73 primary-source assessment](cd73_additional_targets.md).

ITGA5 and ENG remain lower priority despite their descriptive rank shifts. Anti-α5β1 phase-I results did not demonstrate objective responses; TRC105/endoglin plus bevacizumab had one historical CRC partial response, so “no human CRC signal” would be too strong. Neither has an established expression-selected CRC treatment route. Both signals may reflect vascular/stromal composition rather than malignant-cell target density.

## Minimum changes to carry into the final report

1. Keep native signal/peptide support separate from exploratory reference ranks and public paired tumour–normal context.
2. Include the keratin-restored sensitivity panel and avoid purity or immune-exclusion claims from selected marker medians.
3. Export reference coverage and exclusion reasons for every target, including FAP's 21/30 Komor detections.
4. Report exact sequence-count/Top3 definitions, inherited confidence filtering, and full group identifiers.
5. Describe FAP/LRRC15/ROR1 as well-supported detections requiring spatial/current-lesion confirmation, with ROR1's clinical route explicitly conditional.
