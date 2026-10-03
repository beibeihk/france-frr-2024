"""Rebuild frozen E/V support, V covariates, membership and dependency graphs.

Assignment-only: no monthly panel or establishment outcomes are read.
Uses isolated .vendor_rd (recorded in requirements_rd.txt) for V covariate RBC
and unrelated synthetic numerical checks, never as a substitute for real Y.
"""
from pathlib import Path
import sys,runpy,json,hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.vendor_rd'))
import numpy as np,pandas as pd
from scipy import stats

def main():
    helper=ROOT/'docs/sources/assignment2024/review_B_V_assignment_interface.py'
    ns=runpy.run_path(str(helper))
    d=ns['d'];p=ROOT/'data/processed';rep=ROOT/'reports'
    # E was frozen separately: preserve all alternative routes, density<=58.57.
    es=d.loc[d.fixed_prepolicy_common & d.epci_density_2020.le(58.57)].copy()
    es['frr_population']=es.P20_POP*es.listed_initial2024.astype(float)
    eu=es.groupby('epci_2023').agg(population2020=('P20_POP','sum'),selected_communes=('commune_code','size'),
        income2020=('epci_median_income2020','first'),density2020=('epci_density_2020','first'),frr_population=('frr_population','sum')).reset_index()
    eu['running_x']=21570-eu.income2020;eu['criterion_eligible']=(eu.running_x>=0).astype(int)
    eu['initial_frr_population_share']=eu.frr_population/eu.population2020
    records=[]
    for h in (500,750,1000,1500):
        a=eu.loc[eu.running_x.abs()<h];x=a.running_x.to_numpy()/h;z=(x>=0).astype(float);w=1-np.abs(x)
        X=np.column_stack([np.ones(len(a)),z,x,z*x]);B=np.linalg.inv(X.T@(w[:,None]*X))
        beta=B@X.T@(w*a.initial_frr_population_share.to_numpy())
        e=a.initial_frr_population_share.to_numpy()-X@beta;hat=w*np.einsum('ij,jk,ik->i',X,B,X)
        omega=np.array([0.,1,0,0])@B@X.T*w;se=float(np.sqrt(np.sum((omega*e/(1-hat))**2)))
        crit=stats.t.ppf(.975,len(a)-4)
        records.append({'candidate':'E','h':h,'eligible_units':int((z==1).sum()),'ineligible_units':int((z==0).sum()),
            'eligible_distinct_scores':a.loc[a.criterion_eligible.eq(1),'running_x'].nunique(),
            'ineligible_distinct_scores':a.loc[a.criterion_eligible.eq(0),'running_x'].nunique(),
            'ties':int(a.running_x.eq(0).sum()),'population2020':float(a.population2020.sum()),
            'selected_communes':int(a.selected_communes.sum()),'nearest_eligible_distance':float(a.loc[a.running_x.ge(0),'running_x'].min()),
            'nearest_ineligible_distance':float(-a.loc[a.running_x.lt(0),'running_x'].max()),
            'assignment_first_stage_local_linear':float(beta[1]),'hc3_se':se,
            'hc3_student_ci_low':float(beta[1]-crit*se),'hc3_student_ci_high':float(beta[1]+crit*se),
            'max_weighted_leverage':float(hat.max()),'support_gate_passed':bool((z==1).sum()>=20 and (z==0).sum()>=20
                and a.loc[a.criterion_eligible.eq(1),'running_x'].nunique()>=15 and a.loc[a.criterion_eligible.eq(0),'running_x'].nunique()>=15),
            'status':'CLOSED_SUPPORT_INSUFFICIENT','research_outcome_read':False})
    eu.to_csv(p/'rd_E_epci_candidates_assignment_only.csv',index=False)
    es.to_csv(p/'rd_E_epci_selected_communes_assignment_only.csv',index=False)
    pd.DataFrame(records).to_csv(rep/'review_B_E_assignment_support.csv',index=False)
    covhelper=ROOT/'docs/sources/assignment2024/review_B_V_covariate_diagnostics.py'
    runpy.run_path(str(covhelper))
    manifest={'research_outcome_read':False,'script':str(Path(__file__).resolve()),
        'route_E':'Frozen criterion reduced form preserving alternatives; closed for insufficient eligible-side support',
        'route_V':'Frozen BV income criterion; minimum assignment support passes, continuity/inference not cleared',
        'source_sha256':{str(v.relative_to(ROOT)):hashlib.sha256(v.read_bytes()).hexdigest() for v in [Path(__file__).resolve(),helper,covhelper,
            p/'assignment2024_commune_paths.csv',p/'assignment2024_territory_indicators.csv',p/'commune_treatment.csv',ROOT/'.vendor_rd/rdrobust/rdrobust.py']},
        'E_support':records,'V_reports':['review_B_V_assignment_interface.json','review_B_V_covariate_diagnostics.json'],
        'synthetic_check_is_not_research_Y':True}
    (rep/'assignment_extended_support_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'E_support':records,'manifest':str(rep/'assignment_extended_support_manifest.json')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
