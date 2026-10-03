from pathlib import Path
import json
import numpy as np,pandas as pd,networkx as nx
from scipy import stats
ROOT=Path(__file__).resolve().parents[2]
RNG=np.random.default_rng(20241003)

def component_labels(pairs,col1,col2):
 graph=nx.Graph()
 for a,b in zip(pairs[col1].astype(str),pairs[col2].astype(str)):graph.add_edge(a,b)
 lookup={node:i for i,nodes in enumerate(nx.connected_components(graph)) for node in nodes}
 return np.array([lookup[str(x)] for x in pairs[col1]])

def cluster_cov(scores,groups):
 codes,levels=pd.factorize(groups)
 sums=np.zeros((len(levels),scores.shape[1]))
 np.add.at(sums,codes,scores)
 g=len(levels)
 return sums.T@sums*(g/(g-1) if g>1 else np.nan),g,sums

def delta_estimate(values,groups,weights=None):
 if weights is None:weights=np.ones(len(values))
 weights=weights/weights.sum()
 b=float(weights@values);score=(weights*(values-b))[:,None]
 cov,g,sums=cluster_cov(score,groups);se=float(np.sqrt(cov[0,0]))
 crit=stats.t.ppf(.975,g-1)
 p=2*stats.t.sf(abs(b/se),g-1) if se>0 else np.nan
 return {'coefficient':b,'se':se,'ci_low':b-crit*se,'ci_high':b+crit*se,'p_value':p,'clusters':g,
 'minimum_detectable_80pct':(crit+stats.norm.ppf(.8))*se}

def matrix(panel,codes,outcome):
 return panel.pivot(index='commune_code',columns='month',values=outcome).reindex(codes).to_numpy(dtype=float)

def main():
 panel=pd.read_parquet(ROOT/'data/processed/monthly_panel.parquet')
 meta=pd.read_csv(ROOT/'data/processed/commune_treatment.csv',dtype={'commune_code':str,'department':str,'epci_2023':str})
 pairs=pd.read_csv(ROOT/'data/processed/border_pairs.csv',dtype={'treated_code':str,'control_code':str,'treated_epci':str,'control_epci':str,'treated_department':str,'control_department':str})
 months=np.array(sorted(panel.month.unique()),dtype='datetime64[ns]')
 months=pd.DatetimeIndex(months)
 tm=meta.set_index('commune_code')
 T=pairs.treated_code;C=pairs.control_code
 pt=tm.loc[T,'population_2021'].to_numpy(dtype=float)
 pc=tm.loc[C,'population_2021'].to_numpy(dtype=float)
 eg=component_labels(pairs,'treated_epci','control_epci')
 dg=component_labels(pairs,'treated_department','control_department')
 joint=nx.Graph()
 for row in pairs.itertuples():
  members=['E:'+row.treated_epci,'E:'+row.control_epci,'D:'+row.treated_department,'D:'+row.control_department]
  for member in members[1:]:joint.add_edge(members[0],member)
 jlookup={node:i for i,nodes in enumerate(nx.connected_components(joint)) for node in nodes}
 jg=np.array([jlookup['E:'+x] for x in pairs.treated_epci])
 group_counts={'epci_connected_components':len(np.unique(eg)),'department_connected_components':len(np.unique(dg))}
 print(group_counts,flush=True)
 mainpre=(months.year>=2019)&(months.year<=2022)&(months.month>=7)
 mainpost=(months>='2024-07-01')&(months<='2024-12-01')
 wholepre=(months>='2019-06-01')&(months<='2023-05-01')
 yearpost=(months>='2024-07-01')&(months<='2025-06-01')
 def ymat(outcome,scale='per1000'):
  a=matrix(panel,T,outcome);b=matrix(panel,C,outcome)
  if scale=='per1000':a=a*1000/pt[:,None];b=b*1000/pc[:,None]
  elif scale=='log1p':a=np.log1p(a);b=np.log1p(b)
  return a,b
 rows=[]
 for outcome,scale in [('establishment_births','per1000'),('legal_unit_births','per1000'),('establishment_births','log1p'),('employer_births','per1000'),('births_without_recorded_continuity','per1000')]:
  a,b=ymat(outcome,scale)
  delta=(a[:,mainpost].mean(1)-a[:,mainpre].mean(1))-(b[:,mainpost].mean(1)-b[:,mainpre].mean(1))
  for grouping,grp in [('EPCI_components',eg),('department_components',dg),('EPCI_department_joint_components',jg),('independent_pairs',np.arange(len(pairs)))]:
   row=delta_estimate(delta,grp)
   row.update({'sample':'disjoint_borders','outcome':outcome,'scale':scale,'specification':'first_6_months_same_seasons','clustering':grouping,'pairs':len(pairs),
    'treated_pre_mean':float(a[:,mainpre].mean()),'control_pre_mean':float(b[:,mainpre].mean())})
   rows.append(row)
 results=pd.DataFrame(rows);results.to_csv(ROOT/'results/tables/main_border_estimates.csv',index=False)
 # Full monthly event study: pair and pair-by-year-month fixed-effects equivalence.
 a,b=ymat('establishment_births');d=a-b
 ref=months.get_loc('2023-05-01')
 diff=d-d[:,ref,None]
 coefficients=diff.mean(0)
 scores=(diff-coefficients[None,:])/len(pairs)
 cov,g,_=cluster_cov(scores,eg)
 se=np.sqrt(np.maximum(np.diag(cov),0));crit=stats.t.ppf(.975,g-1)
 es=pd.DataFrame({'month':months.strftime('%Y-%m'),'event_month':(months.year-2024)*12+months.month-7,'coefficient':coefficients,
 'se':se,'ci_low':coefficients-crit*se,'ci_high':coefficients+crit*se,'reference':'2023-05','clustering':'EPCI_components'})
 es.to_csv(ROOT/'results/tables/border_event_study.csv',index=False)
 preidx=np.where((months>='2021-06-01')&(months<'2023-05-01'))[0]
 v=cov[np.ix_(preidx,preidx)];q=len(preidx);rank=int(np.linalg.matrix_rank(v))
 wald=float(coefficients[preidx]@np.linalg.pinv(v)@coefficients[preidx])
 diagnostics={'monthly_pretrend_months':q,'covariance_rank':rank,'F':wald/q,'p_value':float(stats.f.sf(wald/q,q,g-1)) if rank==q else None,
 'reference_month':'2023-05','clustering':'EPCI connected components','cluster_count':g,
 'interpretation':'Failure to reject is not proof of parallel trends; shared-boundary controls may have spillovers.'}
 longidx=np.where((months<'2023-06-01')&(months!='2023-05-01'))[0]
 vl=cov[np.ix_(longidx,longidx)];ql=len(longidx);rankl=int(np.linalg.matrix_rank(vl))
 wl=float(coefficients[longidx]@np.linalg.pinv(vl)@coefficients[longidx])
 diagnostics['full_2019_2023_pretrend']={'months':ql,'rank':rankl,'F':wl/ql,'p_value':float(stats.f.sf(wl/ql,ql,g-1)) if rankl==ql else None}
 (ROOT/'reports/pretrend_diagnostics.json').write_text(json.dumps(diagnostics,indent=2),encoding='utf8')
 # Six-month placebo contrasts use identical calendar months and avoid announcement/post periods.
 robustness=[]
 for placebo in [2021,2022]:
  post=(months.year==placebo)&(months.month>=7)
  pre=(months.year<placebo)&(months.year>=2019)&(months.month>=7)
  val=d[:,post].mean(1)-d[:,pre].mean(1)
  r=delta_estimate(val,eg);r.update({'check':f'placebo_{placebo}_07','pairs':len(pairs)});robustness.append(r)
 for label,pre,post,keep,wt in [
  ('last_pre_announcement_year', (months.year==2022)&(months.month>=7),mainpost,np.ones(len(pairs),bool),None),
  ('first_year_excluding_frr_plus',wholepre,yearpost,~tm.loc[T,'status_2025'].eq('FRR+').to_numpy(),None),
  ('population_weighted',mainpre,mainpost,np.ones(len(pairs),bool),pt+pc),
  ('same_department',mainpre,mainpost,pairs.treated_department.eq(pairs.control_department).to_numpy(),None),
  ('excluding_pop_25000_plus',mainpre,mainpost,(pt<25000)&(pc<25000),None),
  ('excluding_covid_baselines', (months.year==2019)&(months.month>=7),mainpost,np.ones(len(pairs),bool),None),
 ]:
  val=d[:,post].mean(1)-d[:,pre].mean(1)
  r=delta_estimate(val[keep],eg[keep],None if wt is None else wt[keep]);r.update({'check':label,'pairs':int(keep.sum())});robustness.append(r)
 # Requested pre-reform 2023-07 placebo is contaminated by announcement: descriptive only.
 post=(months.year==2023)&(months.month>=7);pre=(months.year>=2019)&(months.year<=2022)&(months.month>=7)
 r=delta_estimate(d[:,post].mean(1)-d[:,pre].mean(1),eg);r.update({'check':'2023_07_announcement_period_not_clean_placebo','pairs':len(pairs)});robustness.append(r)
 pd.DataFrame(robustness).to_csv(ROOT/'results/tables/robustness.csv',index=False)
 sectors=[]
 for outcome in ['commerce','accommodation_food','construction','manufacturing','professional_services','health','proximity_services']:
  a,b=ymat(outcome);dd=a-b
  r=delta_estimate(dd[:,mainpost].mean(1)-dd[:,mainpre].mean(1),eg);r.update({'sector':outcome});sectors.append(r)
 sec=pd.DataFrame(sectors)
 from statsmodels.stats.multitest import multipletests
 sec['p_holm']=multipletests(sec.p_value,method='holm')[1]
 sec.to_csv(ROOT/'results/tables/sector_estimates.csv',index=False)
 # Pretrend plots and pair totals are descriptive; no national net-growth claim.
 a,b=ymat('establishment_births');ac,bc=ymat('establishment_births','count')
 pd.DataFrame({'month':months.strftime('%Y-%m'),'treated_per1000':a.mean(0),'control_per1000':b.mean(0),
 'pair_total_entries':(ac+bc).sum(0)}).to_csv(ROOT/'results/tables/border_trends.csv',index=False)
 # Leave one treated département out; retains fixed matching and uses no result-based deletions.
 val=d[:,mainpost].mean(1)-d[:,mainpre].mean(1)
 loo=[]
 for dep in sorted(pairs.treated_department.unique()):
  keep=~pairs.treated_department.eq(dep).to_numpy()
  r=delta_estimate(val[keep],eg[keep]);r.update({'excluded_department':dep,'pairs':int(keep.sum())});loo.append(r)
 pd.DataFrame(loo).to_csv(ROOT/'results/tables/leave_one_department_out.csv',index=False)
 # Wild score bootstrap interval for primary effect when effective assignment groups are few.
 beta=val.mean();score=((val-beta)/len(val))[:,None];_,gc,sums=cluster_cov(score,eg)
 weights=RNG.choice([-1.,1.],size=(9999,gc));perturb=weights@sums[:,0]
 codes,levels=pd.factorize(eg)
 raw_sums=np.bincount(codes,weights=val)/len(val)
 group_weight=np.bincount(codes)/len(val)
 restricted_beta=weights@raw_sums
 restricted_scores=weights*raw_sums[None,:]-restricted_beta[:,None]*group_weight[None,:]
 restricted_se=np.sqrt((restricted_scores**2).sum(1)*gc/(gc-1))
 tstar=restricted_beta/restricted_se
 mainse=np.sqrt((sums[:,0]**2).sum()*gc/(gc-1))
 wild_p=(1+np.sum(np.abs(tstar)>=abs(beta/mainse)))/(1+len(tstar))
 boot={'draws':9999,'seed':20241003,'clusters':gc,'method':'Rademacher cluster-score multiplier, centred at estimate; not an exact randomisation test',
 'ci_low':float(beta-np.quantile(perturb,.975)),'ci_high':float(beta-np.quantile(perturb,.025)),
 'wild_restricted_cluster_t_p_value':float(wild_p),'wild_null':'zero average pair difference-in-differences',
 'restricted_t_bootstrap_method':'Wild cluster restricted Rademacher residual bootstrap for an intercept-only pair-change regression; CR1 bootstrap studentisation'}
 (ROOT/'reports/wild_cluster_score.json').write_text(json.dumps(boot,indent=2),encoding='utf8')
 print(results.query("clustering=='EPCI_components'").to_string(index=False),flush=True)
 print(json.dumps(diagnostics),flush=True)
 (ROOT/'reports/analysis_status.json').write_text(json.dumps({'status':'ESTIMATED_NOT_PUBLICATION_CLEARED',**group_counts,'primary_period':'2024-07 through 2024-12',
 'baseline':'July–December 2019–2022; identical calendar-month composition','short_pretrend_p':diagnostics['p_value'],
 'full_pretrend_p':diagnostics['full_2019_2023_pretrend']['p_value'],
 'causal_clearance':False,'reason':'Full 2019–2023 monthly parallel-trend restrictions rejected; assignment paths and spillovers unresolved.'},indent=2),encoding='utf8')

if __name__=='__main__':main()
