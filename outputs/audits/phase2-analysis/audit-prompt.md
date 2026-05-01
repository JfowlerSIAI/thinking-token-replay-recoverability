# Phase 2 Analysis Audit — Thinking Token Experiment

## Context

This is a Phase 2 confirmatory analysis of an experiment testing whether "thinking tokens" (chain-of-thought reasoning tokens) are inherently useful for small language model performance, or whether they primarily serve as a mechanism to increase effective context at inference time.

**Models under test:**
- Qwen 3.5 (9.7B dense parameters, Q4_K_M)
- Gemma 4 E4B (8.0B total / 4.5B effective parameters via PLE, Q4_K_M)

**Design:** 103 questions x 11 conditions x 10 reps x 2 models = 22,660 primary inferences + 16,890 I_sub voting inferences.

**Conditions:**
- A: Baseline (no thinking, no extra context)
- B: Standard thinking (think mode ON)
- C: Self-trace replay (B's thinking tokens replayed as prefill, think OFF)
- D: Expert scaffold (Sonnet 4.6 reasoning as prefill)
- E: Thinking + scaffold (scaffold in user message, think ON)
- F: Shuffled tokens (B's thinking tokens shuffled, destroying semantics)
- G: Wrong-question trace (B trace from different question, same domain/length)
- H: Wrong scaffold (minimally incorrect Sonnet reasoning)
- I: Token-matched self-consistency (k no-think attempts, majority vote)
- J: Filler tokens (neutral filler matched to B-trace token count)
- O: Visible CoT (explicit step-by-step prompting, think OFF)

**8 pre-registered contrasts:**
1. B-C: Internal reasoning effect
2. C-F: Rationale-content effect
3. G-F: Generic reasoning-shape effect
4. D-C: Expert-scaffold premium
5. E-(B+D-A): Synergy on log-odds scale
6. B-I: Compute allocation
7. B-O: Think-mode vs visible-CoT
8. C-J: Semantic reasoning vs filler

**Known methodological issue:** Qwen B-condition has 36% extraction failures, ALL at the 8192 eval_count ceiling (thinking consumes all tokens before FINAL: tag). Qwen per-protocol B accuracy is 84.2%, close to baseline A (85.0%). All B-involving contrasts for Qwen overall numbers are confounded by this truncation artifact.

## Analysis Report

[Full report follows]

## Audit Questions

Please review the Phase 2 analysis report and address these questions. Cite specific numbers from the report. Rate each finding as CRITICAL, IMPORTANT, or MINOR.

1. **Statistical validity**: Are the marginal odds ratios with Haldane correction appropriate for this design (repeated measures within questions/seeds)? What biases does this introduce vs the planned Bayesian hierarchical model? Are any contrasts so confounded by extraction failures that the OR is misleading?

2. **Qwen B truncation**: 367/1030 Qwen B inferences hit the 8192 ceiling. The ITT analysis counts these as incorrect. Is this the right call, or should the paper present per-protocol as primary for B-involving contrasts? How should contrasts 1 (B-C), 5 (synergy), 6 (B-I), 7 (B-O) be interpreted given this artifact?

3. **Simpson's paradox / model heterogeneity**: Several contrasts show OPPOSITE directions per model (e.g., B-C: Gemma favors B by +5.8%, Qwen favors C by +14.7%). Does pooling these into a single OR obscure the real story? Should the paper report per-model contrasts as primary?

4. **Extraction failure confounds**: F has 45% extraction failures (Qwen 57%, Gemma 34%). J/Qwen has 40%. To what extent do the massive C-F and C-J effects reflect "shuffled/filler text confuses the model into not outputting FINAL:" vs "shuffled text genuinely degrades reasoning"? How to disentangle?

5. **D-C asymmetry**: Expert scaffold premium is huge for Qwen (97.5% vs 68.8%) but near zero for Gemma (82.5% vs 80.5%). The Gemma eval_count for D is 76 tokens (very short). Does this suggest Gemma is "ignoring" the scaffold and just answering from its own knowledge?

6. **Synergy interpretation**: E-(B+D-A) is +1.08 log-odds overall but the CI is wide and per-model results are non-significant. Is the overall significance driven by aggregation artifacts? Is there a better way to test synergy given the model heterogeneity?

7. **B-O finding**: Visible CoT (O=84.0%) beats hidden thinking (B=70.2%), but for Gemma the direction reverses (B=86.3% > O=82.4%). Is the overall result primarily a Qwen truncation artifact? What does B-O look like if restricted to Gemma only?

8. **Missing analyses**: What analyses are missing that a reviewer would expect to see? Consider: sensitivity analyses (ITT vs per-protocol), question-level clustering, effect heterogeneity by domain/difficulty, multiple comparison corrections, or anything else.

Rate each finding CRITICAL/IMPORTANT/MINOR with specific recommendations.
