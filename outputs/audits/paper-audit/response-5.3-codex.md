1. **Claim-evidence consistency**
- Core Abstract claims (i)–(iv) are mostly consistent with §3.2 and §3.4 (especially C−F, D−C, B−C, and the 8K→16K Qwen B shift).
- Clear mismatches/overreach:
  - **§3.1, first paragraph** says “A ≈ 63% baseline” and “C ≈ 56–76%”; **Table 1** shows A = 0.828 (Gemma), 0.749 (Qwen), and C = 0.805/0.688. These are stale or wrong summary numbers.
  - **§3.4, first paragraph** says “367/1030” ceiling hits, then immediately says “those **368** ceiling-hit tuples.” **§6** also uses 368. One of these is wrong.
  - **§8, first paragraph** says replay recovers “most” of Gemma live-thinking benefit; but in Table 1, Gemma C (0.805) is below Gemma A (0.828), so “recoverability” needs clearer definition.
  - **§4 claim 2** (“genuine cross-model architectural difference”) is too strong given acknowledged confounds in **§7** (templates, effective params, engine differences).
  - **§5 first bullet** (“entirely a Qwen truncation artifact”) is stronger than evidence shown; mediation is argued, not formally quantified.

2. **Statistical rigor**
- Strengths: per-model GEE with clustered robust SEs, Holm correction, ITT/PP split, hurdle decomposition, explicit truncation sensitivity.
- Replication detail is **good but not yet sufficient** for a methods-heavy submission:
  - Missing exact model formulas/coding details for all reported contrasts and hurdle parts.
  - Only question-level clustering may miss dependence from paired seeds/rep structure.
  - 103 clusters is modest; no small-sample sandwich correction discussion.
  - 16K sensitivity re-runs only ceiling-hit cases (post-hoc selective continuation), not a full 16K rerun of all B.
  - Pre-registered Bayesian→GEE shift is justified mostly by tooling/runtime; reviewers will want inferential justification plus a completed Bayesian/GLMM sensitivity, not “planned.”

3. **Missing analyses reviewers will ask for**
1. Full 16K rerun for *all* Qwen-B observations (not only truncated ones), then recompute all B-involving contrasts.
2. Domain-level heterogeneity (math/logic/spatial/factual) with interaction tests.
3. Mixed-effects sensitivity (GLMM with question random effects, possibly seed/rep structure) alongside GEE.
4. Scoring reliability audit (manual check sample of `FINAL:` extraction and correctness labels).
5. Budget-matched fairness ablations for B vs O vs I (equalized token/latency compute budgets).

4. **Limitations completeness**
- §7 is strong, but missing:
  - Statistical limitations (small-cluster robust inference uncertainty; separation/saturation issues in hurdle extraction model).
  - Potential bias from selective 16K continuation design.
  - Parser/regex label-noise risk (not just “single pass”).
  - Stronger statement that cross-model effects are confounded by inference stack/template differences, not only architecture.

5. **Writing quality (max 3 fixes)**
1. Fix numeric consistency globally (especially §3.1 descriptors and §3.4/§6 367 vs 368) using auto-generated manuscript tables.
2. Define “recoverability” explicitly in §1 (recover relative to B? or improvement over A?) and align Abstract/§8 wording.
3. Tighten confirmatory vs exploratory separation: keep preregistered core in main text; move most Phase-3 mechanism narrative to appendix.

6. **Desk-reject risk**
- **Risk: 3.5/5**.
- Most likely trigger: **trust/credibility hit from internal numeric inconsistencies plus post-hoc analytic drift** (Bayesian→GEE and selective 16K rerun).
- Fix: one frozen reproducibility pipeline that regenerates every reported number, plus full 16K and Bayesian/GLMM sensitivity in submission package.

7. **Bottom line**
- **Major revisions needed.**
- One-sentence summary: The paper has a solid experimental idea and mostly coherent core findings, but it is not submission-ready until numeric consistency, estimand clarity, and replication-grade statistical sensitivity are tightened.