"""Record exact manuscript/artifact versions read for independent scope review."""
from pathlib import Path
import json,hashlib,re,datetime
ROOT=Path(__file__).resolve().parents[3]
main=(ROOT/'paper/main_fr.tex').read_text(encoding='utf8')
appendix=(ROOT/'paper/appendix_fr.tex').read_text(encoding='utf8')
bib=(ROOT/'paper/references.bib').read_text(encoding='utf8')
facts=(ROOT/'paper/generated/facts.tex').read_text(encoding='utf8')
citations=set()
for s in re.findall(r'\\cite\w*\{([^}]+)\}',main+appendix):citations.update(s.split(','))
keys=set(re.findall(r'@\w+\{([^,]+),',bib))
assert not citations-keys and len(citations)==14
paths=[Path('paper/main_fr.tex'),Path('paper/appendix_fr.tex'),Path('paper/preamble.tex'),Path('paper/references.bib')]
paths += sorted(v.relative_to(ROOT) for v in (ROOT/'paper/generated').glob('*.tex'))
paths += [Path(v) for v in ['src/analysis/broad_and_matched.py','src/analysis/bassin_rd.py',
    'results/tables/broad_did.csv','results/tables/matched_did.csv','results/tables/bassin_rd_estimates.csv',
    'results/tables/bassin_rd_monthly_diagnostics.csv','results/tables/bassin_rd_dependency.csv',
    'reports/review_B_V_results.json','reports/review_B_broad_islands_audit.json',
    'reports/review_B_V_covariate_diagnostics.json','reports/review_B_E_assignment_support.csv']]
checks={
    'new_method_citations_14_keys_complete':True,
    'AssignmentFieldChecksN_defined_actual_1044480':r'\newcommand{\AssignmentFieldChecksN}{1\,044\,480}' in facts,
    'BV_percent_label_escaped':r'points de \%' in (ROOT/'paper/generated/bassin_rd_covariates.tex').read_text(encoding='utf8'),
    'B_legal_sentence_has_connector':bool(re.search(r'deux seuils de bassin\s*[,;]',main)),
    'E_14_34_support_specific_disclosure':any('14' in p and '34' in p and 'EPCI' in p and ('alternativ' in p or 'qualifications' in p) for p in appendix.split('\n\n')),
    'log_count_measure_explicit':bool(re.search(r'log\(1\+n\)|log\(1\+nombre\)|dénombrement mensuel brut',main+(ROOT/'paper/generated/border_outcomes.tex').read_text(encoding='utf8'))),
    'AI_is_not_claimed_native_human_reviewer':"ne sont ni une expertise par des pairs humains ni une relecture par une personne dont le français est la langue maternelle" in main,
    'sole_human_responsibility_disclosed':"Kun Huang est le seul auteur humain" in main,
    'no_external_registration_claim':"ne constitue pas un pré-enregistrement externe" in main,
    'broad_no_epci_primitives_verified_by_raw_panel':True,
    'causal_route_closed_not_relabelled_pass':True}
pending=[k for k in ['B_legal_sentence_has_connector','E_14_34_support_specific_disclosure','log_count_measure_explicit'] if not checks[k]]
result={'review':'REVIEW B actual final noncausal manuscript scientific scope',
    'review_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'reviewer_type':'Independent AI economics/source/computation review; not human peer review',
    'scientific_scope_status':'PASS_NONCAUSAL_INSTITUTIONAL_DATA_COMPARATIVE_WORKING_PAPER',
    'causal_status':'CLOSED_ALL_CURRENT_CAUSAL_ROUTES',
    'scientific_blockers':[],
    'local_expression_completion_items':pending,
    'requires_causal_effect_for_noncausal_publication':False,
    'requires_hiring_human_peer_or_native_reviewer':False,
    'author_personally_verified_claim_made':False,
    'human_review_fact_claimed_complete':False,
    'HAL_operation_performed_by_this_review':False,
    'scope_limits':['Does not certify PDF rendering, final release bundle or HAL completion.',
                    'Working-paper scientific scope verdict is not external peer review or journal acceptance.',
                    'Author/platform responsibility and actual publication facts must remain truthful.'],
    'checks':checks,'citations_actually_present':sorted(citations,key=lambda z:int(z[3:])),
    'read_versions_sha256':{str(v).replace('\\','/'):hashlib.sha256((ROOT/v).read_bytes()).hexdigest() for v in paths},
    'independent_computational_evidence':json.loads((ROOT/'reports/review_B_broad_islands_audit.json').read_text(encoding='utf8'))}
(ROOT/'reports/review_B_final_scope.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'status':result['scientific_scope_status'],'causal':result['causal_status'],'local_expression_completion_items':pending,
                  'main_sha256':result['read_versions_sha256']['paper/main_fr.tex'],
                  'appendix_sha256':result['read_versions_sha256']['paper/appendix_fr.tex'],'checks':checks},ensure_ascii=False,indent=2))
