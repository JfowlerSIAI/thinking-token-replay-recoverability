1. **Statistical validity — CRITICAL**  
Marginal ORs here are descriptive, not confirmatory, because they treat observations as independent while the design is repeated (`103 questions x 10 reps` per condition/model). That likely makes CIs too narrow and p-values too optimistic.  
Haldane correction is not the main problem (with large cells, its bias is usually small); the bigger issues are:
- ignored clustering/pairing by question/seed,
- strong model heterogeneity (opposite effects by model),
- informative missingness from extraction failures.  
Most misleading ORs: all B-involving contrasts (Qwen B has `367/1030 = 36%` extraction failures, all at `8192`), plus partial confounding in C-F and C-J because F/J have high failure rates.

2. **Qwen B truncation — CRITICAL**  
Counting extraction failures as incorrect (ITT) is valid for an end-to-end system metric. But it should not be the only lens for claims about “reasoning usefulness.”  
Use dual reporting: ITT (operational) + conditional/per-protocol (mechanistic), with explicit caveat that PP is selected on successful extraction.

Interpretation with artifact:
- B-C: ITT says B worse (`70.2% vs 74.7%`), but PP reverses (`85.9% vs 77.1%` overall; Qwen PP `84.2% vs 72.1%`).
- B-I: ITT gap is large (`70.2% vs 88.8%`), but much smaller on Qwen PP (`84.2% vs 91.5%`).
- B-O: ITT favors O (`70.2% vs 84.0%`), but PP nearly ties/reverses (`85.9% vs 84.0%` overall; Qwen PP `84.2% vs 85.6%`).
- Synergy includes B in formula, so B truncation directly destabilizes it.

3. **Simpson’s paradox / heterogeneity — CRITICAL**  
Pooling obscures the true story. You have direction reversals:
- B-C: Gemma favors B (`86.3 vs 80.5`, OR `1.527`), Qwen favors C (`54.2 vs 68.8`, OR `0.536`).
- B-O: Gemma favors B (OR `1.343`), Qwen strongly favors O (OR `0.199`).
- D-C: Gemma near null (OR `1.145`, ns), Qwen huge (OR `17.176`).  
Per-model contrasts should be primary; pooled effects should be secondary with explicit interaction modeling.

4. **Extraction-failure confounds — IMPORTANT**  
Yes, part of C-F and C-J is parser/format failure, but not all:
- F failure is `45%` overall (`57%` Qwen, `34%` Gemma).
- J failure is `21%` overall (`40%` Qwen).  
After PP filtering, effects remain:
- C-F PP: `77.1% vs 31.7%` (still very large).
- C-J PP: `77.1% vs 41.0%` (still large overall), but Qwen shrinks notably (`72.1% vs 57.9%`).  
Recommendation: decompose into two outcomes: `P(extraction success)` and `P(correct | extracted)`.

5. **D-C asymmetry — IMPORTANT**  
Qwen shows huge D premium (`97.5% vs 68.8%`), Gemma shows near-zero (`82.5% vs 80.5%`, OR `1.145`, ns).  
Gemma’s short D eval count (`76`) suggests little generation-time deliberation, but does not prove scaffold is ignored. Stronger evidence is performance: Gemma D is basically A (`82.5% vs 82.8%`).  
Interpretation: scaffold benefit is model-specific; for Gemma it adds little measurable signal in this setup.

6. **Synergy interpretation — IMPORTANT**  
Overall synergy is positive (`+1.083`, CI `[+0.192,+1.974]`), but model-specific synergies are both non-significant and opposite in sign:
- Gemma `+1.757` `[-0.685,+4.199]`
- Qwen `-0.217` `[-2.818,+2.384]`  
This is likely aggregation + heterogeneity (and B truncation influence), not robust cross-model evidence.  
Better test: hierarchical logistic with explicit model-specific interaction terms and a pooled random-effects interaction.

7. **B-O finding — IMPORTANT**  
Overall B-O result is mostly a Qwen truncation artifact.  
Gemma-only: B beats O (`86.3% vs 82.4%`, OR `1.343 [1.057,1.706]`).  
Qwen ITT drives pooled reversal (`54.2% vs 85.6%`), while Qwen PP is near parity (`84.2% vs 85.6%`).

8. **Missing analyses reviewers will expect**  
- **CRITICAL:** Planned Bayesian hierarchical logistic model output (question clustering + seed pairing + model interactions), not just marginal ORs.  
- **CRITICAL:** ITT/PP sensitivity for all key contrasts, plus two-part modeling of extraction vs correctness.  
- **CRITICAL:** Formal `model x condition` interaction tests and per-model primary claims.  
- **IMPORTANT:** Paired contrast analyses at question-seed level (not independent-sample approximations).  
- **IMPORTANT:** Token-budget sensitivity (especially reruns for B/F/J with higher cap or stricter stop control).  
- **IMPORTANT:** Multiplicity handling across 8 confirmatory contrasts (or explicit Bayesian posterior decision framework).  
- **IMPORTANT:** Heterogeneity by domain/difficulty.  
- **MINOR:** Extraction robustness checks (alternate parser/manual adjudication sample).