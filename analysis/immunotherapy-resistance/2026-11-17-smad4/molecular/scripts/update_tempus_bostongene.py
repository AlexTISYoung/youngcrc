"""Add independently reviewed Tempus and BostonGene primary-report details."""
from pathlib import Path
import json, sys
if len(sys.argv)!=2: raise SystemExit('Usage: script.py OUTPUT_CHECKOUT')
ROOT=Path(sys.argv[1]).resolve()
TASK=ROOT/'receipts';TASK.mkdir(parents=True,exist_ok=True)
p=ROOT/'data/molecular/summary.json';d=json.loads(p.read_text())
def ts(pages):return {'report_id':'RPT-TEMPUS','url':'reports/tempus/tempus.pdf#page='+str(pages[0]),'pages':pages,'source_ids':['M-SOURCE-002'],'sample_id':'M-SAMPLE-002','assay_id':'M-ASSAY-003'}
def bs(pages):return {'report_id':'RPT-VALIUS-PORTRAIT','url':'reports/valius/valius_portrait.pdf#page='+str(pages[0]),'pages':pages,'source_ids':['M-SOURCE-011'],'sample_id':'M-SAMPLE-002','assay_id':'M-ASSAY-019','collection_date':'2024-10-22','report_date':'2026-09-30'}
def add_source(row,source):
 if source not in row['sources']:row['sources'].append(source)
def put(row):
 old=next((r for r in d['biomarker_rows'] if r['biomarker']==row['biomarker']),None)
 if old:old.update(row)
 else:d['biomarker_rows'].append(row)
burden=next(r for r in d['biomarker_rows'] if r['biomarker']=='Microsatellite status and TMB')
burden['summary']=burden['summary'].replace('TMB 4.2 mutations/Mb.','TMB 4.2 mutations/Mb (provider-reported 54th percentile).')
if 'expression percentile' not in burden['therapy_connection']:
 burden['therapy_connection']+=' The Tempus percentile describes its reported TMB comparison, not a colorectal gene-expression percentile or a TMB-high call.'
add_source(burden,ts([2]))
hla=next(r for r in d['biomarker_rows'] if r['biomarker']=='HLA and antigen presentation')
if 'Tempus class-I' not in hla['summary']:hla['summary']+=' Tempus class-I HLA predictions are also concordant.'
add_source(hla,ts([3]))
met=next(r for r in d['biomarker_rows'] if r['biomarker']=='Pharmacogenomics · drug metabolism')
if 'Tempus also' not in met['summary']:met['summary']+=' Tempus also reports UGT1A1 *1/*28, intermediate metabolizer.'
if 'insufficient evidence' not in met['therapy_connection']:met['therapy_connection']+=' The Tempus report states that evidence is insufficient to recommend dosing changes for this result.'
add_source(met,ts([14]))
negative=next(r for r in d['biomarker_rows'] if r['biomarker']=='Pharmacogenomics · tested negative alleles')
if 'Tempus detected' not in negative['summary']:
 negative['summary']+=' Tempus detected none of its five tested DPYD variants, with normal DPD activity expected for those tested alleles. BostonGene likewise reports no DPYD germline variants in its stated analysis.'
 negative['therapy_connection']+=' BostonGene explicitly says its result is not a standalone pharmacogenetic test and cannot exclude DPD deficiency.'
add_source(negative,ts([12]));add_source(negative,bs([2,7]))
put({'biomarker':'Tempus sequencing coverage and specimen content','summary':'Tempus reports 30% tumour after microdissection. EPHB2 and TGFBR1 are listed as low-DNA-coverage regions; the methods define low coverage as average coverage below 35× across a region.','therapy_connection':'Negative genotype interpretation is limited for those regions. This does not mean TGFBR1 RNA is low, establish loss of ALK5 target protein, or predict benefit from its inhibition. Tumour-content estimates differ across specimens and assays.','sources':[ts([2,3,4])]})
kin=next(r for r in d['biomarker_rows'] if r['biomarker']=='KRAS / NRAS / BRAF and kinase biomarkers')
if 'BostonGene reported' not in kin['summary']:kin['summary']+=' BostonGene reported no oncogenic NTRK1/2/3 or RET fusion, with low tumour content limiting sensitivity.'
add_source(kin,ts([9]));add_source(kin,bs([1,2]))
hgf=next(r for g in d['variant_groups'] for r in g['records'] if r['id']=='CL-VAR-HGF-C149F')
call={'provider':'BostonGene','provider_id':'valius','report_id':'RPT-VALIUS-PORTRAIT','source_ids':['M-SOURCE-011'],'sample_id':'M-SAMPLE-002','assay_id':'M-ASSAY-019','specimen':'Rectal resection, block B4','collection_date':'2024-10-22','report_date':'2026-09-30','pdf_page':19,'gene':'HGF','variant':'p.C149F','dna_annotation':'ENST00000222390.11:c.446G>T','protein_as_printed':'p.(Cys149Phe)','genomic_as_printed':'chr7:81757225C>A','reference_build':'GRCh38','classification':'Not assessed','vaf_percent':5.4,'source_url':'reports/valius/valius_portrait.pdf#page=19','limitation':'15% NGS tumour content; detection sensitivity limited. Not assessed is not a VUS or pathogenic call. The separate Tempus VUS has 12.4% VAF; different assay/sample estimates do not demonstrate clone kinetics.'}
hgf['calls']=[c for c in hgf['calls'] if c.get('provider')!='BostonGene']+[call]
line='BostonGene: HGF p.C149F, 5.4% VAF, classification Not assessed; report 30 September 2026. This is distinct from the Tempus VUS classification and 12.4% VAF.'
if line not in hgf['evidence_lines']:hgf['evidence_lines'].append(line)
hgf['note']='Tempus classified this allele as VUS; BostonGene listed it as Not assessed. Neither is upgraded here, and the differing VAFs do not establish changes in clone abundance.'
hgf['notes']=[hgf['note']];add_source(hgf,bs([19]))
put({'biomarker':'BostonGene PD-L1 RNA','summary':'CD274 (PD-L1) RNA: 1.8 TPM; 71st colorectal percentile and 47th pan-cancer percentile, labelled medium by the report.','therapy_connection':'This is bulk-RNA expression in the treated rectal resection, not PD-L1 IHC TPS/CPS, tumour-cell-specific expression or a validated checkpoint-response predictor.','sources':[bs([2,8,15])]})
put({'biomarker':'BostonGene selected germline findings','summary':'No pathogenic or likely pathogenic POLE/POLD1 finding and no variant listed in the selected germline results table.','therapy_connection':'The report omits benign, likely benign and uncertain variants and does not report germline copy-number alterations. This limited result does not exclude inherited susceptibility and is separate from the somatic HGF entry.','sources':[bs([2,6])]})
d['variant_review_scope']='Primary Caris tissue and Assure blood, Tempus, BostonGene, Guardant and Valius reports and appendices checked against displayed variants and biomarkers; SMAD4 provider call-file annotation and investigator evidence are separately attributed. No clinical reclassification is inferred.'
d['updated']='2026-11-17';d['release']='1.72'
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
(TASK/'tempus_bostongene_applied.json').write_text(json.dumps({'reviewed_on':'2026-11-17','source_reports':['RPT-TEMPUS','RPT-VALIUS-PORTRAIT'],'source_pages':{'Tempus':[2,3,4,9,12,14],'BostonGene':[1,2,6,7,8,15,19]},'added':'Provider TMB percentile, low DNA coverage/specimen content, PGx/HLA corroboration, distinct HGF call, CD274 RNA and limited germline/fusion findings.','no_MMR_ambiguity_claim_added':True,'clinical_classifications_not_upgraded':True,'no_therapeutic_rank_change':True},indent=2)+'\n')
print('Tempus and BostonGene primary-report details reconciled.')
