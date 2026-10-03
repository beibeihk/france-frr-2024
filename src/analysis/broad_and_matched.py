from pathlib import Path
import sys,json
import numpy as np,pandas as pd,networkx as nx
from scipy.spatial.distance import cdist
from scipy.optimize import linear_sum_assignment
from scipy import stats
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src/analysis'))
from estimate import cluster_cov,delta_estimate,component_labels

def main():
 p=pd.read_parquet(ROOT/'data/processed/monthly_panel.parquet')
 m=pd.read_csv(ROOT/'data/processed/commune_treatment.csv',dtype={'commune_code':str,'department':str,'epci_2023':str},low_memory=False)
 m=m[m.analysis_stable&m.treatment_group.isin(['NEW_FRR','NEVER_TREATED'])&m.population_2021.lt(30000)].copy()
 den=pd.read_parquet(ROOT/'data/processed/commune_geography.parquet',columns=['commune_code','density_2021'])
 m=m.merge(den,on='commune_code',validate='1:1').set_index('commune_code')
 # The official EPCI table's ZZZZZZZZZ / Sans objet is not an institution.
 # Isolated communes have their own legal indicators and must not share a cluster.
 m['assignment_cluster']=np.where(m.epci_2023.str.fullmatch(r'[0-9]{9}'),'E:'+m.epci_2023,'C:'+m.index.to_series())
 months=pd.DatetimeIndex(sorted(p.month.unique()));y=p.pivot(index='commune_code',columns='month',values='establishment_births').reindex(m.index).to_numpy(float)*1000/m.population_2021.to_numpy()[:,None]
 tr=m.treatment_group.eq('NEW_FRR').to_numpy();nt=tr.sum();nc=(~tr).sum()
 pre=(months.year>=2019)&(months.year<=2022)&(months.month>=7)
 post=(months>='2024-07-01')&(months<='2024-12-01')
 change=y[:,post].mean(1)-y[:,pre].mean(1);beta=change[tr].mean()-change[~tr].mean()
 score=np.where(tr,(change-change[tr].mean())/nt,-(change-change[~tr].mean())/nc)[:,None]
 cov,g,_=cluster_cov(score,m.assignment_cluster.to_numpy());se=float(np.sqrt(cov[0,0]));crit=stats.t.ppf(.975,g-1)
 result={'sample':'all_stable_below30000','coefficient':beta,'se':se,'ci_low':beta-crit*se,'ci_high':beta+crit*se,
 'p_value':2*stats.t.sf(abs(beta/se),g-1),'clusters':g,'treated':nt,'controls':nc,'clustering':'EPCI_2023_and_isolated_communes'}
 pd.DataFrame([result]).to_csv(ROOT/'results/tables/broad_did.csv',index=False)
 ref=months.get_loc('2023-05-01');diff=y-y[:,ref,None];b=diff[tr].mean(0)-diff[~tr].mean(0)
 scores=np.where(tr[:,None],(diff-diff[tr].mean(0))/nt,-(diff-diff[~tr].mean(0))/nc)
 cv,_,_=cluster_cov(scores,m.assignment_cluster.to_numpy());es=np.sqrt(np.maximum(np.diag(cv),0))
 pd.DataFrame({'month':months.strftime('%Y-%m'),'coefficient':b,'se':es,'ci_low':b-crit*es,'ci_high':b+crit*es}).to_csv(ROOT/'results/tables/broad_event_study.csv',index=False)
 pd.DataFrame({'month':months.strftime('%Y-%m'),'treated_per1000':y[tr].mean(0),'control_per1000':y[~tr].mean(0)}).to_csv(ROOT/'results/tables/broad_trends.csv',index=False)
 # Predetermined matching covariates only: fixed population, density, pre-announcement entries.
 m['pre_entries_per1000']=y[:,pre].mean(1)
 x=np.column_stack((np.log1p(m.population_2021),np.log1p(m.density_2021),m.pre_entries_per1000))
 x=(x-x.mean(0))/x.std(0)
 matches=[]
 for dep in sorted(m.department.unique()):
  it=np.where(tr&m.department.eq(dep).to_numpy())[0];ic=np.where(~tr&m.department.eq(dep).to_numpy())[0]
  if not len(it) or not len(ic):continue
  cost=cdist(x[it],x[ic],metric='sqeuclidean');r,c=linear_sum_assignment(cost)
  for ai,bi in zip(it[r],ic[c]):matches.append((m.index[ai],m.index[bi],ai,bi))
 pairs=pd.DataFrame(matches,columns=['treated_code','control_code','ti','ci'])
 pairs['treated_epci']=m.loc[pairs.treated_code,'epci_2023'].to_numpy();pairs['control_epci']=m.loc[pairs.control_code,'epci_2023'].to_numpy()
 pairs['treated_department']=m.loc[pairs.treated_code,'department'].to_numpy();pairs['control_department']=m.loc[pairs.control_code,'department'].to_numpy()
 pairs['treated_assignment_cluster']=m.loc[pairs.treated_code,'assignment_cluster'].to_numpy();pairs['control_assignment_cluster']=m.loc[pairs.control_code,'assignment_cluster'].to_numpy()
 pairs.to_csv(ROOT/'data/processed/matched_pairs.csv',index=False)
 delta=change[pairs.ti]-change[pairs.ci]
 grp=component_labels(pairs,'treated_department','control_department')
 r=delta_estimate(delta,grp);r.update({'sample':'within_department_optimal_pre_covariate_matching','pairs':len(pairs),'clustering':'department'})
 joint=nx.Graph()
 for row in pairs.itertuples():
  nodes=[row.treated_assignment_cluster,row.control_assignment_cluster,'D:'+row.treated_department,'D:'+row.control_department]
  for node in nodes[1:]:joint.add_edge(nodes[0],node)
 lu={node:i for i,nodes in enumerate(nx.connected_components(joint)) for node in nodes}
 jg=np.array([lu[x] for x in pairs.treated_assignment_cluster])
 rj=delta_estimate(delta,jg);rj.update({'sample':'within_department_optimal_pre_covariate_matching','pairs':len(pairs),'clustering':'EPCI_department_joint_components'})
 pd.DataFrame([r,rj]).to_csv(ROOT/'results/tables/matched_did.csv',index=False)
 # Full pre-period diagnostics must accompany small/non-significant point estimates.
 def pretest(coef,vc,groups):
  ix=np.where((months<'2023-06-01')&(months!='2023-05-01'))[0];v=vc[np.ix_(ix,ix)];rank=int(np.linalg.matrix_rank(v))
  w=float(coef[ix]@np.linalg.pinv(v)@coef[ix])
  return {'months':len(ix),'rank':rank,'F':w/rank,'p_value':float(stats.f.sf(w/rank,rank,groups-1)),'clusters':groups}
 md=diff[pairs.ti]-diff[pairs.ci];mb=md.mean(0);mv,mg,_=cluster_cov((md-mb)/len(pairs),jg)
 diagnostics={'broad':pretest(b,cv,g),'matched_joint_components':pretest(mb,mv,mg),
  'interpretation':'No causal null conclusion is licensed by insignificant average contrasts when pretrends fail.'}
 (ROOT/'reports/broad_matched_pretrends.json').write_text(json.dumps(diagnostics,indent=2),encoding='utf8')
 balance=[]
 for v in ['population_2021','density_2021','pre_entries_per1000']:
  for sample,a,b in [('broad',m.loc[tr,v],m.loc[~tr,v]),('matched',m.loc[pairs.treated_code,v],m.loc[pairs.control_code,v])]:
   sd=np.sqrt((a.var()+b.var())/2)
   balance.append({'sample':sample,'variable':v,'treated_mean':a.mean(),'control_mean':b.mean(),'standardised_difference':(a.mean()-b.mean())/sd})
 pd.DataFrame(balance).to_csv(ROOT/'results/tables/covariate_balance.csv',index=False)
 summary=m.groupby('treatment_group').agg(communes=('population_2021','size'),population_mean=('population_2021','mean'),density_mean=('density_2021','mean'),pre_entries_mean=('pre_entries_per1000','mean')).reset_index()
 summary.to_csv(ROOT/'results/tables/summary_statistics.csv',index=False)
 print(json.dumps({k:int(v) if isinstance(v,np.integer) else float(v) if isinstance(v,np.floating) else v for k,v in result.items()}),flush=True)
 print('MATCHED',r,flush=True)

if __name__=='__main__':main()
