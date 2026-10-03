"""Historical headquarters and legal-unit age at establishment registration.

Only commune-month counts and moments are exported. Administrative age concerns
the legal unit of new establishments, never the stock of active firms. No names,
street addresses, current headquarters, or micro identifiers are exported.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".vendor"))
import duckdb


def sqlpath(path):
    return str(path).replace("\\", "/").replace("'", "''")


def independent_cell_audit(c, ul, uh):
    """Reclassify the existing 20 stratified cells in Python from raw UL files."""
    import calendar
    from collections import defaultdict, Counter
    from datetime import date
    import pandas as pd
    cells = pd.read_csv(ROOT / 'reports/review_C_sample_cells.csv', dtype={'commune_code':str})
    c.register('structure_audit_cells', cells[['commune_code','month']])
    c.execute("""CREATE TEMP TABLE structure_audit_births AS
        SELECT b.siret,b.siren,b.nic,b.commune_code,b.creation_date
        FROM sourcebuild.main.births b JOIN structure_audit_cells a
        ON b.commune_code=a.commune_code AND date_trunc('month',b.creation_date)::DATE=a.month::DATE""")
    births = c.sql('SELECT * FROM structure_audit_births').fetchall()
    dates = dict(c.sql(f"""SELECT siren,dateCreationUniteLegale FROM read_parquet('{ul}')
        WHERE siren IN (SELECT siren FROM structure_audit_births)""").fetchall())
    histories = defaultdict(list)
    for siren,start,end,nic in c.sql(f"""SELECT siren,dateDebut,dateFin,nicSiegeUniteLegale
        FROM read_parquet('{uh}') WHERE siren IN (SELECT siren FROM structure_audit_births)""").fetchall():
        histories[siren].append((start,end,nic))
    counts = defaultdict(Counter)
    observed_ages = defaultdict(list)
    for siret,siren,nic,commune,birth_date in births:
        key = (commune,birth_date.replace(day=1))
        row = counts[key]
        row['establishment_births'] += 1
        periods = [h for h in histories[siren] if h[0] is not None and h[0]<=birth_date and (h[1] is None or h[1]>=birth_date)]
        if not periods: reason='unknown_hq_no_interval'
        elif len(periods)>1: reason='unknown_hq_ambiguous_intervals'
        elif periods[0][2] is None: reason='unknown_hq_missing_nic'
        elif not (len(periods[0][2])==5 and periods[0][2].isascii() and periods[0][2].isdigit()): reason='unknown_hq_invalid_historical_nic'
        elif nic is None or not (len(nic)==5 and nic.isascii() and nic.isdigit()): reason='unknown_hq_invalid_establishment_nic'
        else: reason='headquarters_births' if nic==periods[0][2] else 'non_headquarters_births'
        row[reason] += 1
        if reason.startswith('unknown_'): row['unknown_headquarters_births'] += 1
        legal = dates.get(siren)
        if siren not in dates: age_reason='unknown_age_missing_legal_unit'
        elif legal is None: age_reason='unknown_age_missing_date'
        elif legal==date(1900,1,1): age_reason='unknown_age_date_1900'
        elif legal<date(1800,1,1): age_reason='unknown_age_pre_1800'
        elif legal>birth_date: age_reason='unknown_age_negative'
        else: age_reason=None
        if age_reason:
            row['unknown_legal_age_births'] += 1
            row[age_reason] += 1
        else:
            days = (birth_date-legal).days
            months = (birth_date.year-legal.year)*12+birth_date.month-legal.month
            clamped_day = min(legal.day,calendar.monthrange(birth_date.year,birth_date.month)[1])
            months -= int(clamped_day>birth_date.day)
            row['known_legal_age_births'] += 1
            row['legal_age_zero_day_births' if days==0 else 'legal_age_positive_day_births'] += 1
            row['sum_legal_age_days'] += days
            row['sum_squared_legal_age_days'] += days*days
            row['sum_legal_age_completed_months'] += months
            row['sum_squared_legal_age_completed_months'] += months*months
            observed_ages[key].append((days,months))
    result = c.sql("""SELECT o.* FROM birth_structure_output o JOIN structure_audit_cells a
        ON o.commune_code=a.commune_code AND o.month=a.month::DATE ORDER BY o.commune_code,o.month""")
    columns = result.columns
    comparisons = failures = 0
    for values in result.fetchall():
        actual = dict(zip(columns,values))
        key = (actual['commune_code'],actual['month'])
        expected = counts[key]
        ages = observed_ages[key]
        expected['mean_legal_age_days'] = sum(a[0] for a in ages)/len(ages) if ages else None
        expected['mean_legal_age_completed_months'] = sum(a[1] for a in ages)/len(ages) if ages else None
        expected['min_legal_age_days'] = min(a[0] for a in ages) if ages else None
        expected['max_legal_age_days'] = max(a[0] for a in ages) if ages else None
        for column in columns[2:]:
            comparisons += 1
            lhs,rhs = actual[column],expected[column]
            failures += int((lhs is None)!=(rhs is None) or (lhs is not None and rhs is not None and abs(lhs-rhs)>1e-9))
    if failures:
        raise RuntimeError(f"Independent birth-structure cell audit found {failures} discrepancies; identifiers withheld.")
    return {'sample_cells':len(cells),'sample_births':len(births),'comparisons':comparisons,'failures':failures,'sample_selection':'Existing REVIEW C 20 treatment/control × zero/positive cells; seed 20241003.'}


def main():
    temp = ROOT / "data/intermediate/birth_structure"
    temp.mkdir(parents=True, exist_ok=True)
    c = duckdb.connect()
    c.execute("SET memory_limit='5GB'")
    c.execute("SET threads=2")
    c.execute(f"SET temp_directory='{sqlpath(temp / 'spill')}'")
    c.execute(f"ATTACH '{sqlpath(ROOT / 'data/intermediate/analysis.duckdb')}' AS sourcebuild (READ_ONLY)")

    def run(label, sql):
        print(label, flush=True)
        started = time.time()
        c.execute(sql)
        print(f"{label}: {time.time()-started:.1f}s", flush=True)

    ul = sqlpath(ROOT / "data/raw/stock-stockunitelegale-parquet.parquet")
    uh = sqlpath(ROOT / "data/raw/stock-stockunitelegalehistorique-parquet.parquet")
    run("Project birth keys and fixed legal-unit registration dates", f"""
        CREATE TEMP TABLE birth_keys AS
        SELECT siret,siren,nic,commune_code,creation_date FROM sourcebuild.main.births;
        CREATE TEMP TABLE relevant_units AS SELECT DISTINCT siren FROM birth_keys;
        CREATE TEMP TABLE legal_dates AS
        SELECT u.siren,TRY_CAST(u.dateCreationUniteLegale AS DATE) AS legal_creation_date
        FROM read_parquet('{ul}') u JOIN relevant_units r USING(siren);
    """)
    duplicate_source_units = int(c.sql("""SELECT count(*) FROM
        (SELECT siren FROM legal_dates GROUP BY 1 HAVING count(*)>1)""").fetchone()[0])
    if duplicate_source_units:
        raise RuntimeError("Legal-unit stock has duplicate unit keys; no arbitrary match selected.")
    duplicate_births = int(c.sql("SELECT count(*)-count(DISTINCT siret) FROM birth_keys").fetchone()[0])
    if duplicate_births:
        raise RuntimeError("Primary birth source has duplicate establishment keys; identifiers withheld.")
    run("Project official legal-unit periods for the analysis dates", f"""
        CREATE TEMP TABLE relevant_history AS
        SELECT h.siren,h.dateDebut,h.dateFin,h.nicSiegeUniteLegale
        FROM read_parquet('{uh}') h JOIN relevant_units r USING(siren)
        WHERE h.dateDebut<=DATE '2026-06-30'
          AND coalesce(h.dateFin,DATE '9999-12-31')>=DATE '2019-01-01';
    """)
    run("Identify historical headquarters at each establishment birth", """
        CREATE TEMP TABLE headquarters_matches AS
        SELECT b.siret,count(h.siren)::BIGINT AS interval_matches,
               min(h.nicSiegeUniteLegale) AS historical_hq_nic
        FROM birth_keys b LEFT JOIN relevant_history h
        ON b.siren=h.siren AND h.dateDebut<=b.creation_date
           AND coalesce(h.dateFin,DATE '9999-12-31')>=b.creation_date
        GROUP BY b.siret;
        CREATE TEMP TABLE birth_structure_records AS
        WITH joined AS (
          SELECT b.*,h.interval_matches,h.historical_hq_nic,
                 d.siren AS matched_legal_unit,d.legal_creation_date,
          CASE WHEN h.interval_matches=0 THEN 'no_historical_interval'
               WHEN h.interval_matches>1 THEN 'ambiguous_historical_intervals'
               WHEN h.historical_hq_nic IS NULL THEN 'missing_historical_hq_nic'
               WHEN NOT regexp_full_match(h.historical_hq_nic,'[0-9]{5}') THEN 'invalid_historical_hq_nic'
               WHEN b.nic IS NULL OR NOT regexp_full_match(b.nic,'[0-9]{5}') THEN 'invalid_establishment_nic'
               WHEN b.nic=h.historical_hq_nic THEN 'headquarters'
               ELSE 'non_headquarters' END AS headquarters_category,
          CASE WHEN d.siren IS NULL THEN 'missing_legal_unit'
               WHEN d.legal_creation_date IS NULL THEN 'missing_legal_creation_date'
               WHEN d.legal_creation_date=DATE '1900-01-01' THEN 'unknown_date_1900'
               WHEN d.legal_creation_date<DATE '1800-01-01' THEN 'pre_1800_date_requires_verification'
               WHEN d.legal_creation_date>b.creation_date THEN 'legal_date_after_establishment_birth'
               ELSE 'known' END AS legal_age_category
          FROM birth_keys b JOIN headquarters_matches h USING(siret)
          LEFT JOIN legal_dates d USING(siren)
        ), ages AS (
          SELECT *, CASE WHEN legal_age_category='known'
                    THEN date_diff('day',legal_creation_date,creation_date) END::BIGINT AS legal_age_days,
                    CASE WHEN legal_age_category='known'
                    THEN date_diff('month',legal_creation_date,creation_date) END::BIGINT AS month_boundaries
          FROM joined
        )
        SELECT *,CASE WHEN legal_age_category='known' THEN month_boundaries-
                   CASE WHEN (legal_creation_date+month_boundaries*INTERVAL '1 month')::DATE>creation_date
                        THEN 1 ELSE 0 END END::BIGINT AS legal_age_completed_months
        FROM ages;
    """)
    run("Aggregate historical headquarters and birth-cohort age moments", """
        CREATE TEMP TABLE birth_structure_aggregate AS
        SELECT commune_code,date_trunc('month',creation_date)::DATE AS month,
          count(*)::BIGINT AS establishment_births,
          count(*) FILTER(WHERE headquarters_category='headquarters')::BIGINT AS headquarters_births,
          count(*) FILTER(WHERE headquarters_category='non_headquarters')::BIGINT AS non_headquarters_births,
          count(*) FILTER(WHERE headquarters_category NOT IN ('headquarters','non_headquarters'))::BIGINT AS unknown_headquarters_births,
          count(*) FILTER(WHERE headquarters_category='no_historical_interval')::BIGINT AS unknown_hq_no_interval,
          count(*) FILTER(WHERE headquarters_category='ambiguous_historical_intervals')::BIGINT AS unknown_hq_ambiguous_intervals,
          count(*) FILTER(WHERE headquarters_category='missing_historical_hq_nic')::BIGINT AS unknown_hq_missing_nic,
          count(*) FILTER(WHERE headquarters_category='invalid_historical_hq_nic')::BIGINT AS unknown_hq_invalid_historical_nic,
          count(*) FILTER(WHERE headquarters_category='invalid_establishment_nic')::BIGINT AS unknown_hq_invalid_establishment_nic,
          count(*) FILTER(WHERE legal_age_category='known')::BIGINT AS known_legal_age_births,
          count(*) FILTER(WHERE legal_age_category!='known')::BIGINT AS unknown_legal_age_births,
          count(*) FILTER(WHERE legal_age_category='missing_legal_unit')::BIGINT AS unknown_age_missing_legal_unit,
          count(*) FILTER(WHERE legal_age_category='missing_legal_creation_date')::BIGINT AS unknown_age_missing_date,
          count(*) FILTER(WHERE legal_age_category='unknown_date_1900')::BIGINT AS unknown_age_date_1900,
          count(*) FILTER(WHERE legal_age_category='pre_1800_date_requires_verification')::BIGINT AS unknown_age_pre_1800,
          count(*) FILTER(WHERE legal_age_category='legal_date_after_establishment_birth')::BIGINT AS unknown_age_negative,
          count(*) FILTER(WHERE legal_age_days=0)::BIGINT AS legal_age_zero_day_births,
          count(*) FILTER(WHERE legal_age_days>0)::BIGINT AS legal_age_positive_day_births,
          coalesce(sum(legal_age_days),0)::BIGINT AS sum_legal_age_days,
          coalesce(sum(legal_age_days::HUGEINT*legal_age_days::HUGEINT),0)::BIGINT AS sum_squared_legal_age_days,
          avg(legal_age_days)::DOUBLE AS mean_legal_age_days,
          coalesce(sum(legal_age_completed_months),0)::BIGINT AS sum_legal_age_completed_months,
          coalesce(sum(legal_age_completed_months::HUGEINT*legal_age_completed_months::HUGEINT),0)::BIGINT AS sum_squared_legal_age_completed_months,
          avg(legal_age_completed_months)::DOUBLE AS mean_legal_age_completed_months,
          min(legal_age_days)::BIGINT AS min_legal_age_days,
          max(legal_age_days)::BIGINT AS max_legal_age_days
        FROM birth_structure_records GROUP BY 1,2;
        CREATE TEMP TABLE birth_structure_output AS
        SELECT p.commune_code,p.month,p.establishment_births,
          coalesce(a.headquarters_births,0)::BIGINT AS headquarters_births,
          coalesce(a.non_headquarters_births,0)::BIGINT AS non_headquarters_births,
          coalesce(a.unknown_headquarters_births,0)::BIGINT AS unknown_headquarters_births,
          coalesce(a.unknown_hq_no_interval,0)::BIGINT AS unknown_hq_no_interval,
          coalesce(a.unknown_hq_ambiguous_intervals,0)::BIGINT AS unknown_hq_ambiguous_intervals,
          coalesce(a.unknown_hq_missing_nic,0)::BIGINT AS unknown_hq_missing_nic,
          coalesce(a.unknown_hq_invalid_historical_nic,0)::BIGINT AS unknown_hq_invalid_historical_nic,
          coalesce(a.unknown_hq_invalid_establishment_nic,0)::BIGINT AS unknown_hq_invalid_establishment_nic,
          coalesce(a.known_legal_age_births,0)::BIGINT AS known_legal_age_births,
          coalesce(a.unknown_legal_age_births,0)::BIGINT AS unknown_legal_age_births,
          coalesce(a.unknown_age_missing_legal_unit,0)::BIGINT AS unknown_age_missing_legal_unit,
          coalesce(a.unknown_age_missing_date,0)::BIGINT AS unknown_age_missing_date,
          coalesce(a.unknown_age_date_1900,0)::BIGINT AS unknown_age_date_1900,
          coalesce(a.unknown_age_pre_1800,0)::BIGINT AS unknown_age_pre_1800,
          coalesce(a.unknown_age_negative,0)::BIGINT AS unknown_age_negative,
          coalesce(a.legal_age_zero_day_births,0)::BIGINT AS legal_age_zero_day_births,
          coalesce(a.legal_age_positive_day_births,0)::BIGINT AS legal_age_positive_day_births,
          coalesce(a.sum_legal_age_days,0)::BIGINT AS sum_legal_age_days,
          coalesce(a.sum_squared_legal_age_days,0)::BIGINT AS sum_squared_legal_age_days,
          a.mean_legal_age_days,
          coalesce(a.sum_legal_age_completed_months,0)::BIGINT AS sum_legal_age_completed_months,
          coalesce(a.sum_squared_legal_age_completed_months,0)::BIGINT AS sum_squared_legal_age_completed_months,
          a.mean_legal_age_completed_months,a.min_legal_age_days,a.max_legal_age_days
        FROM sourcebuild.main.monthly_panel p
        LEFT JOIN birth_structure_aggregate a USING(commune_code,month);
    """)
    identity_failures = int(c.sql("""SELECT count(*) FROM birth_structure_output WHERE
        establishment_births!=headquarters_births+non_headquarters_births+unknown_headquarters_births
        OR unknown_headquarters_births!=unknown_hq_no_interval+unknown_hq_ambiguous_intervals+unknown_hq_missing_nic+unknown_hq_invalid_historical_nic+unknown_hq_invalid_establishment_nic
        OR establishment_births!=known_legal_age_births+unknown_legal_age_births
        OR unknown_legal_age_births!=unknown_age_missing_legal_unit+unknown_age_missing_date+unknown_age_date_1900+unknown_age_pre_1800+unknown_age_negative
        OR known_legal_age_births!=legal_age_zero_day_births+legal_age_positive_day_births
        OR (known_legal_age_births=0 AND (mean_legal_age_days IS NOT NULL OR mean_legal_age_completed_months IS NOT NULL))
        OR (known_legal_age_births>0 AND (mean_legal_age_days IS NULL OR mean_legal_age_completed_months IS NULL))
        OR sum_legal_age_days<0 OR sum_legal_age_completed_months<0""").fetchone()[0])
    count_mismatches = int(c.sql("""SELECT count(*) FROM sourcebuild.main.monthly_panel p
        FULL JOIN birth_structure_aggregate a USING(commune_code,month)
        WHERE coalesce(p.establishment_births,0)!=coalesce(a.establishment_births,0)""").fetchone()[0])
    if identity_failures or count_mismatches:
        raise RuntimeError("Birth structure has aggregate identity or main-panel count failures.")
    # Deterministic dispersed observations are checked without exporting keys.
    # Month anniversaries use the same end-of-month clamping as SQL intervals.
    sample = c.sql("""SELECT legal_creation_date,creation_date,legal_age_days,legal_age_completed_months
        FROM birth_structure_records WHERE legal_age_category='known'
        ORDER BY hash(siret,20241003) LIMIT 200""").fetchall()
    import calendar
    arithmetic_failures = 0
    for legal_date, birth_date, days, months in sample:
        m = (birth_date.year-legal_date.year)*12+birth_date.month-legal_date.month
        anniv_day = min(legal_date.day,calendar.monthrange(birth_date.year,birth_date.month)[1])
        expected_months = m-int(anniv_day>birth_date.day)
        arithmetic_failures += int(days!=(birth_date-legal_date).days or months!=expected_months)
    if arithmetic_failures:
        raise RuntimeError("Independent Python age arithmetic differs from SQL; identifiers withheld.")
    hq_distribution = c.sql("SELECT headquarters_category,count(*)::BIGINT AS n FROM birth_structure_records GROUP BY 1 ORDER BY 1").df().to_dict("records")
    age_distribution = c.sql("SELECT legal_age_category,count(*)::BIGINT AS n FROM birth_structure_records GROUP BY 1 ORDER BY 1").df().to_dict("records")
    moments = c.sql("""SELECT count(legal_age_days)::BIGINT AS known_count,
        sum(legal_age_days)::BIGINT AS sum_days,avg(legal_age_days) AS mean_days,
        sum(legal_age_completed_months)::BIGINT AS sum_completed_months,
        avg(legal_age_completed_months) AS mean_completed_months,
        min(legal_age_days)::BIGINT AS minimum_days,max(legal_age_days)::BIGINT AS maximum_days,
        count(*) FILTER(WHERE legal_age_days=0)::BIGINT AS zero_day_count,
        count(*) FILTER(WHERE legal_age_days>0)::BIGINT AS positive_day_count
        FROM birth_structure_records""").df().to_dict("records")[0]
    counts = c.sql("""SELECT count(*)::BIGINT AS panel_rows,count(DISTINCT commune_code)::BIGINT AS panel_communes,
        sum(establishment_births)::BIGINT AS establishment_births
        FROM birth_structure_output""").df().to_dict("records")[0]
    print('Independent Python reclassification of 20 audit cells',flush=True)
    cell_audit = independent_cell_audit(c,ul,uh)
    filename = ROOT / "data/processed/birth_structure.parquet"
    c.execute(f"COPY birth_structure_output TO '{sqlpath(filename)}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    columns = [row[0] for row in c.sql("DESCRIBE birth_structure_output").fetchall()]
    assert not set(columns) & {'siren','siret','nic','historical_hq_nic','legal_creation_date'}
    roundtrip = int(c.sql(f"SELECT count(*) FROM read_parquet('{sqlpath(filename)}')").fetchone()[0])
    assert roundtrip==counts['panel_rows']
    report = {
        'status':'PASSED', 'generated_at_utc':datetime.now(timezone.utc).isoformat(),
        **counts, 'headquarters_categories':hq_distribution,'legal_age_categories':age_distribution,
        'known_legal_age_birth_cohort_moments':moments,
        'pre_1800_flagged_date_years':c.sql("SELECT year(legal_creation_date)::INTEGER AS year,count(*)::BIGINT AS establishment_births FROM birth_structure_records WHERE legal_age_category='pre_1800_date_requires_verification' GROUP BY 1 ORDER BY 1").df().to_dict('records'),
        'duplicate_primary_birth_keys':duplicate_births,'duplicate_legal_unit_stock_keys':duplicate_source_units,
        'aggregate_identity_failures':identity_failures,'primary_monthly_birth_count_mismatches':count_mismatches,
        'independent_age_arithmetic_sample_n':len(sample),'independent_age_arithmetic_failures':arithmetic_failures,
        'independent_raw_source_cell_audit':cell_audit,
        'headquarters_definition':'Compare establishment NIC to unique official legal-unit historical NIC at establishment registration date; inclusive start/end; no current-HQ backfill; unknown/ambiguous intervals or invalid NIC stay unknown.',
        'age_definition':'Fixed legal-unit declared creation date to establishment creation date; days and completed calendar month anniversaries with end-of-month clamping. Missing legal unit/date, official 1900-01-01 sentinel, analyst quality flag dates before 1800-01-01 and negative ages stay unknown.',
        'analyst_age_quality_minimum_date':'1800-01-01',
        'analyst_filter_status':'Conservative analysis quality filter chosen after inspecting source dates; not an official INSEE sentinel or claim that every earlier date is false. Flagged records remain counted and HQ classification is unchanged.',
        'official_date_documentation':'data/external/sirene_dictionary/api_141_2ed989b6-001c-4b22-9989-b6001c6b224e.md, dateCreationUniteLegale section: 1900-01-01 for missing date; no 0001 sentinel definition found in archived official Markdown.',
        'interpretation':'Registration-cohort composition; not average age of active firms, employment, output or economic survival. Establishment-location codes retain the main-panel geographic limitations.',
        'SIRENE_headquarters_natural_persons':'Official dictionary explains that natural-person headquarters have no juridical reality; SIRENE assigns an administrative headquarters by analogy with legal persons.',
        'weighting':'Each establishment registration contributes once; legal units with multiple new establishments contribute multiple times. Means use known-age records only.',
        'output_columns':columns,'output_bytes':filename.stat().st_size,
        'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (ROOT / 'reports/birth_structure_quality.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    hq = {r['headquarters_category']:r['n'] for r in hq_distribution}
    ages = {r['legal_age_category']:r['n'] for r in age_distribution}
    lines = [
        '# 历史总部状态与设立时法律单位年龄：质量核查', '',
        '状态：PASSED。主数据库以只读方式连接；主面板和论文源文件未修改。仅输出 commune×month 聚合计数与年龄矩。', '',
        f"- 覆盖 {counts['panel_rows']:,} 个 commune×month、{counts['panel_communes']:,} 个 communes、{counts['establishment_births']:,} 笔 establishment 设立。",
        f"- 当时总部：{hq.get('headquarters',0):,}；当时非总部：{hq.get('non_headquarters',0):,}；未知：{sum(v for k,v in hq.items() if k not in ('headquarters','non_headquarters')):,}。",
        f"- 法律单位年龄已知：{ages.get('known',0):,}；未知：{sum(v for k,v in ages.items() if k!='known'):,}。",
        f"- 已知年龄记录的均值：{moments['mean_days']:.6f} 日；{moments['mean_completed_months']:.6f} 个已完成历月。",
        f"- 主月度设立计数差异 {count_mismatches}；分类恒等式失败 {identity_failures}；独立 Python 年龄算术检查 {len(sample)} 笔，差异 {arithmetic_failures}。", '',
        f"- 从原始 UL/UH 对既有 20 个审计单元重新执行 Python 分类：{cell_audit['sample_births']} 笔设立，{cell_audit['comparisons']} 项计数/矩比较，差异 {cell_audit['failures']}。", '',
        '总部是 SIRENE 行政定义；官方字典说明自然人的总部不具有法律意义，而是按法人结构类比赋予。总部状态使用设立日涵盖的唯一 UL 历史区间（起止日均包含），将其 nicSiege 与 establishment NIC 比较。无区间、多区间、缺失或异常 NIC 均为未知；不回填当前总部。', '',
        '法律单位日期来自官方 UL 固定 dateCreationUniteLegale。缺失单位、缺失日期、官方规定的 1900-01-01 占位日期及晚于 establishment 设立的日期均为未知。另按分析质量规则把 1800-01-01 以前的日期标记为待核实，并从年龄矩的已知样本中剔除；原设立记录及其总部分类仍保留。这是检查来源日期后采用的保守质量过滤，不是 INSEE 的官方日期规则，亦不宣称所有早期日期肯定错误。归档官方变量文档没有找到 0001 作为占位日期的定义。按日计算差额；已完成历月按从法律创建日起的月周年计算，短月份取月末。日期修订可能产生负年龄，这些记录不作为零岁。', '',
        '这些均值描述新设 establishment 所属法律单位的行政年龄；按 establishment 设立笔数加权，多次设立的法律单位会多次贡献。它们不是活跃企业存量的平均年龄，也不代表首次生产、雇佣或经济存活。零设立或全未知的单元均值保持 NULL，计数及可加总矩为零。', '',
        '未知原因逐类计数见 JSON；输出不包含 SIREN、SIRET、NIC、姓名或详细地址。继承主面板的 establishment 注册地口径与地理限制，不宣称重建了每一地址的历史迁移。', '',
        '| 总部识别类别 | 笔数 |','|---|---:|',
    ]
    lines += [f"| {key} | {value:,} |" for key,value in hq.items()]
    lines += ['', '| 年龄识别类别 | 笔数 |','|---|---:|']
    lines += [f"| {key} | {value:,} |" for key,value in ages.items()]
    (ROOT / 'reports/birth_structure_quality.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    c.close()
    print(json.dumps({k:report[k] for k in ['status','panel_rows','establishment_births','aggregate_identity_failures','primary_monthly_birth_count_mismatches','output_bytes']}),flush=True)


if __name__=='__main__':
    main()
