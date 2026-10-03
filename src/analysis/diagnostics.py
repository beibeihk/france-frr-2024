"""Transparent seasonality, dependence and spatial diagnostics; not a rescue design.

Added after viewing outcomes on 2026-10-03. Preserve the original monthly
event-study test and report all alternatives, including rejections.
"""
from pathlib import Path
import sys,json
import pandas as pd,numpy as np,networkx as nx
from scipy import stats
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/analysis'))
from estimate import cluster_cov,delta_estimate,component_labels

def wald(b,cov,idx,g):
 v=cov[np.ix_(idx,idx)];rank=int(np.linalg.matrix_rank(v));vec=b[idx]
 w=float(vec@np.linalg.pinv(v)@vec)
 return {'restrictions':len(idx),'rank':rank,'F':w/rank,'p_value':float(stats.f.sf(w/rank,rank,g-1)),'clusters':g}

def main():
 p=pd.read_parquet(ROOT/'data/processed/monthly_panel.parquet')
 m=pd.read_csv(ROOT/'data/processed/commune_treatment.csv',dtype={'commune_code':str,'epci_2023':str,'department':str},low_memory=False).set_index('commune_code')
 pairs=pd.read_csv(ROOT/'data/processed/border_pairs.csv',dtype=str)
 months=pd.DatetimeIndex(sorted(p.month.unique()))
 Y=p.pivot(index='commune_code',columns='month',values='establishment_births')
 T=pairs.treated_code;C=pairs.control_code
 pt=m.loc[T,'population_2021'].to_numpy(float);pc=m.loc[C,'population_2021'].to_numpy(float)
 a=Y.loc[T].to_numpy(float)*1000/pt[:,None];b=Y.loc[C].to_numpy(float)*1000/pc[:,None];d=a-b
 eg=component_labels(pairs,'treated_epci','control_epci')
 pre=(months.year>=2019)&(months.year<=2022)&(months.month>=7)
 post=(months>='2024-07-01')&(months<='2024-12-01')
 val=d[:,post].mean(1)-d[:,pre].mean(1)
 bv=pd.read_csv(ROOT/'data/raw/legal/bv2022_composition_cog2023_extracted.csv',dtype=str).set_index('commune_code').bassin_2022_cog2023
 graph=nx.Graph()
 for row in pairs.itertuples():
  nodes=['E:'+row.treated_epci,'E:'+row.control_epci,'D:'+row.treated_department,'D:'+row.control_department,
   'B:'+bv.loc[row.treated_code],'B:'+bv.loc[row.control_code]]
  for x in nodes[1:]:graph.add_edge(nodes[0],x)
 lookup={node:i for i,nodes in enumerate(nx.connected_components(graph)) for node in nodes}
 groups=np.array([lookup['E:'+x] for x in pairs.treated_epci])
 sizes=pd.Series(groups).value_counts()
 r=delta_estimate(val,groups);r.update({'clustering':'EPCI_department_bassin_joint_components','largest_component_pairs':int(sizes.max()),
  'pair_size_effective_components':float(1/((sizes/sizes.sum())**2).sum())})
 pd.DataFrame([r]).to_csv(ROOT/'results/tables/bassin_cluster_sensitivity.csv',index=False)
 # Remove pair-specific calendar-month seasonality using only 2019–2022 observations.
 seasonal=np.empty_like(d)
 for cal in range(1,13):
  base=(months.year<=2022)&(months.month==cal)
  seasonal[:,months.month==cal]=d[:,months.month==cal]-d[:,base].mean(1)[:,None]
 coef=seasonal.mean(0);cov,g,_=cluster_cov((seasonal-coef)/len(pairs),eg)
 se=np.sqrt(np.maximum(np.diag(cov),0));crit=stats.t.ppf(.975,g-1)
 pd.DataFrame({'month':months.strftime('%Y-%m'),'coefficient':coef,'se':se,'ci_low':coef-crit*se,'ci_high':coef+crit*se,
  'normalisation':'2019–2022 mean for each calendar month'}).to_csv(ROOT/'results/tables/season_adjusted_event_study.csv',index=False)
 idx=np.where(months<'2023-06-01')[0]
 tests={'season_adjusted_full_pre':wald(coef,cov,idx,g)}
 # July–December comparisons exactly match the months in the primary estimand.
 annual=np.column_stack([d[:,(months.year==yr)&(months.month>=7)].mean(1) for yr in range(2019,2026)])
 annual=annual-annual[:,3,None] # 2022 reference
 ac=annual.mean(0);cv,_,_=cluster_cov((annual-ac)/len(pairs),eg)
 tests['same_season_2019_2022_pre']=wald(ac,cv,np.arange(3),g)
 ase=np.sqrt(np.maximum(np.diag(cv),0))
 pd.DataFrame({'year':range(2019,2026),'coefficient':ac,'se':ase,'ci_low':ac-crit*ase,'ci_high':ac+crit*ase,
  'complete_July_December':True}).to_csv(ROOT/'results/tables/same_season_annual.csv',index=False)
 # Pre-period linear differential trend plus pair-specific calendar-month offsets.
 # Model-dependence sensitivity, not an assertion that extrapolation is valid.
 train=months<'2023-06-01';t=np.arange(len(months),dtype=float)
 X=np.column_stack([np.ones(len(t)),t,*[(months.month==x).astype(float) for x in range(2,13)]])
 coefp=np.linalg.lstsq(X[train],d[:,train].T,rcond=None)[0]
 residual=d-(X@coefp).T
 lin=delta_estimate(residual[:,post].mean(1),eg)
 lin['specification']='pre_announcement_pair_linear_trend_and_calendar_season_extrapolation'
 pd.DataFrame([lin]).to_csv(ROOT/'results/tables/linear_trend_sensitivity.csv',index=False)
 # Absolute within-group changes and pair totals: descriptive, no external counterfactual.
 acount=Y.loc[T].to_numpy(float);bcount=Y.loc[C].to_numpy(float)
 rows=[]
 for name,z in [('treated_entries',acount),('neighbour_control_entries',bcount),('pair_total_entries',acount+bcount)]:
  old=z[:,pre].mean(1);new=z[:,post].mean(1)
  rows.append({'group':name,'pre_mean_monthly_entries_per_pair':old.mean(),'post_mean_monthly_entries_per_pair':new.mean(),
   'change':(new-old).mean(),'sum_pre_per_month':old.sum(),'sum_post_per_month':new.sum(),
   'interpretation':'within-group descriptive change; no counterfactual for net creation'})
 pd.DataFrame(rows).to_csv(ROOT/'results/tables/spatial_descriptive.csv',index=False)
 # Predetermined density split; all groups reported, added post-estimation.
 geo=pd.read_parquet(ROOT/'data/processed/commune_geography.parquet',columns=['commune_code','density_2021']).set_index('commune_code')
 density=geo.loc[T,'density_2021'].to_numpy(float);cut=float(np.median(density));hr=[]
 for label,keep in [('below_treated_median_density',density<=cut),('above_treated_median_density',density>cut)]:
  rr=delta_estimate(val[keep],eg[keep]);rr.update({'group':label,'density_cutoff':cut,'pairs':int(keep.sum()),'exploratory':True});hr.append(rr)
 pd.DataFrame(hr).to_csv(ROOT/'results/tables/density_exploratory.csv',index=False)
 tests['EPCI_department_bassin_dependence']=r
 tests['status']='DIAGNOSTICS_ONLY_NOT_CAUSAL_CLEARANCE'
 (ROOT/'reports/additional_diagnostics.json').write_text(json.dumps(tests,indent=2),encoding='utf8')
 print(json.dumps(tests),flush=True)

if __name__=='__main__':main()
