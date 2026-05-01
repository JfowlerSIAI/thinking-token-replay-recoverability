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

# Audit angle 3: Mechanism — what's actually happening inside the models

The paper documents *that* certain effects exist but is light on *why*. Your job is to use the raw inference data to surface mechanistic patterns the paper has not analyzed. Concentrate on token-level, content-level, and timing-level patterns rather than rederiving the cell-level accuracy numbers.

## Specific instructions

1. **Trace-content analysis on B vs C for tracking tasks.** The paper found C beats B on tracking for both models. Open the actual `thinking_tokens` field for Qwen B records and the corresponding C-prefill content (which is the prior B run's thinking_tokens) on a sample of tracking questions. What is structurally different between a B trace that got the answer wrong and a C run on the same question that got it right? Look for: redundant re-derivation of state, contradictions, partial-state confusion, "self-correction" loops that don't converge.

2. **Why does Gemma drop the "Box" prefix while Qwen echoes it?** Sample 20 Gemma D records and 20 Qwen D records on Box/Cup questions. Look at the `content` field and the scaffold text. Does Gemma's continuation pattern after the prefill ("FINAL: ...") suggest it's parsing the scaffold differently? Is there a tokenizer-level explanation? Is the `Box ` token segmented differently in Gemma's vocabulary?

3. **Truncation triggers for Qwen B.** What kinds of questions cause Qwen B to truncate? Cross-tabulate ceiling-hit rate against question family, ground-truth length, and prompt length. Is truncation random or systematic? If systematic, does it correlate with question difficulty (paper-scorer A-condition accuracy as a proxy)?

4. **Gemma's empty-thinking traces revisited.** The CLAUDE.md mentions 15/1236 Gemma-B traces have entirely empty thinking — all on modular arithmetic. The interpretation was "model elects to skip thinking on trivial questions." Test: does Gemma's empty-thinking accuracy match its non-empty accuracy on the same questions? If yes, it's a free win. If no, it's a sampling failure mode.

5. **Trace verbosity vs accuracy.** For each model, plot/compute: trace length (chars in `thinking_tokens` for B, chars of prefill for C/D/etc) vs P(correct). Is there a sweet spot? A monotone? An optimum that the data sits at vs misses?

6. **Token-level scaffold leakage.** §3.8 says 87% of scaffolds retain the gold answer in their stripped reasoning. Quantify *where* in the scaffold the answer appears (early/middle/late) and whether D-condition models echo from the scaffold's location vs reproduce it independently. If Qwen always echoes from the same line where the scaffold mentioned the answer, that's a different finding from "Qwen reasons from scaffold."

## Constraints

- This is hands-on data analysis. Spend 70%+ of your effort on actual JSONL inspection, not prose.
- Use python with json/regex/statistics, not just paper text.
- Each finding must include: a quantitative summary (e.g., 18/20 cases), a representative example (inference_id + content excerpt), and an interpretation.
- Don't invent mechanisms that aren't visible in the data.

## Output

Plain Markdown. ≤ 1500 words. One section per investigation above. End with a "what this implies for the paper's claims" paragraph.

Begin now.
