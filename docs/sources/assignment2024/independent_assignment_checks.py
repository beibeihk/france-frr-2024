"""Independent institutional checks. Reads no research outcomes; writes own audit only."""
from pathlib import Path
import hashlib
import importlib.util
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DEST = ROOT / 'docs/sources/assignment2024'

def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()

def main():
    pop = pd.read_csv(ROOT/'data/processed/assignment2024_commune_population_area.csv', dtype={'commune_code': str, 'department': str, 'epci_2023': str})
    inc = pd.read_csv(ROOT/'data/processed/assignment2024_income.csv', dtype={'level': str, 'code': str})
    terr = pd.read_csv(ROOT/'data/processed/assignment2024_territory_indicators.csv', dtype={'level': str, 'code': str})
    bm = pd.read_csv(ROOT/'data/processed/bassin2022_composition.csv', dtype=str)
    p = pop.merge(bm[['commune_code','bassin_2022_cog2023']], on='commune_code', validate='1:1')
    recomputed = {}
    for level, key in [('EPCI','epci_2023'),('BV2022','bassin_2022_cog2023'),('DEP','department')]:
        official = terr[terr.level.eq(level)].set_index('code')
        sums = p.groupby(key)[['P20_POP','SUPERF']].sum().reindex(official.index)
        density = sums.P20_POP/sums.SUPERF
        med = inc[inc.level.eq(level)].set_index('code').med2020.reindex(official.index)
        recomputed[level] = dict(rows=len(official), population_max_abs_difference=float((sums.P20_POP-official.population_2020).abs().max()), area_max_abs_difference=float((sums.SUPERF-official.area_km2).abs().max()), density_max_abs_difference=float((density-official.density_2020).abs().max()), income_max_abs_difference=float((med-official.median_income2020).abs().max()), density_median=float(density.median()), income_median=float(med.median()), income_q75_linear=float(med.quantile(.75)))
        assert np.allclose(sums.P20_POP, official.population_2020, rtol=0, atol=1e-8)
        assert np.allclose(sums.SUPERF, official.area_km2, rtol=0, atol=1e-8)
        assert np.allclose(density, official.density_2020, rtol=0, atol=1e-8)
        assert med.equals(official.median_income2020)
    d = pd.read_csv(ROOT/'data/processed/assignment2024_commune_paths.csv', dtype={'commune_code': str,'epci_2023': str,'bassin_2022_cog2023': str,'department':str}, low_memory=False)
    mandatory = d.eligible_A_epci | d.eligible_A_isolated_commune | d.eligible_C_department
    contingency = []
    for mandatory_flag in [False,True]:
        for b in [False,True]:
            for mountain in [False,True]:
                q=d[mandatory.eq(mandatory_flag)&d.eligible_B_potential.eq(b)&d.eligible_D_potential.eq(mountain)]
                contingency.append(dict(mandatory=mandatory_flag,B_numerically_possible=b,D_upper_bound_possible=mountain,communes=len(q),listed=int(q.listed_initial2024.sum()),not_listed=int((~q.listed_initial2024).sum())))
    q=d[~mandatory & d.eligible_B_potential & ~d.eligible_D_potential & d.listed_initial2024]
    binding_B = dict(communes=len(q),distinct_bassins=q.bassin_2022_cog2023.nunique(),distinct_EPCI=q.epci_2023.nunique(),distinct_departments=q.department.nunique(),meaning='Conditional necessary B route under original legal channels, reconstructed numeric inputs and conservative mountain coverage. Distinct bassin count is subset coverage, not an observed proposal/approval register.')
    movements=pd.read_csv(ROOT/'data/raw/movements_cog2026.csv',dtype=str)
    changes=movements[(movements.DATE_EFF>'2022-01-01')&(movements.DATE_EFF<='2023-01-01')]
    mountain=pd.read_excel(ROOT/'data/raw/assignment2024/mountain_cog2022.xlsx',sheet_name='Perimetre',header=2,dtype=str)
    covered=set(mountain.INSEE_COM.dropna())
    hist=pd.read_csv(ROOT/'data/raw/communes_history_cog2026.csv',dtype=str).fillna('')
    active2022=set(hist.loc[hist.TYPECOM.eq('COM')&hist.DATE_DEBUT.le('2022-01-01')&(hist.DATE_FIN.eq('')|hist.DATE_FIN.ge('2022-01-01')),'COM'])
    targets=changes[changes.TYPECOM_AP.eq('COM')].groupby('COM_AP').COM_AV.agg(lambda z:set(z))
    missing=[str(code) for code,old in targets.items() if old&covered and code not in covered and code in active2022]
    merger_check=dict(movement_rows=len(changes),interval='2022-01-01 < DATE_EFF <= 2023-01-01',unflagged_survivors_absorbing_a_listed_mountain_member=missing,complete_2023_mountain_population_share_recovered=False,limit='This checks published COG movements, not legal zoning changes absent from the COG file or population inside partially classified territory.')
    assert not missing
    isolated=d[~d.actual_epci][['commune_code','P20_POP','density2020','commune_income2020','eligible_A_isolated_commune','isolated_A_income_unknown','eligible_B_potential','eligible_C_department','listed_initial2024']].replace({np.nan:None}).to_dict('records')
    spec=importlib.util.spec_from_file_location('candidate_rules',DEST/'candidate_rules.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert module._and(False,None) is False and module._and(True,None) is None
    assert module._le(float('nan'),1) is None
    assert module.candidate_routes(dict(metro=True,commune_pop2020_municipal=266,isolated_L5210_1_1V=True,commune_density=443.33333333333337,commune_med20=float('nan')))['A_isolated'] is False
    sources=['src/construct/assignment2024.py','data/processed/assignment2024_commune_paths.csv','reports/assignment2024_reconstruction.json','reports/rd_assignment_only_support.csv','data/raw/movements_cog2026.csv','data/raw/communes_history_cog2026.csv','docs/sources/assignment2024/candidate_rules.py']
    result=dict(review_date='2026-10-04',research_outcomes_read=False,territory_indicator_independent_checks=recomputed,metropolitan_communes=len(d),listed_metropolitan_communes=int(d.listed_initial2024.sum()),contingency=contingency,binding_B_subset=binding_B,mountain_merger_check=merger_check,isolated_communes=isolated,source_sha256={n:sha(n) for n in sources},causal_clearance=False,HAL_clearance=False)
    (DEST/'independent_assignment_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    print(json.dumps(dict(territories=recomputed,binding_B=binding_B,mountain_merger_check=merger_check,script_sha256=result['source_sha256'][sources[0]]),ensure_ascii=False))

if __name__=='__main__':
    main()
