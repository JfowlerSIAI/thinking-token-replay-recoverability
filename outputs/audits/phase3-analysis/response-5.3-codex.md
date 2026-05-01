**Tri-Agent Consolidated Audit**

1. **Cross-phase comparison validity — CRITICAL.**  
Not valid as a strong causal comparison; only exploratory/historical-control. Phase 2 references use `10` reps/seeds (`1–10`) and `ollama_version=0.20.2`; Phase 3 uses `8` reps/seeds (`1–8`) and `ollama_version=0.20.6`; model digests are blank in both logs (cannot verify identical weights). Most primary contrasts are cross-phase (`K-C`, `M-C`, `M-D`, `N-B`, `L100-C`, `L25-A`), only `M-L100` is same-phase. A stronger caveat is required.

2. **Qwen L-condition truncation confound — CRITICAL.**  
This is not “thinking on by accident.” `L*` runs with `think=false`, but prefill conditions are forced to `num_predict=8192` ([run_experiment.py:167](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py:167), [run_experiment.py:174](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py:174)) and raw assistant continuation leaves the reasoning stream open ([condition_builder.py:234](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/condition_builder.py:234)). In logs, Qwen `L25/L50/L75/L100` has `121/143/142/143` ceiling hits (total `549/1248`), with `thinking_tokens` non-empty in `0/1248`. So it is long visible completion, not hidden think mode. Dose-response interpretation is strongly confounded: ceiling-hit pooled ITT is `36.8%` vs `70.2%` off-ceiling.

3. **M vs L100 trace-source confound — CRITICAL.**  
Current implementation does not isolate “compression vs full trace.” `M` uses one per-question external compressed artifact reused across all reps/models ([run_experiment.py:144](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py:144), [run_experiment.py:501](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py:501)). Compression source selection prefers correct Qwen traces first ([generate-scaffolds.py:88](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/scripts/generate-scaffolds.py:88), [generate-scaffolds.py:115](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/scripts/generate-scaffolds.py:115)). Also, checked-in generator uses `gpt-5.4`, not Sonnet ([generate-scaffolds.py:34](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/scripts/generate-scaffolds.py:34)). Token lengths are massively unmatched: `M` prefill mean ~`176` tokens for both models vs `L100` mean `438` (Gemma) and `1940` (Qwen). So `M >> L100` is not clean evidence that “compression beats full trace.”

4. **K-C “Simpson’s paradox” interpretation — IMPORTANT.**  
Labeling this as Simpson’s paradox is imprecise; this is crossover interaction plus strong donor-style mismatch. In your data, donor length flips by model: Gemma `K` gets Qwen-style long traces (~`1940` tokens) vs Gemma self-trace in `C` (~`430`), while Qwen `K` gets shorter Gemma-style traces (~`438`) vs Qwen self-trace in `C` (~`1926`). So verbosity/style mismatch is a major competing explanation; cross-model incompatibility is not identified.

5. **Dose-response statistical power — IMPORTANT.**  
Current trend test is too weak because it collapses to 4 aggregated dose points/model. With `n=4`, two-sided Kendall tau cannot reach `p<0.05` even with perfect monotonicity. Use trial-level matched analyses (`39 × 8` paired units per model) as primary. Example paired results (McNemar-style): Gemma `L100>L25` `+11.2pp`, `p=0.00073`; Qwen `L25>L100` `+11.9pp`, `p=2.24e-05` (both survive within-L Holm correction).

6. **Gemma L25 < A finding — IMPORTANT.**  
Signal is likely real but over-claimed if framed as definitive “worse than no context,” because `A` is cross-phase historical control. It remains robust in sensitivity: with Phase 2 restricted to seeds `1–8`, Gemma `L25` vs `A` is still `-10.6pp` ITT (`p=0.0099`), and `L25` is also worse than `L100` within Phase 3 (`-11.2pp`, paired `p=0.00073`). So keep it as strong exploratory evidence, not confirmatory.

7. **Qwen N-B interpretation — CRITICAL.**  
Agree with your concern: this contrast is fundamentally uninformative for mechanism under current cap. Both arms are collapse-dominated (`B`: `242/390` ceiling hits, `241/390` extraction failures; `N`: `184/312`, `200/312`). ITT equality (`23.1%` vs `23.1%`) is mostly shared truncation failure, not evidence about greedy vs stochastic thinking. PP is post-treatment-selected and should be explicitly labeled as such.

8. **Missing analyses / presentation issues — IMPORTANT.**  
Missing analyses reviewers will expect: formal model×condition interaction test; question-clustered or mixed-effects models; within-phase primary anchors (`K` vs `L100`, `M` vs `K`, internal L pairwise with Holm); seed-matched cross-phase sensitivity (`P2` seeds `1–8`); explicit eval_count/ceiling mediation analysis; provenance audit for compressed traces.  
Presentation issues: “monotone” label is misleading for non-monotone sequences and non-significant tau ([analyze_mechanism.py:665](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/analyze_mechanism.py:665)); “DIRECTION REVERSAL” on `N-B` with `+1.7%` vs `+0.0%` is misleading; your pasted table shows a duplicated Qwen `L50` row (current script output does not).

1. If you want, I can draft exact replacement caveat text for the report header and Key Findings section.  
2. I can also generate an addendum table with seed-matched cross-phase sensitivity and within-phase paired L contrasts.  
3. I can patch `analyze_mechanism.py` to include these as default outputs.