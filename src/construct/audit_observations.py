"""Independent official-source checks; published outputs contain no unit IDs.

Run only after construct_panel.py has released its DuckDB write lock.
The random seed is fixed, sample cells are stratified, and interval selection
and outcome classification are recomputed in Python rather than copied SQL.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".vendor"))
import duckdb
import numpy as np
import pandas as pd

SEED = 20241003
MEASURES = ["establishment_births", "employer_births", "known_employer_births",
            "unknown_naf_births", "births_without_recorded_continuity",
            "recorded_continuity_births", "commerce", "accommodation_food",
            "construction", "manufacturing", "professional_services", "health",
            "proximity_services", "legal_unit_births", "individual_births",
            "establishment_closures", "registration_minus_closure_balance"]
SECTORS = {"commerce": set(range(45, 48)), "accommodation_food": {55, 56},
           "construction": {41, 42, 43}, "manufacturing": set(range(10, 34)),
           "professional_services": set(range(69, 76)), "health": {86},
           "proximity_services": {95, 96}}


def sqlpath(path):
    return str(path).replace("\\", "/").replace("'", "''")


def present(value):
    return not pd.isna(value)


def at_date(history, date):
    """Independent inclusive interval lookup; unknown/multiple matches fail."""
    rows = [r for r in history if present(r["start"]) and r["start"] <= date
            and (not present(r["end"]) or date <= r["end"])]
    if len(rows) > 1:
        raise RuntimeError("Overlapping source intervals in the independent audit; unit IDs withheld.")
    return rows[0] if rows else None


def month_key(commune, date):
    return str(commune), pd.Timestamp(date).to_period("M").to_timestamp()


def main():
    started = time.time()
    out = ROOT / "data/intermediate/observation_audit"
    out.mkdir(parents=True, exist_ok=True)
    c = duckdb.connect()
    c.execute("SET memory_limit='4GB'")
    c.execute("SET threads=2")
    c.execute(f"SET temp_directory='{sqlpath(out / 'spill')}'")
    c.execute(f"ATTACH '{sqlpath(ROOT / 'data/intermediate/analysis.duckdb')}' AS mainbuild (READ_ONLY)")
    panel = c.sql(f"SELECT * FROM read_parquet('{sqlpath(ROOT / 'data/processed/monthly_panel.parquet')}')").df()
    meta = pd.read_csv(ROOT / "data/processed/commune_treatment.csv", dtype=str,
                       usecols=["commune_code", "treatment_group", "analysis_stable"])
    panel = panel.merge(meta, on="commune_code", how="left", validate="many_to_one")
    rng = np.random.default_rng(SEED)
    samples = []
    for group in ("NEW_FRR", "NEVER_TREATED"):
        for zero in (True, False):
            pool = panel[(panel.treatment_group == group) & ((panel.establishment_births == 0) == zero)]
            pool = pool.sort_values(["commune_code", "month"])
            if len(pool) < 5:
                raise RuntimeError(f"Insufficient cells in sample stratum {group}, zero={zero}")
            before = pool[pool.month < pd.Timestamp("2024-07-01")]
            after = pool[pool.month >= pd.Timestamp("2024-07-01")]
            if len(before) < 2 or len(after) < 2:
                raise RuntimeError("Sample requires both pre-reform and post-reform observations.")
            chosen = [*rng.choice(before.index.to_numpy(), 2, replace=False),
                      *rng.choice(after.index.to_numpy(), 2, replace=False)]
            left = pool.loc[~pool.index.isin(chosen)]
            chosen.append(rng.choice(left.index.to_numpy()))
            samples.append(pool.loc[chosen])
    sample = pd.concat(samples).sort_values(["treatment_group", "commune_code", "month"]).reset_index(drop=True)
    sample["audit_cell"] = [f"CELL{i:02d}" for i in range(1, 21)]
    c.register("sample_cells", sample[["commune_code", "month"]])
    c.register("sample_communes", sample[["commune_code"]].drop_duplicates())
    def raw(name):
        return f"read_parquet('{sqlpath(ROOT / 'data/raw' / ('stock-' + name + '-parquet.parquet'))}')"
    print("Projecting official source columns for 20 commune-month cells.", flush=True)
    c.execute(f"""CREATE TEMP TABLE source_e AS
        SELECT e.siret,e.siren,e.nic,e.codeCommuneEtablissement AS commune_code,
        e.dateCreationEtablissement AS creation_date,e.statutDiffusionEtablissement AS diffusion,
        e.etatAdministratifEtablissement AS current_state,
        e.activitePrincipaleEtablissement AS current_naf
        FROM {raw('stocketablissement')} e JOIN sample_communes m
        ON e.codeCommuneEtablissement=m.commune_code
        WHERE NOT EXISTS (SELECT 1 FROM {raw('stockdoublons')} d WHERE e.siren=d.sirenDoublon)""")
    c.execute(f"""CREATE TEMP TABLE source_eh AS
        SELECT h.siret,h.dateDebut AS start,h.dateFin AS "end",
        h.etatAdministratifEtablissement AS state,h.activitePrincipaleEtablissement AS naf,
        h.nomenclatureActivitePrincipaleEtablissement AS naf_version,
        h.caractereEmployeurEtablissement AS employer
        FROM {raw('stocketablissementhistorique')} h
        WHERE EXISTS (SELECT 1 FROM source_e e WHERE e.siret=h.siret)""")
    e = c.sql("SELECT * FROM source_e").df()
    eh = c.sql("SELECT * FROM source_eh ORDER BY siret,start NULLS FIRST").df()
    histories = {k: g.to_dict("records") for k, g in eh.groupby("siret", sort=False)}
    cells = {month_key(r.commune_code, r.month): {v: 0 for v in MEASURES} for r in sample.itertuples()}
    birth_records = []
    for r in e.to_dict("records"):
        date = r["creation_date"]
        if not present(date):
            continue
        key = month_key(r["commune_code"], date)
        if key not in cells:
            continue
        state = at_date(histories.get(r["siret"], []), date)
        rec = {**r, "state_at_creation": None, "naf_at_creation": None,
               "naf_version": None, "employer_at_creation": None,
               "historical_start": None, "historical_end": None}
        if state:
            rec.update({"state_at_creation": state["state"], "naf_at_creation": state["naf"],
                        "naf_version": state["naf_version"], "employer_at_creation": state["employer"],
                        "historical_start": state["start"], "historical_end": state["end"]})
        birth_records.append(rec)
        result = cells[key]
        result["establishment_births"] += 1
        result["employer_births"] += int(rec["state_at_creation"] == "A" and rec["employer_at_creation"] == "O")
        result["known_employer_births"] += int(rec["state_at_creation"] == "A" and rec["employer_at_creation"] in ("O", "N"))
        result["unknown_naf_births"] += int(not present(rec["naf_at_creation"]) or rec["naf_version"] != "NAFRev2")
        naf = rec["naf_at_creation"]
        if rec["naf_version"] == "NAFRev2" and isinstance(naf, str) and re.fullmatch(r"\d{2}\.\d{2}[A-Z]", naf):
            division = int(naf[:2])
            for sector, divisions in SECTORS.items():
                result[sector] += int(division in divisions)
    fresh_births = pd.DataFrame(birth_records)
    if fresh_births.empty:
        raise RuntimeError("Positive sample cells yielded no independently projected births.")
    c.register("fresh_birth_ids", fresh_births[["siret", "creation_date"]])
    links = c.sql(f"""SELECT s.siretEtablissementSuccesseur AS siret,s.dateLienSuccession AS date,
        s.continuiteEconomique AS continuity,s.transfertSiege AS transfer
        FROM {raw('stocketablissementlienssuccession')} s
        WHERE EXISTS (SELECT 1 FROM fresh_birth_ids b WHERE b.siret=s.siretEtablissementSuccesseur)""").df()
    link_groups = {k: g.to_dict("records") for k, g in links.groupby("siret", sort=False)}
    for rec in birth_records:
        continuity = any(bool(s["continuity"]) for s in link_groups.get(rec["siret"], [])
                         if present(s["date"]) and s["date"] == rec["creation_date"] and present(s["continuity"]))
        rec["recorded_continuity_at_birth"] = continuity
        result = cells[month_key(rec["commune_code"], rec["creation_date"])]
        result["recorded_continuity_births"] += int(continuity)
        result["births_without_recorded_continuity"] += int(not continuity)
    # Independently locate UL birth using source historical HQ, never current HQ.
    c.execute(f"""CREATE TEMP TABLE source_u AS SELECT u.siren,u.dateCreationUniteLegale AS creation_date
        FROM {raw('stockunitelegale')} u WHERE EXISTS (SELECT 1 FROM source_e e WHERE e.siren=u.siren)""")
    uh = c.sql(f"""SELECT h.siren,h.dateDebut AS start,h.dateFin AS "end",
        h.nicSiegeUniteLegale AS hq_nic,h.categorieJuridiqueUniteLegale AS legal_category
        FROM {raw('stockunitelegalehistorique')} h
        WHERE EXISTS (SELECT 1 FROM source_u u WHERE u.siren=h.siren) ORDER BY h.siren,h.dateDebut NULLS FIRST""").df()
    uhist = {k: g.to_dict("records") for k, g in uh.groupby("siren", sort=False)}
    hq_establishments = {(r["siren"], r["nic"]): r for r in e.to_dict("records")}
    for unit in c.sql("SELECT * FROM source_u").df().to_dict("records"):
        date = unit["creation_date"]
        if not present(date):
            continue
        state = at_date(uhist.get(unit["siren"], []), date)
        if not state or not present(state["hq_nic"]):
            continue
        hq = hq_establishments.get((unit["siren"], state["hq_nic"]))
        if hq is None or not present(hq["creation_date"]) or hq["creation_date"] > date:
            continue
        key = month_key(hq["commune_code"], date)
        if key in cells:
            cells[key]["legal_unit_births"] += 1
            cells[key]["individual_births"] += int(str(state["legal_category"]) == "1000")
    gaps = overlaps = closed_o_periods = 0
    communes_by_siret = dict(zip(e.siret, e.commune_code))
    for siret, history in histories.items():
        previous = None
        for record in history:
            if record["state"] == "F" and record["employer"] == "O":
                closed_o_periods += 1
            if previous and present(previous["end"]) and present(record["start"]):
                overlaps += int(record["start"] <= previous["end"])
                gaps += int(record["start"] > previous["end"] + pd.Timedelta(days=1))
            if previous and record["state"] == "F" and previous["state"] == "A" and present(record["start"]):
                commune = communes_by_siret[siret]
                key = month_key(commune, record["start"])
                if key in cells:
                    cells[key]["establishment_closures"] += 1
            previous = record
    for result in cells.values():
        result["registration_minus_closure_balance"] = result["establishment_births"] - result["establishment_closures"]
    comparisons = []
    for table, names in [("monthly_entries", MEASURES[:13]),
                         ("monthly_units", ["legal_unit_births", "individual_births"]),
                         ("monthly_closures", ["closure_events"])]:
        values = c.sql(f"""SELECT x.* FROM mainbuild.main.{table} x JOIN sample_cells s
            ON x.commune_code=s.commune_code AND x.month=s.month""").df()
        value_map = {month_key(r["commune_code"], r["month"]): r for r in values.to_dict("records")}
        for row in sample.to_dict("records"):
            key = month_key(row["commune_code"], row["month"])
            stored = value_map.get(key, {})
            for name in names:
                target = "establishment_closures" if name == "closure_events" else name
                comparisons.append({"audit_cell": row["audit_cell"], "commune_code": row["commune_code"],
                                    "month": str(row["month"].date()), "treatment_group": row["treatment_group"],
                                    "measure": target, "official_recalculation": int(cells[key][target]),
                                    "intermediate": int(stored.get(name, 0)), "processed": int(row[target])})
    checks = pd.DataFrame(comparisons)
    checks["matches"] = (checks.official_recalculation == checks.intermediate) & (checks.official_recalculation == checks.processed)
    # The balance has no independent intermediate table; compare directly.
    for row in sample.to_dict("records"):
        key = month_key(row["commune_code"], row["month"])
        checks.loc[len(checks)] = [row["audit_cell"], row["commune_code"], str(row["month"].date()),
                                  row["treatment_group"], "registration_minus_closure_balance",
                                  cells[key]["registration_minus_closure_balance"],
                                  cells[key]["registration_minus_closure_balance"], int(row["registration_minus_closure_balance"]),
                                  cells[key]["registration_minus_closure_balance"] == row["registration_minus_closure_balance"]]
    # Audit 20 individual birth records locally; unit IDs never enter reports.
    fresh_births = pd.DataFrame(birth_records).sort_values("siret").reset_index(drop=True)
    if len(fresh_births) < 20:
        raise RuntimeError("Sample contains fewer than 20 establishments; expand the audit sample.")
    chosen = []
    for mask in [fresh_births.employer_at_creation.eq("O"), fresh_births.diffusion.eq("P"),
                 fresh_births.current_state.eq("F"), fresh_births.recorded_continuity_at_birth.eq(True),
                 fresh_births.naf_at_creation.ne(fresh_births.current_naf)]:
        candidates = fresh_births.index[mask & ~fresh_births.index.isin(chosen)].to_numpy()
        if len(candidates):
            chosen.append(int(rng.choice(candidates)))
    available = fresh_births.index[~fresh_births.index.isin(chosen)].to_numpy()
    chosen.extend(int(i) for i in rng.choice(available, 20 - len(chosen), replace=False))
    individual = fresh_births.loc[chosen].copy()
    individual["audit_record"] = [f"EST{i:02d}" for i in range(1, 21)]
    c.register("individual_ids", individual[["siret"]])
    stored_births = c.sql("SELECT b.* FROM mainbuild.main.births b JOIN individual_ids a USING(siret)").df().set_index("siret")
    attrs = ["commune_code", "creation_date", "diffusion", "state_at_creation", "naf_at_creation",
             "naf_version", "employer_at_creation", "historical_start", "historical_end"]
    individual_discrepancies = 0
    for row in individual.to_dict("records"):
        if row["siret"] not in stored_births.index:
            individual_discrepancies += 1
            continue
        other = stored_births.loc[row["siret"]]
        for name in attrs:
            a, b = row[name], other[name]
            if not (pd.isna(a) and pd.isna(b)) and a != b:
                individual_discrepancies += 1
    individual.to_csv(out / "individual_birth_checks_private.csv", index=False, encoding="utf8")
    # Full-panel identities and canonical duplicate exclusion are aggregate only.
    alltotals = {m: int(panel[m].sum()) for m in MEASURES}
    tabletotals = {"establishment_births": int(c.sql("SELECT count(*) FROM mainbuild.main.births").fetchone()[0]),
                   "legal_unit_births": int(c.sql("SELECT count(*) FROM mainbuild.main.unit_births").fetchone()[0])}
    duplicate_retained = int(c.sql(f"""SELECT count(*) FROM mainbuild.main.establishments e
        JOIN {raw('stockdoublons')} d ON e.siren=d.sirenDoublon""").fetchone()[0])
    duplicate_dropped = int(c.sql(f"""SELECT count(*) FROM {raw('stocketablissement')} e
        JOIN (SELECT DISTINCT sirenDoublon FROM {raw('stockdoublons')}) d ON e.siren=d.sirenDoublon
        JOIN (SELECT DISTINCT commune_code FROM mainbuild.main.monthly_panel) m
        ON e.codeCommuneEtablissement=m.commune_code""").fetchone()[0])
    global_identity = bool((panel.establishment_births == panel.recorded_continuity_births + panel.births_without_recorded_continuity).all()
                           and (panel.employer_births <= panel.known_employer_births).all()
                           and (panel.known_employer_births <= panel.establishment_births).all()
                           and (panel.registration_minus_closure_balance == panel.establishment_births - panel.establishment_closures).all()
                           and tabletotals["establishment_births"] == alltotals["establishment_births"]
                           and tabletotals["legal_unit_births"] == alltotals["legal_unit_births"])
    passed = bool(checks.matches.all() and individual_discrepancies == 0 and duplicate_retained == 0
                  and global_identity and overlaps == 0 and not panel.duplicated(["commune_code", "month"]).any())
    summary = {"status": "PASSED" if passed else "FAILED", "seed": SEED, "cell_observations": 20,
               "individual_observations": 20, "individual_attribute_comparisons": 20 * len(attrs),
               "cell_measure_comparisons": len(checks), "cell_measure_discrepancies": int((~checks.matches).sum()),
               "individual_attribute_discrepancies": individual_discrepancies,
               "source_births_in_sample_cells": len(fresh_births), "sample_source_establishments": len(e),
               "sample_source_history_periods": len(eh), "source_interval_overlaps": overlaps,
               "source_interval_gaps": gaps, "closed_employer_O_history_periods_in_sample_communes": closed_o_periods,
               "canonical_duplicate_establishments_dropped_in_analysis_communes": duplicate_dropped,
               "canonical_duplicate_establishments_retained": duplicate_retained,
               "global_panel_identities": global_identity, "panel_rows": len(panel),
               "full_panel_totals": alltotals,
               "construction_script_sha256": hashlib.sha256((ROOT / "src/construct/construct_panel.py").read_bytes()).hexdigest(),
               "generated_at_utc": datetime.now(timezone.utc).isoformat(), "elapsed_seconds": round(time.time()-started, 2),
               "scope": "Administrative register reconstruction, not causal identification or economic survival."}
    checks.to_csv(ROOT / "reports/review_C_cell_checks.csv", index=False, encoding="utf8")
    sample[["audit_cell", "commune_code", "month", "treatment_group", "establishment_births"]].to_csv(
        ROOT / "reports/review_C_sample_cells.csv", index=False, encoding="utf8")
    (ROOT / "reports/review_C_observation_checks.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf8")
    report = ["# REVIEW C — 独立官方来源重算", "", f"状态：**{summary['status']}**；随机种子 {SEED}。",
              "", "20 个 commune-month 按 NEW_FRR / NEVER_TREATED 与注册零值/正值四层各抽 5 个，每层含改革前后。",
              "官方 Parquet 重新投影，Python 独立寻找双端包含的创建期、历史雇主/行业和同日连续关系，另重算历史 HQ 的 UL births 和 A→F 关闭。",
              f"共 {len(checks)} 项 cell-measure 比较，差异 {summary['cell_measure_discrepancies']}；20 个匿名 establishment 的 {20*len(attrs)} 项源属性比较，差异 {individual_discrepancies}。",
              f"样本 commune 内历史 {len(eh):,} 期，重叠 {overlaps}、间隙 {gaps}；F 但 employer O 共 {closed_o_periods:,} 期，计数没有把这些期当作活动雇主。",
              f"canonical sirenDoublon establishment 已排除 {duplicate_dropped:,} 个，analysis 中仍保留 {duplicate_retained} 个。",
              "", "公开附件只含 commune-month、分类和聚合比较。SIRET 与个体源属性留在 ignored 的 data/intermediate/observation_audit/。",
              "本 gate 只核查行政注册重构；不证明政策资格、真实就业、经济存活或因果识别。secondary 留存与 UL HQ 漏配另见相应报告。"]
    (ROOT / "reports/review_C_observations.md").write_text("\n\n".join(report)+"\n", encoding="utf8")
    c.close()
    print(json.dumps(summary, ensure_ascii=True), flush=True)
    if not passed:
        raise RuntimeError("Independent REVIEW C observations failed; consult aggregate discrepancy report.")


if __name__ == "__main__":
    main()
