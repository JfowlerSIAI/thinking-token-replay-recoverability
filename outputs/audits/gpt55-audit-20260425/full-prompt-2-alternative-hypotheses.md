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

# Audit angle 2: Alternative-hypothesis generator

The paper proposes specific causal/mechanistic readings of each Robust Claim. Your job is to propose **alternative explanations** that fit the same data — and where possible, to use the data to discriminate between the paper's reading and your alternative.

## Specific instructions

For each of these surviving findings, propose one or more alternative hypotheses that the paper has not considered, then test them against the data:

1. **C−F content effect (Claim 1).** The paper says "coherent reasoning content beats shuffled tokens." Alternative readings to consider: (a) the shuffled F prefill confuses the model into producing unparseable outputs (extraction-channel effect), (b) F is ungrammatical and the model degrades into copy/repeat behavior, (c) C contains the answer in 87% of scaffolds (per §3.8) and F does not — so C−F may measure answer-leakage-presence, not content. Test what you can with the data.

2. **Gemma B−C numeric premium (Claim 4 partial).** The paper says Gemma live thinking helps on numeric. Alternatives: (a) the numeric subset is dominated by `compound_percentage`, `profit_loss_chain`, `bat_ball_variant` which have fundamentally different difficulty structures; (b) numeric C is more truncation-prone for Gemma (test); (c) Gemma's thinking content for numeric problems is higher quality than for tracking problems for some independent reason (e.g., training data composition).

3. **Qwen tracking C > B (Claim 3 + 4).** The paper says trace-replay beats live thinking on tracking tasks. Alternatives: (a) Qwen's live-thinking traces on tracking tasks are *longer* and more truncation-prone, while C uses a fixed prefilled trace; (b) the prefilled C trace was generated under temperature 0.7 once and then used for all 10 reps — so C has lower variance than B by construction (no fresh sampling); (c) something specific to Qwen's tokenizer or attention pattern on Box/Cup tokens.

4. **Gemma B−O hidden > visible CoT (Claim 8).** The paper says "hidden thinking beats visible CoT for Gemma." Alternatives: (a) the visible-CoT prompt formulation may be suboptimal for Gemma (template effect); (b) `num_predict` differs between conditions, biasing the comparison; (c) visible-CoT doesn't trigger Gemma's `<think>` tag and so Gemma processes O fundamentally differently from B at the inference level.

5. **The "trace replay recovers most of thinking benefit" master claim** (the title of the paper). What if the real finding is "most of the small-model questions in this benchmark are too easy for the live-thinking advantage to manifest"? Test: does the B−C effect grow on the harder subset?

## Constraints

- Use code execution and JSONL inspection to test each alternative where possible.
- For each alternative, output one of: SUPPORTED (data favors alt over paper), CONSISTENT (data fits both), REJECTED (data favors paper).
- Be quantitative. Cite specific row counts, percentages, statistical tests.
- Don't invent alternatives that aren't actually plausible.
- Don't re-find documented prior findings.

## Output

Plain Markdown. ≤ 1200 words. For each of the 5 findings above:
- The paper's reading
- One or more alternatives (specifically named)
- The data test you ran
- The verdict (SUPPORTED/CONSISTENT/REJECTED)
- The implication for the paper claim

End with a one-line recommendation per finding (e.g., "weaken claim", "leave as-is", "add caveat about X").

Begin now.
