from pathlib import Path
import json
import re
import pandas as pd
import numpy as np

base = Path(__file__).resolve().parents[1]
source = base / 'reference' / 'robles_crc' / 'Solid_samples'
out = base / 'analysis'
out.mkdir(parents=True, exist_ok=True)
data = pd.read_csv(source / 'proteinGroups_ppb_final.txt', sep='\t')
meta = pd.read_csv(source / 'Sample_classification.txt', sep='\t')
assert not data['Gene ID'].duplicated().any()
assert not meta['Name'].duplicated().any()
assert set(meta['Name']).issubset(data.columns)
extra = set(data.columns[2:]) - set(meta['Name'])
assert extra == {'ppb.iBAQ.peptides'}, extra

def donor_id(row):
    if row['Dataset'] != 'CPTAC':
        return pd.NA
    assert re.fullmatch(r'ppb\.iBAQ\.TCGA\.[A-Z0-9]{2}\.[A-Z0-9]{4}', row['Name']), row['Name']
    return row['Name'].removeprefix('ppb.iBAQ.').replace('.', '-')

meta['donor_id'] = meta.apply(donor_id, axis=1)
meta['donor_id_basis'] = np.where(meta['Dataset'].eq('CPTAC'), 'TCGA participant barcode in source sample name', 'Unavailable in combined classification file')
meta['measured_gene_count'] = meta['Name'].map(data[meta['Name']].notna().sum())
meta = meta.rename(columns={'Name': 'sample_id', 'Dataset': 'dataset', 'Tissue': 'tissue_class', 'Organ': 'organ'})
meta.to_csv(out / 'public_ibaq_sample_metadata.tsv', sep='\t', index=False, na_rep='')

blocks = []
for (dataset, tissue), members in meta.groupby(['dataset', 'tissue_class'], sort=True):
    q = data[members['sample_id'].tolist()].apply(pd.to_numeric, errors='raise')
    assert not (q < 0).any().any()
    assert not (q == 0).any().any()
    detected = q.gt(0)
    positive = q.where(detected)
    n = len(members)
    q25 = positive.quantile(0.25, axis=1, interpolation='linear')
    q75 = positive.quantile(0.75, axis=1, interpolation='linear')
    b = pd.DataFrame({
        'gene_id': data['Gene ID'],
        'gene_symbol': data['Gene.Symbol'],
        'dataset': dataset,
        'tissue_class': tissue,
        'organs_in_group': '|'.join(sorted(members['organ'].unique())),
        'quantity_unit': 'ppb.iBAQ',
        'n_sample_columns': n,
        'n_unique_donors_verified_from_barcode': members['donor_id'].nunique() if members['donor_id'].notna().all() else pd.NA,
        'n_detected': detected.sum(axis=1),
        'n_missing': positive.isna().sum(axis=1),
        'detection_fraction': detected.sum(axis=1) / n,
        'median_positive_ppb_ibaq': positive.median(axis=1),
        'q25_positive_ppb_ibaq': q25,
        'q75_positive_ppb_ibaq': q75,
        'iqr_positive_ppb_ibaq': q75 - q25,
    })
    assert (b['n_detected'] + b['n_missing']).eq(n).all()
    assert b['detection_fraction'].between(0, 1).all()
    assert b.loc[b['n_detected'].eq(0), 'median_positive_ppb_ibaq'].isna().all()
    blocks.append(b)
result = pd.concat(blocks, ignore_index=True)
result['n_unique_donors_verified_from_barcode'] = result['n_unique_donors_verified_from_barcode'].astype('Int64')
assert len(result) == 8949 * 10
assert not result.duplicated(['gene_id', 'dataset', 'tissue_class']).any()
result.to_csv(out / 'public_ibaq_context.tsv', sep='\t', index=False, na_rep='', float_format='%.10g')
validation = {
    'source_gene_rows': len(data),
    'annotated_samples': len(meta),
    'groups': meta.groupby(['dataset', 'tissue_class']).size().to_dict(),
    'output_rows': len(result),
    'all_missing_gene_group_rows': int(result['n_detected'].eq(0).sum()),
    'one_detection_gene_group_rows': int(result['n_detected'].eq(1).sum()),
    'excluded_non_sample_columns': sorted(extra),
    'CPTAC_distinct_donor_barcodes': int(meta.loc[meta['dataset'].eq('CPTAC'), 'donor_id'].nunique()),
    'cross_platform_patient_comparison_performed': False,
}
validation['groups'] = [{'dataset': k[0], 'tissue_class': k[1], 'n_samples': int(v)} for k, v in validation['groups'].items()]
(out / 'public_ibaq_context_validation.json').write_text(json.dumps(validation, indent=2) + '\n')
print(json.dumps(validation, indent=2))
