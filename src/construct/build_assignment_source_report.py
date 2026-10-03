"""Document audited official FRR-2024 assignment sources, without outcomes."""
from pathlib import Path
import hashlib
import json
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def digest(relative):
    path = ROOT / relative
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source(key, path, url, publisher, role, observation_year=None,
           geography=None, published=None, fields=None, match_status=None,
           note=None, source_page=None, resource_metadata=None):
    record = dict(key=key, path=path, official_url=url, source_page=source_page,
                publisher=publisher, role=role, sha256=digest(path),
                bytes=(ROOT / path).stat().st_size,
                observation_year=observation_year, geography=geography,
                publication_date=published, fields=fields,
                match_status=match_status, note=note)
    if resource_metadata is not None:
        record.update(resource_metadata)
    return record


def main():
    mountain_metadata_path = 'docs/sources/public_release_rights/mountain_official_metadata.json'
    mountain_metadata = json.loads((ROOT / mountain_metadata_path).read_text(encoding='utf-8'))
    mountain_resource = next(row for row in mountain_metadata['resources']
                             if row['id'] == '87bc6d48-f1ed-4924-be55-0142660033de')
    mountain_dates = dict(
        resource_id=mountain_resource['id'],
        resource_created_at=mountain_resource['created_at'],
        resource_last_modified_at=mountain_resource['last_modified'],
        resource_published=mountain_resource.get('published'),
        resource_published_key_present='published' in mountain_resource,
        metadata_evidence=dict(
            path=mountain_metadata_path, sha256=digest(mountain_metadata_path),
            official_url='https://www.data.gouv.fr/api/1/datasets/communes-de-la-loi-montagne-au-code-officiel-geographique-cog-2020-2022/'))
    checks = json.loads((ROOT / 'reports/review_C_assignment_input_checks.json').read_text(encoding='utf-8'))
    population_crosscheck = json.loads((ROOT / 'reports/review_C_assignment_population_crosscheck.json').read_text(encoding='utf-8'))
    basin_crosscheck = json.loads((ROOT / 'reports/review_C_assignment_basin_membership_crosscheck.json').read_text(encoding='utf-8'))
    incomes = pd.read_csv(ROOT / 'data/processed/assignment2024_income.csv', dtype={'code': str})
    communes = pd.read_csv(ROOT / 'data/processed/assignment2024_commune_population_area.csv', dtype={'commune_code': str, 'department': str})
    metro_codes = set(communes.loc[communes.department.str.len().eq(2), 'commune_code'])
    com_income = incomes[incomes.level.eq('COM')]
    sources = [
        source('law_original_2024', 'data/raw/legal/lf2024_art73_438.txt',
               'https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000048727426',
               'Légifrance', 'official_web_tool_snapshot_of_original_JORF',
               published='2023-12-30', fields=['CGI 44 quindecies A II A–E', 'IV'],
               match_status='EXACT_ORIGINAL_LEGAL_VERSION',
               note='The stored file is a web-retrieval text snapshot, not the HTML response. Input availability cutoff 2023-07-01; EPCI perimeter 2023-01-01; density population concept is population municipale.'),
        source('government_reference_year_confirmation', 'data/raw/assignment2024/senat_debate_2023_11_26.pdf',
               'https://www.senat.fr/cra/s20231126/s20231126.pdf',
               'Sénat, intervention de Dominique Faure', 'official_contemporaneous_legislative_record',
               observation_year=2020, published='2023-11-26', fields=['PDF page 66, printed page 63'],
               match_status='DIRECT_2020_CENSUS_AND_FILOSOFI_YEAR_EVIDENCE',
               note='The minister explicitly identifies recensement 2020 and Filosofi 2020. The relevant PDF page was rendered and visually inspected; saved evidence image is available.'),
        source('income2020_all_levels', 'data/raw/assignment2024/insee_filosofi2020_geog2023_csv.zip',
               'https://www.insee.fr/fr/statistiques/fichier/6692392/base-cc-filosofi-2020_CSV.zip',
               'INSEE', 'direct_official_level_specific_income_medians',
               observation_year=2020, geography='2023-01-01', published='2023-04-24',
               fields=['CODGEO', 'MED20'], match_status='REFERENCE_YEAR_AND_GEOGRAPHY_EXACT; ALL_METROPOLITAN_TERRITORY_THRESHOLDS_REPRODUCED',
               note='MED20 is médiane du niveau de vie in euros: disposable household income per unité de consommation. Use official COM/EPCI/BV2022/DEP medians independently; no aggregation of commune medians. Published values are rounded/suppressed under statistical confidentiality, not uncensored microdata.',
               source_page='https://www.insee.fr/fr/statistiques/6692392?sommaire=6692394'),
        source('income_concept_definition', 'data/raw/assignment2024/insee_niveau_de_vie_definition.html',
               'https://www.insee.fr/fr/metadonnees/definition/c1890',
               'INSEE', 'official_level_of_living_definition',
               published='2021-10-18', fields=['Niveau de vie'],
               match_status='DISPOSABLE_HOUSEHOLD_INCOME_DIVIDED_BY_UC',
               note='The official definition identifies niveau de vie as disposable household income divided by consommation units, shared by all persons of a household. This supports the MED20 conceptual correspondence; it is not revenu fiscal médian or average income.'),
        source('population2020_area_geog2023', 'data/raw/assignment2024/base-cc-serie-historique-2020_csv.zip',
               'https://www.insee.fr/fr/statistiques/fichier/7632565/base-cc-serie-historique-2020_csv.zip',
               'INSEE', 'official_census_population_and_commune_area',
               observation_year=2020, geography='2023-01-01', published='2023-06-27',
               fields=['CODGEO', 'P20_POP', 'SUPERF'],
               match_status='REFERENCE_YEAR_AND_GEOGRAPHY_EXACT; DENSITY_MEDIANS_REPRODUCED',
               note='P20_POP is population en 2020 from principal census exploitation; SUPERF is commune area in km². Sum whole-commune population and area by historical membership. The raw file includes 45 municipal arrondissements; these are omitted to avoid duplicate PLM city counts. Mayotte is absent.',
               source_page='https://www.insee.fr/fr/statistiques/7632565'),
        source('epci2023_composition', 'data/raw/epci_2023/Intercommunalite_Metropole_au_01-01-2023.xlsx',
               'https://www.insee.fr/fr/statistiques/fichier/2510634/Intercommunalite_Metropole_au_01-01-2023.zip',
               'INSEE', 'official_historical_EPCI_membership',
               geography='2023-01-01', fields=['EPCI', 'NATURE_EPCI', 'CODGEO', 'DEP'],
               match_status='EXACT_LEGAL_EPCI_PERIMETER',
               note='Stored SHA256 is for the workbook extracted from the official ZIP, not the ZIP. There are 1,232 real metropolitan EPCI à fiscalité propre; ZZZZZZZZZ is a Sans objet placeholder, not an EPCI. Four exempt island communes require their own COM indicators.'),
        source('bassin2022_composition_geog2023', 'data/raw/legal/BV2022_au_01-01-2023.zip',
               'https://www.insee.fr/fr/statistiques/fichier/6676988/BV2022_au_01-01-2023.zip',
               'INSEE', 'official_historical_bassin_membership',
               geography='2023-01-01', fields=['CODGEO', 'BV2022'],
               match_status='MATCHES_PUBLISHED_2023_INCOME_GEOGRAPHY_AND_BASSIN_DENSITY_THRESHOLD',
               note='BV2022 denotes the 2022 zoning definition, carried on COG2023 commune geography. The current webpage exposes a historical 2023 archive. Original publication date of that archive was not independently established. A second Excel parser verified all 34,945 stored commune memberships with zero differences.',
               source_page='https://www.insee.fr/fr/information/6676988'),
        source('dgcl_initial_thresholds_retrospective', 'data/raw/faq_2025.pdf',
               "https://www.collectivites-locales.gouv.fr/files/files/3.%20Animer%20les%20territoires/5.%20La%20coh%C3%A9sion%20territoriale%20et%20l'am%C3%A9nagement%20du%20territoire/FAQ%20FRR_MAJ%20juillet2025.pdf",
               'DGCL', 'official_retrospective_explanation_of_initial_LFI2024_criteria',
               published='2025-07', fields=['Section 3.1.1, pages 5–6'],
               match_status='EXACT_INITIAL_2024_THRESHOLDS; NOT_NEW_2025_ROUTE_RULES',
               note='Section 3.1.1 explicitly concerns LFI2024. Section 3.1.2 on page 7 separately concerns LFI2025 additions. Public thresholds: EPCI 63.57 and 21570; mountain income Q75 22822.5; BV 70.84 and 21600; DEP density <35 and income 21665.'),
        source('government_threshold_confirmation2025', 'data/raw/assignment2024/senat_question05373_2025.html',
               'https://www.senat.fr/questions/base/2025/qSEQ250705373.html',
               'Sénat, ministère chargé de la ruralité', 'official_government_answer',
               published='2025-09-04', fields=['ministerial answer to question 05373'],
               match_status='CONFIRMS_EPCI_AND_BASSIN_INITIAL_THRESHOLDS_AND_PREFECTURAL_PATH',
               note='Official answer gives EPCI 63.57/21570, BV 70.84/21600, and describes complementary préfet proposals. It does not supply a national original computation workbook.'),
        source('mountain1985_geog2022', 'data/raw/assignment2024/mountain_cog2022.xlsx',
               'https://static.data.gouv.fr/resources/communes-de-la-loi-montagne-au-code-officiel-geographique-cog-2020-2022/20220323-152301/dgaln-icapp-sidauh-opendata-loi-montagne-1985-cog-2022.xlsx',
               'Ministère de la Cohésion des territoires / DGALN-SIDAUH', 'official_law_montagne_commune_list',
               geography='2022-01-01', published=None, resource_metadata=mountain_dates,
               fields=['Perimetre.INSEE_COM', 'Réglementation', 'CommunesFusionnees.OLD_INSEE', 'AN_FUSION'],
               match_status='CORRECT_LEGAL_CONCEPT; EXACT_2023_POPULATION_SHARE_NOT_SUPPLIED',
               note='Perimetre has 5,611 listed communes, CommunesFusionnees 233 historical merger records. This is Loi Montagne 1985, not massif geography. Metadata includes partial communes and preservation of classification only for previously classified parts after merger; no population-in-classified-part field is supplied. Mapping to COG2023 and verifying the 50% population condition remain separate tasks. Official resource created_at is 2022-03-10; last_modified is 2022-03-23. The published field is not provided, so the update date is not treated as a publication date.',
               source_page='https://www.data.gouv.fr/datasets/communes-de-la-loi-montagne-au-code-officiel-geographique-cog-2020-2022'),
        source('population2020_geog2022_diagnostic_only', 'data/raw/assignment2024/insee_population2020_geog2022_csv.zip',
               'https://www.insee.fr/fr/statistiques/fichier/6683035/ensemble.zip',
               'INSEE', 'unused_geography_diagnostic_and_population_concept_crosscheck',
               observation_year=2020, geography='2022-01-01', published='2022-12-29',
               fields=['PMUN', 'CODDEP', 'CODCOM'],
               match_status='CORRECT_YEAR_BUT_NOT_CANONICAL_2023_PERIMETER',
               note='Do not join this unadjusted COG2022 file as if it were COG2023. 34,916 of 34,924 nonmissing same-code comparisons equal P20_POP; eight discrepancies are retained, not assumed errors. Legal municipal-arrondissement sums reproduce all three whole-city Paris/Lyon/Marseille P20_POP values.',
               source_page='https://www.insee.fr/fr/statistiques/6683035?sommaire=6683037'),
        source('dgcl_current_map_not_initial_2024', 'data/raw/assignment2024/dgcl_webmap_data.json',
               'https://www.arcgis.com/sharing/rest/content/items/70791b36ca57450db7cf10892eee67c8/data?f=json',
               'DGCL.SDCAT (ArcGIS item owner)', 'discovery_only_current_overwritten_map',
               geography='COG2025/current map',
               match_status='NOT_VALID_AS_INITIAL_2024_ASSIGNMENT_INPUT',
               note='The official linked old app currently points to the FRR_plus layer. Public-service catalog searches did not recover an original 2024 calculation workbook or a complete historical statutory-path field. This is a search limitation, not proof that no such file exists.'),
    ]
    output_files = ['data/processed/assignment2024_income.csv',
                    'data/processed/assignment2024_commune_population_area.csv',
                    'data/processed/assignment2024_geographic_density_income.csv',
                    'data/processed/assignment2024_territory_indicators.csv']
    outputs = []
    for file in output_files:
        data = pd.read_csv(ROOT / file, dtype=str)
        outputs.append({'path': file, 'sha256': digest(file), 'rows': len(data),
                        'headers': data.columns.tolist()})
    missing = {
        'published_COM_rows_after_actual_commune_filter': len(com_income),
        'suppressed_or_missing_published_COM_MED20': int(com_income.med2020.isna().sum()),
        'official_member_communes_absent_from_COM_income_table': sorted(set(communes.commune_code) - set(com_income.code)),
        'metropolitan_communes_absent_from_COM_income_table': sorted(metro_codes - set(com_income.code)),
        'real_metropolitan_EPCI_missing_MED20': checks['missing_real_metropolitan_epci_income'],
        'special_no_EPCI_communes': checks['special_no_epci_communes'],
        'special_COM_29083_income_unknown': True,
        'rule': 'Unknown remains unknown. No mean or current-year substitution. Source-table absent rows must become unknown after a left join.',
    }
    report = {
        'review': 'REVIEW C — initial FRR2024 statutory assignment source audit',
        'reviewed_local_date': '2026-10-04',
        'reviewer_type': 'AI independent data/source audit, not a human verification certificate',
        'scope': 'Source years, geography, definitions, free official availability, thresholds; no outcome data or new causal estimation read.',
        'input_gate': 'PASS_OFFICIAL_2020_COG2023_INPUTS_AND_THRESHOLD_REPRODUCTION',
        'whole_assignment_gate': 'NOT_ESTABLISHED_BY_THIS_SOURCE_AUDIT',
        'sources': sources, 'numerical_checks': checks['results'],
        'population_concept_crosscheck': population_crosscheck,
        'bassin_membership_independent_crosscheck': basin_crosscheck,
        'missingness_and_special_cases': missing, 'outputs': outputs,
        'script': {'path': 'src/construct/assignment_sources.py', 'sha256': digest('src/construct/assignment_sources.py')},
        'quantile_method': 'pandas linear interpolation, numerically equal to the public Q75. Official algorithm is not independently documented; do not claim exact underlying microdata or algorithm recovery.',
        'density_precision_rule': 'Use full-precision recomputed national medians for statutory tests; published 63.57 and 70.84 are two-decimal displays.',
        'remaining_limits': [
            'The bassin numeric condition defines possible supplementary eligibility; actual initial assignment also requires the legal préfet proposal/ministerial decision. Do not deterministically classify every qualifying bassin commune.',
            'Mountain-part population cannot be inferred from a concerned-commune flag; COG2022→COG2023 mergers/partial classification require official corroboration or uncertainty exclusion.',
            'No original national DGCL 2024 calculation workbook or complete statutory-path file was recovered; downloaded current FRR_plus services are not substitutes.',
            'Reproducing national threshold values strongly validates the inputs, but does not alone reproduce the complete initial 17,717-commune arrêté list.',
            'This source gate does not validate regression discontinuity identification, local support, first-stage discontinuity, manipulation checks, or parallel trends.',
        ],
        'privacy': 'No SIRENE micro-identifiers, individual names, or street addresses were read or output for this task.',
        'untouched': ['main panel', 'manuscript', 'empirical claims', 'outcome results', 'public manifest'],
    }
    (ROOT / 'reports/review_C_assignment_sources.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    source_lines = []
    for row in sources:
        source_lines.extend([
            f"### {row['key']}", '',
            f"官方来源：[链接]({row['official_url']})。发布者：{row['publisher']}。",
            f"保存文件：`{row['path']}`；SHA256：`{row['sha256']}`。",
            f"观测年：{row['observation_year'] or '不适用/未给出'}；地理：{row['geography'] or '不适用'}；发布日：{row['publication_date'] or '未独立确定'}。"
            + (f" 资源创建时间：{row['resource_created_at']}；资源更新时间：{row['resource_last_modified_at']}；官方资源未提供 published 字段。"
               if 'resource_last_modified_at' in row else ''),
            f"字段/位置：{', '.join(row['fields'] or [])}。状态：{row['match_status']}。",
            row['note'], '',
        ])
    text = """# REVIEW C：2024 年初始 FRR 赋值变量官方来源审计

审查日：2026-10-04；执行者为 AI 独立数据审查，不能表述为人类专家核验。

结论：**2020 年人口、2020 年 Filosofi 收入以及 2023-01-01 地理口径可以用免费官方资料准确重构，并复现所有已公布的初始全国收入阈值和人口密度中位数。** 本报告通过的是赋值输入及阈值复算关，不是完整划区路径、识别设计或论文发表关。没有读取新 outcome、修改主面板、稿件、实证主张、结果或公共 manifest。

## 年份与口径证据

原始 LFI2024 第 73 条的 CGI 44 quindecies A IV 固定前一年 7 月 1 日可得数据、前一年 1 月 1 日 EPCI 周界，且密度使用 population municipale。2023-11-26 政府部长在参议院明确指定 recensement 2020 和 Filosofi 2020；本次独立查看 PDF 第 66 页（正文页 63）的文字和渲染图。

INSEE 收入文件于 2023-04-24 发布，人口/面积历史表于 2023-06-27 发布，两者均采用 2023-01-01 地理，且早于 2023-07-01。MED20 在 COM、EPCI、BV2022、DEP 四个层级各有官方直接发布值。中位数不可加总；本次未用 commune median 的加权平均冒充 EPCI median。

## 实际复算

| 层级 | metropolitan 单位数 | 完整精度密度中位数 | 公开密度显示值 | 收入中位数（€） | 山地收入 Q75（€） |
|---|---:|---:|---:|---:|---:|
| EPCI-FP | 1,232 | 63.569845464551264 | 63.57 | 21,570 | 22,822.5 |
| BV2022 | 1,681 | 70.84363836218742 | 70.84 | 21,600 | 不适用 |
| DEP | 96 | 83.11740441071805 | 法定条件为 <35 | 21,665 | 不适用 |

EPCI 收入 Q75 采用 linear 分位数插值，复现 22,822.5；没有据此宣称拿到了 DGCL 原始计算算法或未四舍五入的收入微数据。密度的法定比较应使用复算完整精度，而不是只用 FAQ 的两位小数。人口与面积按官方整个市镇的 2023 周界成员求和，密度为人口合计/面积合计。

DEP density <35 且收入 ≤21,665 的交集精确产生 13 个省：04、05、09、12、15、23、32、36、46、48、52、55、58，与 DGCL 列表一致。1,232 个 metropolitan 真实 EPCI、1,681 个 BV 和 96 个 DEP 的官方收入均完整。

源人口文件的 45 个 Paris/Lyon/Marseille 市辖区已排除，仅保留完整市镇，避免城市和其辖区重复加总。canonical commune 表 34,945 行，metropolitan 34,816 行；Mayotte 17 个市镇人口缺失，保持 unknown。与 COG2022 的法律人口 CSV 交叉核对，34,924 个共同非缺失代码中 34,916 个 P20_POP 与 PMUN 一致，8 个差异保留并明确两版地理不同；法律人口市辖区合计分别等于 Paris、Lyon、Marseille 的整市 P20_POP。另用独立 Excel 值读取核对 BV 成员表，34,945 行两向差异均为零。

## 缺失与特殊路径

`ZZZZZZZZZ / Sans objet / NATURE_EPCI=ZZ` 是无 EPCI 占位标记，不是一个真实共同 EPCI；Île-de-Bréhat 22016、Île-de-Sein 29083、Ouessant 29155、L’Île-d’Yeu 85113 应按原法 own-COM 路径处理。Île-de-Sein 的 COM MED20 为缺失，不能补均值。

COM 发布表筛至实际市镇后有 34,874 行，其中 3,599 个 MED20 空缺；另 71 个成员市镇未见于 COM 收入表，均不在 metropolitan。缺行与统计秘空值都必须在左连接后保持 unknown。人口/收入缺失不构成法定不达标的证据。

山地源是 DGALN-SIDAUH 的 Loi Montagne 1985 名单，采用 COG2022；不是 massif 名单。Perimetre 为 5,611 行，CommunesFusionnees 为 233 行。官方元数据明确可能只涉及市镇的一部分，融合后仅原已划区部分保留资格；工作簿没有分部人口字段。因此不能自动把每个 listed commune 的全部人口计为山地人口。COG2022→COG2023 对应及 EPCI 50% 山地人口条件需要额外官方证据或保守排除不明确单位。

生活圈路径带有 préfet 的补充提案及部长决定。数值满足 BV 条件只能判断候选资格，不能自动认定所有这些市镇已经被划区。DGCL 原始全国计算工作簿或完整法定路径字段尚未取得；旧官方 ArcGIS 应用现在指向 2025 FRR_plus 图层，不能把当前图层当作 2024 原始输入。旧版 FAQ 下载链接返回 404，失败有留档，未声称取得。

## 交付与接口

`src/construct/assignment_sources.py` 已真实运行，输入哈希、计数和复算结果保存在 `reports/review_C_assignment_input_checks.json`。接口固定如下：

- `assignment2024_income.csv`：level, code, med2020, metadataGeography, income_reference_year, source_table, source_variable, income_unknown。
- `assignment2024_commune_population_area.csv`：commune_code, department, epci_2023, P20_POP, SUPERF, metadataGeography, population_reference_year, source_table, is_actual_epci, density2020。
- `assignment2024_territory_indicators.csv`：level, code, population_2020, area_km2, density_2020, median_income2020, n_communes, metadataGeography；共 3,009 行。

完整来源、SHA256、输出哈希及单独诊断见同名 JSON。复现全国阈值是对年份、周界和统计口径的强验证，但本报告没有据此宣称完整复现 17,717 个市镇的初始 arrêté，也没有据此宣称 RD 具有有效因果识别。

## 逐项来源与保存哈希

""" + '\n'.join(source_lines)
    (ROOT / 'reports/review_C_assignment_sources.md').write_text(text, encoding='utf-8')
    print(json.dumps({'input_gate': report['input_gate'], 'whole_assignment_gate': report['whole_assignment_gate'],
                      'sources': len(sources), 'outputs': outputs}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
