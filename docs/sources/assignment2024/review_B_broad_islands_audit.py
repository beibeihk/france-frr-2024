"""Read-only independent verification of broad/matched island primitives."""
from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'.vendor_rd'));sys.path.insert(1,str(ROOT/'.vendor'))
import numpy as np,pandas as pd,duckdb
from scipy import stats

m=pd.read_csv(ROOT/'data/processed/commune_treatment.csv',dtype={'commune_code':str,'epci_2023':str,'department':str},low_memory=False)
m=m.loc[m.analysis_stable & m.treatment_group.isin(['NEW_FRR','NEVER_TREATED']) & m.population_2021.lt(30000)].copy().set_index('commune_code')
assert m.epci_2023.notna().all()
real=m.epci_2023.str.fullmatch('[0-9]{9}')
m['primitive']=['E:'+v if r else 'C:'+c for c,v,r in zip(m.index,m.epci_2023,real)]
islands=m.loc[~real,['epci_2023','primitive','treatment_group']]
assert set(islands.index)=={'22016','29083','85113'}
assert islands.primitive.nunique()==3 and m.primitive.nunique()==724 and m.epci_2023.nunique()==722
con=duckdb.connect();con.register('audit_sample',m.reset_index()[['commune_code']])
z=con.execute('''SELECT p.commune_code,
    avg(CASE WHEN year(p.month) BETWEEN 2019 AND 2022 AND month(p.month)>=7 THEN p.establishment_births END) AS pre,
    avg(CASE WHEN p.month BETWEEN DATE '2024-07-01' AND DATE '2024-12-01' THEN p.establishment_births END) AS post
    FROM read_parquet(?) p JOIN audit_sample USING(commune_code) GROUP BY p.commune_code''',
    [(ROOT/'data/processed/monthly_panel.parquet').as_posix()]).df().set_index('commune_code').reindex(m.index)
assert z.notna().all().all()
change=(z.post-z.pre)*1000/m.population_2021
treated=m.treatment_group.eq('NEW_FRR');nt=int(treated.sum());nc=int((~treated).sum())
beta=float(change.loc[treated].mean()-change.loc[~treated].mean())
score=pd.Series(np.where(treated,(change-change.loc[treated].mean())/nt,-(change-change.loc[~treated].mean())/nc),index=m.index)
def summary(score,groups,point):
    gscore=score.groupby(groups).sum();G=len(gscore);se=float(np.sqrt((gscore*gscore).sum()*G/(G-1)));crit=stats.t.ppf(.975,G-1)
    return {'coefficient':point,'se':se,'clusters':G,'ci_low':float(point-crit*se),'ci_high':float(point+crit*se),
            'p_value':float(2*stats.t.sf(abs(point/se),G-1))}
new=summary(score,m.primitive,beta);old=summary(score,m.epci_2023,beta)
rootb=pd.read_csv(ROOT/'results/tables/broad_did.csv').iloc[0]
assert max(abs(new[c]-rootb[c]) for c in new)<1e-10
pairs=pd.read_csv(ROOT/'data/processed/matched_pairs.csv',dtype={'treated_code':str,'control_code':str,'treated_epci':str,'control_epci':str,
    'treated_department':str,'control_department':str,'treated_assignment_cluster':str,'control_assignment_cluster':str})
assert len(pairs)==1908 and pairs.treated_code.is_unique and pairs.control_code.is_unique
assert np.array_equal(pairs.treated_assignment_cluster,m.primitive.reindex(pairs.treated_code))
assert np.array_equal(pairs.control_assignment_cluster,m.primitive.reindex(pairs.control_code))
parent={}
def find(v):
    parent.setdefault(v,v)
    if parent[v]!=v:parent[v]=find(parent[v])
    return parent[v]
def union(a,b):
    aa,bb=find(a),find(b)
    if aa!=bb:parent[max(aa,bb)]=min(aa,bb)
for r in pairs.itertuples():
    nodes=[r.treated_assignment_cluster,r.control_assignment_cluster,'D:'+r.treated_department,'D:'+r.control_department]
    for v in nodes[1:]:union(nodes[0],v)
labels=pd.Series([find(v) for v in pairs.treated_assignment_cluster])
delta=change.reindex(pairs.treated_code).to_numpy()-change.reindex(pairs.control_code).to_numpy();mb=float(delta.mean())
mr=summary(pd.Series((delta-mb)/len(delta)),labels,mb)
rootm=pd.read_csv(ROOT/'results/tables/matched_did.csv').set_index('clustering').loc['EPCI_department_joint_components']
assert max(abs(mr[c]-rootm[c]) for c in mr)<1e-10
result={'broad_sample_treated':nt,'broad_sample_control':nc,'unrelated_island_primitives':islands.reset_index().to_dict('records'),
        'new_broad':new,'counterfactual_wrong_ZZ_broad':old,'coefficient_change':new['coefficient']-old['coefficient'],
        'se_change':new['se']-old['se'],'matched_joint':mr,'matched_islands_included':sorted(set(islands.index)&(set(pairs.treated_code)|set(pairs.control_code))),
        'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['src/analysis/broad_and_matched.py','results/tables/broad_did.csv',
            'results/tables/matched_did.csv','data/processed/commune_treatment.csv','data/processed/matched_pairs.csv']},
        'no_estimation_output_overwritten':True}
(ROOT/'reports/review_B_broad_islands_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,ensure_ascii=False,indent=2))
