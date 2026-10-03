"""Supplementary administrative outcomes and descriptive cohort retention."""
from pathlib import Path
import sys
import pandas as pd,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'src/analysis'))
from estimate import delta_estimate,component_labels

def main():
 pairs=pd.read_csv(ROOT/'data/processed/border_pairs.csv',dtype=str)
 meta=pd.read_csv(ROOT/'data/processed/commune_treatment.csv',dtype={'commune_code':str},low_memory=False).set_index('commune_code')
 panel=pd.read_parquet(ROOT/'data/processed/monthly_panel.parquet')
 events=pd.read_parquet(ROOT/'data/processed/secondary_administrative_events.parquet')
 panel=panel.merge(events.drop(columns='establishment_closures'),on=['commune_code','month'],validate='1:1')
 panel['non_individual_unit_births']=panel.legal_unit_births-panel.individual_births
 months=pd.DatetimeIndex(sorted(panel.month.unique()));pre=(months.year<=2022)&(months.month>=7)
 post=(months>='2024-07-01')&(months<='2024-12-01');groups=component_labels(pairs,'treated_epci','control_epci');rows=[]
 for out in ['individual_births','non_individual_unit_births','establishment_closures','registration_minus_closure_balance','legal_cessation_events','establishment_reopen_events']:
  y=panel.pivot(index='commune_code',columns='month',values=out)
  a=y.loc[pairs.treated_code].to_numpy(float)*1000/meta.loc[pairs.treated_code,'population_2021'].to_numpy(float)[:,None]
  b=y.loc[pairs.control_code].to_numpy(float)*1000/meta.loc[pairs.control_code,'population_2021'].to_numpy(float)[:,None]
  d=a-b;r=delta_estimate(d[:,post].mean(1)-d[:,pre].mean(1),groups);r['outcome']=out;rows.append(r)
 pd.DataFrame(rows).to_csv(ROOT/'results/tables/secondary_estimates.csv',index=False)
 cohort=pd.read_parquet(ROOT/'data/processed/administrative_retention_cohorts.parquet')
 print(cohort.columns.tolist(),flush=True)
 cr=[]
 for horizon in [12,18]:
  h=cohort[cohort.horizon_months.eq(horizon)].copy()
  birth=pd.to_datetime(h.cohort_month)
  for sample,t,c in [('broad',meta[meta.analysis_stable&meta.population_2021.lt(30000)&meta.treatment_group.eq('NEW_FRR')].index,
     meta[meta.analysis_stable&meta.population_2021.lt(30000)&meta.treatment_group.eq('NEVER_TREATED')].index),('border',pairs.treated_code,pairs.control_code)]:
   for name,codes in [('NEW_FRR',t),('NEVER_TREATED',c)]:
    for period,mask in [('2019_2022_July_December',(birth.dt.year<=2022)&(birth.dt.month>=7)),('2024_July_December',birth.dt.year.eq(2024)&birth.dt.month.ge(7))]:
     z=h[mask&h.commune_code.isin(codes)]
     active=int(z.n_active_at_horizon.sum());closed=int(z.n_closed_at_horizon.sum());unknown=int(z.n_unknown_horizon.sum());known=active+closed
     cr.append({'sample':sample,'horizon_months':horizon,'group':name,'birth_period':period,'active':active,'closed':closed,'unknown':unknown,
      'eligible':int(z.n_eligible.sum()),'retention_known':active/known if known else np.nan,
      'retention_lower':active/(known+unknown) if known+unknown else np.nan,
      'retention_upper':(active+unknown)/(known+unknown) if known+unknown else np.nan,'interpretation':'descriptive cohort composition; not a causal survival effect'})
 pd.DataFrame(cr).to_csv(ROOT/'results/tables/cohort_retention.csv',index=False)

if __name__=='__main__':main()
