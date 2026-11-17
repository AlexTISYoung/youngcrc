#!/usr/bin/env python3
"""Recompute downstream protein summaries from full-common-set rank vectors.
Stored vectors were constructed against entireeligible reference universes. This
rerun does not reconstruct those upstreamranks, spectra, or reference matrices.
"""
from pathlib import Path
import argparse,json,gzip
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--output-dir',type=Path,default=ROOT/'recomputed/proteomics');args=parser.parse_args();OUT=args.output_dir;OUT.mkdir(parents=True,exist_ok=True)
cfg=json.loads((ROOT/'definitions/proteomics_computation.json').read_text())
panels=json.loads((ROOT/'definitions/protein_module_definitions.json').read_text())['modules'];targets=cfg['targets'];ALIASES=cfg['aliases']
def load(name,index_col=None):return pd.read_csv(ROOT/'inputs/proteomics'/name,index_col=index_col,float_precision='round_trip')
def output(df,name,index=False):
    raw=df.to_csv(index=index).encode();(OUT/(name+'.gz')).write_bytes(gzip.compress(raw,9,mtime=0))
vectors=load('full_common_set_rank_vectors.csv.gz');b=load('selected_patient_groups.csv.gz')
refs={k:load(f'ratio_reference_{k}.csv.gz',0) for k in cfg['reference_columns']}
strict=pd.DataFrame(index=cfg['strict_genes']);inclusive=load('ratio_patient_intensity.csv.gz',0)
comparisons=[];sensitivities=[]
reference_coverage=load('reference_coverage.csv.gz').to_dict('records')
for rn in refs:
    for un in ['strict','inclusive_flagged_endogenous']:
        for threshold in [.5,.8,1.]:
            v=vectors[(vectors.reference==rn)&(vectors.universe==un)&(vectors.minimum_reference_detection_fraction==threshold)]
            br=v[v.eligible].set_index('gene')
            anchors=int(v.anchor_genes.iloc[0])
            if un=='strict' and threshold==.8:
                for _,r in v.iterrows():
                    reason='eligible common-set rank' if r.eligible else ('not in strict patient support set' if not r.in_patient_support_set else 'reference coverage below80% or gene unmapped')
                    row={'gene':r.gene,'reference':rn,'status':reason,'anchors':anchors,'total_reference_columns':int(r.total_reference_columns)}
                    if r.eligible:
                        row.update({k:r[k] for k in ['query_rank_pct','reference_median_rank_pct','rank_shift_points','reference_q25_rank_pct','reference_q75_rank_pct','n_reference_detected']})
                    comparisons.append(row)
            for p in panels:
                z=br.reindex(p['genes']).dropna(subset=['rank_shift_points'])
                sensitivities.append({'panel':p['id'],'reference':rn,'universe':un,'minimum_reference_detection_fraction':threshold,'anchor_genes':anchors,'panel_genes':len(p['genes']),'eligible_panel_genes':len(z),'genes_used':';'.join(z.index),'median_rank_shift_points':z.rank_shift_points.median(),'q25_rank_shift':z.rank_shift_points.quantile(.25),'q75_rank_shift':z.rank_shift_points.quantile(.75),'positive_rank_shifts':int((z.rank_shift_points>0).sum()),'large_positive_shifts_gt25points':int((z.rank_shift_points>25).sum()),'large_negative_shifts_ltminus25points':int((z.rank_shift_points< -25).sum())})
output(pd.DataFrame(comparisons),'gene_reference_comparisons.csv')
output(pd.DataFrame(reference_coverage),'reference_gene_coverage.csv')
output(pd.DataFrame(sensitivities),'pathway_rank_sensitivity.csv')
main_summary = pd.DataFrame(sensitivities).query("universe=='strict' and minimum_reference_detection_fraction==0.8").copy()
status_by_gene = {}
target_rows = []
for g in targets:
    hits = b[b.gene.fillna('').apply(lambda v: g in v.split(';')) | b.fasta_genes.fillna('').apply(lambda v: g in v.split(';') or any((a in v.split(';') for a, c in ALIASES.items() if c == g)))]
    if hits.empty:
        status = 'not assigned in delivered protein-group table; biological absence not established'
        target_rows.append({'query_gene': g, 'status': status, 'panels': ';'.join((p['id'] for p in panels if g in p['genes']))})
    else:
        statuses = []
        for _, r in hits.iterrows():
            status = 'group listed but no positive patient quantity' if not r.detected else 'detected ambiguous multi-gene assignment' if r.multi_gene else 'detected with shared sequences only' if r.n_unique_sequences == 0 else 'detected single source-labelled sequence' if r.n_unique_sequences == 1 else 'detected >=2 sequences; contaminant-library flag retained' if r.contaminant_library_flag else 'detected higher-support single-gene group'
            statuses.append(status)
            row = {'query_gene': g, 'status': status, 'panels': ';'.join((p['id'] for p in panels if g in p['genes'])), **r.to_dict()}
            for rn in refs:
                z = next((x for x in comparisons if x['gene'] == g and x['reference'] == rn))
                row.update({rn + '_' + key: val for key, val in z.items() if key not in {'gene', 'reference'}})
            target_rows.append(row)
        status = '; '.join(sorted(set(statuses)))
    status_by_gene[g] = status
output(pd.DataFrame(target_rows), 'stromal_gene_by_assay_protein.csv')
for i, row in main_summary.iterrows():
    p = next((x for x in panels if x['id'] == row.panel))
    sub = b[b.gene.isin(p['genes'])]
    panel_rows = [r for r in target_rows if r['query_gene'] in p['genes']]
    main_summary.at[i, 'patient_genes_any_assigned'] = len({r['query_gene'] for r in panel_rows if not r['status'].startswith('not assigned')})
    main_summary.at[i, 'patient_genes_positive_quantity'] = len({r['query_gene'] for r in panel_rows if r.get('detected', False)})
    main_summary.at[i, 'patient_genes_higher_support'] = len(set(p['genes']) & set(strict.index))
    main_summary.at[i, 'patient_genes_ambiguous_assignment'] = len({r['query_gene'] for r in panel_rows if r.get('multi_gene', False)})
    main_summary.at[i, 'patient_genes_only_single_source_peptide'] = len({r['query_gene'] for r in panel_rows if r.get('n_unique_sequences') == 1})
    main_summary.at[i, 'patient_unassigned_genes'] = ';'.join((g for g in p['genes'] if status_by_gene[g].startswith('not assigned')))
output(main_summary, 'pathway_summary.csv')
denominators = {'broad_ECM': ['DCN', 'LUM', 'COL1A1', 'COL1A2', 'COL3A1', 'FN1', 'POSTN'], 'epithelial': ['EPCAM', 'CDH1', 'KRT8', 'KRT18', 'KRT19', 'KRT20', 'VIL1', 'LGALS4'], 'smooth_muscle': ['DES', 'CNN1', 'MYH11', 'TAGLN']}
ratio_targets = 'CTHRC1 FAP LRRC15 THBS2 SULF1 AEBP1 COL11A1 ITGA11 TGFB1 LTBP1 LTBP4 LRRC32 ITGAV ITGA5 ITGB1 DDR1 DDR2 LOX LOXL1 PLOD2 P4HA1 PTK2 YAP1 CCN1 CCN2 CXCL12 CD44 SPP1 LAIR1 ENTPD1 NT5E ENPP1'.split()
ratio_rows = []
for rn, ref in refs.items():
    for pn, members in denominators.items():
        markers = [g for g in members if g in inclusive.index and g in ref.index and (ref.loc[g].notna().mean() >= 0.8)]
        if len(markers) < 3:
            continue
        qm = np.log2(inclusive.loc[markers, 'intensity']).mean()
        rm = np.log2(ref.loc[markers]).mean(axis=0).where(ref.loc[markers].notna().all(axis=0))
        for g in ratio_targets:
            if g not in inclusive.index or g not in ref.index or g in markers:
                continue
            rr = (np.log2(ref.loc[g]) - rm).dropna()
            if len(rr) < 2:
                continue
            qr = float(np.log2(inclusive.loc[g, 'intensity']) - qm)
            ratio_rows.append({'gene': g, 'reference': rn, 'denominator': pn, 'denominator_genes': ';'.join(markers), 'n_complete_reference_columns': len(rr), 'query_log2_target_to_marker_geomean': qr, 'reference_median_log2_ratio': rr.median(), 'query_minus_reference_log2_ratio': qr - rr.median(), 'fraction_reference_ratios_below_query': (rr < qr).mean()})
output(pd.DataFrame(ratio_rows), 'target_to_composition_marker_sensitivity.csv')
print('Recomputed protein modules and composition-ratio sensitivities.')

g=pd.read_csv(OUT/'stromal_gene_by_assay_protein.csv.gz')
key='CTHRC1 FAP LRRC15 THBS2 SULF1 COL10A1 COL11A1 ITGA11 AEBP1 TGFB1 TGFB3 TGFBR2 LTBP1 LTBP4 LRRC32 ITGAV ITGA5 ITGB1 DDR1 DDR2 LOX LOXL1 LOXL2 LOXL3 LOXL4 PLOD2 P4HA1 PTK2 YAP1 CCN1 CCN2 CXCL12 SPP1 LAIR1 LAIR2 PECAM1 VWF PLVAP CD8A CD8B PRF1 NOX4'.split()
output(g[g.query_gene.isin(key)][['query_gene','protein_group','status','intensity','n_unique_sequences','Astral_CRC_rank_shift_points']],'key_protein_evidence.csv')
