"""Reconstruct statutory paths and RD support without reading research outcomes.

The basin path remains discretionary. The mountain workbook records communes
with any coverage, not the population living within the legal mountain zone.
Use conservative barriers rather than inventing those unobserved quantities.
"""
from pathlib import Path
import hashlib,json
import numpy as np,pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'data/processed';REP=ROOT/'reports'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    income=pd.read_csv(OUT/'assignment2024_income.csv',dtype={'level':str,'code':str})
    pop=pd.read_csv(OUT/'assignment2024_commune_population_area.csv',dtype={'commune_code':str,'epci_2023':str,'department':str})
    terr=pd.read_csv(OUT/'assignment2024_territory_indicators.csv',dtype={'level':str,'code':str})
    assert not terr.duplicated(['level','code']).any() and pop.commune_code.is_unique
    levels={k:v.set_index('code') for k,v in terr.groupby('level')}
    epi=levels['EPCI'];bv=levels['BV2022'];dep=levels['DEP']
    cuts={'epci_density':float(epi.density_2020.median()),'epci_income':float(epi.median_income2020.median()),
          'epci_income_q75':float(epi.median_income2020.quantile(.75)),
          'bassin_density':float(bv.density_2020.median()),'bassin_income':float(bv.median_income2020.median()),
          'department_density':35.,'department_income':float(dep.median_income2020.median())}
    assert round(cuts['epci_density'],2)==63.57 and round(cuts['bassin_density'],2)==70.84
    assert cuts['epci_income']==21570 and cuts['epci_income_q75']==22822.5
    assert cuts['bassin_income']==21600 and cuts['department_income']==21665
    bvm=pd.read_csv(OUT/'bassin2022_composition.csv',dtype=str)[['commune_code','bassin_2022_cog2023']]
    assert bvm.commune_code.is_unique
    d=pop[pop.department.str.len().eq(2)].merge(bvm,on='commune_code',how='left',validate='1:1')
    for name,key,table in [('epci','epci_2023',epi),('bassin','bassin_2022_cog2023',bv),('department','department',dep)]:
        for var in ['density_2020','median_income2020']:
            d[name+'_'+var]=d[key].map(table[var])
    d['commune_income2020']=d.commune_code.map(income[income.level.eq('COM')].set_index('code').med2020)
    d['actual_epci']=d.epci_2023.isin(epi.index)
    d['population_below30000']=d.P20_POP.lt(30000)
    d['eligible_A_epci']=d.actual_epci&d.epci_density_2020.le(cuts['epci_density'])&d.epci_median_income2020.le(cuts['epci_income'])&d.population_below30000
    d['eligible_A_isolated_commune']=~d.actual_epci&d.density2020.le(cuts['epci_density'])&d.commune_income2020.le(cuts['epci_income'])&d.population_below30000
    d['isolated_A_income_unknown']=~d.actual_epci&d.commune_income2020.isna()&d.density2020.le(cuts['epci_density'])&d.population_below30000
    qualdep=dep[dep.density_2020.lt(35)&dep.median_income2020.le(cuts['department_income'])].index
    assert set(qualdep)==set(['04','05','09','12','15','23','32','36','46','48','52','55','58'])
    d['department_qualifies']=d.department.isin(qualdep)
    d['eligible_C_department']=d.department_qualifies&d.population_below30000
    # A basin can contain a city above 30,000: the population ceiling applies
    # to each target commune, not to all members of the basin collectively.
    d['bassin_indicators_unknown']=d.bassin_density_2020.isna()|d.bassin_median_income2020.isna()
    d['bassin_potential']=d.bassin_indicators_unknown|(d.bassin_density_2020.le(cuts['bassin_density'])&d.bassin_median_income2020.le(cuts['bassin_income']))
    d['eligible_B_potential']=d.bassin_potential&d.population_below30000
    mountain=pd.read_excel(ROOT/'data/raw/assignment2024/mountain_cog2022.xlsx',sheet_name='Perimetre',header=2,dtype=str)
    mc=set(mountain.INSEE_COM.dropna())
    hist=pd.read_csv(ROOT/'data/raw/communes_history_cog2026.csv',dtype=str).fillna('')
    cog2022=set(hist.loc[hist.TYPECOM.eq('COM')&hist.DATE_DEBUT.le('2022-01-01')&(hist.DATE_FIN.eq('')|hist.DATE_FIN.ge('2022-01-01')),'COM'])
    d['mountain_any_commune2022']=d.commune_code.isin(mc)
    d['mountain_membership_unknown']=~d.commune_code.isin(cog2022)
    d['mountain_population_upper']=np.where(d.mountain_any_commune2022|d.mountain_membership_unknown,d.P20_POP,0)
    grouped=d[d.actual_epci].groupby('epci_2023')
    e=epi.copy();e.index.name='epci_2023'
    e['mountain_any_member']=grouped.mountain_any_commune2022.any()
    e['mountain_membership_unknown']=grouped.mountain_membership_unknown.any()
    e['mountain_population_upper_share']=grouped.mountain_population_upper.sum()/e.population_2020
    e['bassin_any_potential_member']=grouped.bassin_potential.any()
    e['department_any_qualifying_member']=grouped.department_qualifies.any()
    e['department_count']=grouped.department.nunique()
    e['department_members']=grouped.department.agg(lambda x:'|'.join(sorted(set(x))))
    d['epci_mountain_possible']=d.epci_2023.map(e.mountain_population_upper_share).ge(.5)
    d['eligible_D_potential']=d.actual_epci&d.epci_mountain_possible&d.epci_density_2020.le(cuts['epci_density'])&d.epci_median_income2020.le(cuts['epci_income_q75'])&d.population_below30000
    original=pd.read_csv(OUT/'frr_2024_codes_verified.csv',dtype=str)
    d['listed_initial2024']=d.commune_code.isin(original.code_insee)
    definite=d.eligible_A_epci|d.eligible_A_isolated_commune|d.eligible_C_department
    potential=definite|d.eligible_B_potential|d.eligible_D_potential
    d['assignment_audit_status']=np.select([definite&d.listed_initial2024,definite&~d.listed_initial2024,
        d.isolated_A_income_unknown,
        d.listed_initial2024&~potential,d.listed_initial2024&potential,~d.listed_initial2024&potential],
        ['verified_mandatory_path_listed','mandatory_path_missing_from_list','isolated_commune_income_unknown','listed_without_reconstructed_possible_path',
         'listed_only_potential_B_or_D','not_listed_potential_discretionary_or_mountain_path'],default='not_listed_no_path')
    d.to_csv(OUT/'assignment2024_commune_paths.csv',index=False)
    meta=pd.read_csv(OUT/'commune_treatment.csv',dtype={'commune_code':str,'epci_2023':str},low_memory=False)
    # No condition on NEW_FRR/NEVER_TREATED or on later FRR inclusion.
    # Current panel geography is conservatively stable; its selection coverage
    # must also be diagnosed at the running-variable cutoff before clearance.
    fixed=meta[meta.analysis_stable&meta.prior_zrr_effects.eq(False)&meta.metropolitan].commune_code
    d['fixed_prepolicy_candidate']=d.commune_code.isin(fixed)&d.actual_epci&d.population_below30000
    no_mountain=~(e.mountain_any_member|e.mountain_membership_unknown)
    legal_candidates=[];support=[]
    for design in ['A_income_whole_epci_barrier','B_income_commune_barrier','D_density_commune_barrier']:
        if design.startswith('A'):
            keep_e=no_mountain&~e.bassin_any_potential_member&~e.department_any_qualifying_member&e.density_2020.le(58.57)
            selected=d[d.fixed_prepolicy_candidate&d.epci_2023.isin(e.index[keep_e])].copy()
        elif design.startswith('B'):
            keep_e=no_mountain&e.density_2020.le(58.57)
            selected=d[d.fixed_prepolicy_candidate&~d.bassin_potential&~d.department_qualifies&d.epci_2023.isin(e.index[keep_e])].copy()
        else:
            keep_e=e.median_income2020.le(21270)
            selected=d[d.fixed_prepolicy_candidate&~d.bassin_potential&~d.department_qualifies&d.epci_2023.isin(e.index[keep_e])].copy()
        a=selected.groupby('epci_2023').agg(sample_population2020=('P20_POP','sum'),sample_communes=('commune_code','size'),
                initial_eligible_communes=('listed_initial2024','sum'))
        z=e.join(a,how='inner').copy()
        z['selected_population_share']=z.sample_population2020/z.population_2020
        z['legal_assignment_fraction']=z.initial_eligible_communes/z.sample_communes
        income_design=not design.startswith('D')
        z['score']=(z.median_income2020-cuts['epci_income']) if income_design else (z.density_2020-cuts['epci_density'])
        z['instrument_eligible']=z.score.le(0)
        z['design']=design
        z.to_csv(OUT/('rd_candidates_'+design+'.csv'))
        selected['design']=design;legal_candidates.append(selected[['design','epci_2023','commune_code','P20_POP','listed_initial2024']])
        for h in ([500,750,1000,1500] if income_design else [10,15,20,30]):
            q=z[z.score.abs().lt(h)] # endpoints have zero triangular weight
            left=q[q.score.le(0)];right=q[q.score.gt(0)]
            conflicts=q[(q.legal_assignment_fraction-q.instrument_eligible.astype(int)).abs().gt(1e-12)]
            support.append({'design':design,'bandwidth':h,'eligible_side_epci':len(left),'ineligible_side_epci':len(right),
                'eligible_distinct_scores':left.score.nunique(),'ineligible_distinct_scores':right.score.nunique(),
                'cutoff_ties':int(q.score.eq(0).sum()),'nearest_eligible_score':float(left.score.max()) if len(left) else None,
                'nearest_ineligible_score':float(right.score.min()) if len(right) else None,
                'assignment_conflicting_epci':len(conflicts),'sample_population':float(q.sample_population2020.sum()),
                'sample_communes':int(q.sample_communes.sum()),'unique_departments':len(set('|'.join(q.department_members).split('|'))-set([''])),
                'minimum_numerical_support':min(len(left),len(right))>=20 and min(left.score.nunique(),right.score.nunique())>=15,
                'sharp_assignment_consistent':len(conflicts)==0})
    pd.concat(legal_candidates,ignore_index=True).to_csv(OUT/'rd_candidate_communes.csv',index=False)
    pd.DataFrame(support).to_csv(REP/'rd_assignment_only_support.csv',index=False)
    sources=['assignment2024_income.csv','assignment2024_commune_population_area.csv','assignment2024_territory_indicators.csv',
             'bassin2022_composition.csv','commune_treatment.csv','frr_2024_codes_verified.csv']
    audit={'date':'2026-10-04','research_outcomes_read':False,'cutoffs_exact_reconstructed':cuts,
           'cutoffs_density_published_rounded':{'epci':63.57,'bassin':70.84},'metropolitan_communes':len(d),
           'path_audit_counts':d.assignment_audit_status.value_counts().to_dict(),
           'listed_without_possible_path':d.loc[d.assignment_audit_status.eq('listed_without_reconstructed_possible_path'),'commune_code'].tolist(),
           'mandatory_missing_from_list':d.loc[d.assignment_audit_status.eq('mandatory_path_missing_from_list'),'commune_code'].tolist(),
           'isolated_commune_unknown_income':d.loc[d.isolated_A_income_unknown,'commune_code'].tolist(),
           'rd_support':support,'source_sha256':{n:sha(OUT/n) for n in sources},
           'discretionary_bassin_proposal_observed':False,'exact_mountain_population_share_observed':False,
           'mountain_rule':'Any covered or geographically unknown member excludes income candidates; density candidates share the base density condition.',
           'causal_clearance':False,'HAL_clearance':False}
    (REP/'assignment2024_reconstruction.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'cutoffs':cuts,'paths':audit['path_audit_counts'],'support':support},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
