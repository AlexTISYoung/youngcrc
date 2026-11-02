"""Validate delivered analysis invariants, provenance hashes and report links."""
from pathlib import Path
import json,hashlib,sys,urllib.parse
import pandas as pd
import numpy as np
import scipy,openpyxl,markdown,bs4
from bs4 import BeautifulSoup
R=Path(__file__).resolve().parents[1];A=R/'analysis'
checks=[]
def check(name,value):
 assert bool(value),name
 checks.append({'check':name,'passed':True})
b=pd.read_csv(A/'protein_groups.tsv',sep='\t').set_index('protein_group')
t=pd.read_csv(A/'therapeutic_targets.tsv',sep='\t').set_index('gene')
check('7755 unique protein groups;7706 patient measurements',b.index.is_unique and len(b)==7755 and b.detected.sum()==7706)
source=pd.read_csv(next((R/'raw/vendor_delivery').rglob('report.pg_matrix.tsv')),sep='\t').set_index('Protein.Group')
check('All native patient quantities preserved',np.allclose(b.intensity,source.iloc[:,0].reindex(b.index),equal_nan=True))
u=pd.read_csv(A/'unique_peptide_sequences.tsv',sep='\t')
n=u.groupby('Protein.Group')['Stripped.Sequence'].nunique().reindex(b.index).fillna(0)
check('Reconstructed unique sequence counts agree for every group',np.array_equal(n.values,b.n_unique_sequences.values))
check('All147 targets retain full group mapping where measured',len(t)==147 and t.loc[t.detected==True,'protein_group'].notna().all())
for g,wanted in {'CDH17':22,'PTK7':19,'FAP':14,'LRRC15':8,'ROR1':6,'CEACAM5':3,'PTPN1':11,'PTPN2':3}.items():
 check(g+' support and source quantity',int(t.at[g,'n_unique_sequences'])==wanted and t.at[g,'intensity']==b.at[t.at[g,'protein_group'],'intensity'])
check('Undetected MET/TROP2 preserved as missing',t.loc[['MET','TACSTD2'],'intensity'].isna().all())
check('Unfiltered reference coverage retained',t.at['FAP','Komor_CRC_measured_samples_all']==21 and t.at['LRRC15','HPA_colon_one_donor_measured_samples_all']==1)
fap=u[u['Protein.Group']==t.at['FAP','protein_group']]['summed_charge_and_modification_state_signal'].tolist()
check('FAP Top3 independently recomputed',np.isclose(sum(sorted(fap,reverse=True)[:3])/3,t.at['FAP','unique_top3_mean_signal']))
inclusive=pd.read_csv(A/'inclusive_two_peptide_gene_quantification.tsv',sep='\t')
check('Endogenous keratins retained in inclusive sensitivity',set(['KRT8','KRT18','KRT19','KRT20']).issubset(set(inclusive.gene)))
cp=pd.read_csv(A/'cptac_within_cohort_context.tsv',sep='\t').sort_values('wilcoxon_p')
check('Public CPTAC FDR bounded and monotone',len(cp)==5807 and cp.BH_FDR.between(0,1).all() and (np.diff(cp.BH_FDR)>=-1e-14).all())
ib=pd.read_csv(A/'public_ibaq_context.tsv',sep='\t')
check('Public iBAQ sample accounting and missing medians',len(ib)==89490 and (ib.n_detected+ib.n_missing==ib.n_sample_columns).all() and ib.loc[ib.n_detected==0,'median_positive_ppb_ibaq'].isna().all())
prov=json.loads((A/'control_provenance_check.json').read_text())
check('AO exactly corroborates HPA colon',prov['equal_positive_pairs']==4186 and prov['unequal_positive_pairs']==0)
pm=json.loads((A/'target_peptide_mapping_metadata.json').read_text())
check('151 key sequences independently mapped',pm['audited_peptide_rows']==151 and pm['exact_gene_unique_to_target']==150 and pm['il_equivalent_gene_unique_to_target']==148)
for inp in pm['inputs']:
 name=Path(inp['path']).name
 candidates=list(R.rglob(name))
 check('Peptide audit input hash '+name,any(hashlib.sha256(f.read_bytes()).hexdigest()==inp['sha256'] for f in candidates))
manifest=json.loads((R/'download_manifest.json').read_text()); available=0;omitted=[]
for row in manifest['files']:
 f=R/row['local']
 if not row['included']:
  omitted.append(row['local']);continue
 check('Released source hash '+row['local'],f.is_file() and f.stat().st_size==row['bytes'] and hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256']);available+=1
REPORT=R.parents[2]/'reports/proteomics/quantitative-2026-10-29/index.html'
doc=BeautifulSoup(REPORT.read_text(),'html.parser')
ids=[x['id'] for x in doc.find_all(id=True)]
check('HTML IDs unique',len(ids)==len(set(ids)))
check('Report target table contains147rows',len(doc.select('#target-table tbody tr'))==147)
check('Three external scientific figures with accessible descriptions',len(doc.find_all('img'))==3 and all(x.get('src','').startswith('figures/') and (REPORT.parent/x['src']).is_file() and x.get('alt') for x in doc.find_all('img')))
missing=[];external_workspace=[];archive_original_fallbacks=[]
for a in doc.find_all('a',href=True):
 h=a['href'];url=urllib.parse.urlparse(h)
 if url.scheme in ['https','http','mailto']:continue
 if h.startswith('#'):
  if h[1:] not in ids:missing.append(h)
 elif url.path:
  p=((R.parents[2]/urllib.parse.unquote(url.path).lstrip('/')) if url.path.startswith('/') else (REPORT.parent/urllib.parse.unquote(url.path))).resolve()
  if p.name in ['source.zip','public_validation.json']:continue
  if not p.exists() and p.suffix=='.gz':
   original=p.with_suffix('')
   declared=next((x for x in manifest.get('compressed_direct_downloads',[]) if str(p.relative_to(R.parents[2]))==x['public_gzip']['path']),None) if str(p).startswith(str(R.parents[2])) else None
   if declared and original.is_file() and original.stat().st_size==declared['public_gzip']['decompressed_bytes'] and hashlib.sha256(original.read_bytes()).hexdigest()==declared['public_gzip']['decompressed_sha256']:
    archive_original_fallbacks.append(h);continue
  if not p.exists():
   if not str(p).startswith(str(R.parents[2])):external_workspace.append(h)
   else:missing.append(h)
check('All report-internal file and anchor links resolve',not missing)
check('No external executable scripts or remote images',not any(x.get('src') for x in doc.find_all('script')) and not any(x.get('src','').startswith('http') for x in doc.find_all('img')))
result={'date':'2026-10-29','passed':True,'checks':checks,'check_count':len(checks),'available_downloaded_files_verified':available,'originals_not_in_package':omitted,'external_workspace_links_not_present':external_workspace,'website_gzip_links_with_verified_source_archive_originals':archive_original_fallbacks,'versions':{'python':sys.version.split()[0],'pandas':pd.__version__,'numpy':np.__version__,'scipy':scipy.__version__,'openpyxl':openpyxl.__version__,'markdown':markdown.__version__,'beautifulsoup4':bs4.__version__},'report_html_static_validation':True,'scientific_figures_visually_inspected_in_original_analysis':True,'browser_local_preview':'Not repeated by portable-package validator; historical source validation retained separately','raw_spectra_reprocessed':False,'patient_differential_expression_tests':False}
(A/'public_validation.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['checks','originals_not_in_package']},indent=2))
