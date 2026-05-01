# Phase 3 Mechanism Analysis — Tri-Agent Audit

You are auditing the Phase 3 mechanism deep-dive analysis of a thinking-token experiment. Phase 3 tests conditions K (cross-model transfer), L25/L50/L75/L100 (dose-response), M (compressed trace), and N (deterministic thinking) on 39 items × 8 reps × 2 models (Gemma 4 E4B and Qwen 3.5 9B). Phase 2 reference conditions (A, B, C, D) are filtered to the same 39-item subset for comparison.

## Full Report

```
==============================================================================
  PHASE 3 MECHANISM DEEP-DIVE ANALYSIS
==============================================================================
  Mechanism log: outputs/mechanism/20260412_215554/inference_log.jsonl
  Phase 2 log:   outputs/confirmatory/20260408_100418/inference_log.jsonl
  Phase 3 records: 4368
  Phase 2 subset records (same 39 questions): 3120
  Phase 3 conditions: K, L100, L25, L50, L75, M, N
  Phase 2 references: A, B, C, D
  Models: gemma4, qwen3.5:9b

  NOTE: Phase 3 is explicitly exploratory. All contrasts are
  descriptive. Phase 2 reference conditions are filtered to the
  same 39-item subset for valid comparison. Marginal ORs inherit
  the same clustering caveat as Phase 2.

==============================================================================
  1. PER-CONDITION ACCURACY (ITT + PP)
==============================================================================

  Cond   Src      N     ITT      PP   ExtF   Ceil    Eval
  -------------------------------------------------------
  A      P2     780   63.2%   66.6%     5%     0%     401
  B      P2     780   45.8%   67.0%    32%    31%    3655
  C      P2     780   55.9%   57.9%     3%    23%    2625
  D      P2     780   85.3%   85.4%     0%     0%      48
  K      P3     624   59.1%   64.0%     8%     8%     978
  L25    P3     624   56.9%   57.2%     0%    19%    2938
  L50    P3     624   51.9%   52.3%     1%    23%    3027
  L75    P3     624   52.1%   53.7%     3%    23%    2794
  L100   P3     624   56.6%   58.4%     3%    23%    2583
  M      P3     624   81.1%   81.6%     1%     0%      47
  N      P3     624   46.6%   68.6%    32%    29%    3764

  --- gemma4 ---
  Cond   Src      N     ITT      PP   ExtF   Ceil    Eval
  -------------------------------------------------------
  A      P2     390   59.7%   62.0%     4%     0%     466
  B      P2     390   68.5%   69.5%     2%     0%     940
  C      P2     390   61.5%   62.5%     2%     0%      17
  D      P2     390   72.3%   72.3%     0%     0%      34
  K      P3     312   50.3%   58.6%    14%     0%     221
  L25    P3     312   50.0%   50.0%     0%     0%     503
  L50    P3     312   48.7%   48.7%     0%     0%     417
  L75    P3     312   52.9%   53.1%     0%     0%     289
  L100   P3     312   61.2%   62.4%     2%     0%      23
  M      P3     312   73.4%   74.1%     1%     0%      87
  N      P3     312   70.2%   70.2%     0%     0%     955

  --- qwen3.5 ---
  Cond   Src      N     ITT      PP   ExtF   Ceil    Eval
  -------------------------------------------------------
  A      P2     390   66.7%   71.4%     7%     0%     337
  B      P2     390   23.1%   60.4%    62%    62%    6370
  C      P2     390   50.3%   53.1%     5%    46%    5233
  D      P2     390   98.2%   98.5%     0%     0%      63
  K      P3     312   67.9%   68.6%     1%    16%    1735
  L25    P3     312   63.8%   64.4%     1%    39%    5372
  L50    P3     312   55.1%   56.0%     2%    46%    5636
  L75    P3     312   51.3%   54.4%     6%    46%    5300
  L100   P3     312   51.9%   54.4%     4%    46%    5143
  M      P3     312   88.8%   89.1%     0%     0%       6
  N      P3     312   23.1%   64.3%    64%    59%    6572

==============================================================================
  2. TWO-PART DECOMPOSITION: P(extract) and P(correct|extracted)
==============================================================================

  Cond/Model                 Src   P(ext)   P(c|e)   Ceil%      N
  ------------------------------------------------------------
  A/qwen3.5                  P2     93.3%    71.4%    0.0%    390
  B/qwen3.5                  P2     38.2%    60.4%   62.1%    390
  C/qwen3.5                  P2     94.6%    53.1%   46.4%    390
  K/gemma4                   P3     85.9%    58.6%    0.0%    312
  K/qwen3.5                  P3     99.0%    68.6%   16.3%    312
  L100/qwen3.5               P3     95.5%    54.4%   45.8%    312
  L25/qwen3.5                P3     99.0%    64.4%   38.8%    312
  L50/qwen3.5                P3     98.4%    56.0%   45.8%    312
  L75/qwen3.5                P3     94.2%    54.4%   45.5%    312
  N/qwen3.5                  P3     35.9%    64.3%   59.0%    312

==============================================================================
  3. MECHANISM CONTRASTS (per-model PRIMARY)
==============================================================================

  === gemma4 ===

  K-C: Cross-model transfer vs self-trace replay
    ITT: 50.3% vs 61.5%  delta=-11.2%  OR=0.634 [0.469,0.856]  p=0.0030**  p_adj=0.0149*
    PP:  58.6% vs 62.5%  delta=-3.9%  OR=0.849 [0.617,1.167]  p=0.3127ns
    ExtFail: K=14%  C=2%

  M-L100: Compressed trace vs full trace
    ITT: 73.4% vs 61.2%  delta=+12.2%  OR=1.744 [1.243,2.446]  p=0.0013**  p_adj=0.0076**
    PP:  74.1% vs 62.4%  delta=+11.7%  OR=1.719 [1.220,2.424]  p=0.0020**
    ExtFail: M=1%  L100=2%

  M-C: Compressed trace vs self-trace replay
    ITT: 73.4% vs 61.5%  delta=+11.9%  OR=1.720 [1.245,2.375]  p=0.0010***  p_adj=0.0070**
    PP:  74.1% vs 62.5%  delta=+11.6%  OR=1.713 [1.235,2.376]  p=0.0013**
    ExtFail: M=1%  C=2%

  M-D: Compressed trace vs expert scaffold
    ITT: 73.4% vs 72.3%  delta=+1.1%  OR=1.056 [0.756,1.475]  p=0.7510ns  p_adj=1.0000ns
    PP:  74.1% vs 72.3%  delta=+1.8%  OR=1.095 [0.782,1.534]  p=0.5976ns

  N-B: Deterministic think vs stochastic think
    ITT: 70.2% vs 68.5%  delta=+1.7%  OR=1.084 [0.785,1.496]  p=0.6247ns  p_adj=1.0000ns
    PP:  70.2% vs 69.5%  delta=+0.7%  OR=1.031 [0.745,1.427]  p=0.8531ns
    ExtFail: N=0%  B=2%

  L100-C: Full dose trace vs Phase 2 self-trace
    ITT: 61.2% vs 61.5%  delta=-0.3%  OR=0.986 [0.727,1.338]  p=0.9295ns  p_adj=1.0000ns
    PP:  62.4% vs 62.5%  delta=-0.1%  OR=0.996 [0.731,1.358]  p=0.9807ns
    ExtFail: L100=2%  C=2%

  L25-A: Quarter trace vs baseline (any signal?)
    ITT: 50.0% vs 59.7%  delta=-9.7%  OR=0.675 [0.500,0.910]  p=0.0101*  p_adj=0.0403*
    PP:  50.0% vs 62.0%  delta=-12.0%  OR=0.615 [0.454,0.833]  p=0.0017**
    ExtFail: L25=0%  A=4%

  === qwen3.5 ===

  K-C [TRUNC]: Cross-model transfer vs self-trace replay
    ITT: 67.9% vs 50.3%  delta=+17.7%  OR=2.093 [1.536,2.851]  p=0.0000***  p_adj=0.0000***
    PP:  68.6% vs 53.1%  delta=+15.5%  OR=1.924 [1.405,2.637]  p=0.0000***
    ExtFail: K=1%  C=5%

  M-L100 [TRUNC]: Compressed trace vs full trace
    ITT: 88.8% vs 51.9%  delta=+36.9%  OR=7.240 [4.786,10.950]  p=0.0000***  p_adj=0.0000***
    PP:  89.1% vs 54.4%  delta=+34.7%  OR=6.757 [4.436,10.290]  p=0.0000***
    ExtFail: M=0%  L100=4%

  M-C [TRUNC]: Compressed trace vs self-trace replay
    ITT: 88.8% vs 50.3%  delta=+38.5%  OR=7.737 [5.178,11.562]  p=0.0000***  p_adj=0.0000***
    PP:  89.1% vs 53.1%  delta=+36.0%  OR=7.102 [4.720,10.685]  p=0.0000***
    ExtFail: M=0%  C=5%

  M-D [TRUNC]: Compressed trace vs expert scaffold
    ITT: 88.8% vs 98.2%  delta=-9.4%  OR=0.153 [0.069,0.341]  p=0.0000***  p_adj=0.0000***
    PP:  89.1% vs 98.5%  delta=-9.4%  OR=0.136 [0.058,0.320]  p=0.0000***

  N-B [TRUNC]: Deterministic think vs stochastic think
    ITT: 23.1% vs 23.1%  delta=+0.0%  OR=1.001 [0.704,1.424]  p=0.9957ns  p_adj=1.0000ns
    PP:  64.3% vs 60.4%  delta=+3.9%  OR=1.177 [0.710,1.950]  p=0.5271ns
    ExtFail: N=64%  B=62%

  L100-C [TRUNC]: Full dose trace vs Phase 2 self-trace
    ITT: 51.9% vs 50.3%  delta=+1.7%  OR=1.069 [0.794,1.439]  p=0.6613ns  p_adj=1.0000ns
    PP:  54.4% vs 53.1%  delta=+1.2%  OR=1.051 [0.774,1.427]  p=0.7492ns
    ExtFail: L100=4%  C=5%

  L25-A [TRUNC]: Quarter trace vs baseline (any signal?)
    ITT: 63.8% vs 66.7%  delta=-2.9%  OR=0.881 [0.645,1.203]  p=0.4240ns  p_adj=1.0000ns
    PP:  64.4% vs 71.4%  delta=-7.0%  OR=0.724 [0.523,1.002]  p=0.0516ns
    ExtFail: L25=1%  A=7%

==============================================================================
  4. POOLED CONTRASTS (SECONDARY — exploratory)
==============================================================================

  K-C: Cross-model transfer vs self-trace replay
    ITT: 59.1% vs 55.9%  delta=+3.2%  OR=1.141 [0.922,1.412]  p=0.2238ns  p_adj=0.6713ns
    PP:  64.0% vs 57.9%  delta=+6.0%  OR=1.289 [1.031,1.611]  p=0.0256*
    >> DIRECTION REVERSAL: gemma4=-11.2%, qwen3.5=+17.7%

  M-L100: Compressed trace vs full trace
    ITT: 81.1% vs 56.6%  delta=+24.5%  OR=3.283 [2.544,4.236]  p=0.0000***  p_adj=0.0000***
    PP:  81.6% vs 58.4%  delta=+23.2%  OR=3.147 [2.428,4.079]  p=0.0000***

  M-C: Compressed trace vs self-trace replay
    ITT: 81.1% vs 55.9%  delta=+25.2%  OR=3.373 [2.641,4.309]  p=0.0000***  p_adj=0.0000***
    PP:  81.6% vs 57.9%  delta=+23.7%  OR=3.218 [2.508,4.128]  p=0.0000***

  M-D: Compressed trace vs expert scaffold
    ITT: 81.1% vs 85.3%  delta=-4.2%  OR=0.742 [0.560,0.983]  p=0.0373*  p_adj=0.1493ns
    PP:  81.6% vs 85.4%  delta=-3.8%  OR=0.761 [0.573,1.011]  p=0.0592ns
    >> DIRECTION REVERSAL: gemma4=+1.1%, qwen3.5=-9.4%

  N-B: Deterministic think vs stochastic think
    ITT: 46.6% vs 45.8%  delta=+0.9%  OR=1.035 [0.838,1.279]  p=0.7464ns  p_adj=1.0000ns
    PP:  68.6% vs 67.0%  delta=+1.7%  OR=1.078 [0.821,1.416]  p=0.5895ns
    >> DIRECTION REVERSAL: gemma4=+1.7%, qwen3.5=+0.0%

  L100-C: Full dose trace vs Phase 2 self-trace
    ITT: 56.6% vs 55.9%  delta=+0.7%  OR=1.028 [0.831,1.270]  p=0.8013ns  p_adj=1.0000ns
    PP:  58.4% vs 57.9%  delta=+0.5%  OR=1.022 [0.823,1.270]  p=0.8415ns
    >> DIRECTION REVERSAL: gemma4=-0.3%, qwen3.5=+1.7%

  L25-A: Quarter trace vs baseline (any signal?)
    ITT: 56.9% vs 63.2%  delta=-6.3%  OR=0.768 [0.620,0.953]  p=0.0163*  p_adj=0.0817ns
    PP:  57.2% vs 66.6%  delta=-9.5%  OR=0.669 [0.537,0.834]  p=0.0003***

==============================================================================
  5. DOSE-RESPONSE ANALYSIS (L25 → L100)
==============================================================================

  === gemma4 ===
  Dose   Frac      ITT      PP   ExtF   Ceil
  ----------------------------------------
  L25      25%   50.0%   50.0%     0%      0
  L50      50%   48.7%   48.7%     0%      0
  L75      75%   52.9%   53.1%     0%      0
  L100    100%   61.2%   62.4%     2%      0

  Monotonicity (Kendall's tau):
    ITT: tau=+0.667  p=0.3333 ns
    PP:  tau=+0.667  p=0.3333 ns
  Logistic trend (dose -> P(correct)):
    beta=+0.612  se=0.738  p=0.4070 ns  (increasing)

  === qwen3.5 ===
  Dose   Frac      ITT      PP   ExtF   Ceil
  ----------------------------------------
  L25      25%   63.8%   64.4%     1%    121
  L50      50%   55.1%   56.0%     2%    143
  L50      50%   55.1%   56.0%     2%    143
  L75      75%   51.3%   54.4%     6%    142
  L100    100%   51.9%   54.4%     4%    143

  Monotonicity (Kendall's tau):
    ITT: tau=-0.667  p=0.3333 ns
    PP:  tau=-1.000  p=0.0833 ns
  Logistic trend (dose -> P(correct)):
    beta=-0.644  se=0.723  p=0.3732 ns  (decreasing)

  --- gemma4: Per-question dose-response pattern ---
    Monotone increasing: 13
    Monotone decreasing: 3
    Non-monotone:        19
    Flat (<15pp range):   4

  --- qwen3.5: Per-question dose-response pattern ---
    Monotone increasing: 2
    Monotone decreasing: 16
    Non-monotone:        16
    Flat (<15pp range):   5

==============================================================================
  6. KEY FINDINGS
==============================================================================

  Cross-model transfer (K):
    gemma4: K=50.3% vs C=61.5% — cross-model worse than self-trace **
    qwen3.5: K=67.9% vs C=50.3% — cross-model better than self-trace ***

  Compression premium (M vs L100):
    gemma4: M=73.4% vs L100=61.2%  delta=+12.2% **
    qwen3.5: M=88.8% vs L100=51.9%  delta=+36.9% ***

  Deterministic thinking (N vs B):
    gemma4: N=70.2% vs B=68.5%  delta=+1.7% ns
    qwen3.5: N=23.1% vs B=23.1%  delta=+0.0% ns

  Dose-response pattern:
    gemma4: 50% → 49% → 53% → 61% (monotone, tau=+0.67)
    qwen3.5: 64% → 55% → 51% → 52% (monotone, tau=-0.67)

  Truncation artifacts (Qwen):
    Qwen ceiling hits: K=51, L25=121, L50=143, L75=142, L100=143, M=0, N=184
    L-condition ceiling hits inflate extraction failures and depress ITT.
    N-condition: 184/312 ceiling hits + 200/312 extraction failures = collapse.

==============================================================================
  STATISTICAL CAVEAT: Phase 3 is exploratory. All results are descriptive.
  Marginal ORs are anti-conservative (clustering ignored). Cross-phase
  comparisons (P3 vs P2 subset) use same questions but different reps/dates.
  Qwen L/N conditions severely confounded by 8192 ceiling truncation.
==============================================================================
```

## Design context

- **K (cross-model transfer):** Qwen's B-trace is fed to Gemma, and Gemma's B-trace is fed to Qwen (as prefill, same as Condition C but with the other model's trace). Compared to Phase 2 Condition C (self-trace replay) on the same 39-item subset.
- **L25/L50/L75/L100 (dose-response):** The model's own B-trace is prefix-truncated to 25%/50%/75%/100% of BPE tokens, then used as prefill (same as C). Tests whether more trace → better performance.
- **M (compressed trace):** Claude Sonnet 4.6 compresses the model's B-trace to ~35% of original tokens, preserving key reasoning steps. Used as prefill.
- **N (deterministic thinking):** Think mode at temperature 0 (greedy decoding). A deviation from the original plan (empty-trace) because Ollama has no mechanism to force minimal thinking.
- **Phase 2 references:** A=baseline, B=thinking on, C=self-trace replay (think off, B-trace as prefill), D=expert scaffold (Sonnet 4.6 reasoning as prefill).
- **8192 ceiling:** The `num_predict` cap for thinking conditions. Qwen's verbose thinking frequently hits this, causing truncation and extraction failure.
- **39 items:** Selected from the 103 Phase 2 items where both models had 10-99% accuracy in Condition A.

## Audit Questions

Rate each as CRITICAL, IMPORTANT, or MINOR. Cite specific numbers from the report.

### 1. Cross-phase comparison validity
The report compares Phase 3 conditions (run 2026-04-12) to Phase 2 reference conditions (run 2026-04-08) on the same 39 questions. Is this comparison valid? What are the threats — session effects, model version drift, Ollama version differences, temperature/seed alignment? Should the report carry a stronger caveat?

### 2. Qwen L-condition truncation confound
Qwen has 121-143 ceiling hits per L condition (39-46% of inferences) despite L conditions being think-off prefill. Why would L conditions hit the 8192 ceiling if thinking is off? Is there a bug in the condition implementation, or is Qwen generating very long completions even without thinking? How does this affect the dose-response interpretation?

### 3. M vs L100 confound — trace source quality
M uses a Sonnet 4.6 compression of the B-trace, while L100 uses the raw B-trace directly. The M >> L100 finding is attributed to "distilled reasoning beats verbose reasoning." But M's trace was produced by a much stronger model (Sonnet 4.6). Is this actually testing compression, or is it testing the quality of the trace author? How would you disentangle these?

### 4. K-C Simpson's paradox interpretation
The K-C contrast reverses by model: Gemma -11.2pp (cross-model hurts), Qwen +17.7pp (cross-model helps). The report calls this "Simpson's paradox." But consider: K feeds Qwen traces to Gemma and Gemma traces to Qwen. So Gemma-K receives Qwen reasoning, and Qwen-K receives Gemma reasoning. Given that Qwen's traces are much longer and more verbose (mean eval_count 6370 vs 940 for B), could the K-C asymmetry simply reflect trace verbosity mismatch rather than cross-model incompatibility per se?

### 5. Dose-response statistical power
The dose-response analysis uses Kendall's tau on 4 data points (L25, L50, L75, L100). With n=4, no trend test can achieve significance even with perfect monotonicity. Is this analysis meaningful? What alternative approach would have more power? Should the per-question dose-response (312 observations per dose level) be the primary analysis instead?

### 6. Gemma L25 < A finding
For Gemma, L25 (50.0%) is significantly *worse* than baseline A (59.7%, p_adj=0.040). A quarter-length trace as prefill actively hurts performance. This is a surprising finding — partial context is worse than no context. Is this robust, or could it be an artifact of the 39-item subset selection or cross-phase comparison?

### 7. N-B comparison for Qwen
The report says Qwen N=B=23.1% and concludes delta=0.0% ns. But both conditions have ~60% extraction failure from ceiling truncation. The PP comparison (64.3% vs 60.4%, ns) is more informative but is testing "conditional on not truncating, does greedy vs stochastic matter?" which is a post-treatment selection. Is the N-B contrast for Qwen fundamentally uninformative, and should the report say so explicitly?

### 8. Missing analyses and presentation issues
What analyses are missing that a reviewer would expect? Consider: within-phase-only contrasts (L25 vs L100 etc.), pairwise L contrasts with L-internal Holm correction, eval_count analysis (does longer generation within a condition predict accuracy?), question-level random effects, interaction between dose and model as a formal test, and any other gaps. Also flag any presentation issues (mislabeled columns, inconsistent formatting, misleading framings).
