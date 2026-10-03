"""Validate completed internal noncausal reviews and final technical artifacts."""
from pathlib import Path
import ast,hashlib,json,re
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads((ROOT/p).read_text(encoding='utf8'))
def main():
 scripts=list((ROOT/'src').rglob('*.py'))+[ROOT/'run_pipeline.py']
 for p in scripts:ast.parse(p.read_text(encoding='utf8'))
 b=read('reports/review_B_final_scope.json');d=read('reports/review_D_final_scope.json');a=read('reports/review_A_final_scope.json')
 if not b['scientific_scope_status'].startswith('PASS_NONCAUSAL') or b['scientific_blockers'] or b['local_expression_completion_items']:raise RuntimeError('Independent scientific scope not passed')
 if not a['institutional_scope_status'].startswith('PASS_NONCAUSAL') or a['remaining_blockers']:raise RuntimeError('Independent institutional scope not passed')
 if not str(d.get('status','')).startswith('PASS_AI_FRENCH'):raise RuntimeError('French AI editor scope not passed')
 c=read('reports/review_C_assignment_paths.json');cells=read('reports/review_C_observation_checks.json')
 if c['checked_commune_column_values']!=1044480 or any(c['column_differences'].values()):raise RuntimeError('Assignment raw reconstruction differs')
 if cells['cell_observations']<20 or cells['cell_measure_discrepancies'] or cells['individual_attribute_discrepancies']:raise RuntimeError('Raw cell audit incomplete')
 claims=pd.read_csv(ROOT/'claims_audit.csv',dtype=str).fillna('');refs=pd.read_csv(ROOT/'references_verified.csv',dtype=str)
 if not claims.verified.str.lower().eq('true').all():raise RuntimeError('Unverified factual claim')
 if len(refs)!=14 or not refs.verified.str.lower().eq('true').all() or not refs.used_in_paper.str.lower().eq('true').all():raise RuntimeError('Reference inventory invalid')
 tex='\n'.join((ROOT/'paper'/p).read_text(encoding='utf8') for p in ['main_fr.tex','appendix_fr.tex'])
 macros=set(re.findall(r'\\newcommand\{\\(\w+)\}',(ROOT/'paper/generated/facts.tex').read_text(encoding='utf8')))
 for name in re.findall(r'\\([A-Z][A-Za-z]+)\{\}',tex):
  if name not in macros:raise RuntimeError('Missing numerical macro '+name)
 comp=read('reports/compilation.json');pdf=read('reports/pdf_quality.json')
 for name in ['main_fr','appendix_fr']:
  if not comp[name]['compiled'] or comp[name]['overfull_boxes'] or comp[name]['undefined_citations']:raise RuntimeError('TeX issue '+name)
  q=pdf[name]
  if not q['searchable_all_pages'] or not q['all_fonts_embedded'] or q['outside_page_text'] or q['replacement_glyphs'] or q['link_backslash_errors']:raise RuntimeError('PDF technical issue '+name)
  if q['rendered_pages']!=q['pages'] or q['visual_review'].get('status')!='PASSED_INTERNAL_AI_VISUAL_INSPECTION':raise RuntimeError('PDF visual inspection incomplete')
  if q['sha256']!=sha(ROOT/'paper'/(name+'.pdf')):raise RuntimeError('PDF changed after inspection')
 rb=read('reports/review_B_V_results.json')
 if rb['max_aggregate_y_difference']!=0 or rb['all_20_period_bandwidth_results_max_root_difference']>1e-9:raise RuntimeError('Independent V replication differs')
 ids=pd.read_csv(ROOT/'reports/bassin_rd_rbc_identity_checks.csv')
 if len(ids)!=110 or ids[['point_difference','se_difference']].abs().max().max()>1e-9:raise RuntimeError('Official RBC/HC3 identities differ')
 report={'status':'PASS_INTERNAL_NONCAUSAL_WORKING_PAPER_CHECKS','local_date':'2026-10-04','reviewer_type':'AI internal reviews and root technical checks; not human peer review',
  'research_scope':'Eligibility reconstruction, administrative measurement and identification diagnostics',
  'causal_identification':'CLOSED_ALL_CURRENT_CAUSAL_ROUTES','python_scripts_parsed':len(scripts),'source_rows':len(pd.read_csv(ROOT/'data_sources.csv')),
  'claims_verified':len(claims),'references_verified_and_cited':len(refs),'raw_assignment_field_checks':c['checked_commune_column_values'],
  'raw_commune_month_cells':cells['cell_observations'],'RBC_identity_checks':len(ids),'pdf_pages':{n:pdf[n]['pages'] for n in pdf},
  'current_source_and_pdf_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'paper'/n for n in ['main_fr.tex','appendix_fr.tex','main_fr.pdf','appendix_fr.pdf']]},
  'independent_review_reports':{'A':'review_A_final_scope.json','B':'review_B_final_scope.json','C':['review_C_observation_checks.json','review_C_assignment_paths.json','review_C_public_release_rights.json'],'D':'review_D_final_scope.json'},
  'remaining_research_blockers':[],'HAL_status':'NOT_SUBMITTED','GitHub_public_release':'NOT_DONE',
  'limits':['No validated causal policy effect, national net creation, employment effect or economic survival claim.',
   'Actual tax-benefit uptake, local exemption decisions and individual administrative proposals unobserved.',
   'No claim of personal author verification, native human edit, external peer review or absolute anonymisation.'],
  'public_package':'Not certified by this checker; actual whitelist inventory is a subsequent material check.'}
 (ROOT/'reports/final_quality_gate.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 (ROOT/'reports/final_quality_gate.md').write_text('# Final internal quality gate\n\nPASS for the actual noncausal working-paper scope. All causal routes remain CLOSED.\n\nIndependent A/B/C/D reviews and technical rendering checks are documented; these are AI internal checks, not human peer review. No scientific blockers remain within the declared scope. The author responsibility and actual publication transactions are not fabricated.\n\n'+json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 state=read('reports/analysis_status.json');state['status']=report['status'];state['causal_clearance']=False;state['HAL_status']='NOT_SUBMITTED'
 (ROOT/'reports/analysis_status.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf8')
 v=read('reports/bassin_rd_results.json');v['gate']='CLOSED_V_CAUSAL_ROUTE: historical discontinuities, selection composition jumps, concentrated dependencies'
 (ROOT/'reports/bassin_rd_results.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({k:v for k,v in report.items() if k!='current_source_and_pdf_sha256'},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
