"""Administrative cohort retention and historical-HQ attrition diagnostics.

Outputs are aggregates; unit identifiers remain only in ignored local temp
storage. Existing monthly_panel and analysis.duckdb are read, never modified.
"""
from pathlib import Path
from datetime import datetime, timezone
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".vendor"))
import duckdb
import pandas as pd


def sqlpath(path):
    return str(path).replace("\\", "/").replace("'", "''")


def duplicate_graph_diagnostics(pairs):
    """Use every unique directed edge, including ambiguous multiple targets."""
    import networkx as nx
    graph = nx.DiGraph()
    graph.add_edges_from(zip(pairs.sirenDoublon, pairs.siren))
    wrong_ids = set(pairs.sirenDoublon)
    target_counts = pairs.groupby("sirenDoublon").siren.nunique()
    ambiguous_ids = set(target_counts[target_counts>1].index)
    cyclic_components = [component for component in nx.strongly_connected_components(graph)
                         if len(component)>1 or any(graph.has_edge(node,node) for node in component)]
    cyclic_nodes = set().union(*cyclic_components) if cyclic_components else set()
    return {"duplicate_alias_rows": len(pairs), "duplicate_wrong_ids": len(wrong_ids),
            "duplicate_alias_edges": graph.number_of_edges(),
            "duplicate_alias_chain_edges": sum(int(target in wrong_ids) for _, target in graph.edges),
            "duplicate_alias_ambiguous_targets": len(ambiguous_ids),
            "duplicate_alias_cycle_components": len(cyclic_components),
            "duplicate_alias_cycle_nodes": len(cyclic_nodes)}, ambiguous_ids | cyclic_nodes


def main():
    out = ROOT / "data/intermediate/secondary"
    out.mkdir(parents=True, exist_ok=True)
    c = duckdb.connect()
    c.execute("SET memory_limit='5GB'")
    c.execute("SET threads=2")
    c.execute(f"SET temp_directory='{sqlpath(out / 'spill')}'")
    c.execute(f"ATTACH '{sqlpath(ROOT / 'data/intermediate/analysis.duckdb')}' AS mainbuild (READ_ONLY)")
    meta = pd.read_csv(ROOT / "data/processed/commune_treatment.csv", dtype=str,
                       usecols=["commune_code", "analysis_stable", "treatment_group"])
    meta["stable"] = meta.analysis_stable.str.lower().eq("true")
    c.register("commune_meta", meta)
    def raw(name):
        return f"read_parquet('{sqlpath(ROOT / 'data/raw' / ('stock-' + name + '-parquet.parquet'))}')"
    def run(label, sql):
        print(label, flush=True)
        start = time.time()
        c.execute(sql)
        print(f"{label}: {time.time()-start:.1f}s", flush=True)
    def export(table, filename):
        c.execute(f"COPY {table} TO '{sqlpath(ROOT / 'data/processed' / filename)}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    historical_state_distribution = c.sql(f"""SELECT etatAdministratifEtablissement AS administrative_state,
        caractereEmployeurEtablissement AS employer,count(*)::BIGINT AS n_periods
        FROM {raw('stocketablissementhistorique')} GROUP BY 1,2 ORDER BY 1,2 NULLS LAST""").df().to_dict("records")
    birth_state_distribution = c.sql("""SELECT state_at_creation AS administrative_state,
        employer_at_creation AS employer,count(*)::BIGINT AS n_births
        FROM mainbuild.main.births GROUP BY 1,2 ORDER BY 1,2 NULLS LAST""").df().to_dict("records")
    duplicate_pairs = c.sql(f"SELECT sirenDoublon,siren FROM {raw('stockdoublons')}").df()
    graph_stats, anomalous_ids = duplicate_graph_diagnostics(duplicate_pairs)
    # The primary pipeline excludes every listed wrong ID; it does not attempt
    # canonical redirection. Official graph anomalies must be reported, but do
    # not justify fabricating a unique valid ID or stopping unrelated cohorts.
    c.register("anomalous_duplicate_ids", pd.DataFrame({"siren": sorted(anomalous_ids)}))
    anomalous_recent_ul = int(c.sql(f"""SELECT count(*) FROM {raw('stockunitelegale')} u
        JOIN anomalous_duplicate_ids a ON u.siren=a.siren
        WHERE u.dateCreationUniteLegale BETWEEN DATE '2019-01-01' AND DATE '2026-06-30'""").fetchone()[0])
    anomalous_recent_e = int(c.sql(f"""SELECT count(*) FROM {raw('stocketablissement')} e
        JOIN anomalous_duplicate_ids a ON e.siren=a.siren JOIN commune_meta m
        ON e.codeCommuneEtablissement=m.commune_code AND m.stable
        WHERE e.dateCreationEtablissement BETWEEN DATE '2019-01-01' AND DATE '2026-06-30'""").fetchone()[0])
    run("Construct complete-follow-up cohort horizons", """
        CREATE TEMP TABLE cohort_horizons AS
        SELECT siret,commune_code,creation_date,date_trunc('month',creation_date)::DATE AS cohort_month,
        horizon_months,(creation_date+horizon_months*INTERVAL '1 month')::DATE AS horizon_date,
        (state_at_creation='A' AND employer_at_creation='O') AS employer_at_birth
        FROM mainbuild.main.births CROSS JOIN (VALUES (12),(18)) h(horizon_months)
        WHERE (creation_date+horizon_months*INTERVAL '1 month')::DATE<=DATE '2026-06-30';
    """)
    run("Historical administrative status at 12 and 18 months", f"""
        CREATE TEMP TABLE cohort_status AS
        SELECT b.*,h.etatAdministratifEtablissement AS horizon_state
        FROM cohort_horizons b LEFT JOIN {raw('stocketablissementhistorique')} h
        ON b.siret=h.siret AND h.dateDebut<=b.horizon_date
        AND coalesce(h.dateFin,DATE '9999-12-31')>=b.horizon_date;
    """)
    overlaps = int(c.sql("""SELECT count(*) FROM (
        SELECT siret,horizon_months FROM cohort_status GROUP BY 1,2 HAVING count(*)>1)
        """).fetchone()[0])
    if overlaps:
        raise RuntimeError(f"Retention horizon contains {overlaps} overlapping unit-period matches; IDs withheld.")
    run("Aggregate administrative retention with explicit unknowns", """
        CREATE TEMP TABLE retention_results AS
        WITH total AS (
          SELECT commune_code,date_trunc('month',creation_date)::DATE AS cohort_month,horizon_months,
          count(*) AS n_registered_cohort,
          count(*) FILTER(WHERE (creation_date+horizon_months*INTERVAL '1 month')::DATE>DATE '2026-06-30') AS n_censored
          FROM mainbuild.main.births CROSS JOIN (VALUES (12),(18)) h(horizon_months) GROUP BY 1,2,3
        ), observed AS (
          SELECT commune_code,cohort_month,horizon_months,count(*) AS n_eligible,
          count(*) FILTER(WHERE horizon_state='A') AS n_active_at_horizon,
          count(*) FILTER(WHERE horizon_state='F') AS n_closed_at_horizon,
          count(*) FILTER(WHERE horizon_state IN ('A','F')) AS n_known_horizon,
          count(*) FILTER(WHERE horizon_state IS NULL OR horizon_state NOT IN ('A','F')) AS n_unknown_horizon,
          count(*) FILTER(WHERE employer_at_birth) AS n_employer_eligible,
          count(*) FILTER(WHERE employer_at_birth AND horizon_state='A') AS n_employer_active_at_horizon,
          count(*) FILTER(WHERE employer_at_birth AND horizon_state IN ('A','F')) AS n_employer_known_horizon,
          count(*) FILTER(WHERE employer_at_birth AND (horizon_state IS NULL OR horizon_state NOT IN ('A','F'))) AS n_employer_unknown_horizon
          FROM cohort_status GROUP BY 1,2,3
        )
        SELECT p.commune_code,p.month AS cohort_month,h.horizon_months,
        coalesce(t.n_registered_cohort,0) AS n_registered_cohort,coalesce(t.n_censored,0) AS n_censored,
        coalesce(o.n_eligible,0) AS n_eligible,coalesce(o.n_active_at_horizon,0) AS n_active_at_horizon,
        coalesce(o.n_closed_at_horizon,0) AS n_closed_at_horizon,
        coalesce(o.n_known_horizon,0) AS n_known_horizon,coalesce(o.n_unknown_horizon,0) AS n_unknown_horizon,
        coalesce(o.n_employer_eligible,0) AS n_employer_eligible,
        coalesce(o.n_employer_active_at_horizon,0) AS n_employer_active_at_horizon,
        coalesce(o.n_employer_known_horizon,0) AS n_employer_known_horizon,
        coalesce(o.n_employer_unknown_horizon,0) AS n_employer_unknown_horizon,
        o.n_active_at_horizon::DOUBLE/nullif(o.n_known_horizon,0) AS administrative_retention_known,
        o.n_active_at_horizon::DOUBLE/nullif(o.n_eligible,0) AS administrative_retention_lower_bound,
        (o.n_active_at_horizon+o.n_unknown_horizon)::DOUBLE/nullif(o.n_eligible,0) AS administrative_retention_upper_bound,
        o.n_employer_active_at_horizon::DOUBLE/nullif(o.n_employer_known_horizon,0) AS employer_cohort_administrative_retention_known
        FROM mainbuild.main.monthly_panel p CROSS JOIN (VALUES (12),(18)) h(horizon_months)
        LEFT JOIN total t ON p.commune_code=t.commune_code AND p.month=t.cohort_month AND h.horizon_months=t.horizon_months
        LEFT JOIN observed o ON p.commune_code=o.commune_code AND p.month=o.cohort_month AND h.horizon_months=o.horizon_months;
    """)
    identities = int(c.sql("""SELECT count(*) FROM retention_results WHERE
        n_registered_cohort!=n_eligible+n_censored OR n_eligible!=n_known_horizon+n_unknown_horizon
        OR n_known_horizon!=n_active_at_horizon+n_closed_at_horizon
        OR n_employer_eligible!=n_employer_known_horizon+n_employer_unknown_horizon
        OR n_employer_active_at_horizon>n_employer_known_horizon""").fetchone()[0])
    if identities:
        raise RuntimeError(f"Administrative retention has {identities} aggregate identity failures.")
    export("retention_results", "administrative_retention_cohorts.parquet")
    retention = c.sql("""SELECT horizon_months,sum(n_registered_cohort)::BIGINT AS registered,
        sum(n_eligible)::BIGINT AS eligible,sum(n_censored)::BIGINT AS censored,
        sum(n_active_at_horizon)::BIGINT AS active,sum(n_closed_at_horizon)::BIGINT AS closed,
        sum(n_unknown_horizon)::BIGINT AS unknown,sum(n_employer_eligible)::BIGINT AS employer_eligible,
        sum(n_employer_active_at_horizon)::BIGINT AS employer_active
        FROM retention_results GROUP BY 1 ORDER BY 1""").df().to_dict("records")
    run("Project all legal-unit birth dates before HQ location", f"""
        CREATE TEMP TABLE ul_candidates AS SELECT u.siren,u.dateCreationUniteLegale AS creation_date
        FROM {raw('stockunitelegale')} u
        WHERE u.dateCreationUniteLegale BETWEEN DATE '2019-01-01' AND DATE '2026-06-30'
        AND NOT EXISTS (SELECT 1 FROM {raw('stockdoublons')} d WHERE u.siren=d.sirenDoublon);
    """)
    run("Audit historical HQ location stage by stage", f"""
        CREATE TEMP TABLE ul_hq_stage AS
        SELECT u.siren,u.creation_date,h.siren AS history_siren,h.nicSiegeUniteLegale AS hq_nic,
        e.siret AS hq_siret,e.dateCreationEtablissement AS hq_creation_date,
        e.codeCommuneEtablissement AS commune_code,coalesce(m.stable,false) AS stable,
        CASE WHEN h.siren IS NULL THEN '01_no_UL_interval_at_birth'
             WHEN h.nicSiegeUniteLegale IS NULL THEN '02_missing_historical_HQ_NIC'
             WHEN e.siret IS NULL THEN '03_no_HQ_SIRET_in_official_stock'
             WHEN e.dateCreationEtablissement IS NULL THEN '04_HQ_creation_date_NULL'
             WHEN e.dateCreationEtablissement>u.creation_date THEN '05_HQ_created_after_UL_birth'
             WHEN e.codeCommuneEtablissement IS NULL THEN '06_HQ_commune_NULL'
             WHEN NOT coalesce(m.stable,false) THEN '07_outside_stable_analysis_communes'
             ELSE '08_located_in_main_sample' END AS stage
        FROM ul_candidates u LEFT JOIN {raw('stockunitelegalehistorique')} h
        ON u.siren=h.siren AND h.dateDebut<=u.creation_date
        AND coalesce(h.dateFin,DATE '9999-12-31')>=u.creation_date
        LEFT JOIN {raw('stocketablissement')} e ON e.siret=u.siren||h.nicSiegeUniteLegale
        LEFT JOIN commune_meta m ON e.codeCommuneEtablissement=m.commune_code;
    """)
    ul_overlaps = int(c.sql("SELECT count(*) FROM (SELECT siren FROM ul_hq_stage GROUP BY 1 HAVING count(*)>1)").fetchone()[0])
    if ul_overlaps:
        raise RuntimeError(f"UL HQ audit contains {ul_overlaps} duplicate birth-period locations; IDs withheld.")
    stage_counts = c.sql("SELECT stage,count(*)::BIGINT AS n FROM ul_hq_stage GROUP BY 1 ORDER BY 1").df()
    all_stages = ['01_no_UL_interval_at_birth','02_missing_historical_HQ_NIC',
                  '03_no_HQ_SIRET_in_official_stock','04_HQ_creation_date_NULL',
                  '05_HQ_created_after_UL_birth','06_HQ_commune_NULL',
                  '07_outside_stable_analysis_communes','08_located_in_main_sample']
    stage_counts = stage_counts.set_index('stage').reindex(all_stages,fill_value=0).reset_index()
    stage_counts.to_csv(ROOT / "reports/UL_historical_HQ_stage_counts.csv", index=False, encoding="utf8")
    stage_by_month = c.sql("""SELECT date_trunc('month',creation_date)::DATE AS birth_month,stage,count(*) AS n
        FROM ul_hq_stage GROUP BY 1,2 ORDER BY 1,2""").df()
    stage_by_month.to_csv(ROOT / "reports/UL_historical_HQ_stage_counts_monthly.csv", index=False, encoding="utf8")
    located = int(c.sql("SELECT count(*) FROM ul_hq_stage WHERE stage='08_located_in_main_sample'").fetchone()[0])
    mainlocated = int(c.sql("SELECT count(*) FROM mainbuild.main.unit_births").fetchone()[0])
    if located != mainlocated:
        raise RuntimeError("Independently reconstructed UL HQ location total differs from primary pipeline.")
    excluded_dup_ul = int(c.sql(f"""SELECT count(*) FROM {raw('stockunitelegale')} u
        WHERE u.dateCreationUniteLegale BETWEEN DATE '2019-01-01' AND DATE '2026-06-30'
        AND EXISTS (SELECT 1 FROM {raw('stockdoublons')} d WHERE u.siren=d.sirenDoublon)""").fetchone()[0])
    unknown_hq_creation = int(c.sql("SELECT count(*) FROM ul_hq_stage WHERE hq_creation_date=DATE '1900-01-01'").fetchone()[0])
    # Events are dated by historical effective start and located at the HQ of
    # the same historical period. Current UL state and current HQ are not used.
    run("Historical legal cessation and reactivation events", f"""
        CREATE TEMP TABLE legal_events AS
        WITH periods AS (
          SELECT h.siren,h.dateDebut,h.nicSiegeUniteLegale,h.etatAdministratifUniteLegale,
          lag(h.etatAdministratifUniteLegale) OVER(PARTITION BY h.siren ORDER BY h.dateDebut NULLS FIRST) AS previous_state
          FROM {raw('stockunitelegalehistorique')} h
          WHERE EXISTS (SELECT 1 FROM mainbuild.main.establishments e WHERE e.siren=h.siren)
        )
        SELECT h.siren,h.dateDebut AS event_date,h.nicSiegeUniteLegale AS hq_nic,
        h.etatAdministratifUniteLegale AS new_state,h.previous_state,
        e.commune_code,e.creation_date AS hq_creation_date
        FROM periods h LEFT JOIN mainbuild.main.establishments e
        ON e.siret=h.siren||h.nicSiegeUniteLegale
        WHERE h.dateDebut BETWEEN DATE '2019-01-01' AND DATE '2026-06-30'
        AND ((h.previous_state='A' AND h.etatAdministratifUniteLegale='C')
          OR (h.previous_state='C' AND h.etatAdministratifUniteLegale='A'));
        CREATE TEMP TABLE monthly_legal_events AS
        SELECT commune_code,date_trunc('month',event_date)::DATE AS month,
        count(*) FILTER(WHERE previous_state='A' AND new_state='C') AS legal_cessation_events,
        count(*) FILTER(WHERE previous_state='C' AND new_state='A') AS legal_reactivation_events
        FROM legal_events WHERE commune_code IS NOT NULL AND hq_creation_date<=event_date GROUP BY 1,2;
    """)
    # Alias the source explicitly: unqualified siren in a correlated subquery
    # can otherwise bind to its inner table instead of the historical record.
    run("Historical establishment reopen events", f"""
        CREATE TEMP TABLE monthly_reopens AS
        WITH periods AS (
          SELECT h.siret,h.dateDebut,h.etatAdministratifEtablissement,
          lag(h.etatAdministratifEtablissement) OVER(PARTITION BY h.siret ORDER BY h.dateDebut NULLS FIRST) AS previous_state
          FROM {raw('stocketablissementhistorique')} h
          WHERE EXISTS (SELECT 1 FROM mainbuild.main.establishments e WHERE e.siret=h.siret)
        )
        SELECT e.commune_code,date_trunc('month',h.dateDebut)::DATE AS month,count(*) AS establishment_reopen_events
        FROM periods h JOIN mainbuild.main.establishments e ON h.siret=e.siret
        WHERE h.previous_state='F' AND h.etatAdministratifEtablissement='A'
        AND h.dateDebut BETWEEN DATE '2019-01-01' AND DATE '2026-06-30' GROUP BY 1,2;
        CREATE TEMP TABLE administrative_events_results AS
        SELECT p.commune_code,p.month,p.establishment_closures,
        coalesce(r.establishment_reopen_events,0) AS establishment_reopen_events,
        coalesce(l.legal_cessation_events,0) AS legal_cessation_events,
        coalesce(l.legal_reactivation_events,0) AS legal_reactivation_events
        FROM mainbuild.main.monthly_panel p LEFT JOIN monthly_reopens r USING(commune_code,month)
        LEFT JOIN monthly_legal_events l USING(commune_code,month);
    """)
    export("administrative_events_results", "secondary_administrative_events.parquet")
    eventtotals = c.sql("""SELECT sum(establishment_closures)::BIGINT AS establishment_closures,
        sum(establishment_reopen_events)::BIGINT AS establishment_reopens,
        sum(legal_cessation_events)::BIGINT AS legal_cessations,
        sum(legal_reactivation_events)::BIGINT AS legal_reactivations
        FROM administrative_events_results""").df().to_dict("records")[0]
    unknown_event_hq = int(c.sql("SELECT count(*) FROM legal_events WHERE commune_code IS NULL OR hq_creation_date IS NULL OR hq_creation_date>event_date").fetchone()[0])
    summary = {"status": "PASSED", "end_of_followup": "2026-06-30",
               "retention_concept": "Administrative state A at anniversary, not economic or continuous survival.",
               "unknown_rule": "Unmatched or unknown historical state is unknown, never coded as closure.",
               "retention_horizons": retention, "retention_identity_failures": identities,
               "retention_overlap_matches": overlaps, "UL_birth_stages": stage_counts.to_dict("records"),
               "UL_historical_HQ_located": located, "UL_primary_pipeline_located": mainlocated,
               "UL_duplicate_siren_births_excluded": excluded_dup_ul,
               **graph_stats,
               "anomalous_duplicate_UL_births_2019_2026_national": anomalous_recent_ul,
               "anomalous_duplicate_establishment_births_2019_2026_analysis_communes": anomalous_recent_e,
               "duplicate_policy": "All listed sirenDoublon excluded; no ambiguous canonical redirection performed.",
               "UL_historical_HQ_unknown_creation_date_1900": unknown_hq_creation,
               "national_establishment_historical_state_distribution": historical_state_distribution,
               "analysis_birth_state_distribution": birth_state_distribution,
               "administrative_event_totals": eventtotals,
               "legal_events_with_unlocatable_or_future_HQ_in_analysis_candidate_units": unknown_event_hq,
               "generated_at_utc": datetime.now(timezone.utc).isoformat()}
    (ROOT / "reports/secondary_outcomes_quality.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf8")
    lines = ["# 行政留存、历史总部定位与状态事件核查", "", "状态：PASSED。",
             "", "12 / 18 个月留存只使用 horizon 日期不晚于 2026-06-30 的完整随访 cohorts；未知历史区间单列，不当作死亡。",
             "留存为 anniversary 当日 état A，允许关闭后再开业；不代表连续存活或经济存活。known 分母与 unknown bounds 同时提供。",
             "12 个月最后完整 birth 月为 2025-06；18 个月为 2024-12。更晚 cohorts 的 n_censored 明示，留存率为空。",
             "", "| Horizon | Eligible | Active A | Closed F | Unknown | Censored |", "|---|---:|---:|---:|---:|---:|"]
    lines += [f"| {r['horizon_months']} | {r['eligible']:,} | {r['active']:,} | {r['closed']:,} | {r['unknown']:,} | {r['censored']:,} |" for r in retention]
    lines += ["", "UL birth 的历史 HQ 漏配阶段按全国日期有效、去除错误 duplicate SIREN 后的 UL births 计算；缺位阶段无法可靠分配 T/C，不猜测其政策归属。", "",
              "| Stage | N |", "|---|---:|"]
    lines += [f"| {r['stage']} | {r['n']:,} |" for r in stage_counts.to_dict("records")]
    lines += ["", f"历史总部可定位 {located:,}，与主 pipeline {mainlocated:,} 一致。错误 duplicate SIREN births 排除 {excluded_dup_ul:,}。",
              f"官方 duplicate mapping 有 {graph_stats['duplicate_alias_edges']:,} 条唯一边、{graph_stats['duplicate_wrong_ids']:,} 个 wrong IDs，其中链式边 {graph_stats['duplicate_alias_chain_edges']:,}；多目标 {graph_stats['duplicate_alias_ambiguous_targets']}、循环节点 {graph_stats['duplicate_alias_cycle_nodes']}。",
              f"上述多目标/循环涉及日期窗口内全国 UL births {anomalous_recent_ul}、研究 commune establishment births {anomalous_recent_e}。主构造排除全部 sirenDoublon，未重定向合并；不得宣称每个 alias 均已找到唯一最终有效号。",
              f"总部 establishment 的创建日期 1900 占 {unknown_hq_creation:,} 条，单列诊断；location 仍由 birth 时历史 NIC 指向，而非 current HQ。",
              "", "legal A→C / C→A 使用 UL 历史 dateDebut 及同期 HQ；establishment F→A 使用 establishment 历史，均不回填 current state。",
              "", json.dumps(eventtotals, ensure_ascii=False),
              f"候选 UL 中事件 HQ 不可定位或晚于事件日期 {unknown_event_hq:,}，不补零为真实无事件。",
              "", "全国 establishment 历史 A/F × employer O/N/unknown 分布及 analysis birth 时分布见同名 JSON。F/O 历史期间不能因 O 被计为 active employer；birth 状态 F 的注册保留在全体行政注册指标，排除在 active employer birth 及其已知分母外。",
              "", "输出仅为 commune-month/cohort 聚合，原始标识只在 ignored 临时存储。行政状态和注册变更不能直接证明经济活动、政策资格、税收减免或雇员数量。"]
    (ROOT / "reports/secondary_outcomes_quality.md").write_text("\n".join(lines)+"\n", encoding="utf8")
    c.close()
    print(json.dumps(summary, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
