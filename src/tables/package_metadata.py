"""Preserve source provenance and make review-only metadata without fabricating a deposit."""
from pathlib import Path
import csv,json,hashlib,shutil,platform,importlib.metadata,sys
ROOT=Path(__file__).resolve().parents[2]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def assignment_source_rows():
 """Index exact public assignment inputs; never invent absent retrieval dates."""
 raw=ROOT/'data/raw/assignment2024'
 child_log=json.loads((raw/'source_download_log.json').read_text(encoding='utf8'))
 parent_log=json.loads((raw/'official_download_manifest.json').read_text(encoding='utf8'))
 log=child_log+parent_log
 def retrieved(p,url):
  for record in log:
   filename=record.get('file',record.get('filename',''))
   if filename==p.name and record.get('url',record.get('source_url'))==url and record.get('sha256')==digest(p):
    return record.get('retrieved_at_utc',record.get('accessed_utc',''))
  return ''
 license_url='https://www.etalab.gouv.fr/licence-ouverte-open-licence'
 sources=[
  ('insee_filosofi2020_geog2023_csv.zip','https://www.insee.fr/fr/statistiques/fichier/6692392/base-cc-filosofi-2020_CSV.zip','INSEE','2020','2023-01-01','2023-04-24',
   'MED20, native COM/EPCI/BV2022/DEP medians; exact initial income thresholds reproduced; never aggregate commune medians.'),
  ('base-cc-serie-historique-2020_csv.zip','https://www.insee.fr/fr/statistiques/fichier/7632565/base-cc-serie-historique-2020_csv.zip','INSEE','2020','2023-01-01','2023-06-27',
   'P20_POP and SUPERF; exact initial density medians reproduced; exclude 45 municipal arrondissements from whole-commune aggregation.'),
  ('mountain_cog2022.xlsx','https://static.data.gouv.fr/resources/communes-de-la-loi-montagne-au-code-officiel-geographique-cog-2020-2022/20220323-152301/dgaln-icapp-sidauh-opendata-loi-montagne-1985-cog-2022.xlsx','DGALN-SIDAUH / Ministère de la Cohésion des territoires','not applicable: legal mountain zoning','2022-01-01','',
   'Resource updated2022-03-23, created2022-03-10; publication date null in official metadata. Loi Montagne1985 any/partial coverage; not massif geography; population inside classified parts unobserved.'),
 ]
 result=[]
 for filename,url,publisher,year,geography,published,notes in sources:
  p=raw/filename
  timestamp=retrieved(p,url)
  result.append({'path':p.relative_to(ROOT).as_posix(),'source_url':url,'publisher':publisher,'sha256':digest(p),'size_bytes':p.stat().st_size,
   'license':'Licence Ouverte / Open Licence 2.0','license_url':license_url,'retrieval':'http_binary','required_rebuild':'true','verified':'true',
   'source_observation_year':year,'source_geography':geography,'publication_date':published,'retrieved_at_utc':timestamp,
   'notes':notes+(' Retrieval UTC was not recorded in the preserved download logs; left blank.' if not timestamp else '')})
 p=raw/'senat_debate_2023_11_26.pdf'
 dest=ROOT/'docs/sources/assignment2024'/p.name
 dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
 url='https://www.senat.fr/cra/s20231126/s20231126.pdf'
 result.append({'path':dest.relative_to(ROOT).as_posix(),'source_url':url,'publisher':'Sénat','sha256':digest(dest),'size_bytes':dest.stat().st_size,
  'license':'Official parliamentary record; preserve attribution; resource-specific license not verified','license_url':'','retrieval':'http_binary',
  'required_rebuild':'false','verified':'true','source_observation_year':'not applicable: legislative statement','source_geography':'not applicable',
  'publication_date':'2023-11-26','retrieved_at_utc':retrieved(p,url),
  'notes':'Optional source-year evidence: minister specifies recensement2020/Filosofi2020, PDF page66 (printed63); not an assignment microdata input.'})
 return result

def main():
 rows=[]
 sirene=json.loads((ROOT/'data/external/sirene_download_manifest.json').read_text(encoding='utf8'))
 for r in sirene:
  if not r['relative_path'].endswith('.parquet'):continue
  rows.append({'path':r['relative_path'].replace('\\','/'),'source_url':r['url'],'publisher':'INSEE','sha256':r['sha256'],'size_bytes':r['size_bytes'],
   'license':r['license'],'retrieval':'http_binary','required_rebuild':'true','verified':'true','notes':'Exact 2026-10-01 release; stock 2026-09-30; resource redirect may change later.'})
 z=json.loads((ROOT/'data/external/zoning_manifest.json').read_text(encoding='utf8'))
 needed={'frr_2025.xlsx','zrr_2021.xls','communes_cog2026.csv','movements_cog2026.csv','communes_history_cog2026.csv','communes_2024_5m.geojson.gz','epci_2023.zip','epci_2024.zip'}
 for r in z:
  if r['status_code']!=200:continue
  p=ROOT/'data/raw'/r['file']
  rows.append({'path':p.relative_to(ROOT).as_posix(),'source_url':r['url'],'publisher':'French public institution','sha256':r['sha256'],'size_bytes':r['size_bytes'],
   'license':('ODbL1.0; attribution; derived geographic databases share alike' if r['file']=='communes_2024_5m.geojson.gz' else 'Source-specific official terms; attribution required'),
   'license_url':('https://opendatacommons.org/licenses/odbl/1-0/' if r['file']=='communes_2024_5m.geojson.gz' else ''),
   'retrieval':'http_binary','required_rebuild':str(r['file'] in needed).lower(),'verified':'true','notes':'Official source; failed discovery URLs excluded.'})
 pop=json.loads((ROOT/'data/external/population_manifest.json').read_text())
 rows.append({'path':'data/raw/population_2021.xlsx','source_url':pop['url'],'publisher':'INSEE','sha256':pop['sha256'],'size_bytes':pop['size_bytes'],'license':'INSEE public data reuse terms',
  'retrieval':'http_binary','required_rebuild':'true','verified':'true','notes':'Population municipale 2021, effective Jan2024, COG2023.'})
 bv=ROOT/'data/raw/legal/BV2022_au_01-01-2023.zip'
 rows.append({'path':bv.relative_to(ROOT).as_posix(),'source_url':'https://www.insee.fr/fr/statistiques/fichier/6676988/BV2022_au_01-01-2023.zip','publisher':'INSEE','sha256':digest(bv),'size_bytes':bv.stat().st_size,
  'license':'INSEE public data reuse terms','retrieval':'http_binary','required_rebuild':'true','verified':'true','notes':'Bassin de vie 2022 in COG2023, dependence sensitivity; not proof of assignment path.'})
 docs=ROOT/'docs/sources/frr_2024';docs.mkdir(parents=True,exist_ok=True)
 for p in sorted((ROOT/'data/raw/legal').glob('frr_2024_legifrance_web_*.txt')):
  dest=docs/p.name;shutil.copyfile(p,dest)
  rows.append({'path':dest.relative_to(ROOT).as_posix(),'source_url':'https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000049746820','publisher':'Légifrance','sha256':digest(dest),'size_bytes':dest.stat().st_size,
   'license':'Official legal text; preserve attribution','retrieval':'archived_official_text','required_rebuild':'true','verified':'true','notes':'Official web-tool snapshots, line completeness checked by extraction script; HTTP page returns403 in downloader. Not a third-party assignment file.'})
 existing_paths={r['path'] for r in rows}
 for r in assignment_source_rows():
  if r['path'] not in existing_paths:rows.append(r);existing_paths.add(r['path'])
 if len(existing_paths)!=len(rows):raise RuntimeError('Duplicate source-index paths')
 fields=['path','source_url','publisher','sha256','size_bytes','license','retrieval','required_rebuild','verified','notes',
  'source_observation_year','source_geography','publication_date','retrieved_at_utc','license_url']
 with (ROOT/'data_sources.csv').open('w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
 if '--sources-only' in sys.argv:
  print('Source index generated; downstream analysis metadata untouched.',flush=True)
  return
 (ROOT/'data_dictionary.md').write_text('\n\n'.join((ROOT/p).read_text(encoding='utf8') for p in ['docs/data_dictionary.md','docs/analysis_variable_dictionary.md','docs/assignment_data_dictionary.md']),encoding='utf8')
 shutil.copyfile(ROOT/'data/raw/legal/bv2022_composition_cog2023_extracted.csv',ROOT/'data/processed/bassin2022_composition.csv')
 versions={pkg:importlib.metadata.version(pkg) for pkg in ['pandas','numpy','scipy','statsmodels','geopandas','pyarrow','matplotlib','networkx','requests','openpyxl','xlrd','shapely','beautifulsoup4','PyMuPDF']}
 versions['Python']=platform.python_version()
 (ROOT/'reports/environment_versions.json').write_text(json.dumps(versions,indent=2),encoding='utf8')
 sys.path.insert(0,str(ROOT/'.vendor'))
 import duckdb
 versions['duckdb']=duckdb.__version__
 (ROOT/'reports/environment_versions.json').write_text(json.dumps(versions,indent=2),encoding='utf8')
 (ROOT/'requirements.txt').write_text('\n'.join(pkg+'=='+v for pkg,v in versions.items() if pkg!='Python')+'\n',encoding='utf8')
 d=json.loads((ROOT/'reports/pretrend_diagnostics.json').read_text())
 existing=json.loads((ROOT/'reports/analysis_status.json').read_text()) if (ROOT/'reports/analysis_status.json').exists() else {}
 status={'status':existing.get('status','NONCAUSAL_WORKING_PAPER_FINAL_CHECKS'),
  'research_scope':'National legal eligibility reconstruction, administrative measurement and identification diagnostics; no causal policy effect claim',
  'short_pretrend_p':d['p_value'],'full_pretrend_p':d['full_2019_2023_pretrend']['p_value'],'causal_clearance':False,
  'primary_period':'2024-07 through 2024-12',
  'assignment_reconstruction':'Observed mandatory A/C and possible B/D union exactly matches initial mainland list; individual administrative reasons unobserved',
  'causal_routes':'A/B/D/E lack adequate support; V fails continuity/selection and dependence diagnostics',
  'HAL_status':existing.get('HAL_status','NOT_SUBMITTED'),
  'reason':'Noncausal scope retains all failed diagnostics; independent final reviews and technical checks are recorded separately.'}
 (ROOT/'reports/analysis_status.json').write_text(json.dumps(status,indent=2),encoding='utf8')
 print('Source index and local review package metadata generated.',flush=True)
if __name__=='__main__':main()
