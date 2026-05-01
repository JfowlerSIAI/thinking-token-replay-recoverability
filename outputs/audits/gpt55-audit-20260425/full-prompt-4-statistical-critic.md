# Shared context for all four GPT-5.5 audit angles

## Paper

`workflows/thinking-token-experiment/paper/paper.md` — "Replay Recoverability of Thinking-Token Benefits in Small Language Models." Tests on Qwen 3.5 9B and Gemma 4 E4B (4.5B effective, dense + PLE) across 11 conditions on 103 questions × 10 reps. Final dataset is 22,660 records under exact-string scoring with various sensitivities reported.

## Data

- Per-inference JSONL: `workflows/thinking-token-experiment/outputs/confirmatory_merged/20260415/inference_log.jsonl` (~40k rows, primary Phase 2 + 16K rerun for 367 Qwen-B ceiling-hit cases)
- Phase 3 (mechanism): `workflows/thinking-token-experiment/outputs/mechanism/20260412_215554/inference_log.jsonl` (~4.4k rows)
- Questions: `workflows/thinking-token-experiment/questions/selected.jsonl` (103 items with `answer`, `answer_type`)
- Scaffolds: `workflows/thinking-token-experiment/questions/scaffolds/*.json` (per-question GPT-5.4 reasoning, plus `wrong_scaffold` and `compressed`)
- Scorer: `workflows/thinking-token-experiment/runner/score.py`
- Condition builder: `workflows/thinking-token-experiment/runner/condition_builder.py`

## Conditions (recap)

A baseline | B thinking-on | C self-trace replay (prefill) | D expert-scaffold prefill | E thinking + scaffold-as-context | F shuffled-tokens prefill | G wrong-question-trace prefill | H wrong-scaffold prefill | I token-matched self-consistency vote | J filler-tokens prefill | O visible-CoT prompt

Phase 3: K cross-model | L25/L50/L75/L100 dose-response prefill | M strong-model-compressed trace prefill | N deterministic thinking T=0

## Prior audit findings already documented in the paper — DO NOT RE-FIND THESE

These were found by the 2026-04-15 scoring-pipeline audit (gpt-5.3-codex + gpt-5.4) and the 2026-04-25 follow-up (Sonnet-class). They are documented in §3.8–§3.14 and revised Claims 2, 3, 4, 8. You waste your time if you "discover" them again:

1. **Gemma `<end_of_turn>` template-token leakage** in 206 Gemma-D rows and 167 Gemma-H rows; corrupts extraction when the token lands on the same line as `FINAL:`. Strip rescues +8.4 pp on Gemma D.

2. **Qwen `<|endoftext|><|im_start|>user` template-token leakage** in 80 Qwen-C rows and 82 Qwen-G rows. Strip rescues +3.88 pp on each. Flips Qwen B−C TOST equivalence.

3. **"Box N" / "Cup X" structured-label format drift.** 22 of 52 exact-answer items expect `Box 3`-style answers; both models intermittently emit bare `3`. Affects Gemma A/B/C/D/I/J/O substantially (+27 to +86 rescues per cell) and Qwen C/F/G modestly. Caused by absence of alias-aware scoring in `score.py`.

4. **Question-family heterogeneity** in B−C: cond × is_boxcup interaction p=.031 (Gemma), p<.001 (Qwen). Gemma B−C is +0.45 (p=.001) on numeric, null on tracking. Qwen B−C is null on numeric, strongly negative on tracking.

5. **Condition H "wrong scaffold" is broken.** 17/103 are GPT-5.4 refusal templates, 65/103 contain gold-answer substring, 24/103 still end with the exact gold `FINAL:` line after `_strip_final_answer()`.

6. **87% of expert scaffolds (D)** retain the ground-truth answer in their stripped reasoning text. D partially measures answer-extraction-from-context, not pure scaffold-use.

7. **Qwen B at 8K truncates 36% of the time**; 16K rerun rescues to 20%; 16K-merged dataset has Ollama 0.20.2 vs 0.20.6 cross-version drift on the 367 rerun rows.

8. **Gemma B−O Part-2 OR 1.51 (p=.006) under full correction** — hidden thinking beats visible CoT for Gemma. Already promoted to Claim 8.

9. **Phase 3 L-slope magnitudes attenuate ~50% under full correction.** Direction unchanged.

## Core claims as currently in the paper

§4 Robust Claims:
1. C−F content effect (huge, both models, robust to all sensitivities)
2. D−C scaffold helps both models dramatically (asymmetry vanishes under fair scoring)
3. Qwen B−C: trace-replay clearly beats live thinking (~6pp) under full correction (E2E); but Part-2 favors B (OR 1.43, p=.0001) — heterogeneous by question family
4. Gemma B−C: null in aggregate, real on numeric subset (OR 1.56, p=.001), absent on tracking
5. C−J reasoning vs filler (large, both models)
6. G−F shape: positive for Qwen (OR 6.18 full-correction), null for Gemma Part-2
7. Qwen truncation a dominant mediator (not the only one)
8. Gemma B−O: hidden thinking > visible CoT under fair scoring (modest, within-model only)

## Methods recap

GEE (Binomial/Logit), `groups=question_id`, exchangeable working correlation, robust sandwich SEs. Holm-Bonferroni across 7 pairwise contrasts per model. Two-part hurdle (Part 1: extraction failure; Part 2: correctness | extracted). TOST equivalence with SESOI = log-OR (−0.162, +0.166).

## Your job

You are GPT-5.5 at xhigh reasoning. The user wants to know if a newer model surfaces things the older auditors (5.3-codex + 5.4 + Sonnet-class) missed. Each audit angle is given a different stance and target. Be ruthless and specific. If you can't find anything new, say so explicitly and explain what you tried.

Ground every finding in: file paths with line numbers, row counts out of n, specific data observations. Vague theoretical critiques without data backing are not useful here.

---

[shared context follows; read it first]

# Audit angle 4: Statistical-methodology critic

You are a statistician reviewing the analysis pipeline. The paper uses GEE (Binomial/Logit, exchangeable, robust SEs), Holm-Bonferroni, two-part hurdle, and TOST. Your job is to find subtle methodological issues that the prior auditors (focused on scoring artifacts) did not address.

## Specific instructions

Address each of these targeted questions. Do not write a textbook overview — answer with concrete observations about *this* analysis.

1. **Hurdle Part-2 selection bias.** Part-2 conditions on extraction success. Extraction failure is a *post-treatment* outcome (it depends on what the model does, which depends on the condition). So Part-2 estimates are conditional on a post-treatment variable — this is the Heckman/collider-bias problem. The paper's §2.5 gestures at this but treats Part-2 results as primary for some claims (e.g., Claim 1 cites Part-2 OR 8.84/6.99 as preferred). Is that defensible? Quantify the potential bias — for which claims is it large vs negligible?

2. **TOST equivalence with SESOI = log-OR (−0.162, +0.166).** Where did this SESOI come from? Is it actually pre-registered, and is it a sensible practical-equivalence threshold for B−C in this domain? On what scale (raw accuracy, log-odds, OR) was it elicited? Is it symmetric on the right scale? Does the choice of SESOI affect any of the surviving claims if reasonably perturbed (e.g., ±50%)?

3. **Holm-Bonferroni across 7 contrasts per model is anti-conservative for an exploratory paper with multi-stage discovery.** The paper has gone through five rounds of revisions, the question-family decomposition was post-hoc, the scoring corrections were post-hoc. Should multiplicity correction be applied across more than 7 tests? What's the right framing?

4. **GEE with 103 clusters and exchangeable working correlation.** The paper acknowledges "small-cluster corrections (Mancl-DeRouen, Kauermann-Carroll) are not applied." How much do the SEs change under those corrections for the surviving Claim 3 (Qwen B−C log-OR −0.282) and the surviving Claim 4 (Gemma numeric B−C log-OR +0.446)? If you can't run them, estimate the inflation.

5. **The 16K rerun is a post-treatment selection.** §2.7 acknowledges this as an "ITT violation" but reports the 16K-merged primary numbers anyway. What's the cleanest non-ITT estimand that the merged dataset *does* identify? Frame it precisely.

6. **Question-family decomposition (§3.13) is post-hoc.** The cond × is_boxcup interaction p=.031 (Gemma). Is this a credible finding without correction for the implicit search across many possible partitions? The paper argues "single pre-specified partition that motivated §3.10." Is that defense valid? What's the right way to think about post-hoc subgroup analysis here?

7. **Within-question correlation ρ = 0.143 Gemma, 0.118 Qwen.** These are reported as "meaningfully nonzero." Are they *small* enough that a naive logistic regression with cluster-robust SEs gives basically the same answer as GEE-exchangeable? If yes, why does the paper attribute so much to "marginal vs hierarchical" choice in §2.6?

## Constraints

- Where calculations are needed, run them on the data.
- Cite specific numbers and contrasts.
- Don't recapitulate textbook material on GEE or hurdle models — focus on this paper's actual choices.
- Don't re-find documented prior findings.

## Output

Plain Markdown. ≤ 1200 words. One section per question above. End with a "what changes in the paper" recommendation table — for each statistical issue, what (if anything) should the paper acknowledge, weaken, or rerun.

Begin now.
