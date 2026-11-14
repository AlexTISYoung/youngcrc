#!/usr/bin/env python3
"""Check newly emphasized target peptides against the delivered frozen FASTA.
Database specificity only, not raw-spectrum/FDR validation or surface localisation.
"""
import csv,gzip,json,re,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'inputs/proteomics'
OUT=Path(__file__).resolve().parent
TARGETS=set('NT5E ENTPD1 ENPP1 CTHRC1 THBS2 TGFB1 SPP1 SIRPA CD47 STING1 TBK1 IRF3 HLA-A HLA-B HLA-C B2M TAP1 TAP2 PTPN1 PTPN2 STAT1'.split())
parser=argparse.ArgumentParser()
parser.add_argument('--targets',default='')
parser.add_argument('--out-stem',default='new_target_peptide_specificity')
args=parser.parse_args()
if args.targets: TARGETS=set(args.targets.split(','))
matrix=list(csv.DictReader((OUT/'immune_axes_proteomics.csv').open()))
groups={r['protein_group']:r['query_gene'] for r in matrix if r['query_gene'] in TARGETS and r['exact_single_gene_match']=='True'}
path=SOURCE/'report.pr_matrix.tsv.gz'
peptides={g:set() for g in groups}
with gzip.open(path,'rt') as f:
 for r in csv.DictReader(f,delimiter='\t'):
  if r['Protein.Group'] in groups and r['Proteotypic']=='1' and r['FZPR260000422-1A.raw'] and float(r['FZPR260000422-1A.raw'])>0:
   peptides[r['Protein.Group']].add(r['Stripped.Sequence'])
fasta=SOURCE/'homo_sapiens_uniprot_2025_06_11_Swissprot.fasta.txt.gz'
records=[]
with gzip.open(fasta,'rt') as f:
 header=None;seq=[]
 for line in f:
  line=line.strip()
  if line.startswith('>'):
   if header is not None: records.append((header,''.join(seq)))
   header=line;seq=[]
  else:seq.append(line)
 if header is not None:records.append((header,''.join(seq)))
records=[(h.split('|')[1],re.search(r'\bGN=(\S+)',h).group(1) if re.search(r'\bGN=(\S+)',h) else '',s,s.replace('I','L')) for h,s in records]
out=[]
for group,seqs in peptides.items():
 for p in sorted(seqs):
  matches=[(a,g) for a,g,s,t in records if p in s]
  il=[(a,g) for a,g,s,t in records if p.replace('I','L') in t]
  genes=sorted(set(g for a,g in matches));ilgenes=sorted(set(g for a,g in il))
  out.append({'target_gene':groups[group],'protein_group':group,'sequence':p,'exact_matching_accessions':';'.join(a for a,g in matches),'exact_matching_genes':';'.join(genes),'il_equivalent_matching_genes':';'.join(ilgenes),'exact_only_target_gene':genes==[groups[group]],'il_equivalent_only_target_gene':ilgenes==[groups[group]]})
with (OUT/(args.out_stem+'.csv')).open('w') as f:
 w=csv.DictWriter(f,list(out[0]));w.writeheader();w.writerows(out)
summary={g:{'sequences':sum(r['target_gene']==g for r in out),'exact_unique':sum(r['target_gene']==g and r['exact_only_target_gene'] for r in out),'il_equivalent_unique':sum(r['target_gene']==g and r['il_equivalent_only_target_gene'] for r in out)} for g in sorted(TARGETS)}
result={'date':'2026-11-14','fasta_sha256':hashlib.sha256(fasta.read_bytes()).hexdigest(),'database_records':len(records),'target_summaries':summary,'limitation':'Sequence matches only within supplied Swiss-Prot; does not establish raw-spectrum quality, FDR, variants/alleles, functional activity or surface localization.'}
(OUT/(args.out_stem+'.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
