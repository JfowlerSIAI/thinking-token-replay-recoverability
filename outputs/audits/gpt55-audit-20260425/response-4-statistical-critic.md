**1. Hurdle Part-2 Selection**
The paper correctly flags conditional-on-extraction as post-treatment in [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:77), but then sometimes treats Part-2 as the preferred estimand. That is only defensible as “quality among successfully formatted outputs,” not as the causal content effect.

Quantitatively, selection is large exactly where the paper leans hardest on Part-2. Full-correction row counts:

| Contrast | Selection issue | Effect |
|---|---:|---|
| Qwen B−C | B excludes 204/1030, C excludes 47/1030 | E2E log-OR −0.282 favors C; Part-2 flips to B-favoring. This is large collider/selection sensitivity. |
| Qwen B−O | B excludes 204/1030, O excludes 0/1030 | E2E OR 0.36; Part-2 null. Large. |
| Qwen C−F | F excludes 590/1030, C excludes 47/1030 | E2E OR ~19.9; Part-2 OR ~7.5. Direction survives, magnitude heavily selection-dependent. |
| Gemma G−F | F excludes 347/1030, G excludes 29/1030 | E2E significant; Part-2 null. Large. |
| Gemma C−J / B−O | extraction differs by <=15/1030 | negligible. |

Claim 1 should not say Part-2 is “preferred”; say it is a robustness/descriptive estimand.

**2. TOST SESOI**
The SESOI is pre-registered: OR 0.85–1.18 in [osf-preregistration.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/osf-preregistration.md:43) and inference criteria in [osf-preregistration.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/osf-preregistration.md:191). It is nearly symmetric on the log-OR scale: −0.162/+0.166.

But the prereg says this is “approximately ±3 pp at 50% baseline”; that is wrong. At 50%, OR 1.18 is about +4.1 pp and OR 0.85 about −4.1 pp. At observed 70–85% baselines it is closer to ~2–4 pp.

Sensitivity: shrinking SESOI 50% breaks the obsolete Qwen merged equivalence, because its 90% CI [−0.127,+0.108] no longer fits ±0.08. Current full-correction Qwen B−C is not equivalent even with 1.5× SESOI; Gemma aggregate is also not equivalent.

**3. Multiplicity**
This is anti-conservative for the post-audit claims. The current paper applies Holm across seven pairwise contrasts per model in [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:83), while the prereg called eight confirmatory contrasts including synergy and Holm across all eight in [osf-preregistration.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/osf-preregistration.md:25) and [osf-preregistration.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/osf-preregistration.md:193). The code likewise defines seven pairwise contrasts in [analyze.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/analyze.py:33).

For huge effects this does not matter. It matters for Claim 8: Gemma B−O full-correction p=.020 E2E and p=.006 Part-2 are post-hoc and would not both survive a realistic family correction over scoring regimes, E2E/Part-2, subgroup discovery, and follow-up analyses. Present it as exploratory-confirmatory evidence, not a fully confirmatory claim.

**4. Small-Cluster GEE Corrections**
I reran statsmodels GEE with `cov_type="bias_reduced"`.

| Claim | Robust SE | Bias-reduced SE | Inflation | p change |
|---|---:|---:|---:|---:|
| Qwen B−C full-correction log-OR −0.282 | 0.08185 | 0.08265 | +1.0% | .00057 → .00065 |
| Gemma numeric B−C log-OR +0.446 | 0.13513 | 0.13783 | +2.0% | .00097 → .00122 |

So the missing Mancl-DeRouen/KC correction is not material for Claims 3 or 4. Even a crude df/t correction leaves both p<.003.

**5. 16K Rerun Estimand**
The merged dataset does not identify “Qwen B at 16K vs Qwen C at 16K.” The clean estimand is:

> Accuracy under an adaptive Qwen-B policy: run B at 8K; if the 8K run hits the ceiling/no final answer, rerun that same tuple at 16K under Ollama 0.20.6 and use the rerun; otherwise keep the original 8K Ollama 0.20.2 output.

That policy is compared against unre-rerun Qwen-C at 8K. The paper mostly says this in [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:197) and [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:529). Phrase Claim 3 as a policy/sensitivity contrast, not a budget-normalized treatment effect.

**6. Post-Hoc Question Families**
The defense in [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:429) is too strong. The Box/Cup partition is principled, but not pre-specified before seeing the scoring artifact. Gemma interaction p=.031 would not survive even a simple two-model correction if treated as confirmatory; Qwen p<.001 is much stronger.

Gemma numeric B−C p=.001 survives Holm over five families, but the subgroup itself was discovered post hoc. Correct framing: credible exploratory heterogeneity, high priority for preregistered replication. Not “confirmed.”

**7. GEE Exchangeable vs Naive Cluster-Robust**
Yes: with rho 0.143/0.118 reported in [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:131), exchangeable GEE and cluster-robust GLM are numerically identical here.

Examples I reran:

| Contrast | GEE exchangeable | GLM cluster-robust |
|---|---:|---:|
| Qwen B−C | −0.2819 SE .0818 | −0.2819 SE .0823 |
| Gemma numeric B−C | +0.4459 SE .1351 | +0.4459 SE .1366 |
| Qwen C−F | +2.9913 SE .2332 | +2.9913 SE .2344 |

The important issue is clustering vs treating 22,660 rows independent. The paper’s marginal-vs-hierarchical discussion in [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:91) is methodologically fine but overstated for these estimates.

**Recommended Changes**

| Issue | Paper change |
|---|---|
| Part-2 selection | Reword as conditional/descriptive; do not call preferred when extraction differs sharply. |
| SESOI | Keep, but correct “±3 pp at 50%” to ~±4 pp and add ±50% sensitivity note. |
| Multiplicity | Label post-hoc Claim 8 and subgroup claims exploratory unless rerun with broader correction. |
| Small-cluster SE | Add bias-reduced SE check; no claim changes. |
| 16K merge | Define adaptive rescue-policy estimand explicitly. |
| Question families | Downgrade “confirmed” to “credible post-hoc heterogeneity.” |
| GEE exchangeable | Say clustering matters; exchangeable working correlation choice barely matters here. |