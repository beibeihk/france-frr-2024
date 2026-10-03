# Design fixed before observing outcomes

Recorded on 2026-10-03 (Asia/Hong_Kong). No business-creation outcome or regression has yet been inspected.

## Estimand and assignment audit

The target is the intention-to-treat effect of acquiring FRR territorial eligibility on administrative establishment entries, not the effect of taking up a specific tax exemption. FRR includes a bundle of fiscal and non-fiscal measures. The July 2024 original list and the last effective pre-reform ZRR list, including communes benefiting from retained ZRR effects, must be reconstructed before estimation. Classification paths and subsequent extensions must be identified separately. Nominally non-ZRR communes benefiting from old ZRR effects are NOT new recipients.

## Main design

Metropolitan communes never enjoying pre-reform ZRR effects that enter FRR on 2024-07-01 versus communes with neither prior nor subsequent FRR eligibility. The preferred sample consists of shared-boundary neighbours on opposite sides of the policy boundary. Exclude communes with mergers, code changes or boundary changes during 2019 through the latest outcome vintage unless an exact consistent crosswalk is verified. Construct pairs from an official IGN boundary vintage and report topology tolerance. Use an explicit overlap-weighting rule; duplicated communes are never independent observations.

Primary outcome: monthly administrative SIRENE establishment entries per 1,000 fixed pre-treatment residents; secondary: log(1+entries). Legal-unit births require a defensible establishment-at-birth location, never the current headquarters alone. Historical activity and employer status must be measured at creation; current status must not be labelled status at creation. Closures and survival are administrative and require validated historical transitions. Unknown employment is not zero employment.

Main panel: 2019-01 to the most recent reliably complete month, allowing at least a three-month registration lag as a provisional rule. Main treatment: 2024-07. Estimate monthly event studies with commune fixed effects and year-month effects. Border comparisons use pair-by-year-month effects and a documented weighting rule. EPCI is the primary clustering level when EPCI assignment dominates; commune and département clustering are sensitivity analyses. Report assignment-level cluster counts; use wild cluster bootstrap for few effective treatment clusters.

## Pre-specified checks

Joint pretrend test, placebo reforms 2022-07 and 2023-07 using pre-real-treatment observations only; 2019 versus 2022 starts; alternative exposure windows; fixed pre-treatment matching using population, density, income and entry rates if available; avoid big cities and population-ceiling observations; exclude alternative classification paths; population weighting; count PPML and transformed OLS; balanced-panel checks; leave-one-département-out; neighbouring spillovers and pair-total entries. A failed pretrend test or invalid treatment reconstruction prevents unqualified causal language; specification changes must be logged with whether outcomes were already observed.

## Heterogeneity, survival and RD

Seven pre-defined NAF Rev.2 groups: commerce, accommodation-food, construction, manufacturing, professional services, health and proximity services. Report all groups, adjust the family of heterogeneity tests, and call NAF distinctions sectoral exposure rather than observed fiscal eligibility. Employer outcomes depend on dictionary quality. Survival is evaluated at 12 and 18 months only for fully followed cohorts, at 24 months only with complete follow-up. RD is excluded from the main analysis unless original assignment variables and all alternative eligibility paths can be replicated and local sample size and diagnostics suffice.

## Publication gate

No deposit until institutional claims, treatment history, data reconstruction, estimators, uncertainty and French text have passed the requested independent reviews. An incomplete project is not a null-effect result. No outcome, coefficient, affiliation or completed submission may be fabricated.
