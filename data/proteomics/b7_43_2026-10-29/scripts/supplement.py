"""Sensitivity analyses and database joins; descriptive, no patient significance tests."""
from pathlib import Path
import json,re,hashlib
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
R=Path(__file__).resolve().parents[1];O=R/'analysis';S=R/'raw/shared/analysis'
b=pd.read_csv(O/'protein_groups.tsv',sep='\t')
strict=pd.read_csv(O/'high_support_gene_quantification.tsv',sep='\t',index_col=0)
# All endogenous human proteins with two unique sequences: library membership is
# retained as a flag. This sensitivity universe does not certify contaminants.
inclusive=b[b.detected&~b.multi_gene&(b.n_unique_sequences>=2)].sort_values('intensity',ascending=False).drop_duplicates('gene').set_index('gene')
inclusive.to_csv(O/'inclusive_two_peptide_gene_quantification.tsv',sep='\t')
ast=pd.read_csv(O/'astral_reference_gene_matrix.tsv',sep='\t',index_col=0)
k=pd.read_csv(S/'refs/external/PXD012254/ProteinGroups_Normal_Adenoma_Cancer_Search.tsv',sep='\t')
k=k[k['PG.Genes'].notna()&~k['PG.Genes'].fillna('').str.contains(';')]
kw=k.pivot_table(index='PG.Genes',columns=['R.Condition','R.FileName'],values='PG.Quantity',aggfunc='max').replace(0,np.nan)
h=pd.read_csv(S/'refs/ms_tissue_sample_data.tsv',sep='\t');h=h[h.Tissue=='colon'].pivot_table(index='Gene name',columns='sample_name',values='Intensity',aggfunc='max').replace(0,np.nan)
refs={'Astral_CRC':ast,'Komor_CRC':kw['cancer'],'Komor_normal':kw['normal'],'HPA_colon_one_donor':h}
targets=pd.read_csv(O/'therapeutic_targets.tsv',sep='\t').gene.tolist()
results=[]
for un,d in [('strict',strict),('inclusive_contaminant_flags',inclusive)]:
 for rn,ref in refs.items():
  for threshold in [.5,.8,1.]:
   anchors=d.index.intersection(ref.index[ref.notna().mean(axis=1)>=threshold])
   qr=d.intensity.loc[anchors].rank(pct=True)*100;rr=ref.loc[anchors].rank(pct=True)*100
   for g in anchors.intersection(targets):
    results.append({'gene':g,'reference':rn,'universe':un,'minimum_detection_fraction':threshold,'anchors':len(anchors),'query_rank_pct':qr[g],'reference_median_rank_pct':rr.loc[g].median(),'rank_shift_points':qr[g]-rr.loc[g].median(),'reference_measured':int(rr.loc[g].notna().sum())})
pd.DataFrame(results).to_csv(O/'anchor_and_contaminant_sensitivity.tsv',sep='\t',index=False)
# Marker-ratio sensitivity cancels each sample's global scale, but not
# protein-dependent platform response or biological compartment differences.
panels={'ECM':['DCN','LUM','COL1A1','COL1A2','COL3A1','FN1','POSTN'],
 'epithelial':['EPCAM','CDH1','KRT8','KRT18','KRT19','KRT20','VIL1','LGALS4'],
 'smooth_muscle':['DES','CNN1','MYH11','TAGLN']}
ratios=[];panelrows=[]
for rn,ref in refs.items():
 for pn,pg in panels.items():
  marker=[g for g in pg if g in inclusive.index and g in ref.index and ref.loc[g].notna().mean()>=.8]
  if len(marker)<3:continue
  # Complete marker panels per reference sample; no variable denominator.
  rm=np.log2(ref.loc[marker]).mean(axis=0).where(ref.loc[marker].notna().all(axis=0))
  qm=np.log2(inclusive.loc[marker,'intensity']).mean()
  anchors=inclusive.index.intersection(ref.index[ref.notna().mean(axis=1)>=.8])
  rq=inclusive.intensity.loc[anchors].rank(pct=True)*100;rr=ref.loc[anchors].rank(pct=True)*100
  shifts=rq.reindex(marker)-rr.reindex(marker).median(axis=1)
  panelrows.append({'reference':rn,'panel':pn,'markers':';'.join(marker),'n_markers':len(marker),'median_marker_rank_shift_points':shifts.median()})
  for g in targets:
   if g not in inclusive.index or g not in ref.index or g in marker:continue
   r=(np.log2(ref.loc[g])-rm).dropna()
   if len(r)<2:continue
   q=float(np.log2(inclusive.at[g,'intensity'])-qm)
   ratios.append({'gene':g,'reference':rn,'marker_panel':pn,'markers':';'.join(marker),'n_reference_complete':len(r),'query_log2_target_to_marker_geomean':q,'reference_median_log2_target_to_marker_geomean':r.median(),'query_minus_reference_median_log2_ratio':q-r.median(),'fraction_reference_ratios_below_query':(r<q).mean(),'reference_log2_ratio_q25':r.quantile(.25),'reference_log2_ratio_q75':r.quantile(.75)})
pd.DataFrame(ratios).to_csv(O/'marker_ratio_sensitivity.tsv',sep='\t',index=False)
pd.DataFrame(panelrows).to_csv(O/'inclusive_marker_panels.tsv',sep='\t',index=False)
# Review aliases against frozen HPA accessions rather than silently rewriting.
hp=pd.read_csv(S/'refs/proteinatlas.tsv',sep='\t',usecols=['Gene','Gene synonym','Ensembl','Uniprot']).drop_duplicates('Ensembl').set_index('Ensembl')
al=inclusive[~inclusive.fasta_gene_agrees].copy()
al['hpa_synonyms']=al.ensembl.map(hp['Gene synonym'])
al['same_uniprot_in_hpa']=[any(a in str(hp.at[row.ensembl,'Uniprot']).replace(' ','').split(',') for a in str(row.protein_group).split(';')) if row.ensembl in hp.index else False for g,row in al.iterrows()]
al[['protein_group','fasta_genes','ensembl','hpa_synonyms','same_uniprot_in_hpa']].to_csv(O/'gene_symbol_audit.tsv',sep='\t')
# Join existing patient RNA evidence by full protein-group identifier. Keep all
# sample/assay labels; no between-specimen fold change or RNA/protein ratio.
prior=R/'raw/local_context/prior_RNA_annotation.csv'
old=pd.read_csv(prior)
cols=['protein_group']+[c for c in old if c.startswith(('caris_','tempus_','BostonGene_','liver_scRNA_'))]
joined=b.merge(old[cols],on='protein_group',how='left',validate='one_to_one')
joined.to_csv(O/'proteins_with_prior_RNA.tsv',sep='\t',index=False)
joined[joined.gene.isin(targets)].to_csv(O/'targets_with_prior_RNA.tsv',sep='\t',index=False)
rnaqc=[]
for col in [c for c in cols if c.endswith('gene_TPM') or 'log2_TPM' in c]:
 z=joined[joined.high_support][['intensity',col]].dropna();rnaqc.append({'assay':col,'genes':len(z),'spearman':spearmanr(z.intensity,z[col]).correlation})
pd.DataFrame(rnaqc).to_csv(O/'cross_assay_RNA_QC.tsv',sep='\t',index=False)
# Independently join the provided frozen database snapshots, without using the
# explorer's L1/L2/L3 ranking as evidence of indication or efficacy.
surfy=pd.read_csv(S/'refs/derived/surfy_all.tsv',sep='\t')
surface=set(surfy.loc[surfy['Surfaceome Label']=='surface','UniProt accession'])
cspa=pd.read_csv(S/'refs/derived/cspa_human.tsv',sep='\t')
cs=set(cspa.ID_link)
ot=json.loads((S/'refs/opentargets_26.09_snapshot.json').read_text());otmap={x['id']:x for x in ot['targets']}
rows=[];summary=[]
for g,row in inclusive.iterrows():
 target=otmap.get(row.ensembl,{})
 candidates=target.get('drugAndClinicalCandidates',{}).get('rows',[])
 for candidate in candidates:
  drug=candidate['drug'];ind=drug.get('indications',{}).get('rows',[])
  rows.append({'gene':g,'ensembl':row.ensembl,'drug_id':drug.get('id'),'drug':drug.get('name'),'drug_type':drug.get('drugType'),'target_max_stage':candidate.get('maxClinicalStage'),'drug_max_stage_any_indication':drug.get('maximumClinicalStage'),'indication_ids':';'.join(str(x.get('disease',{}).get('id')) for x in ind),'database_release':'26.09','not_a_patient_indication':True})
 summary.append({'gene':g,'protein_group':row.protein_group,'unique_sequences':row.n_unique_sequences,'signal_percentile':row.signal_percentile_all_detected,'contaminant_library_flag':row.contaminant_library_flag,'SURFY_surface':any(a in surface for a in row.protein_group.split(';')),'CSPA_detected_surface':any(a in cs for a in row.protein_group.split(';')),'OT_target_found':bool(target),'OT_candidate_rows':len(candidates),'OT_reported_candidate_count':target.get('drugAndClinicalCandidates',{}).get('count',0),'OT_drugs':' ; '.join(sorted({x['drug'].get('name','') for x in candidates}))})
pd.DataFrame(rows).to_csv(O/'drug_target_database_matches.tsv',sep='\t',index=False)
screen=pd.DataFrame(summary)
br=pd.read_csv(O/'reference_rank_comparisons.tsv',sep='\t');br=br[br.reference_cohort=='Astral_CRC'][['gene','rank_shift_points']]
screen=screen.merge(br,on='gene',how='left');screen.to_csv(O/'surface_and_drug_target_screen.tsv',sep='\t',index=False)
# Small scientific summary plot for contextual rank sensitivity.
rs=pd.DataFrame(results);show=['FAP','LRRC15','ROR1','CDH17','PTK7','EGFR','ERBB2','CD276','PTPN1','PTPN2']
fig,ax=plt.subplots(figsize=(9,5));colors={'strict':'#236678','inclusive_contaminant_flags':'#b96235'}
for i,g in enumerate(show):
 z=rs[(rs.gene==g)&(rs.reference=='Astral_CRC')]
 for un,offset in [('strict',-.1),('inclusive_contaminant_flags',.1)]:
  zz=z[z.universe==un]
  ax.plot([zz.rank_shift_points.min(),zz.rank_shift_points.max()],[i+offset]*2,color=colors[un],lw=3)
  ax.scatter(zz.rank_shift_points,[i+offset]*len(zz),s=16,color=colors[un])
ax.axvline(0,color='#666',lw=.8);ax.set_yticks(range(len(show)));ax.set_yticklabels(show);ax.invert_yaxis();ax.set(xlabel='Patient minus Astral CRC median signal rank (percentage points)',title='Rank sensitivity to 50%, 80%, 100% reference coverage\nBlue: strict set; orange: include flagged endogenous proteins')
fig.tight_layout();fig.savefig(R/'figures/anchor_sensitivity.png',dpi=160);plt.close(fig)
note={'inclusive_genes':len(inclusive),'strict_genes':len(strict),'flagged_endogenous_genes_restored':len(inclusive)-len(strict),'surfaceome_any':int((screen.SURFY_surface|screen.CSPA_detected_surface).sum()),'OT_targets_with_candidate_rows':int((screen.OT_candidate_rows>0).sum()),'OT_match_rows':len(rows),'rna_correlations':rnaqc,'fasta_symbol_mismatches':len(al),'all_mismatch_accessions_in_HPA':bool(al.same_uniprot_in_hpa.all())}
(O/'supplement_summary.json').write_text(json.dumps(note,indent=2));print(json.dumps(note,indent=2))
