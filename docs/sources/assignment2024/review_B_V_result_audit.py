"""Independent REVIEW B result reconstruction after parent authorises new-Y audit."""
from pathlib import Path
import sys,json,hashlib,warnings
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'.vendor_rd'))
sys.path.insert(1,str(ROOT/'.vendor'))
import numpy as np,pandas as pd,duckdb
from scipy import stats
from rdrobust import rdrobust

u=pd.read_csv(ROOT/'data/processed/rd_V_bv_candidates_assignment_only.csv',dtype=str)
for c in u.columns:
    if c!='bassin_2022_cog2023' and not c.startswith('component_'):u[c]=pd.to_numeric(u[c])
u=u.set_index('bassin_2022_cog2023')
s=pd.read_csv(ROOT/'data/processed/rd_V_bv_selected_communes_assignment_only.csv',dtype={'commune_code':str,'bassin_2022_cog2023':str,'epci_2023':str,'department':str})
roots=pd.read_csv(ROOT/'data/processed/bassin_rd_selected_communes.csv',dtype={'commune_code':str,'bassin_2022_cog2023':str,'epci_2023':str,'department':str})
rootu=pd.read_csv(ROOT/'data/processed/bassin_rd_candidates.csv',dtype={'bassin_2022_cog2023':str}).set_index('bassin_2022_cog2023')
joincols=['commune_code','bassin_2022_cog2023','epci_2023','department','P20_POP']
assert s[joincols].sort_values('commune_code').reset_index(drop=True).equals(roots[joincols].sort_values('commune_code').reset_index(drop=True))
assert set(u.index)==set(rootu.index)
assert np.allclose(u.selected_population2020,rootu.sample_population.reindex(u.index))
assert np.allclose(u.running_x,rootu.x.reindex(u.index))
assert np.array_equal(u.selected_n_communes,rootu.sample_communes.reindex(u.index))

# Rebuild aggregation from raw validated panel, not root's derived outcome CSV.
con=duckdb.connect();con.register('audit_selected',s[['commune_code','bassin_2022_cog2023']])
z=con.execute('''SELECT s.bassin_2022_cog2023, CAST(p.month AS VARCHAR) AS "month",
    sum(p.establishment_births) AS births, count(*) AS n_rows,
    count(p.establishment_births) AS n_nonmissing
    FROM read_parquet(?) p JOIN audit_selected s USING(commune_code)
    WHERE CAST(p.month AS DATE) BETWEEN DATE '2019-01-01' AND DATE '2024-12-01'
    GROUP BY 1,2 ORDER BY 1,2''',[(ROOT/'data/processed/monthly_panel.parquet').as_posix()]).df()
z['month']=pd.to_datetime(z['month'])
z['population']=z.bassin_2022_cog2023.map(u.selected_population2020)
z['expected_rows']=z.bassin_2022_cog2023.map(u.selected_n_communes)
assert (z.n_rows==z.expected_rows).all() and (z.n_nonmissing==z.expected_rows).all()
z['y']=1000*z.births/z.population
Y=z.pivot(index='bassin_2022_cog2023',columns='month',values='y').reindex(u.index)
assert Y.notna().all().all() and Y.shape==(346,72)
rootz=pd.read_parquet(ROOT/'data/processed/bassin_rd_monthly_aggregates.parquet')
ag=z.merge(rootz[['bassin_2022_cog2023','month','births','y']],on=['bassin_2022_cog2023','month'],suffixes=('_audit','_root'),validate='one_to_one')
aggregate_maxdiff=float(np.max(np.abs(ag.y_audit-ag.y_root)))
assert aggregate_maxdiff<1e-10 and np.array_equal(ag.births_audit,ag.births_root)

def fit(a,y,h,cluster=None,degree=2):
    x=a.running_x.to_numpy()/h;w=1-np.abs(x);side=x>=0
    X=np.column_stack([np.where(~side,x**j,0) for j in range(degree+1)]+[np.where(side,x**j,0) for j in range(degree+1)])
    B=np.linalg.inv(X.T@(w[:,None]*X));y=np.asarray(y)
    if y.ndim==1:y=y[:,None]
    beta=B@X.T@(w[:,None]*y);e=y-X@beta
    L=np.zeros(2*(degree+1));L[0]=-1;L[degree+1]=1
    omega=L@B@X.T*w;H=w*np.einsum('ij,jk,ik->i',X,B,X)
    sc=omega[:,None]*e/(1-H[:,None]);V=sc.T@sc
    if cluster is not None:
        cs=pd.DataFrame(omega[:,None]*e).groupby(np.asarray(cluster)).sum().to_numpy()
        G=len(cs);V=cs.T@cs*G/(G-1)*(len(a)-1)/(len(a)-X.shape[1])
    return L@beta,V,float(H.max())

periods={'primary_2024H2':pd.date_range('2024-07-01','2024-12-01',freq='MS')}
for year in range(2019,2023):periods[f'placebo_{year}H2']=pd.date_range(f'{year}-07-01',f'{year}-12-01',freq='MS')
rootr=pd.read_csv(ROOT/'results/tables/bassin_rd_estimates.csv').set_index(['period','bandwidth'])
records=[];maxdiff=0.
for h in (500,750,1000,1500):
    a=u.loc[u.running_x.abs()<h];yh=Y.reindex(a.index)
    for name,months in periods.items():
        y=yh.loc[:,months].mean(axis=1).to_numpy()
        with warnings.catch_warnings(record=True):
            obj=rdrobust(y=y,x=a.running_x.to_numpy(),c=0,p=1,q=2,h=h,b=h,kernel='triangular',masspoints='adjust',vce='hc3',level=95)
        point,V,lev=fit(a,y,h);se=float(np.sqrt(V[0,0]));conv,_,_=fit(a,y,h,degree=1)
        assert abs(point[0]-obj.coef.loc['Robust'].iloc[0])<1e-7
        assert abs(se-obj.se.loc['Robust'].iloc[0])<1e-7
        r={'period':name,'bandwidth':h,'conventional':float(conv[0]),'bias_corrected':float(point[0]),
           'se_rbc_hc3':se,'ci_low_hc3':float(point[0]-stats.norm.ppf(.975)*se),
           'ci_high_hc3':float(point[0]+stats.norm.ppf(.975)*se),'p_hc3':float(2*stats.norm.sf(abs(point[0]/se))),
           'n_bv':len(a),'max_weighted_leverage':lev}
        for scope,col,prefix in [('selected',f'component_joint_h{h}','joint'),('full',f'component_joint_full_h{h}','full_joint')]:
            _,cv,_=fit(a,y,h,a[col]);G=a[col].nunique();cs=float(np.sqrt(cv[0,0]));crit=stats.t.ppf(.975,G-1)
            r[prefix+'_se']=cs;r[prefix+'_ci_low']=float(point[0]-crit*cs);r[prefix+'_ci_high']=float(point[0]+crit*cs)
            r[prefix+'_p']=float(2*stats.t.sf(abs(point[0]/cs),G-1));r[prefix+'_groups']=int(G)
        diffs={c:abs(r[c]-float(rootr.loc[(name,h),c])) for c in r if c in rootr.columns and isinstance(r[c],(float,int))}
        r['max_abs_root_difference']=max(diffs.values());maxdiff=max(maxdiff,r['max_abs_root_difference'])
        assert r['max_abs_root_difference']<1e-7
        records.append(r)
pre=pd.date_range('2019-01-01','2023-05-01',freq='MS');a=u.loc[u.running_x.abs()<1000];yp=Y.reindex(a.index).loc[:,pre]
coef,V,lev=fit(a,yp.to_numpy(),1000)
joint={}
for name,C in [('independent_HC3',V),('joint_CR1',fit(a,yp.to_numpy(),1000,a.component_joint_h1000)[1]),
               ('full_joint_CR1',fit(a,yp.to_numpy(),1000,a.component_joint_full_h1000)[1])]:
    rank=int(np.linalg.matrix_rank(C));stat=float(coef@np.linalg.pinv(C)@coef)
    joint[name]={'restrictions':len(pre),'covariance_rank':rank,'wald':stat,'p_chi2_rank_reference':float(stats.chi2.sf(stat,rank)),
                 'full_restrictions_test_available':rank==len(pre),'descriptive_only_if_rank_deficient':rank<len(pre)}
rootmonthly=pd.read_csv(ROOT/'results/tables/bassin_rd_monthly_diagnostics.csv',parse_dates=['month']).set_index('month')
monthpointdiff=float(np.max(np.abs(coef-rootmonthly.loc[pre,'bias_corrected'].to_numpy())))
monthsediff=float(np.max(np.abs(np.sqrt(np.diag(V))-rootmonthly.loc[pre,'se_rbc_hc3'].to_numpy())))
assert max(monthpointdiff,monthsediff)<1e-7
summary={'independent_raw_panel_reaggregation':True,'fixed_sample_matches_root':True,'all_candidate_bv':len(u),'all_selected_communes':len(s),
    'audit_aggregate_months':72,'max_aggregate_y_difference':aggregate_maxdiff,'all_20_period_bandwidth_results_max_root_difference':maxdiff,
    'primary':next(r for r in records if r['period']=='primary_2024H2' and r['bandwidth']==1000),
    'main_four_placebos':[r for r in records if r['period']!='primary_2024H2' and r['bandwidth']==1000],
    'full_pre_joint':joint,'full_pre_monthly_max_root_point_difference':monthpointdiff,'full_pre_monthly_max_root_SE_difference':monthsediff,
    'causal_gate':'CLOSED_V_CAUSAL_ROUTE: historical discontinuities, selection composition jumps, concentrated dependencies',
    'noncausal_scientific_scope':'Possible valuable institutional/data/comparative working paper; must review the actually restructured paper and measurement/source evidence',
    'human_review_completed':False,'HAL_submitted':False,
    'sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['src/analysis/bassin_rd.py','docs/assignment_rd_protocol.md',
             'data/processed/monthly_panel.parquet','data/processed/rd_V_bv_candidates_assignment_only.csv',
             'results/tables/bassin_rd_estimates.csv','reports/bassin_rd_results.json']}}
pd.DataFrame(records).to_csv(ROOT/'reports/review_B_V_results_recomputed.csv',index=False)
(ROOT/'reports/review_B_V_results.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in summary.items() if k!='sha256'},ensure_ascii=False,indent=2))
