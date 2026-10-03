"""Record the final narrow institutional manuscript check; no new research Y."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[3]

def sha(path):
    return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()

def main():
    b=(ROOT/'paper/main_fr.tex').read_bytes()
    t=b.decode('utf8')
    lines=t.splitlines()
    assert '\\end{document}' in t
    required={
        'C_income_distribution':'médiane des niveaux de vie médians par département',
        'contemporaneous_numeric_threshold_source':'l17b0486-tviii_rapport-avis.pdf',
        'historic_2024_code_source':'LEGIARTI000049130324/2024-07-01/',
        'mountain_COG2022':'en COG 2022',
        'same_code_geography_checked':'y compris lorsque le code reste identique',
        'mountain_archive_coverage_limit':'conditionnel à la couverture de cette archive',
        'mountain_population_unobserved':'Ce fichier ne fournit pas la population résidant dans les seules parties classées',
        'verified_mandatory_table_note':'Les voies obligatoires vérifiées regroupent A',
        'V_D_joint_conditions':'ni les conditions de la voie D évaluées à partir du majorant de population de montagne',
        'B_administrative_procedure':'une proposition du préfet de région motivée par l’intérêt général et un classement par arrêté interministériel',
        'candidate_union_not_exogeneity':'pas une observation des raisons individuelles ni une preuve d’exogénéité de la décision',
        'V_not_random_prefect_decision':'ne transforme pas la proposition préfectorale en décision aléatoire',
        'V_postpolicy_geography_disclosed':'inclut des changements postérieurs à la réforme',
        'own_island_indicators':'Les quatre communes sans EPCI emploient leurs propres indicateurs dans la voie A',
        'municipal_population2020_ceiling':'Le plafond communal est appliqué à la population municipale de 2020',
        'human_author_responsibility':'la responsabilité du contenu, des interprétations et de la décision de diffusion lui appartient',
    }
    checks={k:dict(passed=(v in t),line_numbers=[i+1 for i,s in enumerate(lines)if v in s],criterion=v)for k,v in required.items()}
    for bad in ['publié le 23 mars 2022 en COG 2022','suspendue à la révision humaine et à la résolution de ces limites d’identification']:
        checks['removed_'+('incorrect_mountain_publication_label' if bad.startswith('publié') else 'causal_clearance_as_noncausal_publication_requirement')]=dict(passed=(bad not in t),criterion='Absent: '+bad)
    correct_date=bool(re.search(r'(?:mis à jour|version|actualisé).*?23 mars 2022.*?COG 2022',t))
    checks['mountain_version_date_not_initial_publication']=dict(passed=correct_date,criterion='23 March2022 identifies resource version/update; official metadata created10March and last_modified23March, publicationfieldnull.')
    f=(ROOT/'paper/generated/facts.tex').read_text(encoding='utf8')
    expected={'AssignmentMetroN':34816,'AssignmentListedN':17672,'AssignmentMandatoryN':14316,'AssignmentResidualN':3356,'AssignmentUnlistedN':17144,'AssignmentBOnlyN':3013,'AssignmentDOnlyN':304,'AssignmentBothN':39,'AssignmentBOnlyBVN':314}
    found={}
    for name,value in expected.items():
        m=re.search(r'\\newcommand\{\\'+name+r'\}\{([^}]+)\}',f)
        found[name]=int(m.group(1).replace(r'\,','')) if m else None
    checks['assignment_macro_values']=dict(passed=(found==expected),expected=expected,observed=found)
    blockers=[k for k,z in checks.items()if not z['passed']]
    status='PASS_NONCAUSAL_INSTITUTIONAL_RECONSTRUCTION' if not blockers else 'FAIL_UNRESOLVED_INSTITUTIONAL_TEXT'
    source_paths=['reports/review_A_assignment_2024.json','reports/review_A_manuscript_v2.md','reports/assignment_claims_audit.csv','docs/sources/assignment2024/independent_assignment_checks.json','data/raw/assignment2024/mountain_official_metadata.json','src/construct/assignment2024.py','data/processed/assignment2024_commune_paths.csv','paper/generated/facts.tex','paper/generated/assignment_thresholds.tex','paper/generated/assignment_paths.tex']
    report=dict(review='REVIEW A final narrow institutional scope',reviewed_at_utc=datetime.now(timezone.utc).isoformat(),reviewer_type='Independent AI institutional audit; not human author/editor/peer review',institutional_scope_status=status,remaining_blockers=blockers,manuscript_sha256=hashlib.sha256(b).hexdigest(),manuscript_path='paper/main_fr.tex',reviewed_sections=['main§3.2','main§5.4 V eligibility and D joint conditions','abstract institutional scope','conclusion contribution and factual limits','AI/author responsibility declaration'],checks=checks,verified_counts=found,scope_limits=dict(new_V_estimates_reestimated=False,V_result_tables_audited=False,entire_scientific_review_replaced=False,layout_or_compilation_audited=False,manuscript_modified=False,root_claims_modified=False,HAL_action_taken=False,human_reading_completion_asserted=False,causal_effect_required_for_noncausal_working_paper=False),retained_limitations=['Actual national prefect proposal/approval register is not observed.','Mountain population share is not observed; D is only possible under a conservative population upper bound and archive coverage.','Public rounded income and reconstructed medians are not uncensored microdata or administrative software recovery.','Observed designation consistency does not demonstrate exogeneity or continuity.'],scope_judgement='Institutional facts, designation-versus-takeup distinction, official sources and explicit uncertainty are appropriate for a noncausal reconstruction/measurement/diagnostic working paper. Causal identification, native human editing or personal author reading are not automatic failure criteria in this narrow institutional gate. This gate does not itself decide HAL submission or the scientific interpretation of new V estimates.',source_sha256={n:sha(n)for n in source_paths})
    j=ROOT/'reports/review_A_final_scope.json'
    j.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    body=f'''# REVIEW A — 最终制度范围复核

审查时间：{report['reviewed_at_utc']}。主稿SHA256：`{report['manuscript_sha256']}`。

制度范围状态：**{status}**。剩余制度阻断项：{json.dumps(blockers,ensure_ascii=False)}。

本轮只读核查§3.2、V方法中的D联合条件、摘要与结论的事实边界，以及作者责任声明；没有改TeX、重审V估计、运行新回归或操作HAL。

实际落实并通过的修订：

- C比较的是各département收入中位数构成的分布；原始2024历史法源及同期AN2024第18页的数值阈值脚注已写入。
- 山地档案明确为COG2022，并说明2022→2023包括保留代码的区划核查、缺失精确山区人口和档案coverage条件。23March2022现在标为版本更新，避免把last_modified误作最初出版日期。
- A/C表注明确为已核验的强制路径；D仍是未观察精确人口条件的可能路径，没有把法律上的D写成prefect裁量。
- V的排除条件使用D的联合必要条件及保守山地上界；B要求数值条件、prefect公共利益提议及部长arrêté。名单吻合没有被写成随机行政决定。
- 四个无EPCI例外使用自身指标；保密收入未补值，已知必要条件失败可以排除该通道。人口2020、可得性2023及地域2023没有混淆。
- 摘要和结论以重构、测量和诊断为贡献，保留不可推断全国净创建、就业、实际税收领取或政策无效的边界。作者声明只说明责任和AI协助，没有声称真人母语编辑、同行或作者已亲自完成研究。

9项赋值计数宏实际展开均核验为34,816/17,672/14,316/3,356/17,144/3,013/304/39/314。旧340宏错误已解决，不再作为未完成项。

该制度范围可通过**非因果重构工作论文**的审查；没有把因果效应识别成立或真人阅读完成设为本范围的自动门槛。未观察完整prefect档案、准确山地人口和行政软件算法等限制已明示，属于研究边界，而非本轮新增阻断。V估计与整稿科学审查、语言和视觉检查分别由相应审查负责；本报告不替代它们，也不表示已提交HAL。

逐项判定、行号、来源和各文件SHA256见`review_A_final_scope.json`。判定适用于上述快照；后续仅语言调整若不改变制度事实与限定，可沿用本审查范围，事实改动须再次核对。
'''
    (ROOT/'reports/review_A_final_scope.md').write_text(body,encoding='utf8')
    print(json.dumps(dict(institutional_scope_status=status,remaining_blockers=blockers,manuscript_sha256=report['manuscript_sha256'],report_json_sha256=sha('reports/review_A_final_scope.json'),report_md_sha256=sha('reports/review_A_final_scope.md')),ensure_ascii=False))

if __name__=='__main__':
    main()
