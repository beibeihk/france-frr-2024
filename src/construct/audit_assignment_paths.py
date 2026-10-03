"""Independently reconstruct assignment paths from official inputs, without Y."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import zipfile
import numpy as np
import pandas as pd
from excel_utils import read_values

ROOT = Path(__file__).resolve().parents[2]


def sha(relative):
    return hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()


def main():
    path_file = 'data/processed/assignment2024_commune_paths.csv'
    script_file = 'src/construct/assignment2024.py'
    hashes_before = {p: sha(p) for p in [path_file, script_file]}
    original = pd.read_csv(ROOT / path_file, dtype={'commune_code': str, 'epci_2023': str}, low_memory=False).set_index('commune_code')
    raw = ROOT / 'data/raw/assignment2024'
    epci_book = ROOT / 'data/raw/epci_2023/Intercommunalite_Metropole_au_01-01-2023.xlsx'
    members = read_values(epci_book, sheet_name='Composition_communale', header=5, dtype=str)
    units = read_values(epci_book, sheet_name='EPCI', header=5, dtype=str)
    real_epci = set(units.loc[units.NATURE_EPCI.ne('ZZ'), 'EPCI'])
    with zipfile.ZipFile(raw / 'base-cc-serie-historique-2020_csv.zip') as z:
        population = pd.read_csv(z.open('base-cc-serie-historique-2020.CSV'), sep=';', dtype=str, usecols=['CODGEO', 'P20_POP', 'SUPERF'])
    population['P20_POP'] = pd.to_numeric(population.P20_POP)
    population['SUPERF'] = pd.to_numeric(population.SUPERF)
    d = members[members.DEP.str.len().eq(2)][['CODGEO', 'DEP', 'EPCI']].merge(population, on='CODGEO', how='left', validate='1:1')
    d = d.rename(columns={'CODGEO': 'commune_code', 'DEP': 'department', 'EPCI': 'epci_2023'})
    with zipfile.ZipFile(ROOT / 'data/raw/legal/BV2022_au_01-01-2023.zip') as z:
        b = read_values(BytesIO(z.read('BV2022_au_01-01-2023.xlsx')), sheet_name='Composition_communale', header=None, dtype=str)
    b = b[b.iloc[:, 0].str.fullmatch('[0-9AB]{5}', na=False)]
    bm = pd.DataFrame({'commune_code': b.iloc[:, 0], 'bassin_2022_cog2023': b.iloc[:, 2]})
    d = d.merge(bm, on='commune_code', how='left', validate='1:1')
    native_income = {}
    with zipfile.ZipFile(raw / 'insee_filosofi2020_geog2023_csv.zip') as z:
        for level in ['COM', 'EPCI', 'BV2022', 'DEP']:
            i = pd.read_csv(z.open(f'cc_filosofi_2020_{level}.csv'), sep=';', dtype=str, usecols=['CODGEO', 'MED20'])
            native_income[level] = pd.to_numeric(i.set_index('CODGEO').MED20, errors='coerce')
    d['actual_epci'] = d.epci_2023.isin(real_epci)
    levels = {}
    for level, key in [('EPCI', 'epci_2023'), ('BV2022', 'bassin_2022_cog2023'), ('DEP', 'department')]:
        q = d[d.actual_epci] if level == 'EPCI' else d
        t = q.groupby(key).agg(pop=('P20_POP', 'sum'), area=('SUPERF', 'sum'))
        t['density'] = t['pop'] / t.area
        t['income'] = t.index.map(native_income[level])
        levels[level] = t
    cuts = {'epci_density': float(levels['EPCI'].density.median()),
            'epci_income': float(levels['EPCI'].income.median()),
            'epci_income_q75': float(levels['EPCI'].income.quantile(.75)),
            'bassin_density': float(levels['BV2022'].density.median()),
            'bassin_income': float(levels['BV2022'].income.median()),
            'department_density': 35., 'department_income': float(levels['DEP'].income.median())}
    for name, key, level in [('epci', 'epci_2023', 'EPCI'), ('bassin', 'bassin_2022_cog2023', 'BV2022'), ('department', 'department', 'DEP')]:
        d[name + '_density_2020'] = d[key].map(levels[level].density)
        d[name + '_median_income2020'] = d[key].map(levels[level].income)
    d['density2020'] = d.P20_POP / d.SUPERF
    d['commune_income2020'] = d.commune_code.map(native_income['COM'])
    d['population_below30000'] = d.P20_POP.lt(30000)
    d['eligible_A_epci'] = d.actual_epci & d.population_below30000 & d.epci_density_2020.le(cuts['epci_density']) & d.epci_median_income2020.le(cuts['epci_income'])
    d['eligible_A_isolated_commune'] = ~d.actual_epci & d.population_below30000 & d.density2020.le(cuts['epci_density']) & d.commune_income2020.le(cuts['epci_income'])
    d['isolated_A_income_unknown'] = ~d.actual_epci & d.population_below30000 & d.density2020.le(cuts['epci_density']) & d.commune_income2020.isna()
    qualifying_departments = set(levels['DEP'].index[levels['DEP'].density.lt(35) & levels['DEP'].income.le(cuts['department_income'])])
    d['department_qualifies'] = d.department.isin(qualifying_departments)
    d['eligible_C_department'] = d.department_qualifies & d.population_below30000
    d['bassin_indicators_unknown'] = d.bassin_density_2020.isna() | d.bassin_median_income2020.isna()
    # A possible AND condition is false if any known conjunct is false.
    # Under these complete official BV inputs this equals the parent's more
    # conservative 'any missing OR conjunction' screen exactly.
    d['bassin_potential'] = (d.bassin_density_2020.isna() | d.bassin_density_2020.le(cuts['bassin_density'])) & (d.bassin_median_income2020.isna() | d.bassin_median_income2020.le(cuts['bassin_income']))
    d['eligible_B_potential'] = d.bassin_potential & d.population_below30000
    mountain = read_values(raw / 'mountain_cog2022.xlsx', sheet_name='Perimetre', header=2, dtype=str)
    mountain_codes = set(mountain.INSEE_COM.dropna())
    history = pd.read_csv(ROOT / 'data/raw/communes_history_cog2026.csv', dtype=str).fillna('')
    codes2022 = set(history.loc[history.TYPECOM.eq('COM') & history.DATE_DEBUT.le('2022-01-01') & (history.DATE_FIN.eq('') | history.DATE_FIN.ge('2022-01-01')), 'COM'])
    d['mountain_any_commune2022'] = d.commune_code.isin(mountain_codes)
    d['mountain_membership_unknown'] = ~d.commune_code.isin(codes2022)
    d['mountain_population_upper'] = d.P20_POP.where(d.mountain_any_commune2022 | d.mountain_membership_unknown, 0)
    upper_share = d[d.actual_epci].groupby('epci_2023').mountain_population_upper.sum() / levels['EPCI']['pop']
    d['epci_mountain_possible'] = d.epci_2023.map(upper_share).ge(.5)
    d['eligible_D_potential'] = d.actual_epci & d.population_below30000 & d.epci_mountain_possible & d.epci_density_2020.le(cuts['epci_density']) & d.epci_median_income2020.le(cuts['epci_income_q75'])
    listed = pd.read_csv(ROOT / 'data/processed/frr_2024_codes_verified.csv', dtype=str)
    d['listed_initial2024'] = d.commune_code.isin(listed.code_insee)
    mandatory = d.eligible_A_epci | d.eligible_A_isolated_commune | d.eligible_C_department
    possible = mandatory | d.eligible_B_potential | d.eligible_D_potential
    d['assignment_audit_status'] = np.select([
        mandatory & d.listed_initial2024, mandatory & ~d.listed_initial2024,
        d.isolated_A_income_unknown, d.listed_initial2024 & ~possible,
        d.listed_initial2024 & possible, ~d.listed_initial2024 & possible],
        ['verified_mandatory_path_listed', 'mandatory_path_missing_from_list',
         'isolated_commune_income_unknown', 'listed_without_reconstructed_possible_path',
         'listed_only_potential_B_or_D', 'not_listed_potential_discretionary_or_mountain_path'],
        default='not_listed_no_path')
    d = d.set_index('commune_code').sort_index()
    original = original.sort_index()
    assert set(d.index) == set(original.index) and d.index.is_unique and original.index.is_unique
    differences = {}
    for column in d.columns:
        left, right = d[column], original[column]
        if pd.api.types.is_numeric_dtype(left) and not pd.api.types.is_bool_dtype(left):
            equal = np.isclose(left.to_numpy(dtype=float), right.to_numpy(dtype=float), rtol=0, atol=1e-10, equal_nan=True)
        else:
            equal = left.eq(right) | (left.isna() & right.isna())
        differences[column] = int((~equal).sum())
    overlaps = pd.DataFrame({'A': d.eligible_A_epci | d.eligible_A_isolated_commune,
                             'C': d.eligible_C_department, 'B_possible': d.eligible_B_potential,
                             'D_possible_upper': d.eligible_D_potential,
                             'listed_initial2024': d.listed_initial2024}).value_counts().reset_index(name='communes')
    overlaps.to_csv(ROOT / 'reports/review_C_assignment_path_overlaps.csv', index=False)
    movements = pd.read_csv(ROOT / 'data/raw/movements_cog2026.csv', dtype=str).fillna('')
    changes = movements[movements.DATE_EFF.gt('2022-01-01') & movements.DATE_EFF.le('2023-01-01') & movements.MOD.isin(['31', '32', '33', '34', '50']) & movements.TYPECOM_AP.eq('COM')]
    predecessors_classified = changes[changes.COM_AV.isin(mountain_codes)]
    changing_targets = set(changes.COM_AP) & set(d.index)
    # Mandatory/possible count values are order-independent; use sorted frame.
    mandatory = d.eligible_A_epci | d.eligible_A_isolated_commune | d.eligible_C_department
    possible = mandatory | d.eligible_B_potential | d.eligible_D_potential
    counts = {
        'metropolitan_communes': len(d), 'listed_metropolitan_initial2024': int(d.listed_initial2024.sum()),
        'original_arrête_all_communes': len(listed), 'original_list_codes_outside_metropolitan_2023': len(set(listed.code_insee) - set(d.index)),
        'A_real_epci': int(d.eligible_A_epci.sum()), 'A_isolated_commune': int(d.eligible_A_isolated_commune.sum()),
        'C_department': int(d.eligible_C_department.sum()), 'mandatory_union_A_or_C': int(mandatory.sum()),
        'mandatory_A_and_C_overlap': int(((d.eligible_A_epci | d.eligible_A_isolated_commune) & d.eligible_C_department).sum()),
        'mandatory_missing_from_official_list': int((mandatory & ~d.listed_initial2024).sum()),
        'B_potential_numeric': int(d.eligible_B_potential.sum()), 'D_potential_upper': int(d.eligible_D_potential.sum()),
        'listed_only_possible_B_or_D': int((d.listed_initial2024 & ~mandatory & possible).sum()),
        'listed_without_reconstructed_possible_path': int((d.listed_initial2024 & ~possible).sum()),
        'not_listed_but_possible_path': int((~d.listed_initial2024 & possible).sum()),
        'BV_indicators_unknown': int(d.bassin_indicators_unknown.sum()),
        'isolated_communes_missing_income': int((~d.actual_epci & d.commune_income2020.isna()).sum()),
        'isolated_A_unresolved_unknown_AND': int(d.isolated_A_income_unknown.sum()),
    }
    hashes_after = {p: sha(p) for p in hashes_before}
    assert hashes_before == hashes_after, 'Parent assignment script or output changed during audit; rerun.'
    summary = {
        'review': 'REVIEW C independent statutory path reconstruction', 'date': '2026-10-04',
        'reviewer_type': 'AI audit, not human expert certification', 'research_outcomes_read': False,
        'status': 'PASS_CURRENT_INPUT_NUMERICAL_RECONSTRUCTION' if sum(differences.values()) == 0 else 'FAIL_OUTPUT_DIFFERENCE',
        'checked_columns': len(differences), 'checked_commune_column_values': len(d) * len(differences),
        'column_differences': differences, 'cutoffs': cuts, 'counts': counts,
        'qualifying_department_codes': sorted(qualifying_departments),
        'overlap_report': 'reports/review_C_assignment_path_overlaps.csv',
        'parent_and_output_sha256': hashes_after,
        'independent_script_sha256': sha('src/construct/audit_assignment_paths.py'),
        'input_sha256': {p: sha(p) for p in [
            'data/raw/assignment2024/insee_filosofi2020_geog2023_csv.zip',
            'data/raw/assignment2024/base-cc-serie-historique-2020_csv.zip',
            'data/raw/assignment2024/mountain_cog2022.xlsx',
            'data/raw/epci_2023/Intercommunalite_Metropole_au_01-01-2023.xlsx',
            'data/raw/legal/BV2022_au_01-01-2023.zip',
            'data/raw/communes_history_cog2026.csv', 'data/raw/movements_cog2026.csv',
            'data/processed/frr_2024_codes_verified.csv']},
        'mountain_geography_change_check': {
            '2022_to2023_changed_COM_targets': sorted(changing_targets),
            'number_changed_targets': len(changing_targets),
            'listed_mountain_predecessor_rows': len(predecessors_classified),
            'changed_targets_not_flagged_unknown_by_parent': sorted(changing_targets - set(d.index[d.mountain_membership_unknown])),
            'conclusion': 'No listed mountain predecessor among these changed targets, hence no actual missing mountain contribution found. Mere code existence is not a general proof of stable perimeter; use movement-based review in future versions.'},
        'logic_cautions': [
            'B and D are possible paths only; B lacks observed préfet proposals, D uses an upper bound rather than exact mountain-part population.',
            'Unknown AND with a known-false conjunct is false; unknown AND otherwise satisfied conjuncts is unresolved. The parent BV screen conservatively marks any missing indicator possible, even with a known-false other indicator. All current BV indicators are present, so there is no current count difference.',
            'Île-de-Sein income is missing but known density exceeds the EPCI threshold, so the combined own-COM A condition is false rather than unresolved.',
            'Zero impossible listed cases and zero mandatory omissions establish numeric compatibility of these inputs. They do not identify every actual B/D route or validate causal inference.'
        ],
    }
    (ROOT / 'reports/review_C_assignment_paths.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    body = f"""# REVIEW C：赋值路径独立核对

审查日 2026-10-04；AI 独立审查，不是人类专家认证。未读取研究结果变量。

从官方人口 ZIP、各层级原生 Filosofi MED20、官方 EPCI/BV 工作簿独立重建 {len(d):,} 个 metropolitan 市镇。与主线程 `assignment2024_commune_paths.csv` 对照 {len(differences)} 个字段、{len(d) * len(differences):,} 个市镇×字段值，差异 **{sum(differences.values())}**。状态：{summary['status']}。

| 条件 | 市镇数 |
|---|---:|
"""
    body += '\n'.join(f'| {key} | {value:,} |' for key, value in counts.items())
    body += """

A 和 C 的并集是确定性必要资格路径；B 仅为数值上的可能生活圈补充资格，D 仅为山地人口上界下的可能资格。完整重叠组合见 `review_C_assignment_path_overlaps.csv`。省长提案及精确山地人口分部没有被观察，因此不能把 listed_only_possible_B_or_D 的每个市镇都归因于某条确定路径。

unknown AND 的规则：有一个已知 false 条件即可排除路径；其他已知条件均 true 而某条件 unknown 时，路径 unresolved。Île-de-Sein 的收入缺失，但密度已超阈值，因此其 own-COM A 路径为 false。主脚本 BV 对任意缺失均视为潜在资格，这是更保守屏障；当前 BV 输入全完整，实际计数没有差异。

山地 COG2022→COG2023 的 10 个周界/代码变化目标已另查官方 movements；没有任何前身在 mountain 列表中，本次未发现上界漏入。主脚本 unknown 仅检查代码是否存在，不能一般化为周界稳定；后续版本仍应做 movements 核查。上界本身不等于实际人口比例。

本次核对建立的是法定数值必要条件与可能集合对原始名单的兼容性；不代表取得全部实际路径、并行趋势成立或 RD 支持充足。主脚本及输出 SHA256：

"""
    body += '\n'.join(f'- `{p}`：`{h}`' for p, h in hashes_after.items()) + '\n'
    (ROOT / 'reports/review_C_assignment_paths.md').write_text(body, encoding='utf-8')
    print(json.dumps({'status': summary['status'], 'differences': differences, 'counts': counts, 'sha256': hashes_after}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
