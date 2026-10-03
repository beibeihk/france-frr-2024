"""REVIEW B frozen V assignment/covariate interface. Never reads research Y."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
PROC = ROOT / "data" / "processed"
REP = ROOT / "reports"
INPUTS = [PROC / "assignment2024_commune_paths.csv",
          PROC / "assignment2024_territory_indicators.csv",
          PROC / "commune_treatment.csv"]
H = (500, 750, 1000, 1500)

def boolean(s):
    return s.astype("string").str.lower().map({"true": True, "false": False})

d = pd.read_csv(INPUTS[0], dtype={"commune_code": str, "department": str,
                                "epci_2023": str, "bassin_2022_cog2023": str})
m = pd.read_csv(INPUTS[2], dtype={"commune_code": str, "department": str,
                                "epci_2023": str, "epci_2024": str})
t = pd.read_csv(INPUTS[1], dtype={"code": str})
assert d.commune_code.is_unique and m.commune_code.is_unique
meta_cols = ["commune_code", "prior_zrr_effects", "metropolitan", "analysis_stable",
             "administrative_change_since2017", "epci_change_2023_2024"]
d = d.merge(m[meta_cols], on="commune_code", how="left", validate="one_to_one")
for c in meta_cols[1:]:
    d[c] = boolean(d[c])
flags = ["actual_epci", "population_below30000", "eligible_A_epci",
         "eligible_A_isolated_commune", "eligible_C_department", "eligible_D_potential",
         "listed_initial2024"]
for c in flags:
    d[c] = boolean(d[c])
d["fixed_prepolicy_common"] = (d.metropolitan.eq(True) & d.analysis_stable.eq(True)
    & d.prior_zrr_effects.eq(False) & d.actual_epci.eq(True)
    & d.population_below30000.eq(True))
screen = ["eligible_A_epci", "eligible_A_isolated_commune", "eligible_C_department", "eligible_D_potential"]
d["alternative_screen_any"] = d[screen].eq(True).any(axis=1)
d["alternative_screen_unknown"] = d[screen].isna().any(axis=1)
d["selected_V"] = (d.fixed_prepolicy_common & d.bassin_density_2020.le(65.84)
    & d[screen].eq(False).all(axis=1) & d.bassin_median_income2020.notna()
    & d.bassin_2022_cog2023.notna())
d["epci_primitive"] = np.where(d.actual_epci.eq(True), "EPCI:" + d.epci_2023,
                               "COMMUNE:" + d.commune_code)
q = d.loc[d.selected_V].copy()
assert len(q) and q.commune_code.is_unique
native = t.loc[t.level.eq("BV2022")].set_index("code")
assert native.index.is_unique

rows = []
for bv, selected in q.groupby("bassin_2022_cog2023", sort=True):
    f = d.loc[d.bassin_2022_cog2023.eq(bv)]
    n = native.loc[bv]
    pop = float(f.P20_POP.sum())
    pre = f.loc[f.fixed_prepolicy_common]
    prepop = float(pre.P20_POP.sum())
    spop = float(selected.P20_POP.sum())
    income = float(n.median_income2020)
    r = {"bassin_2022_cog2023": bv, "income2020": income,
         "running_x": 21600.0-income, "criterion_eligible": int(income <= 21600),
         "full_bv_population2020": float(n.population_2020),
         "full_bv_density2020": float(n.density_2020), "full_bv_n_communes": int(n.n_communes),
         "mapped_full_population2020": pop, "mapped_full_n_communes": len(f),
         "selected_population2020": spop, "selected_n_communes": len(selected),
         "selected_population_share": spop/float(n.population_2020),
         "selected_commune_share": len(selected)/int(n.n_communes),
         "mapped_full_population_share": pop/float(n.population_2020),
         "fixed_prepolicy_population2020": prepop,
         "fixed_prepolicy_population_share": prepop/float(n.population_2020),
         "initial_frr_selected_population_share": float((selected.P20_POP*selected.listed_initial2024.astype(float)).sum()/spop),
         "log_full_bv_population2020": float(np.log(n.population_2020)),
         "old_zrr_full_population_share": float(f.loc[f.prior_zrr_effects.eq(True), "P20_POP"].sum()/pop),
         "unknown_zrr_full_population_share": float(f.loc[f.prior_zrr_effects.isna(), "P20_POP"].sum()/pop),
         "not_analysis_stable_population_share": float(f.loc[f.analysis_stable.eq(False), "P20_POP"].sum()/pop),
         "missing_metadata_population_share": float(f.loc[f.analysis_stable.isna(), "P20_POP"].sum()/pop),
         "selected_n_epci": selected.epci_primitive.nunique(),
         "selected_n_departments": selected.department.nunique(),
         "full_n_epci_primitives": f.epci_primitive.nunique(),
         "full_n_departments": f.department.nunique()}
    for flag in screen + ["alternative_screen_any", "alternative_screen_unknown",
                         "administrative_change_since2017", "epci_change_2023_2024"]:
        r[flag+"_full_population_share"] = float(f.loc[f[flag].eq(True), "P20_POP"].sum()/pop)
        r[flag+"_unknown_full_population_share"] = float(f.loc[f[flag].isna(), "P20_POP"].sum()/pop)
        r[flag+"_prepolicy_population_share"] = float(pre.loc[pre[flag].eq(True), "P20_POP"].sum()/prepop) if prepop else np.nan
    for scope, a in [("full", f), ("selected", selected)]:
        apop = float(a.P20_POP.sum())
        observed = a.epci_median_income2020.notna()
        r[scope+"_epci_income_missing_population_share"] = float(a.loc[~observed, "P20_POP"].sum()/apop)
        obs = a.loc[observed]
        opop = float(obs.P20_POP.sum())
        r[scope+"_weighted_epci_income_mean_diagnostic"] = float((obs.P20_POP*obs.epci_median_income2020).sum()/opop) if opop else np.nan
        r[scope+"_epci_income_min"] = float(obs.epci_median_income2020.min())
        r[scope+"_epci_income_max"] = float(obs.epci_median_income2020.max())
        r[scope+"_epci_income_le21570_population_share"] = float(a.loc[a.epci_median_income2020.le(21570), "P20_POP"].sum()/apop)
        r[scope+"_epci_income_le22822p5_population_share"] = float(a.loc[a.epci_median_income2020.le(22822.5), "P20_POP"].sum()/apop)
        r[scope+"_epci_income_equals_bv_population_share"] = float(a.loc[a.epci_median_income2020.eq(income), "P20_POP"].sum()/apop)
        r[scope+"_weighted_abs_epci_bv_income_difference"] = float((obs.P20_POP*(obs.epci_median_income2020-income).abs()).sum()/opop) if opop else np.nan
        r[scope+"_nearest_epci_income_to21570"] = float((obs.epci_median_income2020-21570).abs().min())
    rows.append(r)
u = pd.DataFrame(rows).sort_values("bassin_2022_cog2023").reset_index(drop=True)
assert np.allclose(u.mapped_full_population_share, 1) and np.array_equal(u.full_bv_n_communes, u.mapped_full_n_communes)
assert np.array_equal(u.criterion_eligible.astype(float), u.initial_frr_selected_population_share)

membership = []
for scope, a in [("selected", q), ("full", d.loc[d.bassin_2022_cog2023.isin(u.bassin_2022_cog2023)])]:
    for typ, col in [("epci", "epci_primitive"), ("department", "department")]:
        z = a[["bassin_2022_cog2023", col]].drop_duplicates().dropna()
        for bv, node in z.itertuples(index=False, name=None):
            membership.append({"bassin_2022_cog2023": bv, "membership_scope": scope,
                               "node_type": typ, "node_id": str(node)})
links = pd.DataFrame(membership).sort_values(["membership_scope", "node_type", "bassin_2022_cog2023", "node_id"])

def components(active, relation):
    parent = {v:v for v in active}
    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v
    for _, g in relation.groupby(["node_type", "node_id"], sort=True):
        bvs = sorted(g.bassin_2022_cog2023.unique())
        anchor = bvs[0]
        for v in bvs[1:]:
            a, b = find(anchor), find(v)
            if a != b:
                parent[max(a,b)] = min(a,b)
    return {v:find(v) for v in active}

graph_rows, support = [], []
for h in H:
    a = u.loc[u.running_x.abs().lt(h)]
    active = set(a.bassin_2022_cog2023)
    zmap = a.set_index("bassin_2022_cog2023").criterion_eligible
    for scope in ("selected", "full"):
        rel = links.loc[links.membership_scope.eq(scope) & links.bassin_2022_cog2023.isin(active)]
        for typ in ("epci", "department", "joint"):
            rr = rel if typ == "joint" else rel.loc[rel.node_type.eq(typ)]
            mapping = components(active, rr)
            suffix = "" if scope == "selected" else "_full"
            col = f"component_{typ}{suffix}_h{h}"
            u[col] = u.bassin_2022_cog2023.map(mapping)
            sizes = pd.Series(list(mapping.values())).value_counts()
            cross_nodes = []
            cross_bvs = set()
            for key, g in rr.groupby(["node_type", "node_id"]):
                if zmap.reindex(g.bassin_2022_cog2023).nunique() > 1:
                    cross_nodes.append(key)
                    cross_bvs.update(g.bassin_2022_cog2023)
            graph_rows.append({"h": h, "membership_scope": scope, "graph": typ,
                "n_bv": len(a), "n_components": int(len(sizes)),
                "largest_component_bv": int(sizes.max()), "largest_component_share": float(sizes.max()/len(a)),
                "size_effective_components": float(len(a)**2/(sizes*sizes).sum()),
                "n_membership_nodes": int(rr[["node_type","node_id"]].drop_duplicates().shape[0]),
                "n_cross_threshold_nodes": len(cross_nodes), "cross_threshold_bv": len(cross_bvs),
                "cross_threshold_bv_share": len(cross_bvs)/len(a)})
    support.append({"h": h, "eligible_bv": int(a.criterion_eligible.eq(1).sum()),
        "ineligible_bv": int(a.criterion_eligible.eq(0).sum()),
        "eligible_distinct_scores": int(a.loc[a.criterion_eligible.eq(1), "running_x"].nunique()),
        "ineligible_distinct_scores": int(a.loc[a.criterion_eligible.eq(0), "running_x"].nunique()),
        "ties": int(a.running_x.eq(0).sum()), "population2020": float(a.selected_population2020.sum()),
        "selected_communes": int(a.selected_n_communes.sum()),
        "minimum_eligible_x": float(a.loc[a.criterion_eligible.eq(1), "running_x"].min()),
        "nearest_ineligible_distance": float(-a.loc[a.criterion_eligible.eq(0), "running_x"].max()),
        "assignment_mismatches": int(a.criterion_eligible.ne(a.initial_frr_selected_population_share).sum())})
unitpath = PROC / "rd_V_bv_candidates_assignment_only.csv"
communepath = PROC / "rd_V_bv_selected_communes_assignment_only.csv"
linkpath = PROC / "rd_V_bv_membership_assignment_only.csv"
covpath = REP / "review_B_V_assignment_covariates.csv"
graphpath = REP / "review_B_V_dependency_graphs.csv"
u.to_csv(unitpath, index=False)
q.merge(u[["bassin_2022_cog2023", "running_x", "criterion_eligible"]], on="bassin_2022_cog2023", validate="many_to_one").to_csv(communepath, index=False)
links.to_csv(linkpath, index=False)
u[[c for c in u.columns if not c.startswith("component_")]].to_csv(covpath, index=False)
pd.DataFrame(graph_rows).to_csv(graphpath, index=False)
pd.DataFrame(support).to_csv(REP / "review_B_V_assignment_support.csv", index=False)
manifest = {"description": "Frozen V assignment-only interface; no SIRENE/monthly_panel/new research outcomes read",
    "script": str(Path(__file__).resolve()), "inputs_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in INPUTS},
    "outputs_sha256": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [unitpath, communepath, linkpath, covpath, graphpath]},
    "all_candidate_bv": len(u), "all_selected_communes": len(q), "support": support,
    "graph_summary": graph_rows,
    "caveats": ["Native BV medians are not averaged municipal/EPCI medians; weighted EPCI means are diagnostics only.",
                "Components are re-created separately inside each fixed positive-kernel support window.",
                "Full BV graphs include all member communes and give isolated communes their own primitive.",
                "History NA is unknown, never assigned old-ZRR=False.",
                "Analysis stability includes existing administrative-date restrictions and is not asserted wholly pre-policy.",
                "Perfect observed assignment first stage is not evidence of potential-outcome continuity."]}
(REP / "review_B_V_assignment_interface.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"interfaces": [str(p) for p in [unitpath, communepath, linkpath]],
                  "n_candidate_bv": len(u), "n_selected_communes": len(q),
                  "support": support, "graphs_h1000": [r for r in graph_rows if r["h"] == 1000]}, ensure_ascii=False, indent=2))
