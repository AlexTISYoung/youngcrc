#!/usr/bin/env python3
"""Independent mathematical/source audit. Uses generated data only."""
import datetime,hashlib,importlib.util,itertools,json,math,subprocess,sys,tempfile
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'analysis/pathway_response.py'
spec=importlib.util.spec_from_file_location('reviewed_statistics',SRC)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
initial_sha=sha(SRC)
checks={}

def independent_pairwise_statistic(x,y,strata):
    value=0.0
    for s in sorted(set(strata)):
        a=[x[i] for i in range(len(x)) if strata[i]==s and y[i]]
        b=[x[i] for i in range(len(x)) if strata[i]==s and not y[i]]
        value+=sum((float(aa>bb)+0.5*float(aa==bb)-0.5) for aa in a for bb in b)
    return value

def independent_exact(x,y,strata):
    observed=independent_pairwise_statistic(x,y,strata)
    groups=[]
    for s in sorted(set(strata)):
        indices=[i for i in range(len(x)) if strata[i]==s]
        k=sum(y[i] for i in indices)
        groups.append(list(itertools.combinations(indices,k)))
    total=extreme=0
    for parts in itertools.product(*groups):
        positive=set(itertools.chain.from_iterable(parts));yy=[i in positive for i in range(len(x))]
        extreme+=abs(independent_pairwise_statistic(x,yy,strata))>=abs(observed)-1e-12
        total+=1
    return extreme/total,total,observed

examples=[
 ([0,0,1,2,2,4],[1,0,1,0,0,0],['a']*6),
 ([0,0,1,2,4,4,6,7],[1,0,1,0,1,0,0,0],['a']*4+['b']*4),
 ([0,1,1,2,3,3,4,9],[1,0,1,0,0,0,1,1],['a']*4+['b']*2+['c']*2),
 ([1,1,1,1,1,1],[1,1,0,0,0,0],['a']*6),
]
for i,(x,y,s) in enumerate(examples):
    p,n,stat=independent_exact(x,y,s);r=mod.label_permutation(x,y,s)
    checks[f'pairwise_enumeration_case_{i}']=abs(r['p']-p)<1e-12 and r['n_allocations']==n and abs(r['statistic']-stat)<1e-12
    rr=mod.label_permutation(x,[not z for z in y],s)
    checks[f'complement_symmetry_case_{i}']=abs(rr['p']-p)<1e-12
checks['no_mixed_strata_not_estimable']=mod.label_permutation([1,2,3,4],[1,1,0,0],['a','a','b','b'])['p'] is None
checks['one_outcome_not_estimable']=mod.label_permutation([1,2,3],[1,1,1])['p'] is None
for k,expected in [(2,378),(5,98280)]:
    r=mod.label_permutation(np.arange(28),np.arange(28)>=28-k)
    checks[f'exact28_{k}_allocations']=r['n_allocations']==expected and r['draws']==expected and abs(r['p']-2/expected)<1e-12
    checks[f'exact28_{k}_monotonic_invariance']=mod.label_permutation(np.exp(np.arange(28)/10),np.arange(28)>=28-k)['p']==r['p']
effects=mod.effects([2,2,4,1,2,3],[1,1,1,0,0,0]);a=np.array([2,2,4]);b=np.array([1,2,3]);diff=np.subtract.outer(a,b)
checks['AUC_half_credit_ties']=abs(effects['auc_positive_higher']-(5+1)/9)<1e-12
checks['Cliff_delta_pairwise']=abs(effects['cliffs_delta']-np.mean(np.sign(diff)))<1e-12
checks['HL_median_pairwise']=effects['hodges_lehmann_difference']==float(np.median(diff))
checks['group_IQR_medians']=effects['median_positive']==2 and effects['median_negative']==2 and effects['q1_positive']==2 and effects['q3_positive']==3
p=np.array([.04,.001,.03,.2]);checks['BH_known_family']=np.allclose(mod.bh(p,4),[.05333333333333334,.004,.05333333333333334,.2])
checks['BH_missing_hypothesis_equals_padding_P1']=np.allclose(mod.bh([.01,.08,.4],4),mod.bh([.01,.08,.4,1],4)[:3])

sets=json.loads((ROOT/'methodology/locked_pathways.json').read_text());members=sorted({g for p in sets for g in p['genes']})
samples=[f'SYNTHETIC_{i:02d}' for i in range(28)]
genes=members+[f'SYNTH_G_{i:05d}' for i in range(5100)]
array=(np.arange(len(genes))[:,None]*17+np.arange(28)[None,:]*13)%101
matrix=pd.DataFrame(array.astype(float),index=genes,columns=samples)
matrix.loc['ACVR1']=0 # measured global zero: removed, with a distinct reason
matrix.loc['SMAD1']=.1 # retained primary; removed only by stricter >=1 rule
matrix.loc['APC',samples[0]]=0 # measured individual zero retained
matrix=matrix.drop(index='BMP2') # truly unmeasured, never imputed
matrix=matrix.rename(index={'CCN2':'CTGF'}) # documented alias handled
cb=['No']*28
for i in [0,4,8,12,20]:cb[i]='Yes'
orr=['Yes' if i in [0,4] else 'No' for i in range(28)]
metadata=pd.DataFrame({'sample_id':samples,'subject':[f'FAKE_SUBJECT_{i}' for i in range(28)],'timepoint':'screening','objective_response':orr,'clinical_benefit':cb,'dose_level':['200']*12+['300']*16,'liver_metastasis':['No' if i%3 else 'Yes' for i in range(28)]})
synthetic_result_counts=[]
with tempfile.TemporaryDirectory(prefix='independent-statistics-audit-',dir=ROOT/'validation') as d:
    d=Path(d);metadata.to_csv(d/'metadata.csv',index=False);(d/'universe.txt').write_text('\n'.join(genes)+'\n')
    for label in ['full_coverage','one_untestable_pathway']:
        fixture=matrix.copy()
        if label=='one_untestable_pathway':
            for g in ['MMP11','COL11A1','C1QTNF3']:fixture.loc[g]=0
        fixture.to_csv(d/'matrix.csv')
        out=d/label
        command=[sys.executable,str(SRC),'--matrix',str(d/'matrix.csv'),'--metadata',str(d/'metadata.csv'),'--universe',str(d/'universe.txt'),'--pathways',str(ROOT/'methodology/locked_pathways.json'),'--units','TPM','--out',str(out)]
        result=subprocess.run(command,capture_output=True,text=True);assert result.returncode==0,result.stderr
        scores=pd.read_csv(out/'pathway_scores_by_sample.csv');coverage=json.loads((out/'coverage.json').read_text());stats=json.loads((out/'pathway_response_statistics.json').read_text())
        fixed=(out/'gene_universe.txt').read_text().splitlines();strict=(out/'gene_universe_stricter.txt').read_text().splitlines()
        checks[label+'_zero_missing_alias_distinction']='ACVR1' not in fixed and 'BMP2' not in fixed and 'CCN2' in fixed and 'CTGF' not in fixed and 'APC' in fixed and 'SMAD1' in fixed and 'SMAD1' not in strict
        hall=next(c for c in coverage if c['pathway']=='HALLMARK_TGF_BETA_SIGNALING' and c['scoring']=='mean_rank')
        checks[label+'_coverage_reasons']='BMP2' in hall['unmeasured_or_outside_coding_reference'] and 'ACVR1' in hall['measured_zero_in_every_screening_sample']
        normalized=fixture.rename(index={'CTGF':'CCN2'}).loc[fixed]
        sample=samples[0];values=normalized[sample].to_numpy();unique,inv,counts=np.unique(values,return_inverse=True,return_counts=True);ends=np.cumsum(counts);starts=ends-counts+1;mid=(starts+ends)/2
        expected_ranks=(mid[inv]-.5)/len(fixed)*100
        idx={g:i for i,g in enumerate(fixed)};expected=np.mean([expected_ranks[idx[g]] for g in hall['members']])
        observed=scores[(scores.sample_id==sample)&(scores.pathway=='HALLMARK_TGF_BETA_SIGNALING')&(scores.scoring=='mean_rank')].score.item()
        checks[label+'_independent_midrank_score']=abs(observed-expected)<1e-10
        observed_log=scores[(scores.sample_id==sample)&(scores.pathway=='HALLMARK_TGF_BETA_SIGNALING')&(scores.scoring=='mean_log')].score.item()
        checks[label+'_mean_log_score']=abs(observed_log-float(np.log2(normalized.loc[hall['members'],sample]+1).mean()))<1e-10
        primary=[r for r in stats if r['scoring']=='mean_rank' and r['endpoint']=='clinical_benefit'];secondary=[r for r in stats if r['scoring']=='mean_rank' and r['endpoint']=='objective_response']
        checks[label+'_endpoint_counts']=all(r['n_positive']==5 and r['n_negative']==23 for r in primary) and all(r['n_positive']==2 and r['n_negative']==26 for r in secondary)
        checks[label+'_separate_BH4_families']=np.allclose([r['q_primary'] for r in primary],mod.bh([r['p'] for r in primary],4)) and np.allclose([r['q_secondary'] for r in secondary],mod.bh([r['p'] for r in secondary],4))
        checks[label+'_sensitivity_not_promoted']=all(r['q_primary'] is None and r['q_secondary'] is None for r in stats if r['scoring']!='mean_rank')
        checks[label+'_dose_CB_allocations']=all(r['dose_stratified']['n_allocations']==26400 for r in primary)
        if label=='one_untestable_pathway':checks['ineligible_pathway_omitted_without_shrinking_BH_family']=len(primary)==3 and all(r['pathway']!='DOMINGUEZ_LRRC15_TGF_BETA_CAF_11' for r in primary)
        synthetic_result_counts.append({'fixture':label,'primary_tests':len(primary),'secondary_tests':len(secondary),'total_result_rows':len(stats)})

assert sha(SRC)==initial_sha
assert all(checks.values()),{k:v for k,v in checks.items() if not v}
checks={k:bool(v) for k,v in checks.items()}
receipt={'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Source audit and independent synthetic fixtures only. No real expression values, scores, subject rows or outcome associations inspected. No source/process/controller changes.','status':'PASS_WITH_REPORTING_CHECKS','sources_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [SRC,ROOT/'methodology/analysis_plan.json',ROOT/'methodology/locked_pathways.json']},'synthetic_audit_script_sha256':sha(Path(__file__)),'checks':checks,'synthetic_result_counts':synthetic_result_counts,'findings':[],'reporting_checks':['Confirm actual complete-cohort primary5vs23 and secondary2vs26 counts and no endpoint missingness: generic statistics code drops missing endpoint labels, so upstream validated metadata and final counts are necessary.','Check all four signatures meet coverage in the primary score; an ineligible signature is untestable and BH family remains4. Never describe an untestable score as a negative result.','Preserve primary mean-rank/BH4 results separately from ORR/BH4 and descriptive score/stratification sensitivities. No selecting the smallest P among modes.','Effects are descriptive group summaries, pairwise HL difference, AUC/Cliff delta; code does not produce confidence intervals. Exact P is not effect precision, equivalence, treatment interaction or a calibrated personal response prediction.','Final report must display subject-level scatter or equivalent distribution and explicitly disclose small event counts, archival tissue, unknown biopsy organ, dose/liver/TMB/assay quality confounding and zero-vs-missing coverage.','The four published memberships use a uniform new unweighted rank score; do not claim original paper score reimplementation or clinical validation.'],'implementation_boundary':'Fixed28 admission and full metadata/source-hash gating are outside this narrow statistical-code audit and are reviewed by parent. Inputs are TPM in the active run; unused counts/MonteCarlo branches were inspected but not exercised here.'}
# Preserve the sealed historical validation receipt; reruns print results without rewriting it.
print(json.dumps({'status':receipt['status'],'checks_passed':len(checks),'sources_sha256':receipt['sources_sha256'],'synthetic_result_counts':synthetic_result_counts},indent=2))
