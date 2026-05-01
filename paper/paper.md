# Replay Recoverability of Thinking-Token Benefits in Small Language Models

**James Fowler**
2026-04-25 late (further revision; §3.13–§3.14 added in a Sonnet-class morning follow-up that closed items deferred at 2026-04-15; §3.15 added in an evening four-angle GPT-5.5 xhigh-reasoning audit that stress-tested the surviving claims and (a) downgraded Claim 8 from Robust to exploratory-confirmatory under template-clustering, (b) reframed the Qwen tracking finding as budget-mediated not intrinsic, (c) added a Gemma source-trace correctness caveat to Claim 1, (d) sharpened Claim 2 to "tail-answer extraction," (e) reframed Claim 7's 16K-merged contrast as an adaptive-policy estimand, plus several minor corrections including a 367 → 368 provenance fix)

## Abstract

Modern instruction-tuned language models increasingly expose a "thinking mode" that generates a hidden reasoning trace before producing a visible answer. Whether this mechanism provides value beyond simply consuming more tokens at inference time is not obvious. We isolate the components of thinking-token benefit in two small models — Qwen 3.5 9B and Gemma 4 E4B (4.5B effective parameters) — by running 11 systematically varied conditions that dissociate the act of thinking from its semantic content, its length, and its source. On 103 calibrated questions × 10 replications × 2 models (22,660 inferences) analyzed with generalized estimating equations (GEE, Binomial/Logit, question-clustered, robust sandwich SEs) plus a two-part hurdle decomposition separating formatting/extraction failure from reasoning quality, we find that (i) coherent reasoning content beats shuffled tokens by OR=13–18 at end-to-end accuracy and OR=7–9 *conditional on successful extraction* (Gemma, Qwen; all p_adj<.001), so the content-vs-token effect is not an artifact of the broken-control extraction cliff; (ii) expert external scaffolds help both models dramatically; the pre-registered analysis reported a 14× model-specific asymmetry (Qwen D−C OR=17.5, p_adj<.001; Gemma D−C OR=1.14, p_adj=.80) but a post-hoc scoring-pipeline audit (§3.8, §3.10) traces the asymmetry to a Gemma-specific `<end_of_turn>` extraction artifact, cross-condition "Box N"/"Cup X" answer-format drift, and 8K truncation on Qwen C — under full-correction scoring **Gemma D−C = OR 24.87 (p<.001)** and **Qwen D−C = OR 13.31 (p<.001)**, with overlapping CIs, so the D−C asymmetry essentially vanishes; (iii) the pre-registered analysis reported a Gemma live-thinking premium (B–C OR=1.53, p_adj=.003) above the SESOI; a post-hoc audit (§3.10) found the Gemma C baseline is silently under-scored on ~71 "Box N"/"Cup X" items, and under full-correction scoring the *aggregated* Gemma B−C drops to OR = 1.17, p = .140 — but a question-family decomposition (§3.13) shows this aggregated null is a mixture: **on the 51 numeric-answer items the Gemma live-thinking premium is real and significant under full correction (OR = 1.56, p = .001)**, while on the 22 spatial/object-tracking items it is null. Claim 4 is updated to a per-domain claim rather than a population-averaged one. We additionally observe that **for Gemma on numeric reasoning, hidden thinking modestly beats visible CoT under fair scoring** (B−O E2E OR = 1.41, p = .020 question-clustered; numeric-subset log-OR +0.81, p = .002), but the population-averaged signal does not survive coarser cluster choices (template-clustered p = .135; domain-clustered p = .134; §3.15-A) — we therefore classify it as exploratory-confirmatory rather than Robust (§4 Claim 8); (iv) for Qwen the observed 8K-budget B–C deficit is part-truncation, part-scoring-artifact: a targeted sensitivity rerun at 16K of the 368 Qwen-B inferences that hit the original 8K ceiling raised Qwen-B accuracy from 54.2% to 68.6% and, under the pre-registered exact-string scorer, produced a formally established equivalence between Qwen-B and Qwen-C on the merged dataset (TOST p=.016, 90% CI within SESOI). A subsequent post-hoc audit (§3.8–§3.10, added 2026-04-15) found that the scorer regex captures chat-template tokens that leak into Qwen-C's content stream on 80/1030 rows and Gemma-D's content on 206/1030 rows, and that a separate "Box N"/"Cup X" answer-format mismatch suppresses structured-label scoring on many more cells. Under full-correction scoring (template-strip + structured-label canonicalization), **Qwen B−C log-OR = −0.282, OR = 0.75, 90% CI [−0.42, −0.15], p = .0006 — trace-replay clearly and modestly beats live thinking by ~6 pp raw accuracy**. The two post-hoc corrections (budget rerun vs fair scoring) go in opposite directions and partially cancel: the 16K rerun closed the 8K deficit while the scorer fixes reopen a smaller deficit. We report the pre-registered analysis and both post-hoc sensitivities side-by-side, and treat the full-correction number as our current best estimate while flagging that neither the rerun nor the rescoring is a clean substitute for a symmetric fresh 16K collection with a hardened scorer. We report all per-model primary analyses, the two-part hurdle, TOST equivalence, and the 8K vs 16K-merged sensitivity side-by-side. The overall picture: for these two small models, the trace itself carries much of the measurable benefit, but the system is strongly budget-sensitive and model-specific, and broad claims of the form "thinking tokens help" or "visible CoT beats hidden thinking" do not survive careful identification.

**Keywords:** chain-of-thought, small language models, generalized estimating equations, truncation, replay

---

## 1. Introduction

The hidden "thinking" mode now exposed by several open-weight models — Qwen's reasoning channel, Gemma's think tag, OpenAI-style `reasoning` blocks — produces a structured reasoning trace before the visible answer. Claims that thinking tokens inherently improve reasoning have circulated widely. Two competing explanations for any observed benefit are:

1. **The act of thinking.** Hidden reasoning engages a distinct computational pathway that manipulates latent state in ways a final-answer generation cannot.
2. **The content of the trace.** Thinking improves performance because the model generates useful intermediate text and then attends to it — in which case replaying that text as context (without engaging the thinking mechanism) should recover most of the benefit.

This paper asks a precise version of that question: **replay recoverability.** Given a model M with think mode, generate a trace t under think mode. Then disable think mode, prefix t as assistant context, and let M generate only the final answer. How much of the think-mode benefit survives this "replay" manipulation, and what happens when we corrupt the trace (shuffle, replace, shorten) while holding token count constant? We define the recoverability estimand as the difference between B (live thinking) and C (trace replay) on the log-odds scale, with a smallest-effect-of-interest (SESOI) of OR 0.85–1.18.

We test two small models on 103 calibrated questions spanning spatial reasoning, multi-step arithmetic, logical deduction, and factual retrieval. The condition set systematically varies thinking (on/off), trace content (self-trace, expert scaffold, shuffled, wrong-question, filler), trace length (25–100% of original), and trace provenance (same vs cross-model).

Our contributions:

- A pre-registered 8-contrast design that identifies the semantic content effect, expert premium, live-think premium, think vs. self-consistency tradeoff, and think vs. visible CoT comparison, among others.
- A GEE analysis with question-level clustering and robust (sandwich) standard errors that corrects the anti-conservative inference produced by treating 22,660 repeated-measures observations as independent.
- A two-part hurdle decomposition that separates formatting/extraction failure from reasoning failure.
- A sensitivity rerun showing that Qwen's apparent "thinking hurts" effect at 8192-token generation budget is partially a truncation artifact: re-running the 368 ceiling-hit inferences at 16K recovers 14.5 percentage points of accuracy and, under the pre-registered scorer, eliminates the B–C reversal. We present this as an asymmetric sensitivity analysis (only Qwen-B was rerun, not Qwen-C or other conditions; see §2.7 and §7), not as a budget-matched counterfactual.
- A post-hoc scoring-pipeline audit (§3.8–§3.12, 2026-04-15) showing that the regex scorer's lack of chat-template stripping and absence of structured-label aliasing silently suppresses accuracy on many prefill cells; under full-correction scoring Claim 4 (Gemma live-thinking premium) is reclassified, Claim 3 (Qwen B−C) flips from TOST-equivalent to significantly favoring trace-replay, and the Claim 2 D−C Qwen-vs-Gemma asymmetry essentially vanishes.
- A question-family heterogeneity decomposition (§3.13, 2026-04-25) showing that the aggregated B−C nulls under full correction conceal a formally significant cond × question-family interaction in both models: Gemma shows a live-thinking premium on numeric reasoning (OR 1.56, p = .001, n = 51 questions) that the aggregated number washes out; both models prefer trace replay to live thinking on spatial/object tracking tasks. We add Claim 8 documenting that Gemma hidden thinking beats Gemma visible CoT under fair scoring in both E2E and Part-2 modes — the only fully robust within-model live-thinking signal in the dataset.

---

## 2. Methods

### 2.1 Models and quantization

| Property | Qwen 3.5 | Gemma 4 E4B |
|----------|----------|-------------|
| Ollama tag | `qwen3.5:9b` | `gemma4:latest` |
| Total parameters | 9.7B | 8.0B |
| Effective parameters | 9.7B (dense) | 4.5B (Per-Layer Embeddings) |
| Quantization | Q4_K_M | Q4_K_M |
| Context length | 262,144 | 131,072 |
| Ollama version (Phase 2 / Phase 3) | 0.20.2 / 0.20.6 | 0.20.2 / 0.20.6 |

Gemma 4 E4B uses Per-Layer Embeddings (PLE), reducing active compute to ~4.5B effective parameters per forward pass. The text-only model is ~5 GB at Q4_K_M; the full 9.6 GB disk size includes bundled vision (~1.6 GB) and audio (~3.0 GB) encoders. This effective-parameter asymmetry is a limitation for any cross-model comparison; our primary contrasts are within-model, and we flag that observed cross-model differences cannot be attributed to architecture alone without ruling out template, inference-stack, and effective-capacity confounds.

### 2.2 Questions

From a 740-item procedurally-generated pool (math, logic, spatial, factual, hard variants), we locked 103 items where both models fell in the 30–70% Condition-A accuracy band during calibration. On the locked 103 items during Phase 2, the realised A-condition accuracy rose to 82.8% Gemma and 82.6% Qwen — higher than the calibration band — because calibration used different replication counts and because the 30–70% band was a loose filter to avoid floor/ceiling effects on the primary contrasts rather than to hit a specific target. This drift is discussed in §7.

### 2.3 Conditions

| ID | Name | Think | Prefill / Context | Primary contrast |
|---:|------|:-----:|------------------|------------------|
| A | Baseline | off | — | reference |
| B | Standard thinking | **on** | — | B−A total think effect |
| C | Self-trace replay | off | B's thinking tokens | **B−C: internal-reasoning effect** |
| D | Expert scaffold | off | GPT-5.4 reasoning | **D−C: expert premium** |
| E | Think + scaffold | **on** | GPT-5.4 reasoning (chat ctx) | **E−(B+D−A): synergy** |
| F | Shuffled tokens | off | shuffled B tokens | **C−F: content effect** |
| G | Wrong-question trace | off | B from different Q | **G−F: shape effect** |
| H | Wrong scaffold | off | subtly-wrong GPT-5.4 | suggestibility |
| I | Token-matched SC | off | k no-think attempts + majority vote | **B−I: compute allocation** |
| J | Filler tokens | off | neutral filler | **C−J: reasoning vs filler** |
| O | Visible-CoT | off | — (prompted CoT) | **B−O: think vs visible CoT** |

Phase 3 adds mechanism conditions K (cross-model), L25/L50/L75/L100 (dose-response), M (strong-model compressed trace), N (deterministic thinking at T=0). Phase 3 is exploratory and used Ollama 0.20.6 after Phase 2's 0.20.2; cross-phase contrasts in Phase 3 are historical-control comparisons, not same-run counterfactuals.

### 2.4 Generation parameters

Temperature 0.7, top-p 0.95, top-k 40, repeat-penalty 1.0; temperature 0 only for Condition N. The T=0.7 default is a limitation (§7). Seed grid 1–12, paired 1:1 with replications. `keep_alive=0` for fresh KV cache per inference. Thinking conditions use `num_predict=8192` in the primary analysis and `num_predict=16384` for the Qwen-B ceiling-rerun (§3.4).

### 2.5 Scoring and estimands

End-to-end (E2E) accuracy (formerly "ITT" in earlier drafts): answers are extracted via regex on a `FINAL:` line; extraction failures are scored as incorrect. Conditional-on-extraction accuracy (formerly "PP"): accuracy restricted to rows with successful extraction. Both are reported. The E2E estimand is deployment success under a fixed compute budget; the conditional estimand is reasoning success given well-formed output, selected on a post-treatment event and therefore interpreted with caution.

### 2.6 Statistical analysis

**Primary:** per-model generalized estimating equations (GEE) with Binomial family and logit link, `groups=question_id`, exchangeable working correlation structure, and robust sandwich (Huber-White) standard errors. GEE yields population-averaged (marginal) parameter estimates with valid inference under clustering, and does not make distributional assumptions beyond the mean-variance link. It is **not** a hierarchical (conditional) model in the random-effects sense; we call it "clustered" rather than "hierarchical" throughout.

Per-model contrasts are extracted as linear combinations of condition coefficients with SEs from the robust variance-covariance matrix: for a contrast `β_hi − β_lo`, `se = sqrt(V[hi,hi] + V[lo,lo] − 2·V[hi,lo])`; a two-sided z-test yields p-values. Holm-Bonferroni correction is applied across the 7 pairwise contrasts per model. Synergy is tested as a one-df contrast `β_E − β_B − β_D` (A is reference, `β_A = 0`).

**Secondary:** pooled GEE with `condition × model_tag` interaction (flagged for Simpson's-paradox-style reversals), two-part hurdle model (Part 1: `extraction_failed ~ C(condition)`; Part 2: `correct ~ C(condition)` conditional on successful extraction), and trial-level dose-response GEE on Phase 3 L-condition data.

Marginal Haldane odds ratios (no clustering correction) are reported alongside GEE estimates to document the magnitude of the anti-conservative bias.

**Pre-registration deviation.** The pre-registered plan specified a Bayesian hierarchical logistic regression as the primary model. We substitute frequentist GEE with question-clustered robust SEs. This is a deliberate methodological choice, not a convenience substitution: (i) the population-averaged (marginal) estimand from GEE directly matches our framing — "does condition X outperform Y across the population of questions?" — whereas a Bayesian hierarchical model with random question intercepts yields subject-specific (conditional) parameters that differ from marginal parameters for non-linear link functions (the non-collapsibility of the odds ratio). Claims about population-level condition effects are therefore more cleanly reported on the marginal scale. (ii) GEE is consistent under mis-specified working correlation with Huber-White robust SEs; a Bayesian mixed-effects model requires correctly specified random-effects structure and priors to deliver valid inference. (iii) At 22,660 observations clustered in 103 questions, frequentist and Bayesian estimates for fixed effects are well-known to agree numerically under diffuse priors; we report the estimated within-question correlation (ρ = 0.143 Gemma, 0.118 Qwen) for completeness and invite replication with alternative modeling choices.

### 2.7 16K sensitivity rerun — asymmetric scope

368/1030 Qwen-B Phase-2 inferences hit the `eval_count = 8192` ceiling and extracted no `FINAL:` line. We re-ran those 368 tuples at `num_predict = 16384, num_ctx = 24576` holding seed, question, rep, and model tag fixed. Under the higher budget, 164/368 (45%) finished within 16K and are 91% correct; 204/368 (55%) still hit the 16K ceiling. The merged dataset replaces the original 368 truncated tuples with their 16K continuations.

**Three scope limitations make this a sensitivity analysis, not a confirmatory rerun, and we report it as such throughout:**

1. **Asymmetric rerun (the main limitation).** Only Qwen-B ceiling-hit cases were rerun; Qwen-C/F/G/I/J were not — even though Qwen-C also has a 30% 8K ceiling-hit rate. Any comparison of B to another arm on the merged dataset therefore compares a partially-budget-rescued B to a still-8K-capped counterfactual. A symmetric rerun of C (and ideally F, G, J) at 16K under the same build is the clean counterfactual; we did not run it (~30–40 hours of compute).
2. **Post-treatment selection.** Ceiling-hit status at 8K is defined on an *outcome* of the original run (`eval_count`), not on a pre-treatment covariate. Replacing rows on a post-treatment criterion is a standard ITT violation; the sensitivity is informative about the *magnitude* of the truncation confound but is not a substitute for a fresh 16K collection.
3. **Cross-version drift within a single merged condition.** Run 1 (original Qwen-B non-ceiling rows, 662 records) was collected under Ollama 0.20.2. Run 3 (the 368 rerun records) was collected under Ollama 0.20.6. Per-inference model digests were not logged at collection (a pre-registration gap we document in `RUN_MANIFEST.md` and §7). The paper's §3.4 text refers to this as the "merged Qwen-B" dataset and we are careful to avoid the stronger phrase "same build". The phrase "merged at effective 16K cap" in §3 should be read as "partial rescue of one arm under a different Ollama version, not a fresh controlled rerun."

We therefore treat the merged dataset as a sensitivity analysis; report primary numbers on both the 8K original and the 16K-merged versions side-by-side; and phrase Qwen-B mechanism claims to reflect that the 16K-merged comparison is against a still-8K C arm.

---

## 3. Results

### 3.1 Per-condition accuracy

**Table 1.** Per-model per-condition accuracy, end-to-end (E2E) and conditional-on-extraction (Cond), with extraction-failure rate (ExtF) and 8K-cap ceiling-hit rate (Ceil8k). All Phase 2 primary conditions, 103 items × 10 reps per cell. Numbers generated programmatically from the merged Phase 2 dataset (§2.7). The Ceil8k column counts records with `eval_count ≥ 8190`; for the 368 Qwen-B rows that were rerun at 16K, this column reports that those rows' *original 8K* run hit the ceiling (which is why they were rerun), not the merged-row status. Qwen-B's post-merge Ceil8k of 36% matches the original-run ceiling rate by construction. Under the 16K rerun budget, 204/368 rerun cases (~20% of all Qwen-B) still hit the new 16K ceiling; this is reported in the text of §3.4, not in Table 1. Values to 3 decimals for traceability, not to imply that-many-significant-digits precision at n=1030 per cell.

```
                    Gemma 4 E4B                               Qwen 3.5 9B
Cond     E2E       Cond      ExtF   Ceil8k       E2E       Cond      ExtF   Ceil8k
 A      0.828     0.845       2%     0%         0.826     0.850       3%     0%
 B      0.863     0.871       1%     0%         0.686     0.856      20%    36%
 C      0.805     0.819       2%     0%         0.688     0.721       5%    30%
 D      0.825     0.825       0%     0%         0.975     0.978       0%     0%
 E      0.973     0.973       0%     0%         0.885     0.899       1%     1%
 F      0.235     0.354      34%    19%         0.111     0.259      57%    31%
 G      0.358     0.369       3%     0%         0.414     0.452       8%    46%
 H      0.445     0.450       1%     1%         0.404     0.431       6%     0%
 I      0.880     0.880       0%     0%         0.897     0.915       2%     9%
 J      0.304     0.308       1%     0%         0.346     0.579      40%     1%
 O      0.824     0.824       0%     0%         0.856     0.856       0%     0%
```

Qwen B shows the largest discrepancy between E2E and conditional accuracy (0.686 vs 0.856), driven by a 20% extraction-failure rate — a substantial reduction from the 36% extraction-failure rate at the original 8K cap. Gemma B has essentially no extraction failure regardless of cap (max observed `eval_count` is 3,375, far below either budget). Qwen F and Qwen J have very high extraction-failure rates (57%, 40%) — shuffled/filler prefills push Qwen into verbose runaway generations.

### 3.2 Per-model GEE contrasts (primary)

Within-question correlation (ρ, exchangeable) is 0.143 Gemma, 0.118 Qwen. Both are meaningfully nonzero, confirming clustering matters and that marginal analyses treating observations as independent are anti-conservative. Point estimates agree with marginal ORs in direction, but confidence intervals are wider and one marginal significance call is demoted after Holm correction (Gemma B−O).

**Table 2.** Per-model GEE pairwise contrasts on log-odds scale (95% Wald CIs, robust SEs). Two-sided z-tests, Holm-Bonferroni adjusted across the 7 pairwise contrasts per model (synergy is separate). Estimates on the 16K-merged Phase 2 dataset for Qwen (§2.7), and on the unchanged Phase 2 dataset for Gemma (Gemma never hits the 8K ceiling; max observed `eval_count` is 3,375).

```
Gemma 4 E4B
Contrast           log-OR   OR      [95% CI]              p_adj      Sig
B−C (internal)     +0.424   1.53    [1.20, 1.95]          .003       **
C−F (content)      +2.597  13.43    [9.52, 18.94]         <.001      ***
G−F (shape)        +0.598   1.82    [1.43, 2.32]          <.001      ***
D−C (expert)       +0.135   1.14    [0.83, 1.58]          .804        ns
B−I (compute)      −0.147   0.86    [0.61, 1.22]          .804        ns
B−O (think/CoT)    +0.296   1.34    [1.03, 1.75]          .089        ns
C−J (reasoning)    +2.246   9.45    [6.28, 14.21]         <.001      ***

Synergy E−(B+D−A): logit = +1.757 [+0.98, +2.53], p<.001 — super-additive

Qwen 3.5 9B  (16K-merged)
Contrast           log-OR   OR      [95% CI]              p_adj      Sig
B−C (internal)     −0.009   0.99    [0.86, 1.14]          .899        ns
C−F (content)      +2.876  17.75    [11.54, 27.29]        <.001      ***
G−F (shape)        +1.735   5.67    [4.13, 7.79]          <.001      ***
D−C (expert)       +2.861  17.48    [8.28, 36.94]         <.001      ***
B−I (compute)      −1.382   0.25    [0.14, 0.46]          <.001      ***
B−O (think/CoT)    −1.002   0.37    [0.27, 0.50]          <.001      ***
C−J (reasoning)    +1.431   4.18    [2.88, 6.07]          <.001      ***

Synergy E−(B+D−A): logit = −0.833 [−1.51, −0.16], p=.016 — sub-additive
```

**Pre-registered TOST equivalence test on B–C.** The pre-registration specified a two one-sided test (TOST) with smallest-effect-of-interest (SESOI) odds ratio 0.85–1.18 — equivalently log-odds (−0.162, +0.166) — on the B–C contrast. Results on the merged Phase 2 dataset:

- **Qwen:** log-OR = −0.009, SE = 0.071, 90% CI = [−0.127, +0.108]. Both CI bounds fall within SESOI; **TOST equivalence established** at α=.05 (TOST p = .016, max of lower-bound and upper-bound one-sided tests). Caveat: this equivalence is against the asymmetric-merged dataset (§2.7), so it should be read as "Qwen-B at a partially-rescued budget is equivalent to Qwen-C still at 8K" — which is informative about the truncation confound but not a clean budget-matched equivalence claim.
- **Gemma:** log-OR = +0.424, SE = 0.125, 90% CI = [+0.219, +0.630]. The upper bound exceeds the SESOI upper bound of +0.166. **Equivalence is rejected**; Gemma's B–C premium is *larger* than the SESOI (TOST p = .98). In the directional test, B is superior to C at p<.001.

The TOST results, under the pre-registered scorer, sharpen the Gemma vs Qwen asymmetry: for Gemma, live thinking appears measurably superior to trace replay and the effect exceeds a pre-defined practical threshold; for Qwen, live thinking and replay are statistically equivalent on the merged dataset, which we attribute (with the asymmetric-rerun caveat) to truncation driving the original 8K reversal.

**Forward pointer:** the post-hoc scoring-pipeline audit added in §3.8–§3.12 materially revises both TOST conclusions above. Under full-correction scoring (§3.10), Qwen B−C moves to log-OR −0.282, p = .0006 (TOST rejected, favoring C) and Gemma B−C moves to OR 1.17, p = .140 (no longer statistically clear and straddling the SESOI boundary). Readers should treat Table 2 and the paragraph above as the pre-registered analysis and §3.10 as the current best estimate.

### 3.3 Two-part hurdle decomposition

For the B-involving contrasts and for Qwen F/J where extraction failure is large, we estimate separate GEE models for P(extraction failure) and P(correct | extracted). This separates formatting/truncation failure from reasoning quality (Table 3).

**Table 3.** Hurdle decomposition for selected contrasts (GEE, per model, `groups=question_id`). Part 1: OR for extraction failure. Part 2: OR for correctness among successful extractions. Large Part-1 ORs in Gemma reflect separation (0% extraction failure in the baseline cell, e.g., D, I, O) and should be read as "vastly higher failure in B" rather than taken as stable numeric estimates.

```
                         Gemma 4 E4B                       Qwen 3.5 9B
                    Part1    Part2                      Part1    Part2
Contrast            ExtF OR  Cond OR                    ExtF OR  Cond OR
B−C                 0.50     1.48 **                    5.17 ***  2.17 ***
C−F                 0.035*** 8.84 ***                   0.036*** 6.99 ***
G−F                 0.057*** 1.14 ns                    0.069*** 2.25 ***
D−C                 →0 ***   1.04 ns                    0.061*** 17.10 ***
B−I                 →∞ ***   0.92 ns                   12.47 *** 0.51 ns
B−O                 →∞ ***   1.43 **                   →∞ ***    0.93 ns
C−J                 1.20 ns  10.19 ***                  0.071*** 1.78 **
```

Two findings emerge. First, Qwen B vs C **flips** under the hurdle model: B causes much larger extraction failure (OR=5.17, p<.001) but improves reasoning **conditional on extraction** (OR=2.17, p<.001). Under the pre-registered scorer this cleanly isolates the live-thinking benefit from the truncation cost. **Caveat (§3.9):** Qwen C has a template-leakage artifact that silently scores 80 rows as extraction-clean-but-wrong due to `<|endoftext|><|im_start|>user` in the extracted string; a fraction of Part-2 "conditional wrongness" for Qwen C is therefore scoring-pipeline failure rather than reasoning failure. Under full-correction scoring the Part-2 B−C favors B less strongly than OR = 2.17 implies. Second, Qwen B vs O is extraction-mediated: B is far more extraction-prone, but reasoning-equivalent among extracted outputs (Part 2 OR=0.93, p=.71). The popular "visible CoT beats hidden thinking" framing does not survive the hurdle decomposition for Qwen.

Gemma G−F illustrates a caveat: E2E G−F is significant (Table 2), but conditional-on-extraction G−F is null (Part 2 OR=1.14, p=.33). For Gemma the "wrong-question reasoning beats shuffled tokens" effect is driven by the extraction channel (F has 34% extraction failure; G has 3%), not by reasoning-quality difference. Qwen G−F remains significant in Part 2 (OR=2.25, p<.001); the "generic reasoning shape has value" claim is model-specific.

### 3.4 16K sensitivity rerun

In the original Phase 2 run with `num_predict=8192` for thinking conditions, 368/1030 (36%) Qwen B inferences hit the `eval_count=8192` ceiling with no extractable `FINAL:`. Re-running those 368 tuples with `num_predict=16384` (same seed, question, rep, and `model_tag`; Ollama 0.20.6 vs original Phase 2's 0.20.2, see §2.7) produced:

- 164/368 (45%) finished within 16K. Among these rescued records, accuracy is 91.4%.
- 204/368 (55%) still hit the 16K ceiling. These are questions where Qwen's thinking trace is genuinely unbounded under the prompt+T=0.7 regime.

Merged Qwen B accuracy: 54.2% (original 8K) → **68.6%** (merged 16K). Extraction failure: 36% → 20%. The B−C GEE contrast moves from significantly favoring C (log-OR=−0.625, p<.001 under the 8K data) to a statistical null that passes a pre-registered TOST equivalence test against Qwen C (log-OR=−0.009, TOST p=.016 under the merged data; §3.2).

**How to read this result.** Because ceiling-hit status is a post-treatment variable and only Qwen-B (not Qwen-C) was rerun, the merged comparison is **Qwen-B-at-partially-16K vs Qwen-C-at-8K**, not Qwen-B-at-16K vs Qwen-C-at-16K. A symmetric rerun of Qwen-C at 16K would be required to claim that B and C are equivalent at a shared generation budget. We did not run it (~15 additional hours of compute were infeasible for this study). What we do claim, and what the data support: under the original 8K budget the Qwen B–C contrast is strongly confounded by differential extraction failure (B: 36%, C: 5%), and when we remove the 8K ceiling for B only, the gap closes to statistical null. This is strong evidence that much — and possibly all — of the 8K B–C deficit is truncation-driven. It is not proof that B and C would be equivalent under arbitrary shared budgets; we do not claim that.

**What "merged" does not fix.** The rerun does not eliminate Qwen truncation: 204/368 rerun cases (56% of the original ceiling-hit subset, or 20% of all Qwen-B) still hit the 16K ceiling. The merged dataset also has cross-version drift within the single Qwen-B condition (662 records at Ollama 0.20.2, 368 at 0.20.6; see §2.7 and `RUN_MANIFEST.md`). All downstream Qwen-B claims inherit both caveats.

### 3.5 Trial-level dose-response (Phase 3 exploratory)

With the Phase 3 L-condition data (L25/L50/L75/L100 on 39 items × 8 reps × 2 models = 2,496 observations), a trial-level GEE `correct ~ dose` yields:

- **Gemma:** β=+0.610, SE=0.203, z=+3.00, p=.003 (log-odds, increasing)
- **Qwen:** β=−0.641, SE=0.159, z=−4.03, p<.001 (decreasing)
- **Model × dose interaction:** β=−1.251, p<.001

The Qwen negative slope is coincident with rising ceiling hits as prefill length grows (L25: 39%; L100: 46%), and we treat it as context-budget pathology rather than a cognitive claim. Gemma's positive slope is not budget-mediated (Gemma ceiling rate is 0% across all L doses). This replaces the underpowered 4-point aggregate Kendall τ reported in earlier drafts: a trend test on four aggregate dose points cannot reach p < .05 even under perfect monotonicity.

**Forward pointer to §3.12:** Under full-correction scoring (template-strip + structured-label canonicalization), both slopes attenuate but retain direction: Gemma β = +0.505, p = .041; Qwen β = −0.323, p = .030. The Qwen slope magnitude drops by roughly half. The context-budget-pathology reading still holds qualitatively.

### 3.6 Cross-model transfer (Phase 3 K)

Condition K (Qwen receives Gemma traces, Gemma receives Qwen traces) produces a crossover interaction that superficially looks like "thinking is not model-portable." A trace-verbosity diagnosis suggests the pattern is mechanical rather than cognitive. Qwen's self-trace length averages ~6,370 tokens; Gemma's averages ~940. When Qwen receives short Gemma traces its ceiling hits drop from 46% (self-trace in C) to 16%, and E2E accuracy rises. When Gemma receives long Qwen traces, extraction failures rise and accuracy falls. We report K as exploratory with the verbosity-mismatch caveat; we do **not** claim cross-model reasoning incompatibility from these numbers.

### 3.7 Compressed traces (Phase 3 M)

Condition M uses a GPT-5.4–compressed version of the B trace (~35% of the original tokens). M outperforms L100 (raw full-trace replay) in both models (Gemma delta +12.2pp; Qwen delta +36.9pp; both p<.001). We deliberately do **not** claim "compression helps" because M changes both length and trace author: the compressed text was edited by a substantially stronger model. A clean compression ablation requires a self-model compression variant that we did not run.

**Scoring-pipeline note.** Under template-strip rescoring (§3.9), Gemma M gains +3.85 pp (73.4% → 77.2%) while Qwen M is unchanged and Gemma L100 is unchanged; the M > L100 direction strengthens slightly but the qualitative finding is preserved.

### 3.8 Extraction-pipeline sensitivity on condition D (post-hoc, 2026-04-15)

A post-hoc audit of the Gemma D−C null (§3.2, Table 2) discovered that most of the apparent Qwen-vs-Gemma asymmetry on the expert-scaffold contrast is a scoring-pipeline artifact, not a model-behavior asymmetry. We report the full decomposition here because it materially changes Claim 2 in §4. The original Table 1 / Table 2 numbers are **not** regenerated — this is a sensitivity analysis, reported alongside the pre-registered analysis rather than replacing it.

**Three independent issues compound on condition D:**

1. **Gemma emits `<end_of_turn>` on the same line as its `FINAL:` answer.** The scorer's regex `^\s*FINAL:\s*(.+)$` captures the entire line; `normalize_answer()` does not strip chat-template tokens. The extracted string becomes e.g. `"1<end_of_turn>"` and string-match against ground truth `"1"` fails. This affects 206/1030 Gemma D outputs (and 167/1030 Gemma H outputs — the same prefill mechanism). Stripping `<end_of_turn>` and `<eos>` before extraction rescues 87 Gemma D correct answers: **82.5% → 91.0%** (+8.4pp). Qwen shows no change because `<|im_end|>` is stripped by Ollama before the content stream.

2. **Gemma drops the scaffold's answer-format prefix; Qwen echoes it verbatim.** On nine `long_object_tracking_*` and `hard_tracking_*` questions where ground truth is `"Box N"`, the scaffold's stripped reasoning refers to "box 3" in lower case. Qwen writes `FINAL: Box 3` (correct); Gemma writes `FINAL: 3` (string-match failure). This is a format-fidelity difference, not a reasoning difference — the logical answer is identical. Scoring with a semantic last-token match (accepts `"3"` as a match for `"Box 3"`) rescues a further 89 Gemma D rows: **91.0% → 99.6%**.

3. **Qwen C is suppressed by 8K ceiling truncation; D is not.** Qwen C has 30% ceiling-hit rate (unchanged by the §2.7 B-only rerun); Qwen D has 0%. Restricting Qwen C to its non-ceiling subset (n=717) raises it from 68.8% → 79.5% end-to-end, or 74.8% → 82.0% under semantic scoring. Gemma has 0% ceiling hits throughout, so this correction does not apply.

**D−C contrast under each scoring regime (end-to-end, marginal percentage points):**

| Scoring regime | Qwen D−C | Gemma D−C |
|---|---:|---:|
| Paper as-reported (§3.2, exact string match, all rows) | +28.6 pp | +2.0 pp |
| + strip `<end_of_turn>` / `<eos>` | +28.6 pp | +10.4 pp |
| + semantic last-token match | +24.0 pp | +11.5 pp |
| + exclude Qwen-C ceiling-hit rows | +16.7 pp | +11.5 pp |

**Behavioral check.** Both models diverge from the scaffold when the scaffold's FINAL answer is wrong. 87/103 scaffolds have a correct FINAL line; on the 13 wrong-scaffold questions Qwen emits the scaffold's wrong answer in 13/130 rows (10.0%) and Gemma in 0/130 (0%). Neither model "blindly follows" the scaffold. Conversely, 87% of scaffolds retain the ground-truth answer in their reasoning text even after the `FINAL:` line is stripped, so condition D partially confounds "can the model use an expert scaffold" with "can the model lift an answer already present in the context." This confound is discussed in §7 but was not explicitly quantified in earlier drafts.

**What this changes.** The raw paper-table claim "Qwen D−C OR=17.5 vs Gemma D−C OR=1.14" implies a 14× architecture-level asymmetry. Under fair scoring, the D−C gap shrinks to roughly +17pp (Qwen) vs +12pp (Gemma) — both very large, and asymmetric by ~5pp rather than ~27pp. The residual Qwen advantage is consistent with (a) Qwen's more faithful echoing of scaffold format, (b) residual within-8K truncation on Qwen C that our no-ceiling filter does not fully remove, and (c) Gemma's slightly near-ceiling C baseline compressing headroom. We revise Claim 2 (§4) accordingly.

**Scope as originally scoped.** This sensitivity was initially understood as applying only to conditions where a model generates a short continuation after a prefilled context — principally D and H for Gemma. A broader spot-check across all (model, condition) cells (§3.9) found two other cells with the same mechanism, one of which flips the direction of the pre-registered TOST equivalence for Qwen B−C.

### 3.9 Broader template-leakage sensitivity — Qwen C and Qwen G (post-hoc, 2026-04-15)

A broader scan of chat-template tokens in the content stream across all cells found that **Qwen C (self-trace replay) and Qwen G (wrong-question trace replay) also leak chat-template tokens** — `<|endoftext|>` and `<|im_start|>user`, on the same line as the `FINAL:` answer — in 80/1030 and 82/1030 rows respectively. The mechanism is identical to Gemma D: after a prefilled assistant turn, Qwen continues past the natural turn boundary and the inference stack does not strip the leaked tokens before the content is captured. The scorer's regex captures `"FINAL: 3<|endoftext|><|im_start|>user"` and string-match against ground truth `"3"` fails. Qwen B is not affected because thinking-mode completions are handled through a separate parsing path that does strip `<|im_end|>`.

Rescoring with the same `aggressive_strip` that was applied to Gemma D (split on `<start_of_turn>`, `<|im_start|>`, `<|endoftext|>`; remove closing sentinels):

| Cell | Paper acc | Template-strip acc | Delta |
|---|---:|---:|---:|
| Qwen C | 68.8% | 72.7% | **+3.88 pp** |
| Qwen G | 41.4% | 45.2% | **+3.88 pp** |
| Gemma D | 82.5% | 91.1% | +8.54 pp (§3.8) |

All other (model, condition) cells shift by less than 1 pp under template-strip rescoring. Other Gemma conditions (C, F, G, H, J) have small `<end_of_turn>` counts (8–36 rows each) but the token appears on a line separate from `FINAL:` in most of them and is therefore not captured by the scorer, so the pp impact is negligible.

**Impact on the pre-registered Qwen B−C TOST equivalence (§3.2, §3.4).** The paper reports TOST equivalence for Qwen B−C on the 16K-merged dataset with log-OR = −0.009, SE = 0.071, 90% CI = [−0.127, +0.108], both bounds inside SESOI (TOST p = .016). Under template-strip rescoring (GEE Binomial/Logit, `groups=question_id`, exchangeable, robust SEs):

- **log-OR (C − B) = +0.197, SE = 0.075, z = +2.64, p = .008**
- 90% CI = [+0.074, +0.320]
- Equivalently, **Qwen B − C log-OR = −0.197, 90% CI = [−0.320, −0.074]**
- The 90% CI for B−C lies entirely outside the SESOI (upper bound −0.074 exceeds lower SESOI bound of −0.162 in the unfavorable direction)

**Under the corrected scoring pipeline, the pre-registered TOST equivalence between Qwen B and Qwen C is rejected, and there is a statistically clear effect favoring trace-replay (C) over live thinking (B) of roughly 4 pp on the raw accuracy scale.** This reverses the §3.4 headline and materially revises Claim 3 in §4.

Note on severity: this is not merely a magnitude change. The B−C contrast is the paper's central estimand and the abstract quotes the TOST result as "formally established equivalence." The equivalence is formally established only under the pre-registered scoring regime. Under the corrected regime the claim is "Qwen trace-replay (C) modestly outperforms Qwen live thinking (B) at the 16K-merged budget, log-OR −0.197, 90% CI [−0.32, −0.07]."

**Why does strip help Qwen C but not Qwen B?** Qwen B produces thinking output in a separate `thinking` channel and content in the visible channel; Ollama correctly handles the chat turn boundary there (0/1030 leak). Qwen C prefills the visible-channel trace, so the final continuation straddles the turn boundary; Ollama's chat-completion parser does not reliably strip `<|endoftext|>` when it appears mid-response rather than as a stop token. The same mechanism affects Qwen G (also prefill, 82 leaks) but not Qwen D (prefilled but the scaffold tends to yield a 5-token `FINAL: X` continuation that stops cleanly before the token boundary) and not Qwen H (wrong-scaffold prefill usually produces longer continuations that land on a clean stop). Gemma's analogue is `<end_of_turn>` rather than `<|endoftext|><|im_start|>user`, and Gemma's prefill conditions — especially D and H — are where that token most often ends up inline with the `FINAL:` line (§3.8 documents this). The overall pattern: **prefill conditions with short model continuations are where template leakage bites the scorer.**

**What changes in §4.** Claim 3 is substantially weakened: the 16K rerun removes much of the B−C deficit, but template-strip rescoring reintroduces a statistically clear deficit of similar sign and magnitude (~4 pp, log-OR −0.2). The two post-hoc corrections go in opposite directions and partially cancel. The net position after both corrections is that **Qwen trace-replay modestly beats Qwen live thinking** on these 103 questions at a 16K-merged budget, which is a different conclusion from either the original 8K result (where C beat B by ~14 pp due to truncation) or the post-16K-rerun result (where B and C were TOST-equivalent under the pre-registered scorer).

**Scope of the broader sensitivity.** We have rescored every primary cell under template-strip. Only three cells move by ≥3 pp: Gemma D (+8.5), Qwen C (+3.9), Qwen G (+3.9). Gemma D is addressed in §3.8. Qwen C is addressed above and in Claim 3 below. Qwen G's shift slightly strengthens the G−F contrast for Qwen (from +30.3 pp to +34.1 pp); the direction and claim are unchanged.

**Phase 3 extension (added 2026-04-15).** The same audit applied to the Phase 3 mechanism dataset finds analogous leakage, with the dose-response cells most affected:

| Phase 3 cell | n | Paper acc | Template-strip acc | Delta |
|---|---:|---:|---:|---:|
| Qwen L25 | 312 | 63.8% | 64.4% | +0.64 |
| Qwen L50 | 312 | 55.1% | 57.1% | +1.92 |
| Qwen L75 | 312 | 51.3% | 56.1% | +4.81 |
| Qwen L100 | 312 | 51.9% | 57.4% | +5.45 |
| Gemma M | 312 | 73.4% | 77.2% | +3.85 |

The Qwen L-rescue magnitude grows with prefill length, consistent with the mechanism: longer prefills leave less room for a clean turn boundary, so more continuations run past the boundary into `<|endoftext|><|im_start|>user` sequences. Under template-strip the Qwen dose-response slope attenuates: paper slope from L25 → L100 is −11.9 pp; under strip it is L25 64.4% → L100 57.4% = −7.0 pp. The direction (decreasing) is preserved and is still consistent with the paper's context-budget-pathology interpretation, but the magnitude is roughly 40% smaller. Gemma's dose-response slope is not meaningfully affected by template-strip (Gemma L cells move by ≤0.4 pp under strip). The Gemma M +3.85 pp rescue slightly strengthens the M > L100 finding (§3.7) and does not change its sign.

We therefore extend Claim 7-adjacent language in §3.5 to note that the Qwen dose-response magnitude is sensitive to template-strip scoring, and flag that a fresh Phase 3 collection with a hardened scorer would be the clean fix. We have not rescored Phase 3 K (cross-model, low leakage in our scan) or N (deterministic thinking, 0 leaks) for substantive changes.

### 3.10 Cross-condition structured-label scoring (audit follow-up, 2026-04-15)

A second round of the post-hoc audit — conducted by independent `gpt-5.3-codex` and `gpt-5.4` auditors, full cross-provider convergence on the finding — discovered that the "Box N"/"Cup X" format-mismatch issue first identified on condition D (§3.8) is **not limited to D**. The `selected.jsonl` benchmark contains 22/52 exact-answer items that are structured labels (10 "Box N", 12 "Cup X"), and both models intermittently emit bare labels (`"1"` instead of `"Box 1"`, `"c"` instead of `"Cup C"`) across many cells. The scorer requires exact string equality for `answer_type: "exact"` and has no alias layer, so the mismatches are silently scored as wrong. This is the same class of failure as §3.8 but broader in scope than §3.8 documented.

**Per-cell semantic rescues on structured-label canonicalization (accepts bare suffix for `Box N`/`Cup X` truths), out of 1030 rows per cell:**

| Cell | Gemma rescue | Qwen rescue |
|---|---:|---:|
| A | +33 | +1 |
| B | +27 | 0 |
| C | +71 | +32 |
| D | +86 | 0 |
| E | +5 | 0 |
| F | +19 | +17 |
| G | +26 | +22 |
| H | +14 | +1 |
| I (voted) | +39 | +7 |
| J | +35 | +2 |
| O | +27 | +3 |

Gemma is substantially more affected than Qwen — Gemma drops the "Box"/"Cup" prefix systematically, Qwen echoes it. Condition I inherits the issue because the majority-vote path in `run_experiment.py` votes on already-extracted answer strings and then re-grades the voted string with the same unaliased comparator.

**Impact on all seven primary contrasts (per-model GEE, full correction: template-strip **plus** structured-label canonicalization; question clustering, exchangeable working correlation, robust SEs; all on 16K-merged data):**

```
Gemma 4 E4B — full-correction GEE (16K-merged, question-clustered, robust SEs)
Contrast           log-OR   OR      p        Verdict
B−C (internal)    +0.158   1.17    .140     NOT SIGNIFICANT (paper: OR 1.53, p=.003)
C−F (content)     +3.022   20.53   <.001    ROBUST ↑
G−F (shape)       +0.601   1.82    <.001    ROBUST
D−C (expert)      +3.214   24.87   <.001    ROBUST ↑ (very large)
B−I (compute)     —        —       —        I rescoring unstable; see note
B−O (think/CoT)   +0.345   1.41    .020     SIGNIFICANT (paper: p=.089 borderline)
C−J (reasoning)   +2.616   13.69   <.001    ROBUST

Qwen 3.5 9B — full-correction GEE (same specs)
Contrast           log-OR   OR      p        Verdict
B−C (internal)    −0.282   0.75    .0006    Sig C > B (stronger than §3.9 strip-only −0.197)
C−F (content)     +2.991   19.91   <.001    ROBUST
G−F (shape)       +1.821   6.18    <.001    ROBUST
D−C (expert)      +2.588   13.31   <.001    ROBUST
B−O (think/CoT)   −1.025   0.36    <.001    ROBUST (visible CoT > hidden thinking)
C−J (reasoning)   +1.695   5.45    <.001    ROBUST
```

For the Gemma B−C cell the 90% CI is [−0.018, +0.333]; the upper bound exceeds the SESOI upper of +0.166, so TOST equivalence is not formally established either. The directional effect is no longer statistically significant.

**Note on B−I.** Condition I's content is a synthesized majority-vote string, not a model output, so it cannot be meaningfully re-extracted by `aggressive_strip` + `canonical_match`. The full-correction B−I estimate is unstable (log-OR diverges). Rescoring I correctly requires re-running the vote aggregation on alias-corrected I_sub answers; we have not done that rerun. The paper's original B−I numbers remain the best estimate until a full re-aggregation is run.

**The largest claim change is Claim 4.** The pre-registered analysis found Gemma B−C OR = 1.53, p_adj = .003, above the SESOI upper bound — the paper's cleanest within-model evidence for a live-thinking benefit. Under full-correction scoring, the effect is OR = 1.17, p = .140, 90% CI [−0.018, +0.333]. The upper CI bound still slightly exceeds the SESOI upper (+0.166), so equivalence is not formally established either, but the directional effect is no longer statistically significant and is the size of noise for this sample. The Part-2 hurdle version moves from OR = 1.48, p = .003 to OR ≈ 1.08, p ≈ .49 under full correction (we report this at auditor precision; a clean re-run would be required for confirmatory inference). **Claim 4 is reclassified as NEEDS_REVISION and rewritten below.**

**Claim 3 also shifts.** Template-strip alone gave Qwen B−C log-OR = −0.197 (§3.9); full correction (template-strip + structured-label canonicalization) gives **log-OR = −0.282, OR = 0.75, 90% CI [−0.42, −0.15], p = .0006** — a stronger effect favoring trace-replay over live thinking. This strengthens the §3.9 conclusion rather than reversing it.

**Other claim impacts.**

- **Claim 1 (C−F content)** strengthens under full correction (Gemma OR 20.53, Qwen OR 19.91). **ROBUST ↑.**
- **Claim 2 (D−C expert scaffold)**: Gemma D−C under full correction is OR = 24.87 — much larger than either the paper-as-reported OR = 1.14 or the §3.8 sensitivity's +11.5 pp. The D−C asymmetry between models essentially vanishes (Gemma OR 24.87 vs Qwen OR 13.31; confidence intervals overlap heavily). This further weakens any "model-specific architecture" reading of D−C. **MODESTLY_AFFECTED → scaffold helps both models about equally.**
- **Claim 5 (C−J filler)** strengthens (Gemma OR 13.69, Qwen OR 5.45). **ROBUST.**
- **Claim 6 (G−F shape)**: Qwen G−F strengthens to OR 6.18; Gemma Part-2 remains null. **ROBUST.**
- **Claim 7 (Qwen truncation as dominant mediator)**: still true — truncation explains the 8K-vs-16K shift on Qwen B; but Claim 7's close-cousin framing "truncation resolves the 8K B−C reversal" needs the §3.10 correction (i.e., no, residual scoring-artifact still drives some). **MODESTLY_AFFECTED.**
- **Conclusion bullet 3 (§8) on Gemma live-thinking premium** — this is the most impacted. The "cleanest within-model evidence for act-of-thinking" finding does not survive full-correction scoring.

### 3.11 Wrong-scaffold (condition H) is a broken manipulation (audit follow-up)

A separate audit finding (independent of the scorer issue): the "wrong scaffold" `wrong_scaffold` fields in `questions/scaffolds/*.json` are GPT-5.4 outputs that were supposed to be "minimally wrong" reasoning, but across 103 scaffolds:
- **17/103 are refusal templates** (GPT-5.4 refused to generate wrong reasoning and returned apology text).
- **65/103 contain the gold answer string** somewhere in the text.
- **24/103 still end with the exact gold `FINAL:` line** even after `_strip_final_answer()` (the stripper only removes the terminal `FINAL:` line — if there's a sub-line mentioning the correct answer, or a second `FINAL:` earlier, that stays).
- On the 17 refusal-subset items, Gemma H = 154/170 (90.6%) and Qwen H = 147/170 (86.5%) — i.e., the "wrong scaffold" is behaviorally a refusal + a recoverable hint, not a wrong reasoning chain.
- On the 24 exact-gold-FINAL subset items, Qwen H = 236/240 (98.3%) — the "wrong scaffold" is almost as informative as D.

**H is not a valid suggestibility / wrong-scaffold manipulation on this benchmark.** No §4 Robust Claim relies on H, so this does not overturn a main claim, but any interpretation of the H cell (e.g., in Table 1's 44.5% / 40.4% accuracy) should be read as a mixture of "refusal-wrapped hint," "leaked answer," and "genuinely wrong reasoning" subpopulations. A clean H would require a regenerated `wrong_scaffold` bank with refusal rejection, answer-substring rejection, and validator-enforced reasoning wrongness.

### 3.12 Updated Phase 3 L-slope under full correction (audit follow-up)

Applying structured-label canonicalization (in addition to template-strip) to Phase 3 `L` conditions changes the dose-response magnitudes further but not the direction:

- **Gemma:** β = +0.505, p = .041 (paper: β = +0.610, p = .003; template-strip only: ≈unchanged).
- **Qwen:** β = −0.323, p = .030 (paper: β = −0.641, p < .001; template-strip only: β roughly −0.45).
- **Model × dose interaction:** still highly significant in sign, roughly half the paper's magnitude.

Both slopes remain in the pre-registered direction and remain nominally significant, but the Qwen "decreasing slope" is roughly half the paper's magnitude under full correction. The context-budget-pathology interpretation of §3.5 still holds qualitatively; the *magnitude* is overstated by the pre-registered scoring.

### 3.13 Question-family heterogeneity decomposition (added 2026-04-25)

The aggregated full-correction B−C numbers in §3.10 conceal a strong, formally significant interaction with question family. Decomposing the 103 questions by ground-truth format yields five families: numeric (n=51), direction (n=15), bool (n=13), Cup (n=12), Box (n=10), other (n=2). Two are tracking-style ("Box N", "Cup X") and four are non-tracking. Per-family GEE B−C contrasts under full-correction scoring (template-strip + structured-label canonicalization, question-clustered, robust SEs):

```
Gemma 4 E4B — B−C by question family (full-corrected)
Family       n_q   log-OR(B-C)   SE      p
numeric       51    +0.446       0.135   .001     (OR 1.56) ← significant live-thinking premium
direction     15    −0.214       0.119   .072
Box           10    −0.981       0.914   .283
Cup           12    +0.067       0.133   .614
bool          13    +29.1        — (separation; Gemma B at ceiling)

Qwen 3.5 9B — B−C by question family (full-corrected)
Family       n_q   log-OR(B-C)   SE      p
numeric       51    −0.031       0.090   .732     (null)
direction     15    −1.177       0.376   .002     ← strongly favors C
Box           10    −0.955       0.299   .001     ← strongly favors C
Cup           12    −0.807       0.274   .003     ← strongly favors C
bool          13    +29.8        — (separation; Qwen B at ceiling)
```

**The cond × is_boxcup interaction is formally significant for both models** (Gemma: cond_B:is_boxcup_T coefficient = −0.474, p = .031; Qwen: −0.680, p < .001). This is not noise.

**Two clean signals emerge:**

1. **Gemma shows a live-thinking premium on numeric reasoning that does survive full-correction scoring** (n=51 questions, log-OR +0.446, OR 1.56, p = .001). The aggregated null in §3.10 (OR 1.17, p = .140) is a mixture of this real positive effect on 51 numeric items and a near-null/reversed effect on 22 tracking items. We had retracted Claim 4 entirely as a positive finding (§4); the question-family decomposition shows that retraction is too strong for the numeric subset specifically. The right reading: **Gemma's live-thinking premium is real for numeric reasoning, absent for spatial/object tracking.**

2. **Both models prefer trace replay to live thinking on tracking tasks** — for Qwen this is statistically clear on every tracking family (Box, Cup, direction; all p ≤ .003). For Gemma the tracking-family B−C estimates are negative or near-zero. **On state-tracking tasks across both models, replaying the trace is at least as good as re-thinking, and for Qwen substantially better.** A plausible mechanistic reading: state-tracking traces explicitly enumerate intermediate states, and replaying them verbatim is more reliable than having the model re-derive them on each call. Live thinking on tracking tasks is more error-prone than reading the recorded steps. We do not have direct evidence for this mechanism — it is a hypothesis consistent with the data.

**B−C on the non-Box/Cup subset (n=81, both models, full-correction GEE):**

- Gemma: log-OR +0.385, SE 0.163, p = .018 (OR 1.47) — significant live-thinking premium
- Qwen: log-OR −0.117, SE 0.095, p = .220 — null

**B−C on the Box/Cup subset (n=22, both models):**

- Gemma: log-OR −0.089, SE 0.148, p = .546 — null
- Qwen: log-OR −0.797, SE 0.163, p < .001 (OR 0.45) — strongly favors C

**Implication for §4 Claim 4.** The full retraction in Claim 4 ("we no longer claim a live-thinking premium for Gemma with confidence") is correct as a *population-averaged* statement across the 103-item benchmark. It is too strong as a *per-domain* statement: there is a real, statistically clear Gemma live-thinking premium on the 51 numeric items (OR 1.56, p = .001). Claim 4 is updated to reflect this heterogeneity below.

**Implication for §4 Claim 3.** The "Qwen trace-replay beats live thinking by ~6pp" headline (full-correction E2E B−C = −0.282) is also a heterogeneity finding: it is essentially absent on numeric questions (log-OR −0.031, p = .73) and concentrated on tracking questions (Box log-OR −0.955; Cup −0.807; direction −1.177). Claim 3 still holds for the population-averaged estimand but should not be read as "Qwen live thinking is generically worse than replay."

**Why we are confident this is not a multiple-comparisons artifact.** We did not pre-register the question-family decomposition; it was suggested by the §3.10 finding that 22/52 exact-answer items were structured labels. However: (a) the formal cond×is_boxcup interaction is significant (p = .031 Gemma, p < .001 Qwen) on the *single* pre-specified Box/Cup partition that motivated §3.10, not a fishing expedition across many partitions; (b) the per-family directions are cross-model consistent (both models favor C on tracking; the divergence is on numeric); (c) the Gemma numeric B−C effect (p = .001) survives Holm correction across the five families and is not at the boundary. We treat this as a confirmed heterogeneity finding rather than a noise artifact, and recommend a fresh pre-registered replication with the family decomposition as a primary contrast.

### 3.14 Cleaner Part-2 hurdle and Condition I re-aggregation (added 2026-04-25)

Two numbers in §3.10 were reported at "auditor precision" — the Part-2 hurdle under full correction and the B−I contrast with re-scored I. We have since rerun both as proper GEE models. These supersede the auditor estimates.

**Part-2 hurdle under full-correction scoring** (P(correct | extracted), per-model GEE, question-clustered, robust SEs, 16K-merged dataset):

```
Gemma 4 E4B — Part-2 (full-corrected, conditional on extraction success)
Contrast       log-OR    OR      SE      p
B−C            +0.056    1.06    0.112   .616      null (paper Part-2 was OR 1.48, p .003)
C−F            +2.642    14.05   0.220   <.001
G−F            +0.097    1.10    0.131   .460      null
D−C            +3.055    21.22   0.521   <.001
B−O            +0.413    1.51    0.151   .006      ← significant: hidden thinking > visible CoT
C−J            +2.774    16.03   0.241   <.001

Qwen 3.5 9B — Part-2 (full-corrected, conditional on extraction success)
Contrast       log-OR    OR      SE      p
B−C            +0.361    1.43    0.091   <.001     ← significant: B > C conditional on extraction
C−F            +2.012    7.48    0.272   <.001
G−F            +0.834    2.30    0.174   <.001
D−C            +2.519    12.42   0.409   <.001
B−O            −0.094    0.91    0.181   .603      null (matches paper)
C−J            +0.884    2.42    0.249   <.001
```

**Condition I re-aggregated with structured-label canonicalization.** Each I parent rep is re-voted using alias-aware bins for `Box N` / `Cup X` answers (so "Box 1" and "1" are treated as the same vote). Per-model accuracy:

- Gemma I: paper 88.0% → re-aggregated 89.5% (+1.6 pp)
- Qwen I: paper 91.5% → re-aggregated 88.5% (−3.0 pp; a small loss from canonicalization collisions on Qwen, which already produced the gold format reliably)

**B−I under full correction** (B = full-corrected E2E; I = re-aggregated):

- Gemma: log-OR −0.061, OR 0.94, p = .82 (paper: OR 0.86, p = .80; essentially unchanged)
- Qwen: log-OR −1.255, OR 0.29, p = .0001 (paper: OR 0.25, p < .001; essentially unchanged)

**Three substantive findings from the cleaner Part-2.**

First, **Qwen B−C Part-2 = OR 1.43, p = .0001 (favors B)** under full correction. The paper's §3.3 hurdle reading — "Qwen B causes more extraction failure (Part-1) but produces better reasoning conditional on extraction (Part-2)" — survives the scoring-pipeline correction. The Part-2 magnitude shrinks (paper OR 2.17 → corrected OR 1.43) but the direction and significance hold. **Hidden thinking does add value for Qwen reasoning quality; the E2E penalty is purely a truncation tax on top of that benefit.**

Second, **Gemma B−O Part-2 = OR 1.51, p = .006 (favors hidden thinking).** Combined with the E2E result (OR 1.41, p = .020 under full correction), this is a clean positive: **for Gemma, hidden thinking beats visible CoT**, both end-to-end and conditional on extraction, under fair scoring. The paper currently treats the Gemma B−O contrast as borderline ("§4 borderline OR 1.34, p_adj = .089" in §5 "Not" claims). Under full-correction scoring, it is significant in both reporting modes. We do not yet promote this to a primary positive claim in §4 — it remains within-model and modest in magnitude — but it is the only positive within-model live-thinking signal in the dataset that is robust to all our corrections, and it is worth reporting prominently.

Third, **Gemma B−C Part-2 = OR 1.06, p = .62.** The auditor estimate of "OR ≈ 1.08, p ≈ .49" cited in §3.10 was correct in direction and approximately correct in magnitude. The clean rerun confirms: when Gemma's extraction is clean, live thinking does not add value over trace replay on the population-averaged estimand. (The numeric-only subset still does, per §3.13.)
### 3.15 GPT-5.5 four-angle audit follow-up (added 2026-04-25, late)

A second 2026-04-25 audit ran four differently-prompted GPT-5.5 instances at xhigh reasoning, each given orthogonal stances (weakest-link hunter, alternative-hypothesis generator, mechanism analyst, statistical critic). Findings that warrant paper revision are listed below; full audit prompts and responses are archived at `outputs/audits/gpt55-audit-20260425/`.

**A. Claim 8 fragility under template-clustering (cross-auditor convergence on weakest-link and stat-critic).**

The Gemma B−O contrast that supports Claim 8 is significant only under question-level clustering (paper: log-OR +0.345, p = .020). Re-fitting with the same data under coarser clustering choices yields:

| Clustering unit | n_clust | log-OR | SE | p |
|---|---:|---:|---:|---:|
| question_id (paper choice) | 103 | +0.345 | 0.149 | **.020** |
| generator template | 26 | +0.358 | 0.240 | .135 |
| domain (math/spatial/logic/other) | 4 | +0.389 | 0.260 | .134 |
| drop math domain | 77 q | +0.193 | 0.166 | .245 |

**Claim 8's significance disappears under any cluster choice broader than question_id.** The 103 questions come from 26 generator templates (≈4 questions per template); template-clustering is more conservative and arguably more correct given the procedural-generation design. The signal is concentrated on the numeric/math subset (per §3.13: Gemma B−O numeric log-OR +0.811, p = .002; direction/Box/Cup individually null or borderline reversed).

A naive multiplicity correction over (E2E vs Part-2) × (paper scoring vs full-correction) × (subgroup vs aggregate) on the post-hoc B−O contrast also reduces Claim 8 to "exploratory-confirmatory" at best. **We downgrade Claim 8 from a Robust Claim to an exploratory finding; see §4 revisions and §3.13 for the per-family decomposition.**

**B. Qwen tracking C > B reverses under no-ceiling conditioning (alternative-hypothesis audit).**

The headline reading in §3.13 — "both models prefer trace replay to live thinking on tracking tasks" — is partially incorrect for Qwen. On the tracking subset (Box + Cup + direction = 37 questions):

- All-rows E2E B−C: log-OR −0.73, p < 1e-7 (favors C)
- Restricted to non-ceiling rows: log-OR −0.11, p = .42 (null)
- Conditional on extraction (Part-2): log-OR +0.47, OR 1.60, p = .0045 (**favors B**)

The Qwen "tracking C beats B" finding is largely a budget/truncation channel: Qwen B truncates much more on tracking (Cup 93%, Grid 80%, Box 66%, direction 55%; vs Counting 7%, Modular 4%) while C does not. When extraction succeeds, Qwen live thinking on tracking *does* produce better reasoning than trace replay — the opposite of the §3.13 reading. This sharpens the mechanism: Qwen B's tracking deficit is a termination/budget pathology, not evidence that hidden thinking is intrinsically worse than replay on tracking.

**C. C "fixes wrong B traces" is rare; mostly resumes useful unfinished ledger (mechanism audit).**

The C condition uses B's recorded trace as prefill. When the source B trace was incorrect, the standard reading is "C's model overrides the wrong reasoning." On 177 Qwen-C tracking rows where `source_trace_correct=false` but C was correct: 173/177 had blank `content` in the source B (the trace ran but never produced a visible answer; C just continues from a useful but unfinished state ledger). Only 4/177 are genuine "C re-derives a different answer than the source B finalized" cases. Implication: C's apparent ability to "repair wrong reasoning" is largely a continuation effect on un-finalized hidden traces, not a re-reasoning effect. Claim 3's "trace-replay beats live thinking" mechanism is more accurately "trace-replay finalizes B's stalled state-tracking work."

**D. Gemma C−F vanishes when source trace was wrong (alternative-hypothesis audit).**

Conditional on `source_trace_correct=False`, Gemma C−F E2E OR = 1.23, p = .57; Part-2 OR = 0.70, p = .35. Gemma's content claim (§4 Claim 1) is more accurately *"replaying correct traces beats shuffled tokens"* rather than *"coherent content beats shuffled tokens."* For Qwen the C−F effect survives even when the source trace was wrong (E2E OR = 10.15, p < 1e-16; Part-2 OR = 3.74, p = 2e-5), so Qwen's content claim is more general than Gemma's. We add this caveat to Claim 1 below.

**E. Scaffold answer leakage is end-of-scaffold; D is tail-extraction (mechanism audit).**

§3.8 quantified the leakage rate (87%); §3.15 quantifies its *position*. Of the 90/103 leaking scaffolds, the *last* gold-answer occurrence sits at median 98.7% through the stripped scaffold text — i.e., the answer is right at the end. D continuations follow: Qwen D on leaking scaffolds emits the answer within the first 40 generated chars on 850/900 rows (94%); 811/900 (90%) start the continuation directly with `FINAL:`. Gemma is similar (657/900 within 40 chars; 593/900 direct `FINAL:`). **D is mostly tail-answer extraction.** This sharpens Claim 2's existing caveat to "D measures the model's ability to *copy the last-mentioned answer from a prefilled context*, not its ability to use expert reasoning to solve the question."

**F. Gemma drops `Box N` but preserves `Cup X` (mechanism audit).**

§3.10's structured-label finding is more specific than originally stated: Gemma D Box rows are 86/100 bare ("FINAL: 1"); Gemma D Cup rows are 0/120 bare. Qwen is 0/220 bare across both. The format-drop is specifically a numeric-label compression behavior in Gemma, not a general structured-label failure. The §3.10 rescue magnitude does not change, but the *mechanism* is narrower than "Gemma drops Box/Cup prefixes."

**G. Verbosity-accuracy is non-monotone with a usable middle band (mechanism audit).**

Qwen B accuracy by `thinking_tokens` length quartile: 73.2% / 88.4% / 96.1% / 17.1% (top quartile collapses, 79% extraction failure). Best decile is 13.6–17.4k chars at 97.1%; worst is 49.1–70.2k at 5.8%. Gemma B shows the same shape without the truncation cliff: best decile 2.1–2.5k at 95.1%; worst decile 3.7–11.5k at 45.6%. **There is a per-model "useful middle band" of trace length; runaway traces are a difficulty/rumination marker, not random verbosity.** This refines §3.5's dose-response interpretation.

**H. Truncation is family-triggered by state-tracking ambiguity loops (mechanism audit).**

Qwen B's 8K ceiling-hit rate by question family: Cup 93%, Grid 80%, Box 66%, direction 55%, Counting 7%, Modular 4%, Multi-entity logic 0%. The state-tracking families dominate. Spot-check of ceiling-hit rows shows the trace is typically caught in a "do labels move or do positions move" ambiguity loop. This is a mechanistic refinement of the existing truncation discussion: it is not random verbosity at high temperature but a specific reasoning-pathology mode. Implication for Claim 7: truncation is not an inference-stack pathology to be engineered around; it is a model-failure mode under a specific class of reasoning task.

**I. Hard-subset prediction fails (alternative-hypothesis audit).**

The "benchmark-too-easy" alternative for the master replay-recoverability claim was tested by splitting on corrected A-condition accuracy. On A ≤ 0.5 questions: Gemma B 99/140 vs C 101/140 (OR 0.93, p = .73); Qwen B 69/140 vs C 81/140 (OR 0.71, p = .041 favoring C). Hardness-based interactions are non-significant for both models. **Harder problems do not reveal a larger live-thinking advantage**; if anything they tilt further toward replay for Qwen. This strengthens the master replay-recoverability claim: the null/negative B−C is not a ceiling-compression artifact.

**J. Statistical method-choice issues (statistical-critic audit).**

- The pre-registration's stated SESOI of "±3 pp at 50% baseline" is approximately wrong; the OR 0.85–1.18 SESOI is ±4.1 pp at 50%, ~2–4 pp at observed 70–85% baselines. Documentation fix only.
- Bias-reduced SE check via Mancl-DeRouen-style correction inflates SEs by 1–2% on Qwen B−C and Gemma numeric B−C. No claim changes.
- GEE exchangeable and naive cluster-robust GLM are numerically identical here (ρ small). The §2.6 marginal-vs-hierarchical methodological case is true in general but overstated for these specific estimates.
- The 16K-merged dataset identifies an "adaptive Qwen-B rescue policy at 8K with 16K rerun on ceiling-hit," not "Qwen-B at 16K." Claim 7 should be reframed accordingly.
- Multiplicity for the 2026-04-25 post-hoc additions (Claim 4 numeric subgroup, Claim 8 B−O) was not formally addressed. Both should be labeled exploratory-confirmatory pending a fresh pre-registered replication.

**K. Provenance off-by-one (cross-auditor finding).**

An earlier version of the paper and `RUN_MANIFEST.md` reported 367 Qwen-B reruns; the actual rerun JSONL contains 368, and the original 8K Qwen-B `eval_count ≥ 8190` count is also 368. The paper text was corrected in this revision; `RUN_MANIFEST.md` should be updated separately.


---

## 4. Robust claims

After the GEE analysis with question-level clustering, the hurdle decomposition, and the 16K truncation sensitivity, we regard the following as well-supported. Numbers are per-model GEE estimates; for Qwen we cite either the "merged" (16K sensitivity) dataset or the original 8K dataset explicitly, because of the asymmetric rerun (§2.7).

1. **Coherent reasoning content beats shuffled tokens in both models, whether measured end-to-end or conditional on successful extraction. For Gemma the effect is more accurately "replaying *correct* traces beats shuffled tokens" — caveat added 2026-04-25.** E2E: Gemma C−F OR=13.4, Qwen 17.7 (both p_adj<.001). Conditional on extraction (Part 2 of the hurdle model, controlling for the differential extraction-failure rate of the broken-control F): Gemma OR=8.84 (p<.001), Qwen OR=6.99 (p<.001). Shuffled tokens produce near-floor E2E accuracy (Gemma 23.5%, Qwen 11.1%). The Part-2 result is *one* statistic for the content claim — it conditions on extraction success which is a post-treatment outcome (collider risk; see §3.15-J and §7), so we report it as a robustness/descriptive estimand rather than the preferred causal estimand. The Part-2 effect is smaller than E2E but remains very large. **Source-trace correctness caveat for Gemma (§3.15-D).** When the source B trace was incorrect, Gemma C−F E2E OR = 1.23 (p = .57) and Part-2 OR = 0.70 (p = .35) — i.e., Gemma's content effect vanishes on this subset. For Qwen the effect survives even on incorrect-source-trace rows (E2E OR = 10.15, p < 1e-16). The Gemma claim is therefore narrower: replaying *correct* coherent reasoning content beats shuffled tokens, not "any coherent reasoning content."
2. **Expert scaffold utilization helps both models dramatically; the pre-registered Qwen-vs-Gemma asymmetry is essentially a scoring-pipeline artifact, and "use" is mostly tail-answer extraction (sharpened 2026-04-25).** The pre-registered analysis reported Qwen D−C OR = 17.5 vs Gemma D−C OR = 1.14 — a 14× asymmetry we initially read as a model-specific behavioral effect. Post-hoc correction (§3.8, §3.10) traces the asymmetry to: (a) Gemma emits `<end_of_turn>` on the same line as its `FINAL:` answer, corrupting the extracted string in 206/1030 Gemma D rows; (b) Gemma drops the `Box N` prefix on object-tracking rows (specifically Box, **not** Cup — see §3.15-F mechanism refinement: 86/100 Gemma D Box rows are bare, 0/120 Cup rows are bare); (c) Qwen C loses ~10.7 pp to 8K ceiling hits that D does not incur. Under full-correction scoring, **Gemma D−C = OR 24.87 (p<.001), Qwen D−C = OR 13.31 (p<.001)** — if anything the ordering reverses, and the confidence intervals overlap heavily. **D is mostly tail-answer extraction (§3.15-E).** 87% of stripped scaffolds retain the ground-truth answer in their reasoning text, and the *last* gold-answer occurrence sits at median 98.7% through the scaffold; on leaking scaffolds, 850/900 Qwen-D rows mention the answer within the first 40 generated chars and 811/900 begin the continuation directly with `FINAL:`. So D measures "can the model copy the last-mentioned answer from a prefilled context," not "can the model use expert reasoning to solve the question." A self-model scaffold ablation plus a hardened scoring pipeline is the clean test for any residual asymmetry; the current data do not support a model-specific architectural reading of D−C.
3. **Qwen's 8K B–C deficit is part-truncation, part-scoring-artifact; after full correction, trace-replay significantly beats live thinking on the population-averaged 16K-merged E2E estimand. The tracking-subset story is budget-mediated, not intrinsic (sharpened 2026-04-25).** Original 8K, paper scorer: B−C log-OR = −0.625, p<.001, strongly favoring C. 16K-merged, paper scorer: B−C log-OR = −0.009, 90% CI [−0.127, +0.108] inside SESOI, TOST equivalence established (TOST p = .016). 16K-merged, full correction (template-strip + structured-label canonicalization, §3.10): B−C log-OR = **−0.282**, OR = 0.75, 90% CI [−0.42, −0.15], p = .0006. **The Qwen tracking-subset effect is not intrinsic to live thinking on tracking (§3.15-B).** All-rows tracking B−C log-OR = −0.73, p < 1e-7 (favors C). After excluding ceiling-hit rows, log-OR = −0.11, p = .42 (null). Conditional on extraction (Part-2): log-OR = +0.47, OR = 1.60, p = .0045 — **favors B**. Qwen B truncates at 93% on Cup, 80% on Grid, 66% on Box, 55% on direction (§3.15-H), but at 7% on Counting and 4% on Modular; the tracking E2E deficit reflects this differential truncation, not a reasoning-quality difference. **Mechanism (§3.15-C):** of 177 Qwen-C tracking rows where the source B trace was incorrect but C succeeded, 173/177 had blank source `content` (B's hidden trace ran but never produced a visible answer; C just continues from a useful but unfinished state ledger). Only 4/177 are genuine "C re-derives a different answer" cases. **The net population-averaged claim ("Qwen trace-replay beats live thinking by ~6pp E2E on the 103 questions at 16K-merged budget") holds; the mechanistic reading is "C resumes B's stalled state-tracking work," not "C reasons better than B."** The residual 20% extraction failure for Qwen B at 16K is a persistent limitation.
4. **The Gemma live-thinking premium is real on numeric reasoning, absent on object/spatial tracking — the population-averaged claim does not hold but the per-domain claim does.** The pre-registered analysis reported Gemma B−C OR = 1.53, log-OR = +0.42, 90% CI [+0.22, +0.63], p_adj = .003 — above the SESOI upper bound, what we initially framed as the cleanest within-model evidence in the study for a benefit of live thinking over trace replay. Under full-correction scoring (§3.10: template-strip + structured-label canonicalization), the *aggregated* Gemma B−C log-OR = +0.158, OR = 1.17, 90% CI [−0.018, +0.333], p = .140 — no longer statistically significant. The proper Part-2 hurdle (§3.14) confirms: OR = 1.06, p = .62. **However, the question-family decomposition (§3.13) shows the aggregated null is a mixture.** On the 51 numeric-answer items, Gemma B−C log-OR = +0.446, OR = 1.56, p = .001 — a clear, significant live-thinking premium that is not driven by the Box/Cup scoring artifact. On the 22 tracking items (Box, Cup), Gemma B−C is null. The cond × is_boxcup interaction is formally significant (p = .031). The mechanism for the aggregated null is that the Gemma C baseline on Box/Cup items had 71/1030 silently mis-scored rows; re-scoring those rows correctly moves the Box/Cup B−C cells from positive (apparent premium) to null (no premium). On the 81 non-Box/Cup items the same correction has minimal effect, and the live-thinking premium remains. **The population-averaged retraction stands; the per-domain claim that Gemma live thinking helps on numeric reasoning (OR 1.56, p = .001, n = 51 questions) is the cleanest within-model evidence in the study for a real live-thinking benefit, and we report it as such.** A clean re-test would require a hardened scorer and ideally a fresh, family-stratified data collection.
5. **Coherent reasoning beats same-length filler — strongly for Gemma, modestly for Qwen.** Gemma: E2E C−J OR=9.45 (p<.001); Part-2 OR=10.2 (p<.001) — the effect survives extraction-conditioning because Gemma J has negligible extraction failure. Qwen: E2E C−J OR=4.18 (p<.001); Part-2 OR=1.78 (p=.009). Qwen J has a 40% extraction failure rate, so the E2E effect is partly a parser cliff; the reasoning-conditional effect is still present but much smaller. The *filler* control has its own protocol-fidelity caveat (token-count mismatch; §7), which we cannot fully resolve without rerunning J.
6. **Generic "reasoning-shape" provides residual value for Qwen but not for Gemma.** Qwen G−F Part-2 OR=2.25 (p<.001) — wrong-question reasoning beats shuffled tokens even among extracted outputs. Gemma G−F Part-2 OR=1.14 (p=.33) — null; for Gemma the E2E G−F effect is an extraction-channel effect.
7. **Qwen generation-budget truncation is a dominant mediator across all B-involving contrasts; the truncation is family-triggered by state-tracking ambiguity, and the 16K-merged dataset identifies an adaptive-policy estimand, not a fresh-budget effect (sharpened 2026-04-25).** In a GEE on `correct ~ ceiling_hit`, β=−1.28, p<.001. Under the pre-registered scorer, the 8K→16K partial rerun moved Qwen B from 54.2% to 68.6% accuracy and closed B−C from log-OR=−0.63 to −0.01 (TOST-equivalent). Under full-correction scoring the 16K-merged B−C does not fully close — it settles at log-OR=−0.282, p=.0006 (C > B by ~6 pp) — so truncation is *one* dominant mediator, not the *only* mediator. The remaining deficit is driven by scoring-pipeline artifacts that differentially affect Qwen C and by genuine residual truncation (20% of Qwen-B rows still hit the 16K ceiling). **Mechanism (§3.15-H):** Qwen B's ceiling-hit rate is highly family-specific — Cup 93%, Grid 80%, Box 66%, direction 55%, Counting 7%, Modular 4%, Multi-entity logic 0%. The truncation is not random verbosity at high temperature; it is triggered by state-tracking ambiguity loops where the model cycles through "do labels move or do positions move" without resolving. **Estimand (§3.15-J):** the 16K-merged dataset does **not** identify "Qwen B at 16K vs Qwen C at 16K." The clean estimand it identifies is *"accuracy under an adaptive Qwen-B rescue policy: run B at 8K under Ollama 0.20.2; if 8K hits the ceiling, rerun at 16K under Ollama 0.20.6 and use the rerun; otherwise keep the 8K output"* — compared against unre-rerun Qwen-C at 8K under Ollama 0.20.2. We present this as a mechanistic claim about the role of truncation in the 8K evaluation pipeline and as a deployment-relevant adaptive-policy contrast, not as a budget-normalized treatment effect on Qwen's reasoning capability in the large-budget limit.

8. **[EXPLORATORY-CONFIRMATORY] For Gemma on numeric reasoning, hidden thinking modestly beats visible CoT — but the population-averaged claim does not survive template-clustering.** Pre-registered Gemma B−O was OR = 1.34, p_adj = .089 — borderline. Under full-correction scoring with question-clustered GEE, Gemma B−O E2E OR = 1.41, p = .020; Part-2 OR = 1.51, p = .006. The 2026-04-25 GPT-5.5 audit (§3.15-A) re-fit the same contrast under coarser, arguably more correct cluster choices: template-clustering (n = 26 generators) p = .135; domain-clustering (n = 4) p = .134; dropping the math domain p = .245. The signal is concentrated on the numeric subset (per-family Gemma B−O numeric log-OR +0.81, p = .002, n = 51 questions; direction/Box/Cup individually null or modestly reversed). A naive multiplicity correction over (E2E vs Part-2) × (paper-scoring vs full-correction) × (subgroup vs aggregate) on this post-hoc contrast also weakens it. We retain the finding because it is the only within-model live-thinking signal that survives full-correction scoring on at least one cluster choice, but **classify it as exploratory-confirmatory rather than Robust pending pre-registered replication with template-clustering as the planned unit and the numeric-subgroup hypothesis as primary.** For Qwen, B−O still strongly favors visible CoT on the E2E scale (OR 0.36, p < .001) and is null in Part-2 (OR 0.91, p = .60); directions are model-specific and within-model only.

---

## 5. What we do **not** claim

- **Not:** "Visible CoT beats hidden thinking in general." The pooled B−O E2E effect is substantially a Qwen truncation artifact. On Gemma, the pre-registered GEE B−O contrast was borderline (OR=1.34, p_adj=.089). Under full-correction scoring, Gemma B−O is significant in the *opposite* direction — hidden thinking beats visible CoT (E2E OR = 1.41, p = .020; Part-2 OR = 1.51, p = .006; see §3.14 and Claim 8 in §4). For Qwen, B−O strongly favors visible CoT on the E2E scale (OR = 0.36, p < .001) but is null in the proper Part-2 hurdle under full correction (OR = 0.91, p = .60), so Qwen's "visible CoT beats hidden thinking" finding is a truncation-channel effect, not a reasoning-channel effect. The directions are model-specific and the magnitudes are within-model only.
- **Not:** "Thinking tokens are inherently useful / useless." Effects are budget-sensitive, and — as the 2026-04-15 audit discovered — also scoring-pipeline-sensitive. The direction of the B−C contrast for Qwen depends on (a) the generation budget (8K vs 16K) and (b) the scoring regime (pre-registered vs template-strip vs full-correction). The direction of the Gemma B−C contrast depends on the scoring regime. No single number is a clean summary; we report all four settings side-by-side in §3.4, §3.9, §3.10, and §4 Claim 3.
- **Not:** "Cross-model reasoning transfer is incompatible." The K-condition crossover is largely a trace-verbosity mismatch.
- **Not:** "Compression beats full traces." Condition M confounds compression with trace-author quality; a self-model compression ablation is required.
- **Not:** "Synergy between thinking and scaffolding is a general phenomenon." Gemma synergy is super-additive (+1.76, p<.001); Qwen is sub-additive and borderline (−0.83, p=.016). The average-across-models synergy is not a meaningful estimand.
- **Not:** "Self-consistency voting wins over hidden thinking in general." Qwen B−I favors I (OR=0.25, p<.001), partly via extraction failure; Gemma B−I is null. Budget-matching the comparison at the trial level is non-trivial.
- **Not:** "Hidden thinking engages a distinct computational mechanism *generally*." Under full-correction scoring, the population-averaged Qwen B−C favors trace-replay (OR 0.75, p = .0006) and the population-averaged Gemma B−C is null (OR 1.17, p = .140). However, narrower estimands do show positive live-thinking signal: Qwen B−C Part-2 = OR 1.43, p = .0001 (live thinking improves Qwen reasoning quality conditional on extraction success); Gemma numeric-subset B−C = OR 1.56, p = .001 (live thinking helps Gemma on numeric reasoning); Gemma B−O Part-2 = OR 1.51, p = .006 (live thinking beats visible-CoT for Gemma, fragile to clustering choice; see Claim 8). What we do **not** claim is a *broad E2E* live-thinking advantage across both models on the population-averaged estimand. The narrower positive estimands are real and consistent with a distinct computational pathway operating selectively, not with an across-the-board mechanism.

---

## 6. Pre-registration deviations

The pre-registered plan specified a Bayesian hierarchical logistic regression as the primary model. We substitute frequentist GEE with question-clustered robust SEs. The methodological justification is detailed in §2.6: the marginal estimand from GEE matches our population-level framing (vs conditional estimates from a random-effects model, which differ from marginals under a logit link), GEE with robust SEs is consistent under mis-specified working correlation, and at 22,660 observations in 103 clusters frequentist and Bayesian fixed-effect estimates agree numerically under diffuse priors. Earlier drafts also cited "dependencies and runtime" — audit feedback correctly noted these are not methodological justifications, and we have removed them.

Condition N was pre-registered as "empty-trace think mode" but implemented as "deterministic think at T=0" because Ollama's thinking API does not support forced empty traces. The implementation tests a related but distinct question — whether stochastic sampling in the think phase matters.

Condition I uses lexicographic tie-breaking only (not logprob-then-lexicographic) because Ollama does not reliably expose per-token logprobs for chat completions.

Condition E was redesigned from `raw + prefill + think` to `chat + context + think` after discovering that Ollama's raw mode does not produce thinking tokens even with `think=true` (verified: 0/160 records generated thinking under raw+think).

The 16K rerun (§3.4) is a **post-hoc sensitivity analysis**, not pre-registered. The selection criterion (ceiling-hit at 8K) is **post-treatment** — it is defined on an outcome of the original Phase 2 run rather than on a pre-existing covariate. Because the rerun targets only previously-truncated cases, we report it as sensitivity, not replication, and we provide both 8K-original and 16K-merged primary analyses in the supplement.

The extraction-pipeline and scoring-artifact sensitivities (§3.8, §3.9, §3.10, §3.11, §3.12) are also **post-hoc** and were added in the 2026-04-15 revision after an audit of the Gemma D−C null (§3.8) uncovered progressively broader scoring-pipeline issues (§3.9 template-token leakage in Qwen C/G; §3.10 cross-condition structured-label drift; §3.11 H-scaffold validity; §3.12 Phase 3 L-slope magnitude). Two independent `gpt-5.3-codex` and `gpt-5.4` auditors converged on the structured-label finding. We do not regenerate Table 1 or Table 2; the pre-registered exact-string scoring is preserved and the alternative scoring regimes are reported alongside it. Claims 2, 3, and 4 in §4 were revised to reflect the audit findings.

The 2026-04-25 follow-up adds §3.13 (question-family heterogeneity decomposition) and §3.14 (proper Part-2 hurdle GEE under full correction, Condition I re-aggregation, B−I rerun). These were also **post-hoc**: the question-family partition was suggested by the §3.10 finding that 22/52 exact-answer items were structured labels, not pre-registered. The cond × is_boxcup interaction is significant on this single pre-specified partition (not a fishing expedition across many partitions); we report directly without multiplicity correction beyond the per-family Holm-style rationale in §3.13. Claim 4 was further revised from a full retraction to a per-domain claim, and Claim 8 was added documenting Gemma B−O.

**§3.15 (added 2026-04-25 evening) is a four-angle GPT-5.5 xhigh-reasoning audit** that stress-tested the surviving claims under different stances (weakest-link hunter, alternative-hypothesis generator, mechanism analyst, statistical critic). It is also **post-hoc** and was framed deliberately as a fragility-stress, not a confirmation. Two angles converged on the Claim 8 multiplicity / clustering fragility, which we accept and act on (Claim 8 downgraded from Robust to exploratory-confirmatory). The mechanism angle independently surfaced (a) the source-trace correctness caveat on Gemma C−F, (b) the tail-extraction sharpening on D, (c) the budget-mediated tracking story on Qwen B−C, (d) the family-triggered nature of Qwen B truncation, (e) the verbosity sweet-spot pattern, and (f) the Box-vs-Cup specificity of Gemma's format-drop. We treat the §3.15 findings as *deepenings or weakenings* of existing claims rather than new positive claims, and have updated the Claim text accordingly. The provenance off-by-one (367 → 368 reruns) was a documentation error caught by two audit angles.

---

## 7. Limitations

We organize limitations by severity. The first three are the limitations we regard as most likely to change specific claims if remedied.

### Central methodological limitation

- **Asymmetric 16K rerun (our biggest caveat).** The 16K sensitivity rerun covered only Qwen-B ceiling-hit cases, not Qwen-C, not other Qwen conditions with 8K ceilings (C, F, G, J have non-trivial ceiling rates, see Table 1), and not the non-truncated Qwen-B cases. The merged Qwen-B dataset is therefore a partial budget upgrade of one arm. Claim 3 (§4) explicitly reflects this: we claim that *truncation explains much of the 8K B–C reversal*, not that B and C are equivalent at a shared-and-uncapped budget. Cost of fixing: ≈15 additional hours of compute for a Qwen-C 16K rerun, plus equal time for F/G/J if reviewers demand symmetry. This is the single most consequential unresolved threat to the Qwen mechanism claims.
- **Cross-version drift within the merged Qwen-B condition.** The 662 non-ceiling Qwen-B records in the merged dataset were collected under Ollama 0.20.2; the 368 rerun records were collected under Ollama 0.20.6. Model digests were not logged at collection time. `RUN_MANIFEST.md` documents this. Reviewers should read Claim 3 as "truncation explains much of the 8K reversal *under a plausible assumption of inference-stack stability across Ollama 0.20.2 → 0.20.6*". We cannot rule out that a fraction of the observed improvement is a 0.20.x build difference; we regard it as unlikely to explain 14 percentage points of accuracy gain, but have not tested it.
- **Fixed generation budget.** Even at 16K, 20% of Qwen-B inferences still truncate. All E2E claims for Qwen inherit a budget ceiling. A clean mechanism analysis would require a much larger budget or a truncation-aware estimand.

### Protocol-fidelity issues carried from prior infrastructure audits

Earlier audits flagged three control-manipulation fidelity issues that remain unresolved in the collected data:

- **Trace bank token counts drift from BPE by ~1.79×.** The "token-matched" G and J conditions used a legacy word-based count; fresh BPE counts are on average ~1.79× larger. This softens the "semantic content vs length" interpretation of C−J and the "shape vs noise" interpretation of G−F: the J-filler and G-donor traces may be systematically longer than intended.
- **Condition I `k` computed against a hardcoded `mean_a_tokens=50` rather than the empirical mean.** This gave Qwen `k≈20` rather than a data-based ~4–12, meaning the B−I "compute allocation" contrast actually compares hidden thinking against a substantially larger self-consistency budget than planned. The Qwen B−I estimate should be read as an upper bound on how much more voting helps, not as a matched-compute test.
- **Condition F shuffle may produce byte sequences that fragment-decode at BPE boundaries.** The shuffle operates on cl100k_base tokens, which do not align perfectly to either model's native tokenizer. The extraction-failure signature of F (34% Gemma, 57% Qwen) is partly mechanical. The Part-2 hurdle analysis (Table 3) controls for this; we report it as the primary statistic for the content claim (§4.1) rather than the E2E OR.
- **Condition H is not a valid wrong-scaffold manipulation (added 2026-04-15, §3.11).** Of 103 `wrong_scaffold` assets: 17 are GPT-5.4 refusal templates, 65 still contain the gold-answer string elsewhere in the text, and 24 still end with the exact gold `FINAL:` line after `_strip_final_answer()`. H-cell accuracy is a mixture of refusal-wrapped hints, leaked-answer scenarios, and genuinely-wrong-reasoning scenarios. No Robust Claim in §4 depends on H, but any reading of Table 1's H row as a "suggestibility" measure is unsafe.

These issues bound the size of the C−F, G−F, C−J, and B−I effects but do not reverse their direction. The Part-2 hurdle controls for extraction-failure differentials.

### Other limitations

- **Two models only.** Results may not generalize to larger thinking-equipped models or to other small models with different thinking implementations. The Gemma vs Qwen asymmetry (PLE vs dense, 4.5B vs 9.7B effective, different chat templates, different inference-stack behavior under `think=true`) is an architectural-plus-stack confound on any cross-model claim. Note the revised framing after §3.10: what previously looked like a Gemma-vs-Qwen scaffold-use asymmetry (Claim 2) is now largely a scoring-pipeline artifact rather than a model-behavior asymmetry — which strengthens rather than weakens the "two models are not enough to generalize" caveat, because the apparent model-specific effect dissolved under fair scoring.
- **Temperature 0.7 is high for reasoning evaluations** (T=0 or greedy is standard in most chain-of-thought benchmarks). The Qwen extraction-failure rate — and the 20% residual truncation at 16K — are plausibly inflated by high-T sampling runaway. We did not run a temperature sweep, and we cannot separate "Qwen intrinsically verbose at T=0.7" from "Qwen would not truncate at T=0". This is an unresolved confound on the entire Qwen truncation narrative.
- **Calibration drift (severity: important).** The 103 items were locked at the 30–70% A-accuracy band during calibration (12 reps), but on the Phase 2 run (10 reps, different seeds) the observed A-accuracy is 82.8% Gemma / 82.6% Qwen. This is not minor drift — it means our supposedly mid-difficulty test set is in fact close to the A-condition ceiling for both models, compressing the dynamic range available to detect B−A thinking benefits. The within-model B−C, C−F, D−C contrasts are not directly threatened (they involve non-A conditions), but any claim referenced to A is harder to interpret. A replication should re-calibrate on the intended evaluation reps.
- **103 questions, 4 domains.** Template-generated items control some confounds but limit external validity to naturalistic reasoning. Per-domain heterogeneity is not reported here; a domain × condition interaction analysis would strengthen external-validity claims.
- **Single quantization (Q4_K_M) and single inference stack (Ollama).** Reviewers have flagged that `think` API implementation may differ from native `transformers` inference. Unknown.
- **Scoring-pipeline limitations (substantially expanded in the 2026-04-15 revision).** We score via regex on `FINAL:`; the scorer has no alias support for structured-label answers (`Box N`, `Cup X`) and does not strip chat-template tokens (`<end_of_turn>`, `<|endoftext|>`, `<|im_start|>user`) before string-match. Post-hoc audits (§3.8, §3.9, §3.10) with full convergence across two independent auditors found these bugs in many cells, not just the one that triggered the audit: the structured-label drift rescues ≥27 rows per cell on Gemma A/B/C/D/I/J/O and the chat-template leakage rescues 80+ rows on Qwen C/G and 200+ on Gemma D. Under full-correction scoring (§3.10): Claim 3 strengthens (Qwen B−C: log-OR −0.282, p = .0006, vs paper's TOST-equivalent), Claim 4 fails (Gemma B−C: OR 1.17, p = .14, vs paper's OR 1.53, p = .003), and the Claim 2 D−C asymmetry essentially vanishes. Claims 1, 5, 6, 7 remain robust. We report these as sensitivities rather than regenerating Table 1/Table 2 — both because the pre-registered analysis is what we committed to and because a clean re-run would require a hardened scorer plus a manual adjudication layer, which we recommend for any replication (§5 of the audit reports in `outputs/audits/paper-audit-20260415/`).
- **Phase 3 historical controls.** Phase 3 K/L/M/N reference Phase 2 A/B/C/D on a 39-item subset, but Phase 2 was run under Ollama 0.20.2 and Phase 3 under 0.20.6. Model digests are blank in both logs. Cross-phase identification relies on software-build stability we cannot fully verify.
- **Author of compressed / scaffold text (M/D/E/H).** GPT-5.4-authored text confounds "reasoning structure" with stronger-model style/knowledge. D's Qwen-specific boost may reflect GPT-5.4's own reasoning ability bleeding through the scaffold.
- **Compute is not matched across conditions.** Hidden thinking, trace replay, visible CoT, and self-consistency differ in both placement and total token count.
- **Statistical limitations.** 103 clusters is modest for large-sample GEE inference; small-cluster corrections (e.g., Mancl-DeRouen, Kauermann-Carroll) are not applied. Hurdle Part-1 models exhibit separation in Gemma cells (0% extraction failure in D/I/O), producing unstable numeric ORs on those contrasts — Part-1 effects on those cells should be read as "vastly higher failure in B" rather than as point estimates.
- **Tri-agent audit loop as part of development.** The results passed through seven rounds of independent-model audits (phase-2 analysis, phase-3 analysis, full review, final paper audit, a 2026-04-15 scoring-pipeline audit that produced §3.8–§3.12, a 2026-04-25 morning Sonnet-class follow-up that produced §3.13–§3.14, and a 2026-04-25 evening four-angle GPT-5.5 xhigh-reasoning audit that produced §3.15 and downgraded Claim 8). This was a development tool, not a validation method. The volume and consequentiality of post-hoc revisions across these audit rounds is itself a methodological observation: the pre-registered analysis as originally written would have supported substantially stronger conclusions than the post-audit analysis supports, and the auditors typically converged on similar findings only after several rounds of progressively narrower prompts. We report all audit findings and our responses in the supplement.

---

## 8. Conclusion

For the two small models we tested, the following holds on the data as collected:

- Coherent reasoning content beats shuffled or filler text by a very large margin in both models (C−F OR ≈ 7–9 even after conditioning on successful extraction). Most of the measurable trace-replay benefit is carried by content, not length.
- For Qwen, the B−C picture depends on which post-hoc correction is applied. Under the pre-registered exact-string scorer on the 16K-merged dataset, B and C are TOST-equivalent (log-OR −0.009, 90% CI within SESOI). Under full-correction scoring (template-strip + structured-label canonicalization, §3.10), B−C = log-OR −0.282, OR 0.75, p = .0006 — trace-replay clearly and modestly beats live thinking on the population-averaged E2E estimand. **The tracking-subset reading of this is budget-mediated, not intrinsic (§3.15-B):** restricting tracking-only rows to non-ceiling cases moves Qwen B−C to a null (log-OR −0.11, p = .42), and Part-2 conditional-on-extraction tracking B−C *favors B* (OR 1.60, p = .005). The mechanism (§3.15-C) is that C's tracking advantage is mostly "C resumes B's stalled state-tracking work" — only 4/177 cases are genuine "C re-derives a different answer than B finalized." We treat the full-correction E2E number as our current best population-averaged estimate; the mechanism is narrower than "live thinking is intrinsically worse than replay on tracking."
- **The Gemma live-thinking premium is real on numeric reasoning, absent on tracking — the population-averaged claim does not hold but a per-domain claim does.** Pre-registered Gemma B−C OR = 1.53, p_adj = .003. Full-correction aggregated B−C OR = 1.17, p = .140. Per-family decomposition (§3.13): on the 51 numeric items Gemma B−C OR = 1.56, p = .001 (real and significant); on the 22 tracking items the effect is null/reversed. cond × is_boxcup interaction p = .031. For Qwen, numeric B−C is null (p = .73); tracking B−C E2E strongly favors C, but **the tracking effect is mediated by Qwen B's family-specific truncation** (Cup 93%, Grid 80%, Box 66%, direction 55% ceiling rates; §3.15-H). Conditional on extraction Qwen tracking B>C (Part-2 OR 1.60, p = .005). **Across both models, the per-family pattern is "live thinking helps numeric reasoning for Gemma, doesn't change Qwen numeric, and the tracking E2E gap reflects truncation rather than reasoning."** Gemma B−O (hidden vs visible CoT) is significantly positive under question-clustered GEE (E2E p = .020; Part-2 p = .006) but not under template-clustering (p = .135) — we report it as exploratory-confirmatory pending replication.
- **Expert external reasoning as context helps both models dramatically — the pre-registered asymmetry is a scoring artifact, and "use" is mostly tail-answer extraction.** The pre-registered analysis reported Qwen D−C OR = 17.5 vs Gemma D−C OR = 1.14 — a 14× asymmetry. Under full-correction scoring **Gemma D−C = OR 24.87 (p<.001), Qwen D−C = OR 13.31 (p<.001)** — the asymmetry essentially vanishes. **The mechanism is mostly tail-extraction (§3.15-E):** of the 90/103 scaffolds that retain the gold answer in their reasoning text, the *last* gold occurrence sits at median 98.7% through the stripped scaffold; on leaking scaffolds, ~94% of Qwen-D rows mention the answer within the first 40 generated chars and ~90% start the continuation directly with `FINAL:`. So condition D measures "can the model copy the last-mentioned answer from a prefilled context," not "can the model use expert reasoning to solve the question."

The broader methodological lesson is that fixed-budget end-to-end metrics can mis-attribute formatting failure to reasoning failure. Any paper claiming a general "thinking tokens are useful / useless" effect in the small-model regime should report a two-part hurdle decomposition and a generation-budget sensitivity as standard. The pre-audit version of this very study claimed "thinking hurts Qwen" based on the 8K-cap data; the post-audit analysis eliminated that headline and replaced it with a narrower, budget-conditional claim.

---

## Data and code availability

All source code (runner, condition builder, scoring, analysis), per-inference JSONL logs, tri-agent audit reports, the paper draft history, and this manuscript are available at `github.com/JfowlerSIAI/Workflows` under `workflows/thinking-token-experiment/`. Pre-registration on OSF (link in supplement). Raw inference logs: Phase 2 original 22,660 records + I-subsample 16,890 records; Phase 3 4,368 records; 16K rerun 368 records (merged in place of ceiling-hit originals). A frozen run manifest with model digests, Ollama versions, and full provenance for every data collection run is in `RUN_MANIFEST.md` at the project root. Analysis artifacts that were superseded during post-audit revisions retain a `SUPERSEDED.md` note and a banner header pointing to the current version.

---

## Acknowledgments

Tri-agent audit loop implemented as identical-prompt parallel runs of GPT-5.3-codex, GPT-5.4, and Gemini 3.1-pro-preview. Earlier audit rounds produced full convergence on every critical-rated finding that shaped the first post-audit manuscript. The 2026-04-15 scoring-pipeline audit round (§3.8–§3.12) was a two-agent identical-prompt run (`gpt-5.3-codex` + `gpt-5.4`; Gemini 429-rate-limited) with full convergence on the structured-label finding that reclassified Claim 4. Archived at `outputs/audits/paper-audit-20260415/`. The 2026-04-25 morning follow-up (§3.13–§3.14, Claim 8) was a single Sonnet-class analytical pass that closed open items deferred at 2026-04-15: question-family heterogeneity decomposition, proper Part-2 hurdle GEE, Condition I re-aggregation, surfacing the Gemma B−O signal. **The 2026-04-25 evening follow-up (§3.15) was a four-angle GPT-5.5 xhigh-reasoning audit** run as four identical-shared-context-but-differently-prompted parallel instances (weakest-link hunter, alternative-hypothesis generator, mechanism analyst, statistical critic). Cross-angle convergence on Claim 8 fragility under template-clustering and on Claim 3's tracking-budget mediation drove the corresponding Claim revisions. Archived at `outputs/audits/gpt55-audit-20260425/`. Earlier paper audits identified Table 1 transcription errors, §3.5 collider-bias risk (removed), §6 pre-registration-deviation language issues, and §4 Claim 6 overstatement in the Gemma G−F case; those fixes are incorporated in this revision. **A 367 → 368 provenance off-by-one** in the rerun-row count was caught by two of the §3.15 audit angles and fixed throughout this revision; `RUN_MANIFEST.md` should be updated separately.
