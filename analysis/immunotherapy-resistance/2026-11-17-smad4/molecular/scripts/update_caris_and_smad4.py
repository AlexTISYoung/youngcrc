from pathlib import Path
import json, sys
if len(sys.argv)!=2: raise SystemExit('Usage: script.py OUTPUT_CHECKOUT')
ROOT=Path(sys.argv[1]).resolve()
TASK=ROOT/'receipts';TASK.mkdir(parents=True,exist_ok=True)
p=ROOT/'data/molecular/summary.json';d=json.loads(p.read_text())
PKG='data/research/immunotherapy-resistance/2026-11-17-smad4/'
def cs(pages):return {'report_id':'RPT-CARIS','url':'reports/caris/caris.pdf#page='+str(pages[0]),'pages':pages,'source_ids':['M-SOURCE-001'],'sample_id':'M-SAMPLE-001','assay_id':'M-ASSAY-001','collection_date':'2024-03-27'}
assure={'report_id':'RPT-CARIS-ASSURE','url':'reports/caris/portal_caris_assure_2026_02_06.pdf#page=2','pages':[1,2],'collection_date':'2026-01-27'}
record={
 'id':'CL-VAR-SMAD4-G359E','gene':'SMAD4','variant':'SMAD4 p.G359E','dna_annotation':'NM_005359.5:c.1076G>A','dna_change':'c.1076G>A','category':'vus','evidence_class':'provider_call_file_annotation_and_investigator_functional_evidence',
 'calls':[{'provider_id':'caris','provider':'Caris — original variant call file','report_id':None,'source_url':PKG+'smad4/provider_annotation.json','sample_id':'M-SAMPLE-001','assay_id':'M-ASSAY-001','specimen':'Initial rectal primary biopsy','collection_date':'2024-03-27','classification':'VUS (CI field in provider VCF; not listed in printed clinical variant tables)','vaf_percent':None,'reference_support_reads':1275,'alternate_support_reads':477,'allele_support_total':1752}],
 'evidence_lines':[
  'G359E means glycine is replaced by glutamate at SMAD4 protein position 359. The original Caris biopsy variant call file annotates CI=VUS (variant of uncertain significance); it is not listed in the printed Caris clinical variant tables.',
  'The retained DNA call has 477 alternate reads out of 1,752 supporting reads (27.2%, calculated). This is a research read fraction, not a clinical-report VAF or tumour fraction.',
  'Monash investigators report a strongly damaging result in a SMAD4-dependent TGF-beta reporter screen and functional evidence supporting PS3, while retaining an overall VUS assessment (17 November 2026, unpublished personal communication).'
 ],
 'note':'The clinical Caris report labels SMAD4 copy number indeterminate (page 20). Neither the read fraction nor the functional screen establishes loss of both gene copies or retention in the current node. PS3 is functional classification evidence, not proof of treatment sensitivity.',
 'notes':['Provider VCF annotation and investigator interpretation are distinct from a printed clinical-report classification.','Current-node genotype and tumour dependence remain unestablished.'],
 'sources':[{'label':'Caris VCF annotation: reviewed derived record','url':PKG+'smad4/provider_annotation.json','sample_id':'M-SAMPLE-001','collection_date':'2024-03-27'},cs([20]),{'label':'Monash functional result: attributed summary and limitations','url':PKG+'smad4/functional_assessment.json'}],
 'therapy_connection':'Supports impaired canonical SMAD4 signalling in the tested model. It strengthens one biological premise for investigating TGF-beta blockade, including vactosertib, but does not establish ERK activation or predict benefit. The mutation is also a nominated vaccine target; functional impairment does not demonstrate antigen presentation or vaccine efficacy.',
 'therapy_links':[{'label':'Immunotherapy-resistance report','url':'reports/research/immunotherapy_resistance_report_2026-11-17_smad4.pdf#page=13'}],
 'research_variant_id':'M-VARIANT-014','support_read_ids':[]
}
variants=json.loads((ROOT/'data/molecular/variants.json').read_text())['records']
actual=next(r for r in variants if r['gene_label']=='SMAD4_G359E');record['research_variant_id']=actual['variant_id']
group=next(g for g in d['variant_groups'] if g['id']=='vus')
existing=next((r for r in group['records'] if r['gene']=='SMAD4'),None)
if existing:existing.update(record)
else:group['records'].insert(0,record)
group['note']='VUS means variant of uncertain significance. Provider-specific clinical calls are shown with their specimen and source. SMAD4 G359E is a separate provider call-file annotation with investigator functional evidence; it was omitted from the printed clinical variant tables. A damaging assay result is not itself a treatment-response biomarker.'
d['variant_count_note']='Each alteration appears once. SOX9 and SMARCA4 retain their differing Caris/Tempus classifications. SMAD4 is explicitly identified as a call-file annotation plus research functional evidence; it is not presented as a new clinical diagnosis.'
d['variant_review_scope']='Primary Caris, Tempus and Guardant clinical reports and report appendices checked against displayed variants and biomarkers; SMAD4 vendor call-file annotation and investigator evidence are separately attributed. No clinical reclassification is inferred.'
overview={'title':'SMAD4 G359E · VUS with functional evidence','text':'The Caris variant file labels G359E VUS. Monash reports impaired SMAD4-dependent signalling but retains overall VUS; the clinical report’s SMAD4 copy number is indeterminate.'}
if not any('SMAD4' in x['title'] for x in d['overview']):d['overview'].append(overview)
rows=[
 {'biomarker':'SMAD4 / SMAD2 copy number','summary':'Caris lists SMAD4 and SMAD2 copy-number results as indeterminate in the March 2024 biopsy (appendix, page 20).','therapy_connection':'This does not establish deletion, amplification, loss of the remaining SMAD4 allele or complete loss of either gene. It limits interpretation of the G359E alteration and does not predict response to TGF-beta inhibitors.','sources':[cs([20])]},
 {'biomarker':'Other uncertain copy-number results','summary':'Caris lists BCL2, SETBP1 and ZNF521 copy number as indeterminate. AURKA and GNAS are called intermediate on page 4 but indeterminate in the appendix on page 20.','therapy_connection':'The source wording differs between tables; no numerical copy number or definitive amplification is supplied. These results should not be converted into positive or negative copy-number calls.','sources':[cs([4,20])]},
 {'biomarker':'Genomic loss of heterozygosity (LOH)','summary':'Caris: low genomic LOH, 5% of tested segments (assay high threshold: at least 16%).','therapy_connection':'A genome-wide summary, separate from HLA-A LOH and locus-specific SMAD4 status. This result does not establish homologous-recombination deficiency or a PARP-inhibitor response.','sources':[cs([2,16])]},
 {'biomarker':'Consensus molecular subtype','summary':'Caris classifies the historical primary-biopsy RNA as CMS2.','therapy_connection':'A bulk-RNA subtype for that specimen, not a current-metastasis diagnosis or a validated treatment selector. The report cites guidance that does not recommend CMS classification for routine clinical practice.','sources':[cs([15])]},
 {'biomarker':'Indeterminate DNA coverage','summary':'Caris reports insufficient coverage of some or all exons for ATP6AP2, COL2A1, DACH1, MDH2, PLCB4, PRDM6, PRKD1, RASA1, RXRA and SMARCA2.','therapy_connection':'These are indeterminate results; those genes should not be described as mutation-negative on this assay.','sources':[cs([3,19])]},
 {'biomarker':'Incidental inherited / blood-cell findings','summary':'Caris Assure reports no incidental pathogenic or likely pathogenic germline variants or clonal-haematopoiesis findings in its stated report scope.','therapy_connection':'This is not a comprehensive negative germline test or evidence excluding every blood-cell clone. It is distinct from the tumour-derived findings and Guardant TRAF2 VUS.','sources':[assure]}
]
for row in rows:
 old=next((r for r in d['biomarker_rows'] if r['biomarker']==row['biomarker']),None)
 if old:old.update(row)
 else:d['biomarker_rows'].append(row)
negative=next(r for r in d['biomarker_rows'] if r['biomarker']=='KRAS / NRAS / BRAF and kinase biomarkers')
negative['summary']=negative['summary'].replace('KRAS, NRAS and BRAF mutations not detected','KRAS, NRAS, BRAF, EGFR, NF1, PIK3CA and POLE mutations not detected')
hla=next(r for r in d['biomarker_rows'] if r['biomarker']=='HLA and antigen presentation')
if 'buffy-coat' not in hla['summary']:
 hla['summary']+=' Caris tissue and Assure buffy-coat predictions are concordant with these alleles; Caris recommends confirmatory HLA typing.'
 hla['sources'].append(assure)
pgx=next(r for r in d['biomarker_rows'] if r['biomarker']=='Pharmacogenomics · tested negative alleles')
pgx['summary']+=' Caris Assure also reports DPYD activity score 2.0, normal metabolizer, with no variants detected.'
pgx['sources'].append(assure)
d['updated']='2026-11-17';d['release']='1.72'
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
(TASK/'smad4_and_caris_applied.json').write_text(json.dumps({'record':record,'added_biomarkers':[r['biomarker'] for r in rows],'clinical_classification_not_upgraded':True,'therapeutic_rankings_unchanged':True},indent=2,ensure_ascii=False)+'\n')
print('SMAD4 annotation and primary Caris report gaps reconciled.')
