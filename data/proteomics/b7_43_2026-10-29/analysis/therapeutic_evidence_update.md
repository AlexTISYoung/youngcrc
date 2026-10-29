# Therapeutic interpretation of quantitative proteomics — evidence update, 29 October 2026

This is a primary-source therapeutic evidence audit for the quantitative analysis. It does not assign the new abundance values, which are being analysed separately, and does not infer a treatment indication from protein detection. Current trial records were downloaded on 29 October into `analysis/registry/`; record update dates are distinguished from retrieval dates. No website was changed or clinician contacted.

## Material developments since the 22 October review

1. **MET ADC evidence has matured:** a randomized phase-I Temab-A plus bevacizumab paper appeared on **24 October 2026**, replacing reliance on the earlier conference report. This is a small randomized signal, not a confirmatory phase-III survival result. The study did not select participants by MET protein expression.
2. **CDH17 ARR-217/MRG007 now has human CRC data:** the **25 October 2026** sponsor release reports early responses. The headline response rate mixes confirmed and unconfirmed responses and must be labelled accordingly. See the surface-target evidence section below.
3. **TROP2 should not be upgraded merely because more quantitative signal becomes available:** the 2026 TROPHIT1 final abstract reported low activity and did not advance to its randomized stage despite frequent TROP2 staining.
4. Current registry checks retain meaningful gates: IDE034 excludes recent ordinary irinotecan as well as TOP1 ADCs; ifinatamab's CRC cohort excludes prior irinotecan; ZL-6201 has a prior-line restriction. These are agent-specific rules, not universal ADC exclusions.

## What quantitative expression can and cannot change

A reproducible intensity estimate can improve confidence that a target is present and help compare that same protein across suitably processed samples. It cannot directly substitute for tumour membrane IHC, programme-specific FAP PET, an activating mutation, a gene fusion, target dependency, phosphatase activity, or a treatment-response biomarker. Unique-peptide counts are identification evidence, not comparable abundances across proteins. Different proteins produce and ionize different peptides; within-run intensity ranks also are not molecule counts unless calibrated.

For a surgical specimen, abundant protein may derive from normal epithelium, smooth muscle, fibroblasts, extracellular matrix or immune cells. A relative signal in this specimen cannot establish current metastatic expression. Missing MS signal does not establish absence from all cancer cells. The original treated-primary assignment should follow the independent provenance audit; the new folder/run identifiers must not be silently equated with a pathology block.

The validation depends on mechanism:

| Therapeutic class | Most relevant validation | What bulk protein abundance cannot establish |
|---|---|---|
| Antigen-directed ADC/CAR-T/bispecific | Tumour membrane staining, percentage and heterogeneity; trial-specific central assay | Accessible surface density, internalization, payload susceptibility or therapeutic window |
| FAP radioligand | Current-lesion tracer uptake, retention and dosimetry with the specific programme's tracer | Radiation delivery to all important lesions or safety for normal organs |
| HER2/EGFR/MET pathway treatment | Indication-specific IHC/ISH, copy-number or current mutation/resistance testing | Oncogenic signalling dependence from ordinary receptor presence |
| PTPN1/PTPN2 inhibition | Pharmacodynamic/functional response and native tumour killing in a research setting | Excess enzyme activity or predicted clinical response |
| Neoantigen/TCR strategy | Retained mutant transcript, relevant HLA, natural peptide presentation and T-cell recognition | Mutant peptide–HLA display from source-protein or HLA/TAP detection |

## CDH17: two early clinical ADC signals, no approved match

**ARR-217/MRG007 has new human CRC results.** The sponsor's 25 October release reports 123 treated patients, including 113 with CRC. At 6 mg/kg, 13/29 evaluable CRC patients had reported responses (44.8%), comprising **7 confirmed, 4 pending confirmation and 2 unconfirmed** at the August 5 cutoff. Thus 44.8% is not confirmed ORR: 7/29 (24.1%) were confirmed at that cutoff. Across doses ≥4 mg/kg, 25/73 reported responses included 15 confirmed. Grade ≥3 treatment-related events occurred in 30.1% of all treated patients; neutropenia and diarrhoea were the main severe events. These uncontrolled, immature data cannot establish superiority to another CDH17 ADC. [Primary sponsor release](https://ir.arrivent.com/news-releases/news-release-details/arrivent-announces-initial-phase-1-data-cdh17-targeted-adc-arr).

**AMT-676** has an independent CRC signal: the ESMO GI 2026 abstract reports 23/125 responses (18.4%; confirmation status unspecified), with 94.4% previously exposed to irinotecan. Median PFS was 6.0 months in a 26-patient 6.4-mg/kg cohort. Grade-3 anaemia, neutropenia and diarrhoea were 11.6%, 10.1% and 4.0%, and one grade-3 colitis DLT occurred. These small single-arm cohorts are not directly comparable with ARR-217. [Primary AMT-676 abstract](https://www.annalsofoncology.org/article/S0923-7534%2826%2900297-8/fulltext).

Current registry distinctions matter:

- [AMT-676, NCT06400485](https://clinicaltrials.gov/study/NCT06400485), recruiting: requires tissue, measurable disease and ECOG 0–1. Prior CDH17 therapy or TOP1-payload ADC excludes; this is **not** a blanket conventional-irinotecan prohibition. Australian recruiting sites are verified; no UK route is established.
- [ARR-217/MRG007, NCT07066657](https://clinicaltrials.gov/study/NCT07066657), recruiting: requires CDH17-testable tissue or baseline biopsy, measurable disease and ECOG 0–1. Prior CDH17 therapy excludes. Public criteria do not show a blanket prior TOP1-ADC prohibition, although the full protocol may add restrictions. US sites are listed.
- [DB-1324, NCT07263594](https://clinicaltrials.gov/study/NCT07263594), recruiting: no human CRC response data verified here. Prior CDH17 therapy or TOP1 ADC excludes; gastrointestinal bleeding, obstruction, perforation and fistula are material screening concerns.
- [CHM2101 CAR-T, NCT06055439](https://clinicaltrials.gov/study/NCT06055439), active **not recruiting** in its 22 October update; it is not an available enrolling option on that evidence.

**Case interpretation:** strong quantitative CDH17 would reinforce current-metastasis membrane IHC as a useful validation, not establish response probability. Normal intestinal epithelium can contribute CDH17 to bulk surgical tissue. Score malignant-cell membrane intensity, percentage and heterogeneity, and use the programme's assay if required. No CDH17-directed approved CRC indication was identified.

## PTK7 and dual PTK7×B7-H3 targeting

[KIVU-107, NCT07229313](https://clinicaltrials.gov/study/NCT07229313), is recruiting phase I with broad solid-tumour criteria and CRC keywords. This supports a screening enquiry but does not confirm an accepting CRC cohort. Prior PTK7 therapy or a TOP1 ADC excludes; ordinary irinotecan is not explicitly prohibited by that clause. Measurable disease and ECOG 0–1 are required. No human CRC response results were verified. [Primary trial-in-progress abstract](https://ascopubs.org/doi/pdfdirect/10.1200/JCO.2026.44.16_suppl.TPS3158).

[IDE034, NCT07503808](https://clinicaltrials.gov/study/NCT07503808), is a recruiting B7-H3×PTK7 TOP1 ADC study explicitly including CRC. Its rule is different: **any TOP1 inhibitor within six months includes conventional irinotecan**; prior B7-H3/PTK7 ADC also excludes. The sponsor anticipates first data at the end of 2026/early 2027. Bulk PTK7 and CD276 co-detection does not demonstrate the same-cell coexpression relevant to the design. Current tumour membrane staining and, if pursuing this programme, spatial/multiplex coexpression are more informative than adding separate abundance ranks. [Primary sponsor update](https://ir.ideayabio.com/2026-08-04-IDEAYA-Biosciences-Reports-Second-Quarter-2026-Financial-Results-and-Provides-Business-Update).

PTK7 remains an investigational target. The original report's DAY301, LY4175408 and HWK007 matches should not substitute for CRC-cohort verification; the October 22 audit did not identify CRC among their listed histologies.

## LRRC15: stromal localisation and prior-line gate

[ZL-6201, NCT07374848](https://clinicaltrials.gov/study/NCT07374848), is recruiting phase Ia/b, and the [NYU primary listing](https://clinicaltrials.med.nyu.edu/cancer/clinicaltrial/3066/an-open-label-phase-1ab/?qd=77054292) includes colon cancer. No human CRC efficacy was verified. The public criteria limit selected epithelial tumours to **no more than three prior systemic lines in the metastatic/relapsed refractory setting** and require tissue, measurable disease and ECOG 0–1. Prior TOP1 ADC excludes; that is not a blanket conventional-irinotecan exclusion.

Score LRRC15 in malignant cells and fibroblast-rich stroma separately. Sponsor preclinical evidence supports stromal delivery and bystander killing, but is not a validated patient response test. A strong bulk signal could derive principally from fibroblasts. [Primary preclinical poster](https://www.zailaboratory.com/wp-content/uploads/2026/05/2026_ZL-6201-AACR-Poster.pdf). The October investor disclosure still anticipates proof-of-concept data in the first half of 2027. [Primary disclosure](https://ir.zailaboratory.com/node/15316/ixbrl-viewer).

## B7-H3 / CD276: CRC trials, with important access restrictions

**Risvutatug rezetecan:** [EMBOLD PanGI-201, NCT06885034](https://clinicaltrials.gov/study/NCT06885034), is recruiting, with CRC included and Manchester listed. Prior TOP1 ADC excludes; conventional irinotecan is a different exposure. The [ASCO GI protocol abstract](https://ascopubs.org/doi/pdfdirect/10.1200/JCO.2026.44.2_suppl.TPS264) and [hospital/network listing](https://recherchesantequebec.ca/public/projects/455901) specify **one to two previous CRC lines**. Its omission from abbreviated registry text is not evidence that the limit was removed. Recent significant bleeding and relevant pneumonitis also matter. [GSK study page](https://www.gsk-studyregister.com/trials/223675).

The wider [EMBOLD PanTumor-101, NCT06551142](https://clinicaltrials.gov/study/NCT06551142), has broad monotherapy criteria but a three-prior-line limit for combination escalation; a currently accepting CRC cohort is unconfirmed. GSK's October efficacy announcements concern small-cell lung cancer and osteosarcoma, not CRC. [GSK primary programme update](https://www.gsk.com/en-gb/media/press-releases/gsk-showcases-pipeline-momentum-across-lung-gynaecological-and-gastrointestinal-cancers-at-esmo-2026/).

**Ifinatamab deruxtecan:** [NCT06330064](https://clinicaltrials.gov/study/NCT06330064), recruiting in its 26 October record, still explicitly excludes previous irinotecan/topotecan or other TOP1 inhibitor from its CRC cohort. Prior irinotecan therefore remains disqualifying under those published criteria. [NCI primary listing](https://www.cancer.gov/research/participate/clinical-trials-search/v?id=NCI-2025-00431).

CD276 detection in the earlier report was not evidence of B7-H3-high tumour. Quantitative abundance still needs malignant-cell membrane localisation and heterogeneity assessment. None of these B7-H3 approaches has an approved CRC indication identified here.

## MET / telisotuzumab adizutecan (Temab-A, ABBV-400)

**New primary evidence:** the 24 October randomized phase-I publication reports 83 treated patients: 63 received Temab-A plus bevacizumab and 20 received trifluridine–tipiracil plus bevacizumab. At the two Temab-A dose levels, objective responses were 19% and 30%, versus 0% in the control group; median PFS was 5.6 and 6.8 months versus 4.2 months. Median OS was 11.2 and 14.7 months versus 10.2 months. The population was unselected for MET expression, with a median three previous lines. Small groups, dose exploration and the early-phase design limit certainty; the abstract's favourable conclusion is not definitive proof of an OS advantage. [Primary randomized report](https://pubmed.ncbi.nlm.nih.gov/42926107/), [DOI](https://doi.org/10.1016/j.annonc.2026.10.105).

The earlier monotherapy study included 122 CRC patients and reported 15.6% ORR, median PFS 4.6 months and median response duration 5.9 months. Exploratory enrichment with strong MET IHC does not turn an uncalibrated MS signal into a validated selection threshold. The primary paper describes enrichment at at least 10% 3+ staining; prior liver staining in this case had no 3+ cells and was described as cytoplasmic, so it is not interchangeable. [Primary JCO study](https://ascopubs.org/doi/10.1200/JCO-25-01525).

Temab-A remains **investigational**. Its October FDA breakthrough designation is not approval. Phase III [NCT07525206](https://clinicaltrials.gov/study/NCT07525206) is recruiting (record updated 19 October), and [NCT05982873](https://clinicaltrials.gov/study/NCT05982873) remains an available expanded-access record (updated 6 February); a record does not establish current individual acceptance or supply. [Primary sponsor designation statement](https://news.abbvie.com/2026-10-07-AbbVies-Telisotuzumab-Adizutecan-Temab-A-Receives-Two-Breakthrough-Therapy-Designations-From-the-U-S-FDA-for-CRC-and-NSCLC?sf281905045=1).

**Case interpretation:** a new MET detection would add assay evidence, but neither an archival low signal nor non-detection should eliminate this investigational route. Conversely, high bulk MET would not establish amplification or justify a lung-cancer MET inhibitor in CRC. Current tumour membrane scoring and the precise trial criteria matter; bevacizumab eligibility is separate.

## CEACAM5 / CEA

Precemtabart tocentecan/M9140 remains an investigational CEA ADC. The May 2026 sponsor update reported **6/29 confirmed responses, 20.7%**, at its recommended development dose, with median PFS 6.9 months. This is a small early-phase cohort. It must not be pooled with the earlier 41-patient abstract whose 11 responses included only five confirmed at its cutoff. [Sponsor update](https://www.emdserono.com/us-en/company/news/press-releases/phase-three-proceade-study-investigates-antibody-drug-conjugate-in-colorectal-cancer-05-21-2026.html).

The primary escalation publication demonstrates preclinical and human activity in irinotecan-refractory CRC, but not a validated continuous relationship between generic protein abundance and benefit. Its specific IHC assay and combined membrane/cytoplasm score are different from MS intensity and from serum CEA. [Primary phase-I paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC12532702/).

[PROCEADE-CRC-03, NCT07549412](https://clinicaltrials.gov/study/NCT07549412), remains recruiting with a public limit of no more than two prior metastatic systemic regimens. Current protocol review is required for prior anti-VEGF and other treatment requirements. Pfizer's [PF-08046050/SGN-CEACAM5C](https://www.pfizeroncologydevelopment.com/clinical_trial/NCT06131840/molecule/790) remains another early clinical route; no reliable human CRC response denominator was identified in this update.

**Case interpretation:** retain the archived liver **CEA H-score 300, 100% 3+** as the most direct prior tumour-distribution evidence. A lower quantitative value from a different tissue does not prove CEA loss. If a feasible trial requires confirmation, current-node staining tests retention. The three unique peptides in the earlier summary do not denote low membrane density. No new approved CEA-directed CRC indication was identified.

## TROP2 / TACSTD2

**Negative CRC evidence is decision-relevant.** TROPHIT1 treated 24 patients, with 20 evaluable under its protocol. Confirmed ORR was **5%**, median PFS **3.7 months**, and median OS **7.4 months**. TROP2 staining was present in 18/20 samples. Treatment-related grade 3/4 toxicity occurred in 70.8% of treated patients. The study failed its advancement criteria and did not proceed to the randomized part. The exploratory trend associated with staining included stable disease in its response grouping; it is not a validated predictive threshold. [2026 primary final-results abstract](https://www.annalsofoncology.org/article/S0923-7534%2826%2900312-1/fulltext).

The historical IMMU-132-01 CRC cohort also had limited activity: one response among 31 patients. [Primary study](https://pubmed.ncbi.nlm.nih.gov/33741442/), [manufacturer's CRC evidence summary](https://www.askgileadmedical.com/docs/trodelvy/trodelvy-use-in-patients-with-colorectal-cancer). These results do not prove every TROP2 ADC will fail: sacituzumab tirumotecan has a different payload/linker and is in the CRC-inclusive [MK-9999-02A study, NCT06428409](https://clinicaltrials.gov/study/NCT06428409), recruiting in the record updated 29 October 2026. No CRC efficacy estimate for that agent was verified.

**Case interpretation:** previously weak liver TROP2 IHC (H-score 20) remains more spatially informative than bulk primary-tissue signal. Newly detected TACSTD2 would support confirmation if a real trial becomes feasible; it would not justify off-label sacituzumab govitecan by itself. Neither Trodelvy nor Datroway has an FDA CRC indication identified in the reviewed current labels. [Trodelvy label](https://dailymed.nlm.nih.gov/dailymed/search.cfm?label=all&query=Sacituzumab+Govitecan), [2026 Datroway label](https://www.accessdata.fda.gov/drugsatfda_docs/label/2026/761394s003lbl.pdf).

## ERBB2 / HER2 and approved eligibility

There are genuine HER2-directed approved pathways, but their required biomarkers are stronger and more specific than ordinary protein detection:

- Tucatinib plus trastuzumab has an FDA CRC indication for **RAS-wild-type, HER2-positive** unresectable/metastatic disease after fluoropyrimidine, oxaliplatin and irinotecan. The approval's MOUNTAINEER population had 38% ORR; this is a biomarker-selected population, not an estimate for this case. [FDA CRC approval](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-grants-accelerated-approval-tucatinib-trastuzumab-colorectal-cancer).
- Trastuzumab deruxtecan has an FDA tumour-agnostic indication for previously treated **IHC3+** solid tumours without satisfactory alternatives. [FDA indication](https://www.fda.gov/drugs/resources-information-approved-drugs/fda-grants-accelerated-approval-fam-trastuzumab-deruxtecan-nxki-unresectable-or-metastatic-her2). DESTINY-CRC02's final analysis retained 37.8% confirmed ORR in the selected 5.4-mg/kg group, with meaningful ILD risk; this does not validate HER2-low/IHC0 CRC treatment. [Primary final analysis](https://www.annalsofoncology.org/article/S0923-7534%2825%2902231-8/fulltext).

**Case interpretation:** ERBB2 detection or a high rank does not override prior HER2 IHC0/no established amplification. If the new quantitative result is strongly discordant, verify protein mapping and specimen composition first, then use validated current tumour IHC with reflex ISH/copy-number assessment as appropriate. Do not transfer breast-cancer HER2-low indications to CRC or assume FDA approval guarantees UK funding.

## EGFR and EGFR/MET combinations

Panitumumab is an established CRC therapy selected in its usual setting by **RAS-wild-type molecular status**, not a high bulk EGFR intensity. [Current label](https://dailymed.nlm.nih.gov/dailymed/fda/fdaDrugXsl.cfm?setid=e0fa4bca-f245-4d92-ae29-b0c630a315c2). Following anti-EGFR exposure, acquired resistance is more decision-relevant than target abundance. In the prospective single-arm CHRONOS study, ctDNA screening excluded 16/52 patients with RAS/BRAF/EGFR resistance mutations; among 27 treated patients, eight responses included six confirmed and two unconfirmed. This supports molecularly informed rechallenge as a concept, not using protein expression to predict renewed sensitivity. [Primary CHRONOS report](https://www.nature.com/articles/s41591-022-01886-0).

Amivantamab remains investigational/off-label for CRC. The peer-reviewed OrigAMI-1 subgroup most analogous to prior anti-EGFR exposure reported **10/54 responses (19%)**, median PFS 4.6 months and response duration 6.1 months in left-sided disease. Cross-trial comparisons and exploratory interval/subtype analyses cannot establish superiority. [Primary OrigAMI-1 report](https://ascopubs.org/doi/10.1200/JCO-25-02187).

**Case interpretation:** measured EGFR supports presence of a familiar target, not a new option. A prior benefit from panitumumab and current molecular/imaging evidence matter more. Absence of MET from one archival proteome does not negate the dual-target clinical rationale, nor does EGFR/MET co-detection prove both are on the same malignant cell.

## FAP radioligands and the immune-combination question

FAP is expressed by activated fibroblasts in cancer **and** repair/fibrosis. A treated primary enriched for bowel wall/stroma can produce high FAP without demonstrating that current nodes are FAP-rich or that FAP causes immune resistance. For radioligand selection, programme-specific uptake, retention and absorbed dose are more informative than IHC alone. Early FAPI compounds can show rapid washout despite diagnostic uptake. [SNMMI/EANM guideline](https://pmc.ncbi.nlm.nih.gov/articles/PMC11705787/).

Current routes are investigational, and the records do not confirm an individual slot:

| Programme | Current primary evidence/access | Important selection distinction |
|---|---|---|
| Lu-177 NNS309, NCT06562192 | Recruiting; CRC in registry and sponsor page; European locations available | Own Ga-68 NNS309 PET. The prior trial-in-progress expansion plan omitted CRC, so confirm an accepting escalation/backfill cohort rather than assuming any listed site will admit CRC. |
| Lu-177 OncoFAP-23 ± L19-IL2, TheraTri, NCT06640413 | Registry updated 26 October: recruiting at Bergamo and Milan; no published human efficacy results found | Own OncoFAP PET and a measurable nonirradiated lesion; serious nonhealing ulcer and treatment/radionuclide washouts matter. Combination activation/slots unresolved. Uses **IL-2**, not IL-12/15; L19 targets ED-B fibronectin. |
| LY4337713, FiREBOLT, NCT07213791 | Registry updated 27 October: recruiting, CRC included; active sites mainly US, German/Dutch sites still not yet recruiting | Local FAP evidence and protocol imaging/RECIST criteria; prior CAR-T/TCR/adoptive T-cell therapy excluded. The October update explicitly clarifies that prior immunotherapy/VEGF treatment may be included but is not required for CRC. |
| 3BP-3940 individual-treatment experience | Published heterogeneous experience and a German specialist-enquiry route | Pooled tumour-type outcomes cannot establish CRC benefit; no verified individual acceptance, compound supply or funding. |

Sources: [NNS309 sponsor](https://www.novartis.com/clinicaltrials/study/nct06562192), [NNS309 registry](https://clinicaltrials.gov/study/NCT06562192), [TheraTri registry](https://clinicaltrials.gov/study/NCT06640413), [FiREBOLT sponsor](https://trials.lilly.com/en-US/trial/660077), [FiREBOLT registry](https://clinicaltrials.gov/study/NCT07213791), [3BP-3940 primary publication](https://pubmed.ncbi.nlm.nih.gov/42225357/). This update did not independently re-extract the complete 3BP-3940 article; retain the October 22 audit's denominator and mixed-treatment cautions rather than introduce a new efficacy claim.

FAP radiation plus checkpoint blockade has biological support, but the often-cited 2024 study tested the combination in engineered murine CRC models; its five-patient human component received radioligand, not a human checkpoint-combination trial. Some circulating T/NK/B-cell measures decreased after treatment. This is a reason to measure immune effects, not assume radiation universally improves them. [Primary study](https://www.nature.com/articles/s41392-024-01853-w).

The closest direct human caution is QuICC: CEA/MUC1 vaccine plus IL-15 agonist and PD-L1/TGF-β blockade produced 0/12 responses; adding targeted IL-12 produced 1/20. The durable responder's nodal RAS-wild-type phenotype is interesting but not predictive, and all enrolled patients were checkpoint-naive. This shared-antigen vaccine study does not establish the benefit or safety of adding personalised vaccination, FAP radiation and AC484 after BOT/BAL. [Primary QuICC publication](https://pubmed.ncbi.nlm.nih.gov/41520164/).

## PTPN1/PTPN2 / AC484

Quantitative PTPN1/PTPN2 expression is **not a phosphatase-activity assay**. There is no clinically validated abundance or IHC cutoff selecting AC484 responders. The inhibitor acts in both malignant and host immune compartments; low bulk expression is not a validated exclusion either. The 2023 mechanism study shows enhanced interferon responses and T/NK activity, including NK-dependent activity in experimental JAK1- or B2M-deficient settings. This does not mean it restores an absent HLA allele or missing mutant antigen for a specific conventional TCR. [Primary mechanism study](https://www.nature.com/articles/s41586-023-06575-7).

Additional 2026 CRC-specific preclinical evidence showed IFN-dependent CXCL9/10/11 induction and enhanced trafficking of Vδ1-enriched Delta One T cells in cell lines, primary samples and experimental models. It supports studying chemokine induction and immune recruitment, not claiming a clinical CRC response or an accessible validated AC484/cellular regimen. [Primary JITC report](https://pmc.ncbi.nlm.nih.gov/articles/PMC13223943/).

The September 2026 clinical abstract reported 18% ORR in 22 anti-PD-1-exposed clear-cell renal-cancer patients pooled across monotherapy and pembrolizumab combinations, with transient inflammatory adverse events. It supplies neither an MSS-CRC response rate nor a randomized combination comparison. [Primary abstract](https://academic.oup.com/oncolo/article/31/Supplement_3/oyag312.017/8773830).

[NCT04777994](https://clinicaltrials.gov/study/NCT04777994) remains recruiting in the June-updated record: broad dose escalation may admit CRC, but reviewed expansion cohorts are HNSCC, NSCLC, ccRCC and MSI-H tumours, not a dedicated MSS-CRC expansion. RECIST-measurable disease is required. [NCT06188975](https://clinicaltrials.gov/study/NCT06188975) remains an available expanded-access record but was last updated January 2024; current acceptance and supply require confirmation. No clinical protocol validating the complete FAP/checkpoint/IL-12/15/vaccine/AC484 combination was identified.

**Functional validation:** if viable contemporary material is suitable, distinguish tumour-only and immune-cell effects. A research assay can assess interferon responsiveness, surface HLA/B2M, chemokines and ultimately native autologous tumour recognition/killing, with appropriate controls. Increased pSTAT1 alone is insufficient. Cytokine-signalling amplification also creates overlapping inflammatory risks; proteomics cannot choose a safe combination schedule.

## HLA-A/B/C, B2M, TAP1/2 and antigen presentation

Detecting these proteins argues against their complete absence from the entire specimen; it does not establish a functional peptide-loading complex on malignant-cell membranes. Immune/stromal cells can supply the bulk signal. HLA sequence polymorphism and shared peptides also complicate allele-level assignment; pan-HLA abundance cannot prove that the vaccine-restricting allele is retained. Bulk proteomics is not immunopeptidomics.

Direct CRC organoid immunopeptidomics illustrates the gap: only three MS-detectable neoantigens were found across 612 nonsilent mutations in five organoids. IFNγ raised HLA expression and changed the repertoire but did not reveal additional mutant ligands in that experiment. MS sensitivity limits prevent treating 0.5% as a universal biological fraction. The result supports direct/functional testing rather than concluding that more HLA protein guarantees presentation of a particular vaccine peptide. [Primary CRC organoid study](https://pmc.ncbi.nlm.nih.gov/articles/PMC6859637/).

For a small current nodal FFPE block, the informative immune panel is **HLA-ABC and B2M scored specifically on tumour membranes**, plus a tumour mask and spatial CD8/FAP interpretation. Nodal lymphocytes provide strong background/internal controls and must not be counted as intratumoural effectors. IHC still cannot identify which mutant peptides are displayed. Allele-specific DNA/RNA/HLA assessment and native tumour recognition are complementary; source-protein presence is not a substitute.

## Priorities pending the quantitative results

- Strong quantitative CDH17/PTK7 signals would strengthen the case for current membrane IHC and trial screening, without ranking drug response probabilities.
- Strong FAP/LRRC15 signals would strengthen spatial stromal characterization and, for radioligands, ligand-specific imaging; they would not prove a causal stromal resistance mechanism.
- Newly visible MET or TACSTD2 could resolve an earlier detection-limit issue without erasing prior tissue-specific IHC.
- HER2 abundance alone would not establish an approved indication. EGFR abundance alone would not establish restored anti-EGFR sensitivity.
- HLA/B2M/TAP/PTPN1/PTPN2 measurements should guide falsifiable validation questions, not a claim that the proposed immune combination is now clinically selected.

The new literature strengthens CDH17 and MET investigational discussions independently of the quantitative result. It does not create a new approved treatment match from bulk protein abundance alone.

