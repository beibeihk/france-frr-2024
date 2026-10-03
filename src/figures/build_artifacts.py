"""Every table, plot and numerical manuscript macro is generated from outputs."""
from pathlib import Path
import json,re,sys
import numpy as np,pandas as pd,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
ROOT=Path(__file__).resolve().parents[2]
TAB=ROOT/'results/tables';FIG=ROOT/'results/figures';TEX=ROOT/'paper/generated'
TEX.mkdir(parents=True,exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
BLUE='#28648c';ORANGE='#c45b32'
NAMES={'establishment_births':'Immatriculations d’établissements','legal_unit_births':'Créations d’unités légales localisables',
 'employer_births':'Établissements employeurs actifs à la création','births_without_recorded_continuity':'Sans continuité économique enregistrée',
 'individual_births':'Entrepreneurs individuels','non_individual_unit_births':'Autres catégories juridiques',
 'establishment_closures':'Fermetures administratives A→F','registration_minus_closure_balance':'Immatriculations moins fermetures',
 'legal_cessation_events':'Cessations administratives des unités légales','establishment_reopen_events':'Réouvertures F→A'}
SECT={'commerce':'Commerce','accommodation_food':'Hébergement-restauration','construction':'Construction','manufacturing':'Industrie manufacturière',
 'professional_services':'Services professionnels','health':'Santé humaine','proximity_services':'Services de proximité'}
def read(name):return pd.read_csv(TAB/(name+'.csv'))
def esc(x):
 return str(x).replace('&',r'\&').replace('%',r'\%').replace('_',r'\_').replace('#',r'\#')
def f(x,d=3):return f'{float(x):.{d}f}'.replace('.',',') if pd.notna(x) else '—'
def pformat(x):return r'$<0{,}001$' if float(x)<.001 else f(x)
def integer(x):return f'{int(x):,}'.replace(',',r'\,')
def interval(r):return '['+f(r.ci_low)+' ; '+f(r.ci_high)+']'
def table(name,headers,rows,widths=None):
 spec=('l'+'r'*(len(headers)-1)) if widths is None else widths
 text=r'\begin{tabularx}{\linewidth}{'+spec+'}\n'+r'\toprule'+'\n'
 text+=' & '.join(map(esc,headers))+r' \\'+'\n'+r'\midrule'+'\n'
 text+='\n'.join(' & '.join(str(x) for x in row)+r' \\' for row in rows)+'\n'+r'\bottomrule'+'\n'+r'\end{tabularx}'+'\n'
 (TEX/(name+'.tex')).write_text(text,encoding='utf8')
def save(fig,name):
 fig.savefig(FIG/(name+'.pdf'),bbox_inches='tight');fig.savefig(FIG/(name+'.png'),dpi=160,bbox_inches='tight');plt.close(fig)
def date_axis(ax):
 ax.xaxis.set_major_locator(mdates.YearLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
 ax.axvspan(pd.Timestamp('2023-06-01'),pd.Timestamp('2024-06-30'),color='#b9b8ae',alpha=.17)
 ax.axvline(pd.Timestamp('2024-07-01'),color=ORANGE,lw=1.1)
 ax.grid(axis='y',alpha=.15)

def write_facts(vals):
 institution=ROOT/'reports/review_A_institutional_macro_values.json'
 if institution.exists():
  vals.update({k:integer(v) for k,v in json.loads(institution.read_text())['institutional_macro_values'].items()})
 birth=ROOT/'reports/birth_structure_quality.json'
 if birth.exists():
  b=json.loads(birth.read_text());hq={r['headquarters_category']:r['n'] for r in b['headquarters_categories']}
  ages={r['legal_age_category']:r['n'] for r in b['legal_age_categories']}
  vals.update({'HQBirthN':integer(hq['headquarters']),'NonHQBirthN':integer(hq['non_headquarters']),
   'UnknownHQN':integer(b['establishment_births']-hq['headquarters']-hq['non_headquarters']),
   'UnknownAgeN':integer(b['establishment_births']-ages['known']),'AgeFlaggedN':integer(ages['pre_1800_date_requires_verification'])})
 (TEX/'facts.tex').write_text('\n'.join('\\newcommand{\\'+k+'}{'+v+'}' for k,v in vals.items())+'\n',encoding='utf8')
 (ROOT/'reports/numerical_facts.json').write_text(json.dumps(vals,ensure_ascii=False,indent=2),encoding='utf8')

def main():
 if '--refresh-facts-only' in sys.argv:
  write_facts(json.loads((ROOT/'reports/numerical_facts.json').read_text(encoding='utf8')))
  return
 meta=pd.read_csv(ROOT/'data/processed/commune_treatment.csv',dtype={'commune_code':str},low_memory=False)
 geo=gpd.read_parquet(ROOT/'data/processed/commune_geography.parquet')
 gg=geo.copy();gg.geometry=gg.geometry.simplify(200)
 manifest={}
 for mode in ['frr','transition']:
  fig,ax=plt.subplots(figsize=(7,7))
  if mode=='frr':
   colors=np.where(gg.frr_2024,BLUE,'#e0e3e5');handles=[Patch(color=BLUE,label='Code présent dans la liste initiale de 2024'),Patch(color='#e0e3e5',label='Autre code cartographiable')]
  else:
   palettes={'NEW_FRR':ORANGE,'CONTINUING':BLUE,'FORMER_ZRR_BENEFICIARY':'#b89b48','NEVER_TREATED':'#e0e3e5','EXCLUDE_UNRESOLVED_OR_PARTIAL':'#8f7b9c'}
   labels={'NEW_FRR':'Nouvellement classée','CONTINUING':'ZRR maintenue en FRR','FORMER_ZRR_BENEFICIARY':'Ancienne ZRR bénéficiaire','NEVER_TREATED':'Jamais bénéficiaire dans les listes auditées','EXCLUDE_UNRESOLVED_OR_PARTIAL':'Statut partiel ou non résolu'}
   colors=gg.treatment_group.map(palettes);handles=[Patch(color=v,label=labels[k]) for k,v in palettes.items()]
  gg.plot(ax=ax,color=colors,edgecolor='none');ax.set_axis_off();ax.legend(handles=handles,loc='lower left',fontsize=7,frameon=False)
  fig.text(.5,.025,'Fond : Contours administratifs 2024 (data.gouv.fr), IGN AdminExpress — ODbL 1.0\nhttps://www.data.gouv.fr/datasets/contours-administratifs',ha='center',fontsize=6,color='#4b4b4b')
  save(fig,mode+'_map')
  manifest[mode+'_map']={'mapped_codes':len(gg),'mapped_initial_frr_codes':int(gg.frr_2024.sum()),'geometry':'official 2024 5m contours; 200m simplification for display only',
   'coverage':'metropolitan codes in current DGCL universe with a direct match to 2024 geometry; not the complete COG2023 decree'}
 for sample in ['broad','border']:
  z=read(sample+'_trends');z['date']=pd.to_datetime(z.month)
  fig,ax=plt.subplots(figsize=(7.1,3.5))
  ax.plot(z.date,z.treated_per1000,label='Nouvelles communes FRR',color=BLUE,lw=1.2)
  ax.plot(z.date,z.control_per1000,label='Communes témoins',color=ORANGE,lw=1.2)
  ax.set_ylabel('Immatriculations / 1 000 habitants / mois');date_axis(ax);ax.legend(loc='upper left',fontsize=8,frameon=False)
  save(fig,sample+'_trends')
 for name in ['broad_event_study','border_event_study','season_adjusted_event_study']:
  z=read(name);x=pd.to_datetime(z.month)
  fig,ax=plt.subplots(figsize=(7.1,3.5));ax.plot(x,z.coefficient,color=BLUE,lw=1)
  ax.fill_between(x,z.ci_low,z.ci_high,color=BLUE,alpha=.18)
  ax.axhline(0,color='black',lw=.7);ax.set_ylabel('Contraste / 1 000 habitants / mois');date_axis(ax)
  save(fig,name)
 s=read('sector_estimates');fig,ax=plt.subplots(figsize=(7.1,3.8))
 y=np.arange(len(s));ax.errorbar(s.coefficient,y,xerr=[s.coefficient-s.ci_low,s.ci_high-s.coefficient],fmt='o',color=BLUE,capsize=3)
 ax.set_yticks(y,[SECT[x] for x in s.sector]);ax.invert_yaxis();ax.axvline(0,color='black',lw=.7)
 ax.set_xlabel('Contraste / 1 000 habitants / mois — IC ponctuels à 95 %');ax.grid(axis='x',alpha=.15);save(fig,'sector_heterogeneity')
 (ROOT/'reports/figure_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
 # Core tables
 trans=pd.read_csv(ROOT/'tables/treatment_transition_matrix.csv')
 order=['NEW_FRR','CONTINUING','FORMER_ZRR_BENEFICIARY','NEVER_TREATED','EXCLUDE_UNRESOLVED_OR_PARTIAL']
 labels=['Non-ZRR → FRR initiale','ZRR → FRR initiale','ZRR → maintien des effets','Non-ZRR → non-FRR','Partiel ou non résolu']
 rows=[]
 for code,label in zip(order,labels):
  r=trans[trans.transition.eq(code)].set_index('universe').n_communes
  rows.append([label,integer(r['all_DGCL_2025_codes']),integer(r['stable_metropolitan'])])
 table('transitions',['Transition','Codes courants DGCL','Métropole stable'],rows,'Xrr')
 summary=read('summary_statistics')
 table('summary',['Groupe','Communes','Population','Densité','Entrées préalables'],[[{'NEW_FRR':'Nouvelle FRR','NEVER_TREATED':'Témoin'}[r.treatment_group],integer(r.communes),f(r.population_mean,0),f(r.density_mean,1),f(r.pre_entries_mean)] for r in summary.itertuples()],'Xrrrr')
 balance=read('covariate_balance');pairs=pd.read_csv(ROOT/'data/processed/border_pairs.csv',dtype=str)
 gm=geo.set_index('commune_code');mm=meta.set_index('commune_code')
 panel=pd.read_parquet(ROOT/'data/processed/monthly_panel.parquet')
 panel['month']=pd.to_datetime(panel.month)
 pre=panel[panel.month.dt.year.le(2022)&panel.month.dt.month.ge(7)].groupby('commune_code').establishment_births.mean()
 mm['pre_entries_per1000']=pre.reindex(mm.index)*1000/mm.population_2021
 mm['density_2021']=gm.density_2021.reindex(mm.index)
 for v in ['population_2021','density_2021','pre_entries_per1000']:
  a=mm.loc[pairs.treated_code,v];b=mm.loc[pairs.control_code,v];sd=np.sqrt((a.var()+b.var())/2)
  balance=pd.concat([balance,pd.DataFrame([{'sample':'border','variable':v,'treated_mean':a.mean(),'control_mean':b.mean(),'standardised_difference':(a.mean()-b.mean())/sd}])],ignore_index=True)
 balance.to_csv(TAB/'covariate_balance_all.csv',index=False)
 vl={'population_2021':'Population fixe','density_2021':'Densité fixe','pre_entries_per1000':'Entrées préalables / 1 000'}
 table('balance',['Échantillon / variable','FRR','Témoin','Écart standardisé'],[[esc(r.sample+' : '+vl[r.variable]),f(r.treated_mean,2),f(r.control_mean,2),f(r.standardised_difference,2)] for r in balance.itertuples()],'Xrrr')
 broad=read('broad_did').iloc[0];matched=read('matched_did').query("clustering=='EPCI_department_joint_components'").iloc[0]
 border=read('main_border_estimates').query("clustering=='EPCI_components' & outcome=='establishment_births' & scale=='per1000'").iloc[0]
 table('main_comparisons',['Comparaison','Contraste','Écart type','IC à 95 %','p'],[
  ['Large',f(broad.coefficient),f(broad.se),interval(broad),f(broad.p_value)],
  ['Appariée dans le département',f(matched.coefficient),f(matched.se),interval(matched),f(matched.p_value)],
  ['Frontières adjacentes',f(border.coefficient),f(border.se),interval(border),f(border.p_value)]],'Xrrrr')
 main=read('main_border_estimates').query("clustering=='EPCI_components'")
 table('border_outcomes',['Variable (échelle)','Contraste','Écart type','IC à 95 %'],[[esc(NAMES[r.outcome]+(' — log(1+nombre)' if r.scale=='log1p' else ' / 1 000')),f(r.coefficient),f(r.se),interval(r)] for r in main.itertuples()],'Xrrr')
 sec=read('sector_estimates')
 table('sectors',['Secteur','Contraste','Écart type','p brut','p Holm'],[[SECT[r.sector],f(r.coefficient),f(r.se),f(r.p_value),f(r.p_holm)] for r in sec.itertuples()],'Xrrrr')
 robust=read('robustness');rl={'placebo_2021_07':'Fausse réforme : juillet 2021','placebo_2022_07':'Fausse réforme : juillet 2022','last_pre_announcement_year':'Seul second semestre 2022 en référence',
  'first_year_excluding_frr_plus':'Douze mois, hors futures FRR+','population_weighted':'Pondération par population de la paire','same_department':'Frontières dans le même département',
  'excluding_pop_25000_plus':'Deux communes sous 25 000 habitants','excluding_covid_baselines':'Seul second semestre 2019 en référence','2023_07_announcement_period_not_clean_placebo':'Juillet 2023 : période d’annonce'}
 table('robustness',['Spécification','Paires','Contraste','Écart type','p'],[[rl[r.check],integer(r.pairs),f(r.coefficient),f(r.se),pformat(r.p_value)] for r in robust.itertuples()],'Xrrrr')
 cl=read('main_border_estimates').query("outcome=='establishment_births' & scale=='per1000'")
 cl=pd.concat([cl,read('bassin_cluster_sensitivity')],ignore_index=True)
 cn={'EPCI_components':'Composantes EPCI','department_components':'Composantes département','EPCI_department_joint_components':'Composantes EPCI + département',
  'independent_pairs':'Paires indépendantes (repère)','EPCI_department_bassin_joint_components':'Composantes EPCI + département + bassin'}
 table('clustering',['Dépendance autorisée','Groupes','Écart type','IC à 95 %'],[[cn[r.clustering],integer(r.clusters),f(r.se),interval(r)] for r in cl.itertuples()],'Xrrr')
 sp=read('spatial_descriptive');sl={'treated_entries':'Côté FRR','neighbour_control_entries':'Côté témoin voisin','pair_total_entries':'Somme des deux côtés'}
 table('spatial',['Série','Pré / mois / paire','Après / mois / paire','Variation'],[[sl[r.group],f(r.pre_mean_monthly_entries_per_pair),f(r.post_mean_monthly_entries_per_pair),f(r.change)] for r in sp.itertuples()],'Xrrr')
 retention=read('cohort_retention').query("sample=='border'")
 table('retention',['Horizon / groupe / cohorte','Suivies','Inconnues','Actives (%)'],[[f'{r.horizon_months} mois / '+('FRR' if r.group=='NEW_FRR' else 'témoin')+' / '+('2019–22' if r.birth_period.startswith('2019') else '2024'),integer(r.eligible),integer(r.unknown),f(100*r.retention_known,1)] for r in retention.itertuples()],'Xrrr')
 secondary=read('secondary_estimates')
 table('secondary',['Variable administrative','Contraste','Écart type','IC à 95 %'],[[NAMES[r.outcome],f(r.coefficient),f(r.se),interval(r)] for r in secondary.itertuples()],'Xrrr')
 # Macros prevent transcription of coefficients or counts into prose.
 prediag=json.loads((ROOT/'reports/pretrend_diagnostics.json').read_text());diag=json.loads((ROOT/'reports/additional_diagnostics.json').read_text())
 quality=json.loads((ROOT/'reports/data_quality.json').read_text());ppml=read('conditional_ppml').iloc[0]
 wild=json.loads((ROOT/'reports/wild_cluster_score.json').read_text())
 vals={'BorderCoef':f(border.coefficient),'BorderLo':f(border.ci_low),'BorderHi':f(border.ci_high),'BorderSE':f(border.se),
  'BroadCoef':f(broad.coefficient),'BroadLo':f(broad.ci_low),'BroadHi':f(broad.ci_high),'MatchedCoef':f(matched.coefficient),
  'MatchedLo':f(matched.ci_low),'MatchedHi':f(matched.ci_high),'BorderPairs':integer(len(pairs)),'NewN':integer(broad.treated),'ControlN':integer(broad.controls),
  'MatchedPairs':integer(matched.pairs),'PanelN':integer(quality['panel_rows']),'CommuneN':integer(quality['panel_communes']),
  'BirthN':integer(quality['birth_records']),'ULBirthN':integer(quality['unit_birth_records_located_at_historical_headquarters']),
  'ShortPreP':f(prediag['p_value']),'SeasonPreP':f(diag['season_adjusted_full_pre']['p_value'],6),
  'AnnualPreP':f(diag['same_season_2019_2022_pre']['p_value']),'PPMLRatio':f(ppml.rate_ratio),
  'MapFRRN':integer(manifest['frr_map']['mapped_initial_frr_codes']),
  'PPMLPairs':integer(ppml.pairs_informative),'PPMLExcluded':integer(ppml.pairs_excluded_zero_or_separated),
  'WildP':f(wild['wild_restricted_cluster_t_p_value'],4)}
 write_facts(vals)
 print('Figures, 12 tables and numerical macros generated.',flush=True)

if __name__=='__main__':main()
