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

# Audit angle 1: Weakest-link hunter

You are an adversarial reviewer assigned to find the **weakest claim that is still standing** after the multi-round audit revisions. The paper has been heavily revised; many findings were retracted or revised. Your job is to identify which surviving claim has the most fragile evidentiary basis.

## Specific instructions

1. Read every Robust Claim in §4 (1 through 8) carefully.

2. For each claim, identify the chain of inference: (raw data) → (scoring decision) → (statistical model) → (interpretation). Find the weakest link in each chain.

3. Pick the **single** claim whose chain has the weakest link, and explain in concrete terms what additional analysis or data would dissolve it. Quantify if possible (e.g., "a 5pp shift in cell X would flip this").

4. Then identify the **single most overstated word, phrase, or sentence** in §4 — a place where the paper's language outruns its evidence even after revision.

5. Finally, identify any claim in §5 ("What we do not claim") that is over-disclaimed — a place where the paper is being too modest given the data actually supports the claim.

## Constraints

- Use the data: read JSONL records, run python analysis, query the scorer behavior.
- Cite specific row counts, file paths, and statistical numbers.
- Do not re-find documented prior findings (see shared context list of 9 known findings).
- Be specific. "The B−C interpretation is fragile" is not useful. "On the 51 numeric questions, if you exclude the 13 modular-arithmetic items where Gemma at temperature 0.7 has a 4× higher per-rep variance, the B−C OR drops from 1.56 to 1.13 and loses significance" is useful.

## Output

Plain Markdown. ≤ 1000 words. Sections:
1. Per-claim weakest-link table (8 rows, one per Robust Claim, with link and severity).
2. The single weakest-link claim, expanded.
3. The single most overstated phrase in §4.
4. Anything over-disclaimed in §5.
5. (Optional) Any methodological smell that doesn't fit the above.

Begin now.
