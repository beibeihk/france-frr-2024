"""Assignment-only covariate RD diagnostics plus synthetic software identity check.

No business panel, real outcome aggregate, or research-outcome estimate is read.
"""
from pathlib import Path
import sys, json, hashlib, warnings
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".vendor_rd"))
import numpy as np
import pandas as pd
from scipy import stats
from rdrobust import rdrobust

u = pd.read_csv(ROOT / "data/processed/rd_V_bv_candidates_assignment_only.csv",
                dtype={"bassin_2022_cog2023": str, **{f"component_{g}{s}_h{h}": str
                for g in ("epci", "department", "joint") for s in ("", "_full")
                for h in (500, 750, 1000, 1500)}})

def fit(a, values, h, cluster=None):
    x = a.running_x.to_numpy()/h
    w = 1-np.abs(x)
    right = x >= 0
    X = np.column_stack([np.where(~right, x**j, 0) for j in range(3)]
                         + [np.where(right, x**j, 0) for j in range(3)])
    y = np.asarray(values, float)
    if y.ndim == 1: y = y[:,None]
    bread = np.linalg.inv(X.T@(w[:,None]*X))
    beta = bread@X.T@(w[:,None]*y)
    residual = y-X@beta
    contrast = np.array([-1.,0,0,1.,0,0])
    omega = contrast@bread@X.T*w
    leverage = w*np.einsum("ij,jk,ik->i", X, bread, X)
    score = omega[:,None]*residual/(1-leverage[:,None])
    covariance = score.T@score
    if cluster is not None:
        rawscore = pd.DataFrame(omega[:,None]*residual).groupby(np.asarray(cluster)).sum().to_numpy()
        G = len(rawscore)
        covariance = rawscore.T@rawscore*G/(G-1)*(len(a)-1)/(len(a)-6)
    return contrast@beta, covariance, leverage

# This synthetic vector is unrelated to any observed establishment outcome.
rng = np.random.default_rng(20241004)
synthetic = 0.5*u.criterion_eligible.to_numpy() + (u.running_x.to_numpy()/1000)**3 + rng.normal(size=len(u))
checks = []
rows = []
exclude = {"bassin_2022_cog2023", "income2020", "running_x", "criterion_eligible",
           "initial_frr_selected_population_share"}
covariates = [c for c in u if c not in exclude and not c.startswith("component_")]
for h in (500,750,1000,1500):
    a = u.loc[u.running_x.abs().lt(h)].copy()
    theta, V, lev = fit(a, synthetic[a.index], h)
    with warnings.catch_warnings(record=True) as caught:
        rr = rdrobust(y=synthetic[a.index], x=a.running_x.to_numpy(), c=0, p=1, q=2,
                      h=h, b=h, kernel="triangular", vce="hc3", masspoints="adjust")
    pointdiff = abs(theta[0]-rr.coef.loc["Robust"].iloc[0])
    sediff = abs(np.sqrt(V[0,0])-rr.se.loc["Robust"].iloc[0])
    assert max(pointdiff,sediff) < 1e-7
    checks.append({"h":h,"point_abs_difference":float(pointdiff),"hc3_se_abs_difference":float(sediff),
                   "max_weighted_leverage":float(lev.max()), "synthetic_only":True,
                   "warnings":[str(v.message) for v in caught]})
    for c in covariates:
        if a[c].isna().any():
            rows.append({"h":h,"variable":c,"status":"missing_covariate_no_unit_deletion", "n_bv":len(a)})
            continue
        y = a[c].to_numpy(float)
        if np.ptp(y) <= 1e-12:
            rows.append({"h":h,"variable":c,"status":"constant_by_construction_no_balance_test",
                         "n_bv":len(a),"bias_corrected_jump":0., "constant_value":float(y[0])})
            continue
        point, cv, lv = fit(a,y,h)
        estimate = float(point[0]);se = float(np.sqrt(cv[0,0]))
        r = {"h":h,"variable":c,"status":"estimated_assignment_covariate_only", "n_bv":len(a),
             "bias_corrected_jump":estimate, "hc3_se":se, "hc3_ci_low":estimate-1.959963984540054*se,
             "hc3_ci_high":estimate+1.959963984540054*se, "hc3_p":float(2*stats.norm.sf(abs(estimate/se))),
             "left_mean":float(np.mean(y[a.running_x.to_numpy()<0])),
             "right_mean":float(np.mean(y[a.running_x.to_numpy()>=0])),"max_weighted_leverage":float(lv.max())}
        for scope, col in [("selected", f"component_joint_h{h}"), ("full", f"component_joint_full_h{h}")]:
            assert a[col].notna().all()
            _,vc,_ = fit(a,y,h,a[col]);s = float(np.sqrt(vc[0,0]));G=a[col].nunique();crit=stats.t.ppf(.975,G-1)
            r[scope+"_joint_groups"] = int(G)
            r[scope+"_joint_se"] = s
            r[scope+"_joint_ci_low"] = estimate-crit*s
            r[scope+"_joint_ci_high"] = estimate+crit*s
            r[scope+"_joint_p"] = float(2*stats.t.sf(abs(estimate/s),G-1)) if s else np.nan
        rows.append(r)
r = pd.DataFrame(rows)
# Each bandwidth gives a complete pre-fixed covariate family; no p-based omission.
for h in (500,750,1000,1500):
    for pc in ("hc3_p", "selected_joint_p", "full_joint_p"):
        ix = r.index[r.h.eq(h) & r[pc].notna()]
        vals = r.loc[ix,pc].sort_values()
        adj = np.maximum.accumulate(vals.to_numpy()*(len(vals)-np.arange(len(vals))))
        r.loc[vals.index,pc+"_holm_within_h"] = np.minimum(adj,1)
r.to_csv(ROOT / "reports/review_B_V_covariate_discontinuities_assignment_only.csv", index=False)
manifest = {"no_research_Y_read":True,"methods":"fixed h=b, p1/q2 triangular RBC-equivalent two-side q2; HC3 and joint CR1/t(G-1)",
            "synthetic_identity_checks":checks,"n_covariates":len(covariates),"family":covariates,
            "input_sha256":hashlib.sha256((ROOT / "data/processed/rd_V_bv_candidates_assignment_only.csv").read_bytes()).hexdigest(),
            "rdrobust_source_sha256":hashlib.sha256((ROOT / ".vendor_rd/rdrobust/rdrobust.py").read_bytes()).hexdigest(),
            "caveats":["Diagnostic p-values never establish potential-outcome continuity.",
                       "Full-member component inference has very few and highly uneven components.",
                       "Constant selected-policy fractions are consequences of sample rules, not balance evidence.",
                       "Multiple h are complete sensitivities, never a basis for choosing balanced windows.",
                       "Observed period outcomes and establishment counts are absent from this computation."]}
(ROOT / "reports/review_B_V_covariate_diagnostics.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding="utf8")
print(json.dumps({"synthetic_identity_checks":checks,"n_covariates":len(covariates),
                  "primary_h1000_covariate_estimates":r.loc[r.h.eq(1000) & r.variable.isin([
                      "selected_population_share", "selected_commune_share", "old_zrr_full_population_share",
                      "unknown_zrr_full_population_share", "full_bv_density2020", "log_full_bv_population2020",
                      "alternative_screen_any_full_population_share", "full_epci_income_equals_bv_population_share",
                      "full_epci_income_le21570_population_share", "epci_change_2023_2024_full_population_share"]),
                      ["variable","status","bias_corrected_jump","hc3_ci_low","hc3_ci_high","hc3_p", "hc3_p_holm_within_h",
                       "selected_joint_ci_low","selected_joint_ci_high","full_joint_ci_low","full_joint_ci_high"]].to_dict("records")},
                  ensure_ascii=False,indent=2))
