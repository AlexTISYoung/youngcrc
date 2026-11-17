"""Reconcile primary-report findings already public with the visible molecular summary."""
from pathlib import Path
import json, sys
if len(sys.argv)!=2: raise SystemExit('Usage: script.py OUTPUT_CHECKOUT')
ROOT=Path(sys.argv[1]).resolve()
TASK=ROOT/'receipts';TASK.mkdir(parents=True,exist_ok=True)
p=ROOT/'data/molecular/summary.json';d=json.loads(p.read_text())
guardant={'report_id':'RPT-GUARDANT360-LIQUID','url':'reports/guardant/portal_guardant_2025_12_24.pdf#page=2','pages':[2],'source_ids':['CL-SRC-242'],'collection_date':'2025-12-18'}
personalis={'report_id':'RPT-TEMPUS-PERSONALIS-AMENDED','url':'reports/tempus/portal_personalis_amended_2026_02_27.pdf#page=1','pages':[1,2],'source_ids':['CL-SRC-241'],'collection_date':'2025-12-18'}
hla=next(r for r in d['biomarker_rows'] if r['biomarker']=='HLA and antigen presentation')
hla['summary']=hla['summary'].replace('Predicted HLA-A','Guardant360 reported HLA-A')
if guardant not in hla['sources']:hla['sources'].append(guardant)
rows=[
 {'biomarker':'Pharmacogenomics · drug metabolism','summary':'Guardant360 reports UGT1A1 *1/*28 and CYP2D6 *1/*4, both intermediate-metabolizer genotypes (CYP2D6 activity score 1.0).','therapy_connection':'These are host drug-metabolism findings, not tumour-driver mutations. The report flags altered irinotecan metabolism with UGT1A1 *1/*28; this genotype does not determine an individual dose or prove the cause of toxicity. CYP2D6 effects are drug-specific.','sources':[guardant]},
 {'biomarker':'Pharmacogenomics · tested negative alleles','summary':'Guardant360 detected no abnormal variant among its reportable DPYD, TPMT and HLA-B*57:01 alleles.','therapy_connection':'This is a limited tested-allele result, not proof that every possible pharmacogenetic risk is absent. HLA-B*57:01 pharmacogenetic screening is separate from the full HLA class-I typing above.','sources':[guardant]},
 {'biomarker':'Tumour-informed ctDNA · Personalis','summary':'Tempus xM / Personalis detected 245 parts per million (PPM) in plasma collected 18 December 2025; the amended report corrected the collection date from 19 to 18 December.','therapy_connection':'A tumour-informed monitoring result, not a list of actionable variants. It concerns the same blood-draw date as the low-fraction Guardant profile but uses a different assay; the Guardant findings do not establish absence of tumour DNA. PPM and Signatera MTM/mL should not be interchanged.','sources':[personalis]}
]
for row in rows:
 old=next((r for r in d['biomarker_rows'] if r['biomarker']==row['biomarker']),None)
 if old:old.update(row)
 else:d['biomarker_rows'].append(row)
her2=next(r for r in d['expression_rows'] if r['target']=='HER2')
her2['protein_summary']='Valius liver block C4: IHC 0; H-score 0; no tumour or stromal staining, negative by colorectal HERACLES criteria. The UCLA add-on IHC report dated 29 April 2026 also records HER2 0 on previously collected surgical tissue.'
source={'report_id':'RPT-CLINICAL-HER2-PATHOLOGY','url':'reports/clinical/clinical_her2_pathology.pdf#page=1','pages':[1,2],'label':'UCLA HER2 add-on IHC, 29 April 2026'}
if source not in her2['sources']:her2['sources'].append(source)
for i,note in enumerate(d['provenance_limits']):
 if note.startswith('The recent node has documented'):
  d['provenance_limits'][i]='The 6 October 2026 node biopsy has histology: A1 shows extensive necrosis; A2 contains colorectal-type adenocarcinoma. This does not establish tumour fraction, post-thaw viable-cell recovery or a molecular profile for the current node. Nodal site linkage is patient-reported. The immunotherapy-resistance report records the source and limitations.'
d['updated']='2026-11-17';d['release']='1.72'
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
(TASK/'additional_biomarker_audit.json').write_text(json.dumps({'reviewed_on':'2026-11-17','status':'primary_report_checked','primary_pages_visually_checked':['Guardant360 page 2','Personalis amended page 1','UCLA HER2 add-on page 1','Valius CEA / cMET / HER2 / TROP2 one-page reports'],'findings_added':[r['biomarker'] for r in rows],'other_changes':['Attribute HLA class-I genotypes to Guardant clinical report','Add UCLA HER2 0 corroboration without asserting an independent specimen','Replace stale unavailable-node-histology statement with previously reviewed and publication-approved annotations'],'unchanged':['Four Valius liver IHC scores and scoring compartments already accurate','Guardant plasma VUS, tumour-fraction, MSI and TMB already represented'],'no_treatment_change':True},indent=2)+'\n')
print('Additional primary-report biomarkers reconciled.')
