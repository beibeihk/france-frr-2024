"""Whitelist public research outputs; no raw, micro, credentials or dependencies."""
from pathlib import Path
import csv,hashlib,json,shutil,zipfile,re
import pandas as pd
import pyarrow.parquet as pq
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'release/france-frr-2024'
PROCESSED=['monthly_panel.parquet','bassin_rd_monthly_aggregates.parquet','commune_treatment.csv',
 'frr_2024_codes_verified.csv','bassin2022_composition.csv','border_edges.csv','border_pairs.csv','matched_pairs.csv',
 'assignment2024_commune_paths.csv','assignment2024_commune_population_area.csv','assignment2024_territory_indicators.csv',
 'bassin_rd_candidates.csv','bassin_rd_selected_communes.csv','rd_V_bv_candidates_assignment_only.csv',
 'rd_V_bv_membership_assignment_only.csv','rd_V_bv_selected_communes_assignment_only.csv',
 'rd_candidate_communes.csv','rd_candidates_A_income_whole_epci_barrier.csv','rd_candidates_B_income_commune_barrier.csv',
 'rd_candidates_D_density_commune_barrier.csv','rd_E_epci_candidates_assignment_only.csv','rd_E_epci_selected_communes_assignment_only.csv']
REPORTS=['analysis_status.json','final_quality_gate.json','final_quality_gate.md','numerical_facts.json','data_quality.json',
 'compilation.json','pdf_quality.json','pdf_visual_review.md','legal_source_audit_manifest.json','review_A_institutional_macro_values.json',
 'review_A_assignment_2024.json','review_A_manuscript_v2.md','review_A_manuscript_v2_scope.json','review_A_resolutions.json',
 'review_A_final_scope.json','review_A_final_scope.md',
 'review_B_final_scope.json','review_B_final_scope.md','review_B_results.json','review_B_results.md',
 'review_B_V_results.json','review_B_V_results.md','review_B_broad_islands_audit.json',
 'review_B_V_assignment_interface.json','review_B_V_covariate_diagnostics.json','review_B_V_dependency_graphs.csv',
 'review_B_V_covariate_discontinuities_assignment_only.csv','review_B_E_assignment_support.csv',
 'review_C_observation_checks.json','review_C_assignment_sources.json','review_C_assignment_sources.md',
 'review_C_assignment_paths.json','review_C_assignment_paths.md','review_C_public_release_rights.json',
 'review_D_final_scope.json','review_D_final_scope.md','pretrend_diagnostics.json','broad_matched_pretrends.json',
 'additional_diagnostics.json','bassin_rd_results.json','bassin_rd_execution_freeze.json','bassin_rd_rbc_identity_checks.csv',
 'rd_assignment_only_support.csv','assignment2024_reconstruction.json','assignment_extended_support_manifest.json',
 'wild_cluster_score.json','environment_versions.json','secondary_outcomes_quality.json','birth_structure_quality.json',
 'root_final_copy_edits.json','review_C_mountain_metadata_correction.json']
FORBIDDEN={'siren','siret','nic','nomUniteLegale','prenom1UniteLegale','nomUsageUniteLegale','numeroVoieEtablissement','libelleVoieEtablissement'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def license_for(rel):
 if rel.endswith('.py'):return 'MIT (original code); dependencies not included'
 if rel in ['data/processed/border_edges.csv','data/processed/border_pairs.csv','data/processed/matched_pairs.csv'] or rel=='results/tables/covariate_balance_all.csv':return 'ODbL1.0 for spatial database derivatives; third-party source notices retained'
 if rel.startswith('data/processed/'):
  return 'Source-specific Open Licence; Insee/ANCT/DGCL/DGALN attribution; see LICENSES.md'
 if 'map_' in rel:return 'CC BY4.0 original Produced Work; Contours administratifs ODbL notice retained'
 return 'CC BY4.0 original contributions; third-party citations/source rights retained'
def main():
 gate=json.loads((ROOT/'reports/final_quality_gate.json').read_text())
 if gate['status']!='PASS_INTERNAL_NONCAUSAL_WORKING_PAPER_CHECKS':raise RuntimeError('Final internal gate not yet complete')
 paths=[]
 def take(path,required=True):
  p=ROOT/path
  if not p.exists():
   if required:raise RuntimeError('Missing public input '+str(path))
   return
  if p.is_file():paths.append(p)
 for name in ['README.md','LICENSES.md','requirements.txt','requirements_rd.txt','run_pipeline.py','.gitignore',
  'data_sources.csv','data_dictionary.md','claims_audit.csv','empirical_claims_audit.csv','references_verified.csv']:
  take(name)
 for glob in ['src/**/*.py','paper/*.tex','paper/*.bib','paper/*.pdf','paper/generated/*.tex',
  'results/tables/*.csv','results/figures/*.pdf','results/figures/*.png','docs/sources/frr_2024/*.txt',
  'docs/sources/assignment2024/*.py','docs/sources/public_release_rights/official_access_log.json']:
  for p in ROOT.glob(glob):paths.append(p)
 for name in ['design_before_results.md','design_changes.md','assignment_2024_rules.md','assignment_data_dictionary.md',
  'assignment_rd_protocol.md','data_dictionary.md','analysis_variable_dictionary.md','institutional_background.md',
  'literature_audit.md','public_release_rights.md']:take('docs/'+name)
 for name in PROCESSED:take('data/processed/'+name)
 for name in REPORTS:take('reports/'+name,required=name not in ['review_A_final_scope.json','review_A_final_scope.md'])
 for name in ['hal_metadata.md','hal_metadata.json','ai_disclosure.md','hal_checklist.md','hal_policy_verified.md','submission_record.md','publication_state.json']:
  take('submission/'+name)
 for name in ['sirene_download_manifest.json','zoning_manifest.json','population_manifest.json']:take('data/external/'+name)
 paths=sorted(set(paths))
 paths=[p for p in paths if 'provisional' not in p.name]
 manifest=[];privacy=[]
 for p in paths:
  rel=p.relative_to(ROOT).as_posix()
  if any(v in rel.split('/') for v in ['raw','intermediate','.vendor','.vendor_rd','.git','tmp']):raise RuntimeError('Forbidden path '+rel)
  if p.suffix=='.parquet' or rel.startswith('data/processed/') and p.suffix=='.csv':
   names=pq.read_schema(p).names if p.suffix=='.parquet' else pd.read_csv(p,nrows=0).columns.tolist()
   if FORBIDDEN & set(names):raise RuntimeError('Individual field in package '+rel)
   privacy.append({'file':rel,'columns':names,'no_micro_identifiers':True})
  if p.suffix in ['.md','.tex','.json','.csv','.txt','.py','.bib']:
   s=p.read_text(encoding='utf8',errors='replace')
   if p.suffix!='.py' and '@agent.qq.com' in s:raise RuntimeError('Agent account address in public prose '+rel)
   if re.search(r'\b(?:ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{40,}|sk-proj-[A-Za-z0-9_-]{40,})\b',s):raise RuntimeError('Credential marker '+rel)
  dest=DEST/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
  manifest.append({'path':rel,'size_bytes':p.stat().st_size,'sha256':sha(p),'reuse_terms':license_for(rel)})
 DEST.mkdir(parents=True,exist_ok=True)
 with (DEST/'public_manifest.csv').open('w',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,fieldnames=['path','size_bytes','sha256','reuse_terms']);w.writeheader();w.writerows(manifest)
 # Use only the current whitelist in the archive; an old directory cannot add files.
 archive=ROOT/'release/france-frr-2024-replication.zip'
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for r in manifest:z.write(DEST/r['path'],'france-frr-2024/'+r['path'])
  z.write(DEST/'public_manifest.csv','france-frr-2024/public_manifest.csv')
 report={'status':'WHITELIST_PACKAGE_PREPARED','files':len(manifest)+1,'zip_size_bytes':archive.stat().st_size,
  'zip_sha256':sha(archive),'aggregate_schema_checks':privacy,'raw_micro_detailed_cohort_geometry_dependencies_excluded':True,
  'scope':'No absolute anonymity certificate. No Github/HAL publication performed by this builder.',
  'ODbL_rebuild_methods':['src/construct/prepare_communes.py','src/geography/border_pairs.py','src/analysis/broad_and_matched.py'],
  'ODbL_inputs':'frozen source URLs/hashes, public commune treatment/composition and complete transformation code provided'}
 (ROOT/'reports/public_package_inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({k:v for k,v in report.items() if k!='aggregate_schema_checks'},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
