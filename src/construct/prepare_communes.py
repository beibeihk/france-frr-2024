from pathlib import Path
import argparse,gzip,json,sys
import numpy as np,pandas as pd,geopandas as gpd
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/construct'))
from excel_utils import read_values

def prepare(provisional=False):
 raw=ROOT/'data/raw'; out=ROOT/'data/processed'
 latest=pd.read_excel(raw/'frr_2025.xlsx',dtype=str)
 latest.columns=['commune_code','department','commune_name','status_2025']
 assert latest.commune_code.is_unique
 zrr=pd.read_excel(raw/'zrr_2021.xls',sheet_name=0,header=5,dtype=str)
 zrr=zrr[['CODGEO','ZRR_SIMP','ZONAGE_ZRR']].rename(columns={'CODGEO':'commune_code','ZONAGE_ZRR':'zrr_2021_path'})
 zrr['prior_zrr_effects']=~zrr.zrr_2021_path.str.startswith('NC')
 d=latest.merge(zrr,on='commune_code',how='left',validate='1:1')
 verified=out/'frr_2024_codes_verified.csv'
 if verified.exists():
  frr=pd.read_csv(verified,dtype=str)
  frr=frr.rename(columns={'code_insee':'commune_code'})
  d['frr_2024']=d.commune_code.isin(frr.commune_code)
  source_status='original_2024_codes_official'
 elif provisional:
  d['frr_2024']=d.status_2025.isin(['FRR socle','FRR+'])
  source_status='PROVISIONAL_2025_CORE_PROXY_NOT_2024_ASSIGNMENT'
 else: raise RuntimeError('Original 2024 official FRR codes not yet verified. No estimation allowed.')
 d['beneficiary_2025']=d.status_2025.str.contains('bénéficiaire',case=False,na=False)
 d['partial']=d.status_2025.str.contains('partiellement',na=False)|d.zrr_2021_path.str.startswith(('P','PA','PM'),na=False)
 d['treatment_group']=np.select([
  d.prior_zrr_effects.eq(False)&d.frr_2024&~d.partial,
  d.prior_zrr_effects.eq(True)&d.frr_2024&~d.partial,
  d.prior_zrr_effects.eq(True)&d.beneficiary_2025&~d.partial,
  d.prior_zrr_effects.eq(False)&~d.frr_2024&d.status_2025.eq('Non classée')&~d.partial,
 ],['NEW_FRR','CONTINUING','FORMER_ZRR_BENEFICIARY','NEVER_TREATED'],default='EXCLUDE_UNRESOLVED_OR_PARTIAL')
 mv=pd.read_csv(raw/'movements_cog2026.csv',dtype=str)
 changed=mv[mv.DATE_EFF.ge('2017-01-01')&~mv.MOD.eq('10')]
 changed_codes=set(changed.COM_AV)|set(changed.COM_AP)
 d['administrative_change_since2017']=d.commune_code.isin(changed_codes)
 d['metropolitan']=d.department.str.len().eq(2)
 pop=read_values(raw/'population_2021.xlsx',sheet_name='Communes',header=7,dtype=str)
 pop['commune_code']=pop['Code département'].str.zfill(2)+pop['Code commune'].str.zfill(3)
 pop['population_2021']=pd.to_numeric(pop['Population municipale'],errors='coerce')
 assert pop.commune_code.is_unique
 d=d.merge(pop[['commune_code','population_2021']],on='commune_code',how='left',validate='1:1')
 for year in [2023,2024]:
  f=next((raw/f'epci_{year}').glob('*.xlsx'))
  e=read_values(f,sheet_name='Composition_communale',header=5,dtype=str)
  e=e[['CODGEO','EPCI']].rename(columns={'CODGEO':'commune_code','EPCI':f'epci_{year}'})
  d=d.merge(e,on='commune_code',how='left',validate='1:1')
 d['epci_change_2023_2024']=d.epci_2023.ne(d.epci_2024)
 d['analysis_stable']=d.metropolitan&~d.administrative_change_since2017&~d.partial&d.population_2021.gt(0)&d.epci_2023.notna()&~d.epci_change_2023_2024
 d['assignment_source_status']=source_status
 suffix='_provisional' if source_status.startswith('PROVISIONAL') else ''
 d.to_csv(out/f'commune_treatment{suffix}.csv',index=False)
 rows=[]
 for label,subset in [('all_DGCL_2025_codes',d),('stable_metropolitan',d[d.analysis_stable])]:
  for group,n in subset.treatment_group.value_counts().items():
   rows.append({'universe':label,'transition':group,'n_communes':int(n),'status':source_status})
 matrix=pd.DataFrame(rows)
 matrix.to_csv(ROOT/'tables'/f'treatment_transition_matrix{suffix}.csv',index=False)
 (ROOT/'reports'/f'treatment_audit{suffix}.md').write_text(
  '# Treatment audit\n\nSource status: '+source_status+'\n\n```text\n'+matrix.to_string(index=False)+'\n```'+
  '\n\nPrior exposure includes all retained ZRR effects (ANCT codes A/M/CM/D), not only nominally classed communes. Partial, missing and unresolved status is excluded. Main stable sample excludes all non-name COG movements since 2017 and EPCI membership changes 2023–2024. The 2025 table is used to exclude beneficiary and partial controls, never silently as an original 2024 assignment. Classification and sample choices were fixed before the original outcome analysis; rerunning this construction does not establish new independent blindness. Original FRR geography uses COG 2023; counts on the current COG are not claimed as original decree counts.\n',encoding='utf8')
 print(matrix.to_string(index=False),flush=True)
 print('Reading official IGN-derived 2024 contours',flush=True)
 with gzip.open(raw/'communes_2024_5m.geojson.gz','rt',encoding='utf8') as f:features=json.load(f)['features']
 geo=gpd.GeoDataFrame.from_features(features,crs='EPSG:4326')
 print('GEOGRAPHY FIELDS',geo.columns.tolist(),flush=True)
 code='code' if 'code' in geo else 'code_insee'
 geo=geo.rename(columns={code:'commune_code'})
 geo=geo[geo.commune_code.isin(d[d.metropolitan].commune_code)].copy()
 geo=geo.merge(d,on='commune_code',validate='1:1')
 geo=geo.to_crs(2154)
 geo['area_km2']=geo.geometry.area/1e6
 geo['density_2021']=geo.population_2021/geo.area_km2
 geo.to_parquet(out/f'commune_geography{suffix}.parquet',index=False)
 # Maps may use cartographic simplification; adjacency uses the original 5m product.
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.patches import Patch
 colors={'NEW_FRR':'#c9512c','CONTINUING':'#2b7a78','FORMER_ZRR_BENEFICIARY':'#bb9a45','NEVER_TREATED':'#dfe2e4','EXCLUDE_UNRESOLVED_OR_PARTIAL':'#7c669b'}
 fig,ax=plt.subplots(figsize=(9,9))
 gg=geo.copy();gg.geometry=gg.geometry.simplify(200)
 gg.plot(ax=ax,color=gg.treatment_group.map(colors),edgecolor='none')
 ax.set_axis_off();ax.set_title('Transitions ZRR–FRR'+(' — audit provisoire' if provisional else ''),fontsize=15)
 ax.legend(handles=[Patch(color=v,label=k) for k,v in colors.items()],loc='lower left',fontsize=8,frameon=False)
 fig.text(.08,.02,'Sources : ANCT ; DGCL ; INSEE ; IGN/data.gouv.fr. Hors territoires ultramarins.',fontsize=8)
 fig.savefig(ROOT/'results/figures'/f'transition_map{suffix}.pdf',bbox_inches='tight')
 fig.savefig(ROOT/'results/figures'/f'transition_map{suffix}.png',dpi=170,bbox_inches='tight')
 plt.close(fig)

if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--provisional',action='store_true');args=a.parse_args();prepare(args.provisional)
