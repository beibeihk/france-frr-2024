"""Official SIRENE projections and interval joins. Never read names or street addresses."""
from pathlib import Path
import sys,json,time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.vendor'))
import duckdb,pandas as pd

def sqlpath(p):return str(p).replace('\\','/').replace("'","''")

def construct():
 p=ROOT/'data/raw';out=ROOT/'data/intermediate';out.mkdir(exist_ok=True)
 meta=ROOT/'data/processed/commune_treatment.csv'
 if not meta.exists():raise RuntimeError('Final official treatment audit must precede outcome construction.')
 communes=pd.read_csv(meta,dtype={'commune_code':str,'epci_2023':str,'epci_2024':str})
 stable=communes[communes.analysis_stable.astype(str).str.lower().eq('true')][['commune_code']]
 c=duckdb.connect(str(out/'analysis.duckdb'))
 c.execute("SET memory_limit='6GB'")
 c.execute('SET threads=6')
 c.execute(f"SET temp_directory='{sqlpath(out/'spill')}'")
 c.register('stable_communes',stable)
 def run(label,sql):
  print(label,flush=True);start=time.time();c.execute(sql);print(f'{label}: {time.time()-start:.1f}s',flush=True)
 E=sqlpath(p/'stock-stocketablissement-parquet.parquet')
 EH=sqlpath(p/'stock-stocketablissementhistorique-parquet.parquet')
 U=sqlpath(p/'stock-stockunitelegale-parquet.parquet')
 UH=sqlpath(p/'stock-stockunitelegalehistorique-parquet.parquet')
 S=sqlpath(p/'stock-stocketablissementlienssuccession-parquet.parquet')
 DUP=sqlpath(p/'stock-stockdoublons-parquet.parquet')
 run('Project establishment register',f"""
 CREATE OR REPLACE TABLE establishments AS
 SELECT e.siret,e.siren,e.nic,e.codeCommuneEtablissement AS commune_code,
 TRY_CAST(e.dateCreationEtablissement AS DATE) AS creation_date,
 e.statutDiffusionEtablissement AS diffusion,
 e.etatAdministratifEtablissement AS current_state,
 e.trancheEffectifsEtablissement AS current_band,
 e.anneeEffectifsEtablissement AS band_year
 FROM read_parquet('{E}') e JOIN stable_communes s ON s.commune_code=e.codeCommuneEtablissement
 WHERE e.siren NOT IN (SELECT sirenDoublon FROM read_parquet('{DUP}') WHERE sirenDoublon IS NOT NULL);
 """)
 run('Creation dates and status at birth',f"""
 CREATE OR REPLACE TABLE births AS
 SELECT e.*,h.etatAdministratifEtablissement AS state_at_creation,
 h.activitePrincipaleEtablissement AS naf_at_creation,
 h.nomenclatureActivitePrincipaleEtablissement AS naf_version,
 h.caractereEmployeurEtablissement AS employer_at_creation,
 TRY_CAST(h.dateDebut AS DATE) AS historical_start,
 TRY_CAST(h.dateFin AS DATE) AS historical_end
 FROM establishments e LEFT JOIN read_parquet('{EH}') h
 ON e.siret=h.siret AND TRY_CAST(h.dateDebut AS DATE)<=e.creation_date
 AND coalesce(TRY_CAST(h.dateFin AS DATE),DATE '9999-12-31')>=e.creation_date
 WHERE e.creation_date BETWEEN DATE '2019-01-01' AND DATE '2026-06-30';
 """)
 dup=c.sql('SELECT count(*)-count(DISTINCT siret) FROM births').fetchone()[0]
 if dup:raise RuntimeError(f'Overlapping birth intervals: {dup}')
 run('Legal-unit creation and historical headquarters',f"""
 CREATE OR REPLACE TABLE unit_births AS
 SELECT u.siren,TRY_CAST(u.dateCreationUniteLegale AS DATE) AS creation_date,
 e.commune_code,h.categorieJuridiqueUniteLegale AS legal_category_at_creation,
 h.nicSiegeUniteLegale AS historical_headquarters_nic
 FROM read_parquet('{U}') u
 JOIN read_parquet('{UH}') h ON u.siren=h.siren
 AND TRY_CAST(h.dateDebut AS DATE)<=TRY_CAST(u.dateCreationUniteLegale AS DATE)
 AND coalesce(TRY_CAST(h.dateFin AS DATE),DATE '9999-12-31')>=TRY_CAST(u.dateCreationUniteLegale AS DATE)
 JOIN establishments e ON u.siren=e.siren AND h.nicSiegeUniteLegale=e.nic
 AND e.creation_date<=TRY_CAST(u.dateCreationUniteLegale AS DATE)
 WHERE TRY_CAST(u.dateCreationUniteLegale AS DATE) BETWEEN DATE '2019-01-01' AND DATE '2026-06-30';
 """)
 dup=c.sql('SELECT count(*)-count(DISTINCT siren) FROM unit_births').fetchone()[0]
 if dup:raise RuntimeError(f'Overlapping unit birth intervals: {dup}')
 run('Succession links for entry interpretation',f"""
 CREATE OR REPLACE TABLE succession_flags AS
 SELECT s.siretEtablissementSuccesseur AS siret,
 bool_or(s.continuiteEconomique) AS continuity,
 bool_or(s.transfertSiege) AS headquarters_transfer
 FROM read_parquet('{S}') s JOIN births b ON b.siret=s.siretEtablissementSuccesseur
 AND TRY_CAST(s.dateLienSuccession AS DATE)=b.creation_date
 GROUP BY 1;
 """)
 run('Aggregate administrative entries',"""
 CREATE OR REPLACE TABLE monthly_entries AS
 SELECT b.commune_code,date_trunc('month',b.creation_date)::DATE AS month,
 count(*) AS establishment_births,
 count(*) FILTER(WHERE b.employer_at_creation='O' AND b.state_at_creation='A') AS employer_births,
 count(*) FILTER(WHERE b.employer_at_creation IN ('O','N') AND b.state_at_creation='A') AS known_employer_births,
 count(*) FILTER(WHERE b.naf_at_creation IS NULL OR b.naf_version IS DISTINCT FROM 'NAFRev2') AS unknown_naf_births,
 count(*) FILTER(WHERE coalesce(s.continuity,false)=false) AS births_without_recorded_continuity,
 count(*) FILTER(WHERE s.continuity) AS recorded_continuity_births,
 count(*) FILTER(WHERE b.naf_version='NAFRev2' AND TRY_CAST(substr(b.naf_at_creation,1,2) AS INT) BETWEEN 45 AND 47) AS commerce,
 count(*) FILTER(WHERE b.naf_version='NAFRev2' AND TRY_CAST(substr(b.naf_at_creation,1,2) AS INT) IN (55,56)) AS accommodation_food,
 count(*) FILTER(WHERE b.naf_version='NAFRev2' AND TRY_CAST(substr(b.naf_at_creation,1,2) AS INT) BETWEEN 41 AND 43) AS construction,
 count(*) FILTER(WHERE b.naf_version='NAFRev2' AND TRY_CAST(substr(b.naf_at_creation,1,2) AS INT) BETWEEN 10 AND 33) AS manufacturing,
 count(*) FILTER(WHERE b.naf_version='NAFRev2' AND TRY_CAST(substr(b.naf_at_creation,1,2) AS INT) BETWEEN 69 AND 75) AS professional_services,
 count(*) FILTER(WHERE b.naf_version='NAFRev2' AND TRY_CAST(substr(b.naf_at_creation,1,2) AS INT)=86) AS health,
 count(*) FILTER(WHERE b.naf_version='NAFRev2' AND TRY_CAST(substr(b.naf_at_creation,1,2) AS INT) IN (95,96)) AS proximity_services
 FROM births b LEFT JOIN succession_flags s USING(siret) GROUP BY 1,2;
 CREATE OR REPLACE TABLE monthly_units AS
 SELECT commune_code,date_trunc('month',creation_date)::DATE AS month,count(*) AS legal_unit_births,
 count(*) FILTER(WHERE legal_category_at_creation='1000') AS individual_births
 FROM unit_births GROUP BY 1,2;
 """)
 run('Administrative closure transitions',f"""
 CREATE OR REPLACE TABLE monthly_closures AS
 WITH h AS (
 SELECT siret,dateDebut,etatAdministratifEtablissement,
 lag(etatAdministratifEtablissement) OVER(PARTITION BY siret ORDER BY TRY_CAST(dateDebut AS DATE)) AS previous_state
 FROM read_parquet('{EH}') WHERE siret IN (SELECT siret FROM establishments))
 SELECT e.commune_code,date_trunc('month',TRY_CAST(h.dateDebut AS DATE))::DATE AS month,
 count(*) AS closure_events
 FROM h JOIN establishments e USING(siret)
 WHERE h.etatAdministratifEtablissement='F' AND h.previous_state='A'
 AND TRY_CAST(h.dateDebut AS DATE) BETWEEN DATE '2019-01-01' AND DATE '2026-06-30'
 GROUP BY 1,2;
 """)
 run('Fixed balanced commune-month panel',"""
 CREATE OR REPLACE TABLE monthly_panel AS
 SELECT c.commune_code,t.month::DATE AS month,
 coalesce(e.establishment_births,0) AS establishment_births,
 coalesce(u.legal_unit_births,0) AS legal_unit_births,
 coalesce(u.individual_births,0) AS individual_births,
 coalesce(e.employer_births,0) AS employer_births,
 coalesce(e.known_employer_births,0) AS known_employer_births,
 coalesce(e.unknown_naf_births,0) AS unknown_naf_births,
 coalesce(e.births_without_recorded_continuity,0) AS births_without_recorded_continuity,
 coalesce(e.recorded_continuity_births,0) AS recorded_continuity_births,
 coalesce(e.commerce,0) AS commerce,coalesce(e.accommodation_food,0) AS accommodation_food,
 coalesce(e.construction,0) AS construction,coalesce(e.manufacturing,0) AS manufacturing,
 coalesce(e.professional_services,0) AS professional_services,coalesce(e.health,0) AS health,
 coalesce(e.proximity_services,0) AS proximity_services,
 coalesce(f.closure_events,0) AS establishment_closures,
 coalesce(e.establishment_births,0)-coalesce(f.closure_events,0) AS registration_minus_closure_balance
 FROM stable_communes c CROSS JOIN generate_series(DATE '2019-01-01',DATE '2026-06-01',INTERVAL '1 month') t(month)
 LEFT JOIN monthly_entries e ON c.commune_code=e.commune_code AND t.month=e.month
 LEFT JOIN monthly_units u ON c.commune_code=u.commune_code AND t.month=u.month
 LEFT JOIN monthly_closures f ON c.commune_code=f.commune_code AND t.month=f.month;
 """)
 c.execute(f"COPY monthly_panel TO '{sqlpath(ROOT/'data/processed/monthly_panel.parquet')}' (FORMAT PARQUET, COMPRESSION ZSTD)")
 quality={
 'stock_date':'2026-09-30','analysis_start':'2019-01','analysis_end':'2026-06',
 'birth_records':c.sql('SELECT count(*) FROM births').fetchone()[0],
 'births_with_historical_interval':c.sql('SELECT count(*) FROM births WHERE historical_start IS NOT NULL').fetchone()[0],
 'births_known_employer':c.sql("SELECT count(*) FROM births WHERE employer_at_creation IN ('O','N')").fetchone()[0],
 'births_with_partial_diffusion':c.sql("SELECT count(*) FROM births WHERE diffusion='P'").fetchone()[0],
 'unit_birth_records_located_at_historical_headquarters':c.sql('SELECT count(*) FROM unit_births').fetchone()[0],
 'panel_rows':c.sql('SELECT count(*) FROM monthly_panel').fetchone()[0],
 'panel_communes':len(stable)}
 (ROOT/'reports/data_quality.json').write_text(json.dumps(quality,indent=2),encoding='utf8')
 print(json.dumps(quality),flush=True)
 c.close()

if __name__=='__main__':construct()
