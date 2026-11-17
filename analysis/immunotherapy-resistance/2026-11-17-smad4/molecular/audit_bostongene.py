"""Reproduce a bounded primary-PDF transcription audit; no inference from omics.

Pass the public BostonGene portrait PDF and an optional website summary JSON.
Scientific fields were manually read from full-page source images, not OCR-only.
"""
from pathlib import Path
import argparse, hashlib, json

p=argparse.ArgumentParser()
p.add_argument('--pdf', type=Path, required=True)
p.add_argument('--summary', type=Path)
p.add_argument('--output', type=Path, required=True)
a=p.parse_args()
sha=hashlib.sha256(a.pdf.read_bytes()).hexdigest()
assert sha=='a996b19275f3d264d4c2de9fc8c5f026daad5cc7e9bdec75889dcb45ed753a69'
call={'provider':'BostonGene','provider_id':'valius','report_id':'RPT-VALIUS-PORTRAIT','source_ids':['M-SOURCE-011'],'sample_id':'M-SAMPLE-002','assay_id':'M-ASSAY-019','specimen':'Rectal resection, block B4','collection_date':'2024-10-22','report_date':'2026-09-30','pdf_page':19,'gene':'HGF','variant':'p.C149F','dna_annotation':'ENST00000222390.11:c.446G>T','protein_as_printed':'p.(Cys149Phe)','genomic_as_printed':'chr7:81757225C>A','reference_build':'GRCh38','classification':'Not assessed','vaf_percent':5.4,'source_url':'reports/valius/valius_portrait.pdf#page=19','limitation':'15% NGS tumour content; detection sensitivity limited. Not assessed is not a VUS or pathogenic call. Same allele as the separate Tempus VUS, whose VAF is 12.4%; differences are assay/specimen estimates, not demonstrated clone kinetics.'}
data={'reviewed_on':'2026-11-17','source_url':'https://youngcrc.com/reports/valius/valius_portrait.pdf','source_sha256':sha,'source_pages':25,'individually_viewed_pages':[1,2,3,6,8,15,19],'manual_primary_transcription':True,'variant_delta':{'target_existing_record':'CL-VAR-HGF-C149F','action':'Append a distinct BostonGene call; retain Tempus VUS classification separately','call':call},'other_findings':[
 {'pages':[1,8],'finding':'15% NGS tumour content; microdissection performed. MSI and copy-number alterations not reported because of low tumour content; ploidy unavailable.','website_status':'Core limitation already present; do not convert dashes into negative CNA calls.'},
 {'pages':[1,2],'finding':'TMB 0.42 mutations/Mb; negative oncogenic fusions involving NTRK1/2/3 and RET.','website_status':'TMB present; add BostonGene fusion result with low-content sensitivity limitation.'},
 {'pages':[2,6],'finding':'No pathogenic/likely pathogenic germline POLE/POLD1 finding; selected germline table reports no variants detected. Benign/likely benign/VUS are not reported. Germline CNAs are not reported.','website_status':'Add only as limited report-scope result, not exclusion of inherited susceptibility.'},
 {'pages':[2,7],'finding':'DPYD germline variants not detected; report states not a standalone pharmacogenetic test and cannot rule out DPD deficiency.','website_status':'May add alongside separate Tempus/Guardant/Caris tested-allele results without merging scopes.'},
 {'pages':[2,8,15],'finding':'CD274/PD-L1 RNA 1.8 TPM; selected colorectal percentile 71, pan-cancer percentile 47; source label MED.','website_status':'Medium RNA context already present; numeric contextual values may be added. Not an IHC TPS/CPS or predictive checkpoint biomarker.'},
 {'pages':[2],'finding':'Table shows Proficient under BostonGene IHC, while footnote describes proficient MMR documented in a different sample.','website_status':'Source-specific ambiguity: preserve wording or seek clarification, do not label current-node IHC as newly assessed.'},
 {'pages':[19,22],'finding':'HGF C149F is the only named somatic alteration in the printed variants table. Methods specify GRCh38.','website_status':'Do not mistake no predictive biomarkers for no somatic alteration or zero mutations.'}
 ],'not_claimed':['Complete review of every RNA expression row','Current-metastasis genotype','Treatment-selection validity','New clinical variant classification']}
if a.summary:
 d=json.loads(a.summary.read_text()); rows=[r for group in d['variant_groups'] for r in group['records']]
 row=next(x for x in rows if x['id']=='CL-VAR-HGF-C149F')
 data['website_check']={'HGF_record_exists':True,'BostonGene_call_already_present':any(c.get('provider')=='BostonGene' for c in row['calls']),'existing_calls':[{k:c.get(k) for k in ['provider','classification','vaf_percent','pdf_page']} for c in row['calls']]}
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
print(json.dumps({'source_verified':True,'main_delta':'HGF C149F 5.4% Not assessed','output':str(a.output)},indent=2))
