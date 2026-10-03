"""Conditional Poisson FE for disjoint two-commune pairs, no dummy explosion.

Conditioning on each pair-month's total yields binomial counts, with pair intercept
and common post log-odds. Since post and pair intercepts are constant within period,
collapsing the binomial likelihood to pre/post counts is exact for this specification.
"""
from pathlib import Path
import json,sys
import numpy as np,pandas as pd
from scipy.special import expit
from scipy import stats
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/analysis'))
from estimate import component_labels,cluster_cov

def main():
 panel=pd.read_parquet(ROOT/'data/processed/monthly_panel.parquet')
 pairs=pd.read_csv(ROOT/'data/processed/border_pairs.csv',dtype={'treated_code':str,'control_code':str,'treated_epci':str,'control_epci':str})
 months=pd.DatetimeIndex(sorted(panel.month.unique()))
 y=panel.pivot(index='commune_code',columns='month',values='establishment_births')
 t=y.reindex(pairs.treated_code).to_numpy(float);c=y.reindex(pairs.control_code).to_numpy(float)
 pre=(months.year>=2019)&(months.year<=2022)&(months.month>=7)
 post=(months>='2024-07-01')&(months<='2024-12-01')
 yt=np.column_stack((t[:,pre].sum(1),t[:,post].sum(1)))
 yc=np.column_stack((c[:,pre].sum(1),c[:,post].sum(1)))
 keep=(yt.sum(1)>0)&(yc.sum(1)>0)&((yt+yc)>0).all(1)
 yt=yt[keep];yc=yc[keep];n=yt+yc
 alpha=np.log((yt.sum(1)+.5)/(yc.sum(1)+.5));beta=0.
 for iteration in range(100):
  pr=expit(alpha[:,None]+np.array([0,beta]));r=yt-n*pr;w=n*pr*(1-pr)
  ga=r.sum(1);gb=r[:,1].sum();haa=w.sum(1);hab=w[:,1]
  bread=w[:,1].sum()-(hab**2/haa).sum()
  db=(gb-(ga*hab/haa).sum())/bread
  da=(ga-hab*db)/haa
  step=min(1.,2/max(np.max(np.abs(da)),abs(db),2))
  alpha+=step*da;beta+=step*db
  if max(np.max(np.abs(ga)),abs(gb))<1e-7:break
 else:raise RuntimeError('Conditional PPML did not converge')
 pr=expit(alpha[:,None]+np.array([0,beta]));r=yt-n*pr;w=n*pr*(1-pr)
 bread=w[:,1].sum()-(w[:,1]**2/w.sum(1)).sum()
 groups=component_labels(pairs,'treated_epci','control_epci')[keep]
 cov,g,_=cluster_cov((r[:,1]/bread)[:,None],groups);se=np.sqrt(cov[0,0]);crit=stats.t.ppf(.975,g-1)
 result={'specification':'conditional Poisson: commune FE + pair-by-year-month FE, first 6 months versus same-season baseline',
 'coefficient':float(beta),'se':float(se),'p_value':float(2*stats.t.sf(abs(beta/se),g-1)),
 'ci_low':float(beta-crit*se),'ci_high':float(beta+crit*se),'rate_ratio':float(np.exp(beta)),
 'pairs_informative':int(keep.sum()),'pairs_excluded_zero_or_separated':int((~keep).sum()),'clusters':g,'iterations':iteration+1}
 pd.DataFrame([result]).to_csv(ROOT/'results/tables/conditional_ppml.csv',index=False)
 print(json.dumps(result),flush=True)

if __name__=='__main__':main()
