"""Official 2020/COG2023 assignment inputs, never outcome-dependent.

Income medians are official at the requested level; they are not aggregated
from commune medians. Population and area can be summed across whole communes.
"""
from pathlib import Path
import hashlib
import json
import zipfile
import pandas as pd
from excel_utils import read_values

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/assignment2024'


def main():
    income_zip = RAW / 'insee_filosofi2020_geog2023_csv.zip'
    population_zip = RAW / 'base-cc-serie-historique-2020_csv.zip'
    composition_file = ROOT / 'data/raw/epci_2023/Intercommunalite_Metropole_au_01-01-2023.xlsx'
    members = read_values(composition_file,sheet_name='Composition_communale',header=5,dtype=str)
    assert members.CODGEO.is_unique
    real_epci = read_values(composition_file,sheet_name='EPCI',header=5,dtype=str)
    real_epci = real_epci[real_epci.NATURE_EPCI!='ZZ']
    metro_members = members[members.DEP.str.len()==2]
    metro_epci = set(metro_members.EPCI)&set(real_epci.EPCI)
    incomes = []
    with zipfile.ZipFile(income_zip) as z:
        for level in ['COM','EPCI','DEP','BV2022']:
            table = f'cc_filosofi_2020_{level}.csv'
            df = pd.read_csv(z.open(table),sep=';',dtype=str,usecols=['CODGEO','MED20'])
            assert df.CODGEO.is_unique
            if level=='COM':
                df = df[df.CODGEO.isin(set(members.CODGEO))].copy()
            out = df.rename(columns={'CODGEO':'code','MED20':'med2020'})
            out['med2020'] = pd.to_numeric(out.med2020,errors='coerce')
            out['level'] = level
            out['metadataGeography'] = '2023-01-01'
            out['income_reference_year'] = 2020
            out['source_table'] = table
            out['source_variable'] = 'MED20'
            out['income_unknown'] = out.med2020.isna()
            incomes.append(out)
            (RAW/'filosofi_tables').mkdir(exist_ok=True)
            for entry in [table,'meta_'+table]:
                (RAW/'filosofi_tables'/entry).write_bytes(z.read(entry))
    income = pd.concat(incomes,ignore_index=True)
    income = income[['level','code','med2020','metadataGeography','income_reference_year','source_table','source_variable','income_unknown']]
    income.to_csv(ROOT/'data/processed/assignment2024_income.csv',index=False,encoding='utf-8')
    with zipfile.ZipFile(population_zip) as z:
        population = pd.read_csv(z.open('base-cc-serie-historique-2020.CSV'),sep=';',dtype=str,
                                 usecols=['CODGEO','P20_POP','SUPERF'])
        (RAW/'meta_base-cc-serie-historique-2020.CSV').write_bytes(z.read('meta_base-cc-serie-historique-2020.CSV'))
    assert population.CODGEO.is_unique
    population['P20_POP'] = pd.to_numeric(population.P20_POP,errors='coerce')
    population['SUPERF'] = pd.to_numeric(population.SUPERF,errors='coerce')
    # The raw historical file includes 45 municipal arrondissements; restrict
    # to official commune membership before any population/area summation.
    commune = members[['CODGEO','DEP','EPCI']].merge(population,on='CODGEO',how='left',validate='1:1')
    commune = commune.rename(columns={'CODGEO':'commune_code','DEP':'department','EPCI':'epci_2023'})
    commune['P20_POP'] = commune.P20_POP.astype('Int64')
    commune['metadataGeography'] = '2023-01-01'
    commune['population_reference_year'] = 2020
    commune['source_table'] = 'base-cc-serie-historique-2020.CSV'
    commune['is_actual_epci'] = commune.epci_2023.isin(set(real_epci.EPCI))
    commune['density2020'] = commune.P20_POP/commune.SUPERF
    commune.to_csv(ROOT/'data/processed/assignment2024_commune_population_area.csv',index=False,encoding='utf-8')
    metro = commune[commune.department.str.len()==2].copy()
    assert metro.P20_POP.notna().all() and metro.SUPERF.gt(0).all()
    basins = pd.read_csv(ROOT/'data/raw/legal/bv2022_composition_cog2023_extracted.csv',dtype=str)
    assert basins.commune_code.is_unique
    metro = metro.merge(basins[['commune_code','bassin_2022_cog2023']],on='commune_code',how='left',validate='1:1')
    assert metro.bassin_2022_cog2023.notna().all()
    results = {}
    density_tables = []
    for level,key,subset,official_density,official_income in [
        ('EPCI','epci_2023',metro[metro.is_actual_epci],63.57,21570.0),
        ('BV2022','bassin_2022_cog2023',metro,70.84,21600.0),
        ('DEP','department',metro,None,21665.0),
    ]:
        grouped = subset.groupby(key).agg(P20_POP=('P20_POP','sum'),SUPERF=('SUPERF','sum'),n_communes=('commune_code','size')).reset_index().rename(columns={key:'code'})
        grouped['density2020'] = grouped.P20_POP/grouped.SUPERF
        grouped['level'] = level
        grouped['metadataGeography'] = '2023-01-01'
        grouped = grouped.merge(income[income.level==level][['code','med2020']],on='code',how='left',validate='1:1')
        median_density = float(grouped.density2020.median())
        known = grouped.med2020.dropna()
        results[level] = {
            'n_units':len(grouped),'n_communes':int(grouped.n_communes.sum()),
            'income_known':int(grouped.med2020.notna().sum()),'income_missing':int(grouped.med2020.isna().sum()),
            'density_median_full_precision':median_density,'official_density_median_rounded':official_density,
            'density_median_rounds_to_official':round(median_density,2)==official_density if official_density is not None else None,
            'income_median':float(known.median()),'official_income_median':official_income,
            'income_median_matches_official':float(known.median())==official_income,
            'income_q75_linear':float(known.quantile(.75)),
        }
        if level=='EPCI':
            results[level]['official_income_q75']=22822.5
            results[level]['income_q75_matches_official']=float(known.quantile(.75))==22822.5
        if level=='DEP':
            eligible = grouped[(grouped.density2020<35)&(grouped.med2020<=21665.0)]
            results[level]['department_criterion_eligible_codes']=eligible.code.tolist()
            results[level]['department_criterion_n']=len(eligible)
        density_tables.append(grouped)
    territories = pd.concat(density_tables,ignore_index=True)
    territories.to_csv(ROOT/'data/processed/assignment2024_geographic_density_income.csv',index=False,encoding='utf-8')
    interface = territories.rename(columns={'P20_POP':'population_2020','SUPERF':'area_km2','density2020':'density_2020','med2020':'median_income2020'})
    interface[['level','code','population_2020','area_km2','density_2020','median_income2020','n_communes','metadataGeography']].to_csv(ROOT/'data/processed/assignment2024_territory_indicators.csv',index=False,encoding='utf-8')
    summary = {
        'observation_year_population':2020,'observation_year_income':2020,'geography':'2023-01-01',
        'income_source_page_publication_date':'2023-04-24','population_area_source_publication_date':'2023-06-27',
        'legal_data_available_cutoff':'2023-07-01','results':results,
        'income_rows':len(income),'income_unknown_rows':int(income.income_unknown.sum()),
        'canonical_commune_rows':len(commune),'metropolitan_commune_rows':len(metro),
        'nonmetropolitan_population_missing_communes':int(commune.P20_POP.isna().sum()),
        'raw_municipal_arrondissements_omitted':int((~population.CODGEO.isin(members.CODGEO)).sum()),
        'special_no_epci_communes':metro[~metro.is_actual_epci].commune_code.tolist(),
        'missing_real_metropolitan_epci_income':sorted(metro_epci-set(income[income.level=='EPCI'].code)),
        'income_aggregation_rule':'Use official MED20 separately at each level; never average commune medians.',
        'density_aggregation_rule':'Sum P20_POP and SUPERF over official whole-commune 2023 membership; density=sum population/sum area.',
        'input_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [income_zip,population_zip,composition_file,ROOT/'data/raw/legal/bv2022_composition_cog2023_extracted.csv']},
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (ROOT/'reports/review_C_assignment_input_checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
