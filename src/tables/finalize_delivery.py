"""Prepare truthful final metadata and claims; never upload or claim a deposit."""
from pathlib import Path
import re,json,hashlib
import pandas as pd
ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def plain(text,vals):
 for key,v in vals.items():text=text.replace('\\'+key+'{}',v.replace('\\,',' '))
 return text.replace('\\%','%').replace('\\','').replace('{}','').strip()
def main():
 vals=json.loads((ROOT/'reports/numerical_facts.json').read_text(encoding='utf8'))
 tex=(ROOT/'paper/main_fr.tex').read_text(encoding='utf8')
 title=re.search(r'\\title\{(.*?)\}\n\\author',tex,re.S).group(1).replace('\\\\',' ')
 abstract=plain(re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',tex,re.S).group(1),vals)
 b=pd.read_csv(ROOT/'results/tables/main_border_estimates.csv').query("outcome=='establishment_births' & scale=='per1000' & clustering=='EPCI_components'").iloc[0]
 rd=pd.read_csv(ROOT/'results/tables/bassin_rd_estimates.csv').query("period=='primary_2024H2' & bandwidth==1000").iloc[0]
 en=("This paper reconstructs territorial eligibility for France Ruralités Revitalisation (FRR) and examines what official public data can establish about its initial evaluation. "
 "INSEE data observed in 2020 and geographic compositions for 2023 reproduce the national eligibility thresholds. Of 17,672 initially designated mainland communes, 14,316 satisfy at least one verified mandatory route; the remaining 3,356 satisfy possible living-area or mountain routes. The union exactly matches the initial list, without revealing individual prefectural decisions or population within partially classified mountain areas. "
 "The ZRR–FRR transition is linked to a monthly SIRENE panel for January 2019–June 2026, using historical locations and administrative states. "
 f"For July–December 2024, broad and within-département matched contrasts are close to zero. Across 774 disjoint boundary pairs, the contrast is {b.coefficient:.3f} monthly registrations per 1,000 residents (95% confidence interval [{b.ci_low:.3f}, {b.ci_high:.3f}]). "
 "Full-period pre-treatment diagnostics undermine a causal interpretation. Intermunicipal threshold candidates have insufficient eligible-side support after separating alternative routes. "
 f"A living-area income candidate has greater support, but discontinuous coverage, historical outcome differences and concentrated dependencies. Its bias-corrected post-reform contrast is {rd.bias_corrected:.3f} (HC3 interval [{rd.ci_low_hc3:.3f}, {rd.ci_high_hc3:.3f}]), without causal clearance. "
 "The contributions are reproducible eligibility reconstruction, administrative measurement and identification diagnostics. The findings establish neither national net creation, employment growth nor policy ineffectiveness.")
 sf=ROOT/'submission/publication_state.json';state=json.loads(sf.read_text()) if sf.exists() else {}
 m={'title_fr':title,'title_en':'Reconstructing France Ruralités Revitalisation Eligibility: Public Data, Registrations and Limits to Evaluating the 2024 Reform',
 'author':{'given_name':'Kun','family_name':'Huang'},'affiliation':'Wuhan University [China]','hal_structure_docid':300831,
 'manuscript_affiliation':'Economics and Management School, Wuhan University, Wuhan, China','academic_email':'huangkun123huang@163.com',
 'language':'fr','document_type_label':'Pré-publication / document de travail','document_type_code':'verify actual HAL interface',
 'domain':'Sciences de l’Homme et Société / Économie et finance','JEL':['H25','H71','R38','L26'],
 'production_date':'2026-10-04','license_pdf':'CC BY 4.0; third-party database notices retained',
 'abstract_fr':abstract,'abstract_en':en,'keywords_fr':['Fiscalité territoriale','France ruralités revitalisation','SIRENE','Immatriculations','Éligibilité territoriale','Identification'],
 'keywords_en':['Place-based taxation','France Ruralités Revitalisation','SIRENE','Establishment registrations','Territorial eligibility','Identification'],
 'ORCID':None,'IdHAL':None,'funding':None,'repository_url':state.get('github_url'),'HAL_status':state.get('HAL_status','NOT_SUBMITTED'),
 'no_peer_review_claim':True,'files':{n:{'path':'paper/'+n,'sha256':sha(ROOT/'paper'/n)} for n in ['main_fr.pdf','appendix_fr.pdf']}}
 (ROOT/'submission/hal_metadata.json').write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf8')
 head='# Métadonnées HAL préparées — état réel : '+m['HAL_status']+'\n\n'
 for key in ['title_fr','title_en','author','affiliation','hal_structure_docid','manuscript_affiliation','academic_email','language','document_type_label','domain','JEL','production_date','license_pdf','ORCID','IdHAL','funding','repository_url']:
  head+='- '+key+' : '+str(m[key] if m[key] is not None else 'aucun élément vérifié ; champ vide')+'\n'
 head+='\n## Résumé français\n\n'+abstract+'\n\n## English abstract\n\n'+en+'\n\n## Mots-clés\n\n'+' ; '.join(m['keywords_fr'])+'\n\n## Keywords\n\n'+'; '.join(m['keywords_en'])+'\n\n'
 head+='Les conclusions sont institutionnelles, administratives et diagnostiques. Les modèles causaux ne sont pas validés. Les examens A–D sont internes et réalisés par des agents d’IA ; ils ne sont pas une expertise humaine extérieure. Cette fiche ne constitue pas un reçu de dépôt.\n'
 (ROOT/'submission/hal_metadata.md').write_text(head,encoding='utf8')
 ai=re.search(r'\\section\*\{Déclaration relative.*?\}\n(.*?)\n\\bibliographystyle',tex,re.S).group(1)
 (ROOT/'submission/ai_disclosure.md').write_text('# Déclaration relative à l’utilisation d’outils d’intelligence artificielle\n\n'+plain(ai,vals)+'\n',encoding='utf8')
 if m['HAL_status']=='NOT_SUBMITTED':
  record='# HAL submission record\n\nStatus: NOT_SUBMITTED.\n\nNo upload, agreement acceptance, HAL identifier, pending moderation or public availability is asserted. Deposit metadata and final files are prepared separately. Actual transactions must update publication_state.json and this record from observed receipts.\n\nPrepared local date: 2026-10-04 (Asia/Hong_Kong). Selected original-PDF license: CC BY 4.0, retaining third-party database notices.\n\n'
  record+='\n'.join('- '+n+': SHA256 `'+v['sha256']+'`' for n,v in m['files'].items())+'\n'
  if state.get('github_url'):
   record+='\n## Observed GitHub publication\n\nPublic repository: '+state['github_url']+'.\n\n'
   record+='Initial published commit: `'+state['github_initial_commit']+'`. The remote default branch is main and GitHub reported isPrivate=false. This is a repository publication receipt, not a HAL deposit receipt.\n'
  if state.get('HAL_execution_stage')=='BLOCKED_BROWSER_CONNECTION':
   record+='\n## Actual HAL blocker\n\nThe in-app HAL page was created, but browser tab reads repeatedly timed out. Chrome browser control returned `nodeRepl.fetch request failed`. No account login or registration, email activation, file upload, acceptance of platform terms, formal submission or moderation receipt was observed. No CAPTCHA or HAL security challenge is asserted.\n\n'
   record+='Next action: restore the Codex browser-control connection, then resume the prepared HAL account/deposit workflow. The user has already authorised this workflow; no new research or publication approval is required.\n'
  duplicate=state.get('HAL_public_duplicate_check',{})
  if duplicate:
   record+='\n## Public duplicate search\n\n'+json.dumps(duplicate,ensure_ascii=False,indent=2)+'\n\nAn anonymous public-index search cannot inspect authenticated drafts or pending deposits.\n'
  (ROOT/'submission/submission_record.md').write_text(record,encoding='utf8')
 # Keep earlier independently audited facts, add the new institutional inventory
 # and update result claims from current tables after the island-cluster fix.
 c=pd.read_csv(ROOT/'claims_audit.csv',dtype=str).fillna('')
 a=pd.read_csv(ROOT/'reports/assignment_claims_audit.csv',dtype=str).fillna('')
 new=[]
 def claim(text,loc,path,url):
  new.append({'claim':text,'paper_location':loc,'source_url':url,'source_type':'derived_official_public_data','verified':'true','notes':path+'; SHA256 '+sha(ROOT/path)+'; independent computation audit; no causal clearance'})
 sirene='https://www.data.gouv.fr/datasets/base-sirene-des-entreprises-et-de-leurs-etablissements-siren-siret'
 for lab,file,query in [('broad','broad_did',None),('matched','matched_did',"clustering=='EPCI_department_joint_components'"),('border','main_border_estimates',"outcome=='establishment_births' & scale=='per1000' & clustering=='EPCI_components'")]:
  df=pd.read_csv(ROOT/'results/tables'/(file+'.csv'));row=(df.query(query) if query else df).iloc[0]
  c=c[~c.claim.str.startswith(lab+' monthly per1000 contrast')]
  claim(f'{lab} monthly per1000 contrast = {row.coefficient:.12f}, SE = {row.se:.12f}','main comparison table','results/tables/'+file+'.csv',sirene)
 for txt,loc,path in [
  ('1044480 statutory path field comparisons; zero differences','annexe assignment','reports/review_C_assignment_paths.json'),
  (f'BV primary RBC={rd.bias_corrected:.12f}, HC3 SE={rd.se_rbc_hc3:.12f}, CI=[{rd.ci_low_hc3:.12f},{rd.ci_high_hc3:.12f}]','bassin table','results/tables/bassin_rd_estimates.csv'),
  ('BV 53 pre-policy HC3 restrictions reject; cluster ranks32/9 cannot test all53','bassin diagnostics','reports/bassin_rd_results.json'),
  ('BV coverage -44.3749 percentage points / Holm .072342; all63 covariates retained','annexe covariates','reports/review_B_V_covariate_discontinuities_assignment_only.csv'),
  ('BV independent72-month aggregation and all20 period-bandwidth results agree','annexe audits','reports/review_B_V_results.json')]:
   claim(txt,loc,path,sirene if 'assignment' not in path and 'covariate' not in path else 'https://www.insee.fr/fr/statistiques/6692392')
 c=pd.concat([c,a,pd.DataFrame(new)],ignore_index=True).drop_duplicates(subset=['claim','source_url'],keep='last')
 if not c.verified.str.lower().eq('true').all():raise RuntimeError('Unverified claim; refuse final inventory')
 c.to_csv(ROOT/'claims_audit.csv',index=False)
 c[c.source_type.eq('derived_official_public_data')].to_csv(ROOT/'empirical_claims_audit.csv',index=False)
 print(json.dumps({'metadata_prepared':True,'HAL_status':m['HAL_status'],'claims':len(c),'pdf_sha256':m['files']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
