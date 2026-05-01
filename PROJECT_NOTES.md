# Thinking Token Experiment

## Purpose

Determine whether "thinking tokens" (chain-of-thought / reasoning tokens) are inherently useful for small language model performance, or whether they primarily serve as a mechanism to increase effective context at inference time. Framed as a mechanistic case study on two small models, not a universal claim.

**Key reframing:** The main claim is about *replay recoverability* — how much of think-mode's benefit can be recovered by replaying the visible reasoning trace as context.

## Models Under Test

| Property | Qwen 3.5 | Gemma 4 E4B |
|----------|----------|-------------|
| Ollama tag | `qwen3.5:9b` | `gemma4:latest` (alias: `gemma4:e4b`) |
| Architecture | qwen35 (dense) | gemma4 (Per-Layer Embeddings / PLE) |
| Total parameters | 9.7B | 8.0B |
| Effective parameters | 9.7B | 4.5B |
| Quantization | Q4_K_M | Q4_K_M |
| Context length | 262,144 | 131,072 |
| Embedding dimension | 4,096 | 2,560 |
| Disk size | ~6.0 GB | ~9.6 GB (includes vision + audio encoders) |
| Capabilities | completion, vision, tools, thinking | completion, vision, audio, tools, thinking |

**Asymmetry note:** Although both models are in the "small / <10B" tier, Gemma 4 E4B
uses Per-Layer Embeddings (PLE), reducing active compute to ~4.5B effective parameters
per forward pass vs Qwen's full 9.7B dense parameters. The 9.6 GB disk size for Gemma
is inflated by bundled multimodal encoders (vision ~1.6 GB + audio ~3.0 GB at FP16);
the text model itself is ~5.0 GB at Q4_K_M. This effective-parameter asymmetry should
be noted in the paper's methods section as a limitation — differences in per-condition
accuracy between models may partly reflect capacity differences, not just architectural
ones. The experiment's primary contrasts (B−C, C−F, etc.) are within-model, so this
asymmetry does not threaten internal validity, but it limits cross-model generalization.

**Identification method:** Variant confirmed via tri-agent audit (gpt-5.3-codex +
gpt-5.4 + gemini-3.1-pro, full convergence). Key discriminator: embedding dimension
2560 uniquely identifies E4B in HuggingFace config. Ollama digest `c6eb396dbd59`
matches `gemma4:e4b` tag.

## Core Question

When a model with thinking enabled performs better, is the improvement caused by:
1. The structured reasoning process itself (the "act of thinking")
2. The additional context/tokens available at inference time
3. The specific semantic content of the reasoning
4. The compute allocation (more tokens = more FLOPs)
5. Standard CoT prompting vs a special think-mode mechanism
6. Some combination of the above

## Experimental Conditions (v1.1)

### Primary Conditions (Phases 1–2)

| ID | Name | Thinking | Extra Context | Key Contrast |
|----|------|----------|---------------|--------------|
| **A** | Baseline | Off | None | — |
| **B** | Standard thinking | On | None | B−A: total think effect |
| **C** | Self-trace replay | Off | B's thinking tokens (prefill) | B−C: internal reasoning effect |
| **D** | Expert scaffold | Off | Sonnet 4.6 reasoning (prefill) | D−C: expert premium |
| **E** | Thinking + scaffold | On | Sonnet scaffold (prefill + think) | Synergy test |
| **F** | Shuffled tokens | Off | Shuffled B tokens (prefill) | C−F: semantic content effect |
| **G** | Wrong-question trace | Off | B from different question (prefill) | G−F: reasoning shape effect |
| **H** | Wrong scaffold | Off | Minimally-wrong Sonnet (prefill) | Suggestibility test |
| **I** | Token-matched SC | Off | k no-think attempts, majority vote | B−I: think vs compute |
| **J** | Filler tokens | Off | Neutral filler (prefill) | C−J: reasoning vs filler |
| **O** | Visible-CoT | Off | None (prompted CoT) | B−O: think-mode vs explicit CoT |

### Mechanism Deep-Dive (Phase 3)

| ID | Name | Description |
|----|------|-------------|
| **K** | Cross-model transfer | Qwen trace → Gemma answer, vice versa |
| **L** | Dose-response | Prefix-truncated B trace at 25/50/75/100% |
| **M** | Compressed trace | Strong model compresses B's reasoning to ~35% |
| **N** | Deterministic thinking | Think mode at temperature 0 (greedy decoding) — see deviations |

### 8 Pre-registered Confirmatory Contrasts

1. B−C: Internal-reasoning effect
2. C−F: Rationale-content effect
3. G−F: Generic reasoning-shape effect
4. D−C: Expert-scaffold premium
5. E−(B+D−A): Synergy (log-odds scale)
6. B−I: Compute-allocation
7. B−O: Think-mode vs visible-CoT
8. C−J: Semantic reasoning vs filler

## Directory Structure

```
questions/
  generators/                # Procedural question generators (math, logic, spatial, factual, hard)
  calibration-pool.jsonl     # 740+ candidate questions with ground truth
  selected.jsonl             # 103 locked items for Phase 2 (both models in 30-70% band)
  phase3-subset.jsonl        # 39 items for Phase 3 (both models in 10-99% band)
  scaffolds/                 # Sonnet 4.6 reasoning per question (Phase 2)
runner/
  run_experiment.py          # Main experiment loop (CLI: --phase calibration/validation/mechanism/etc.)
  ollama_client.py           # Ollama API wrapper with per-inference JSONL logging
  condition_builder.py       # Prompt construction per condition (A-O, L25/L50/L75/L100)
  trace_bank.py              # B-trace bank management, BPE token counting (tiktoken)
  score.py                   # Answer extraction + grading (ITT: failures = incorrect)
analysis/
  calibrate.py               # Phase 1 calibration analysis + item selection
  validate.py                # Validation analysis: sanity checks, per-condition accuracy
  analyze.py                 # Phase 2 confirmatory analysis (post-audit: per-model primary, ITT/PP, Holm-Bonferroni)
  analyze_mechanism.py       # Phase 3 mechanism analysis (post-audit: context-window pathology, trace-source confound)
scripts/
  run-validation.sh          # Shell wrapper: run validation inferences + analysis
outputs/
  audits/                    # Tri-agent audit reports (infra, validation, fixes, model ID)
  trace_bank/                # Frozen B traces for C/F/G/J derivation
  pilot/                     # Phase 1 raw data (calibration + validation)
  confirmatory/              # Phase 2 raw data
  mechanism/                 # Phase 3 raw data
  results/                   # Aggregated statistics + plots
```

## Key Parameters

- Temperature: 0.7 (primary), 0.0 (Condition N only — see deviations below)
- Seed grid: 1–12 (fixed, paired 1:1 with reps)
- KV cache: `keep_alive: 0` (fresh state per inference)
- Reps per condition: 8–12 (determined by Phase 1 power analysis)
- Questions: 103 locked items (from 740+ calibration pool, both models in 30–70% band)
- Calibration accuracy: Qwen 59%, Gemma 51% (mean across selected items)
- Token counting: BPE via cl100k_base (tiktoken), consistent across all conditions
- Evaluation: ITT — extraction failures scored as incorrect
- Statistical model: Bayesian hierarchical logistic regression
- SESOI: Odds ratio 0.85–1.18 for equivalence testing

## Execution Phases

1. **Phase 1 — Pilot** (~15K invocations, ~1 week)
   - Calibrate items to 30–70% accuracy band (Condition A × 12 reps)
   - Validate infrastructure (B/C/F/O × 4 reps)
   - Smoke-test all conditions (D/E/H/I/J × 4 reps × 20-item subset)
   - Estimate variance components, determine optimal rep count

2. **Phase 2 — Confirmatory** (~48K invocations, ~1-2 weeks)
   - All 11 primary conditions × locked items × 8-12 reps × 2 models
   - Pre-registered on OSF before first inference

3. **Phase 3 — Mechanism Deep-Dive** (~7K invocations, ~1 week)
   - K/L/M/N on 40-60 item subset
   - Explicitly exploratory

## Deviations from Plan

Documented deviations from `plans/thinking-token-experiment.md` (the plan is kept
as-is for pre-registration reference; deviations are noted here and in the paper):

1. **Condition N: temperature 0 instead of empty-trace.** Plan specifies "empty-trace
   think mode / forced minimal trace." Ollama has no reliable mechanism to force an
   empty or minimal thinking trace across both model families. Implemented as
   deterministic thinking (temperature 0, greedy decoding) instead. Tests whether
   stochastic sampling in the think phase adds value — a different but still meaningful
   variable. (Tri-agent audited, all three models agreed this is acceptable.)

2. **Token counting: cl100k_base proxy.** Neither model uses cl100k_base natively, but
   the protocol requires consistency across conditions, not exact native counts.
   cl100k_base (BPE, ~100k vocab) produces counts within ~10% of both models' native
   tokenizers. Used for: shuffle (F), length-matching (G/J), k computation (I),
   dose-response truncation (L).

3. **Condition I tie-break: lexicographic only.** Plan specifies logprob-then-
   lexicographic. Ollama does not reliably expose per-token logprobs for chat
   completions. Lexicographic is deterministic and reproducible. Documented in code
   and paper methods.

4. **Question pool: 103 items from 740+ (not 120–160 from 260).** Hard generator
   added after initial pool was too easy. More items generated, stricter calibration
   yielded 103 in-band for both models.

5. **Condition E: chat-mode context injection instead of raw-mode prefill + think.**
   Plan specifies scaffold as assistant prefill with thinking enabled. However,
   Ollama's `/api/generate` raw mode does not support thinking — `think: true` is
   accepted but no thinking tokens are ever generated (verified: 0/160 records
   across both models). Additionally, the missing `num_predict` expansion for raw
   mode caused Qwen to hit a 512-token ceiling (2.5% accuracy, 81% extraction
   failures). Fixed by: (a) adding `num_predict` expansion to `generate_raw()`,
   (b) redesigning E to use `/api/chat` with scaffold as explicit context in the
   user message and thinking enabled. This tests scaffold + thinking synergy via
   context injection rather than prefill continuation — a different mechanism but
   the same contrast (E − (B + D − A)).

## Known Data Anomalies

### Gemma 4 E4B empty-thinking traces (15/1,236)

**Summary:** 15 of 1,236 Gemma 4 B-condition traces have empty thinking tokens
despite `think: true` being set. Qwen 3.5 has zero empty traces under identical
conditions. All 15 are correct answers to modular arithmetic questions.

**Root cause: model genuinely skips thinking, not a parser bug.** Verified by
comparing `eval_count` (total tokens generated by the model) between empty and
non-empty traces for the same question:

| Condition | eval_count | `thinking` key in API response | content chars |
|-----------|-----------|-------------------------------|---------------|
| Empty thinking (e.g. seed 1) | 552–806 | **absent** (not empty — missing) | 1,303–1,759 |
| Has thinking (e.g. seed 2) | 919–1,324 | present | 806–1,265 |

If Ollama's parser were silently dropping thinking content, eval_count would be
similar (model still generated the tokens). Instead, eval_count is 40–55% lower
for empty cases — the model produced fewer tokens total and never entered the
think phase. The `thinking` key is entirely absent from the API response (not
present-but-empty), confirming no thinking block was generated.

**Reproducibility:** 11/15 reproduce deterministically at the same seed. 4/15
produced thinking on re-run (seeds 4, 8 for some questions), consistent with a
sampling-path phenomenon at the boundary of the model's think/don't-think decision.

**Pattern:**
- All 15 are Gemma 4 only (0 from Qwen 3.5)
- All 15 are correct (15/15)
- All are modular arithmetic (7 `hard_modular_*`, 1 `modular_arithmetic_*`)
  plus 1 `math_system_of_equations_hard_*`
- Seed 1 accounts for 8/15 (all 8 affected questions have empty thinking at seed 1)
- Bimodal: 0 chars or 800+ chars thinking, nothing in between

**Interpretation:** The `<|think|>` token in Gemma 4's system prompt *enables*
thinking but does not *force* it. At certain sampling paths (determined by
seed × temperature interaction), the model bypasses the think phase entirely and
goes straight to answering. This is an emergent behavior — Google's documentation
describes thinking as a hard on/off toggle and does not mention the model electing
to skip it. The behavior may reflect E4B's smaller effective capacity (4.5B params)
making the think/don't-think boundary more sensitive to sampling randomness on
questions it finds trivial.

### Condition O truncation (fixed)

Condition O produces visible CoT in the content stream (not a separate thinking
channel). The default `num_predict=512` caused 69% extraction failures — reasoning
consumed all tokens before `FINAL:`. Fixed by setting `num_predict=4096` for
Condition O in `run_experiment.py`, matching the thinking-condition budget.

### Scaffold FINAL: tag causing immediate EOS (fixed)

GPT 5.4 scaffolds include `FINAL: <answer>` at the end (as instructed). When used
as prefill, the model sees a completed answer and emits immediate EOS (`eval_count=1`,
empty content). Fixed by adding `_strip_final_answer()` in `condition_builder.py`
for conditions D, E, H, and M — strips the `FINAL:` line before prefill, so the
model must generate its own answer after the reasoning.

### Condition E raw-mode thinking failure (fixed)

Condition E (scaffold + think) originally used raw `/api/generate` with assistant
prefill and `think: true`. Two bugs:

1. **Missing num_predict expansion** in `generate_raw()` — Qwen hit the 512-token
   ceiling (eval_count=500-512), causing 81% extraction failures and 2.5% accuracy.
   Fixed by adding the same `if think: num_predict = THINKING_NUM_PREDICT` logic
   that `chat()` already had.

2. **Raw mode doesn't support thinking** — Ollama's `/api/generate` with `raw: true`
   never generates thinking tokens even when `think: true` is set (0/160 records
   across both models). This made E functionally equivalent to D (scaffold prefill
   without thinking), defeating the synergy test.

**Fix:** Redesigned E to use `/api/chat` (where thinking works) with the scaffold
as explicit context in the user message. Updated `CONDITION_REGISTRY` to
`prefill: False`. This routes E through the chat endpoint where thinking tokens
are reliably generated. The scaffold is presented as "An expert provided the
following step-by-step reasoning..." rather than as assistant prefill. Post-fix
results show thinking tokens generated for both models.

### Qwen B-condition 8192-token truncation (Phase 2)

367/1030 (36%) Qwen B inferences hit the 8192 eval_count ceiling. All extraction
failures have eval_count=8192 — the model's verbose thinking (mean 13,704 chars,
max 32,283) consumes all tokens before generating FINAL:. Per-protocol accuracy
is 84.2% (vs 54.2% ITT). This confounds all B-involving contrasts for Qwen.

**Not fixed** — the 8192 cap is already 2x the original, and raising further would
proportionally increase inference time. Documented as a limitation. Analysis reports
both ITT and PP for all B-involving contrasts.

### Qwen N-condition collapse (Phase 3)

Condition N (deterministic thinking, temperature 0) produces 23.1% ITT accuracy
for Qwen vs 70.2% for Gemma. **Post-audit reframing:** The Qwen N-B comparison
is VOID — both arms are truncation-dominated (N: 64% extraction failure, B: 62%).
The ITT tie at 23.1% reflects shared context-window exhaustion, not a meaningful
mechanism comparison. PP (64.3% vs 60.4% ns) is post-treatment-selected and
uninformative. For Gemma, N ~ B (ns) — greedy decoding works fine.

### Strong-model compressed traces outperform raw traces (Phase 3)

Condition M outperforms L100 for both models: Gemma 73.4% vs 61.2%, Qwen 88.8%
vs 51.9%. **Post-audit reframing:** M traces were compressed by a strong external
model (GPT 5.4 / Sonnet), not just mechanically shortened. The M vs L100 finding
conflates trace authorship with compression — it tests "strong-model edited trace
vs raw self-trace," not pure compression. Evidence: Gemma M (73.4%) matches D
(72.3%, ns), and Qwen M (88.8%) approaches D (98.2%). The "compression premium"
claim is overclaimed; this is a "trace quality premium."

### Dose-response: Gemma weakly increasing, Qwen context-window pathology (Phase 3)

The L dose-response (25/50/75/100% of B-trace) shows divergent patterns. Gemma:
L25=50.0%, L50=48.7%, L75=52.9%, L100=61.2% (weakly increasing, within-phase
L100 > L25 by +11.2pp, p=.005). Qwen: L25=63.8%, L50=55.1%, L75=51.3%,
L100=51.9% (decreasing). **Post-audit reframing:** Qwen's decreasing pattern is
context-window exhaustion, not a cognitive effect. Qwen B-traces average ~6370
tokens; longer prefills consume more of the 8192 budget (ceiling hits: L25=39%,
L50=46%, L75=46%, L100=46%), leaving less room for FINAL:. The Gemma L25 < A
finding (-9.7pp, p_adj=.040) is suggestive that partial traces hurt, confirmed
within-phase (L25 < L100).

### Cross-model transfer: verbosity mismatch, not incompatibility (Phase 3)

Condition K shows crossover interaction: Gemma K=50.3% < C=61.5% (cross-model
hurts), Qwen K=67.9% > C=50.3% (cross-model helps). **Post-audit reframing:**
The reversal is mechanically explained by donor trace verbosity. Qwen K receives
short Gemma traces (~940 tokens) and ceiling hits drop from 46% to 16% — the
model finally has room to answer. Gemma K receives long Qwen traces (~6370 tokens)
and extraction failure rises from 2% to 14%. This is "trace length matters," not
"cross-model reasoning is incompatible."

## Phase 2 Tri-Agent Audit Findings (2026-04-12)

Full convergence across gpt-5.3-codex, gpt-5.4, and gemini-3.1-pro on all findings.
Audit reports: `outputs/audits/phase2-analysis/`.

### Implemented in analyze.py

1. **Per-model contrasts as primary** — pooled ORs demoted to secondary with
   Simpson's paradox warning. B-C, B-O reverse direction between models.
2. **ITT + PP dual reporting** — all contrasts report both. B-C flips from
   favoring C (ITT) to favoring B (PP) when truncation is removed.
3. **Two-part decomposition** — P(extract FINAL:) and P(correct|extracted)
   reported for all conditions with >1% extraction failure.
4. **Holm-Bonferroni correction** — 7 pairwise contrasts corrected per model.
   Most survive correction; Gemma D-C and B-I remain non-significant.
5. **Truncation flag** — B-involving contrasts marked [!TRUNC] in report.
6. **Direction reversal detection** — pooled contrasts flag when models disagree.

### Paper-stage (requires hierarchical model)

7. **Bayesian hierarchical logistic regression** — needed before any confirmatory
   claims. Question/seed clustering + model×condition interactions.
8. **Formal model×condition interaction tests** — per-model is primary, but
   formal interaction testing needed for cross-model generalization claims.
9. **Token-budget sensitivity analysis** — rerun B with higher cap or examine
   whether truncation correlates with question difficulty.
10. **Domain/difficulty heterogeneity** — check if effects vary by question type.
11. **Extraction robustness** — manual adjudication sample for borderline cases.

## Phase 3 Tri-Agent Audit Findings (2026-04-14)

Full convergence across gpt-5.3-codex, gpt-5.4, and gemini-3.1-pro on all findings.
Audit reports: `outputs/audits/phase3-analysis/`.

### Implemented in analyze_mechanism.py

1. **Cross-phase caveat strengthened** — Phase 2 references relabeled as "historical
   controls" with explicit Ollama version mismatch (0.20.2→0.20.6), differing rep
   counts (10 vs 8), and blank model digests. Only M-L100 and within-L contrasts
   are same-phase.
2. **Qwen L/N reframed as context-window pathology** — header caveat explains that
   Qwen's verbose B-traces (~6370 tokens) consume the 8192 budget when replayed
   as prefill. All Qwen L/N ITT results primarily reflect "room to answer."
3. **Qwen N-B explicitly voided** — marked [VOID: both arms truncation-dominated]
   in per-model contrasts. ITT tie at 23.1% reflects shared truncation, not mechanism.
4. **M trace-source confound documented** — M traces authored/edited by strong
   external model. "Compression premium" relabeled as "trace quality + compression."
5. **K-C relabeled from "Simpson's paradox" to "crossover interaction"** — reversal
   explained by donor trace verbosity mismatch, not cross-model incompatibility.
6. **Within-phase L pairwise contrasts added** — L100 vs L25 etc. with no cross-phase
   confound. Gemma L100 > L25 by +11.2pp (p=.005), Qwen L25 > L100 by -11.9pp
   (context-window effect).
7. **Dose-response power caveat** — Kendall tau on 4 points cannot reach p<.05.
   Trial-level mixed-effects models needed for power.

### Paper-stage

8. **Trial-level dose-response model** — mixed-effects logistic regression on all
   1248 observations per model with question random intercepts and dose as covariate.
9. **Seed-matched cross-phase sensitivity** — restrict Phase 2 to seeds 1-8 for
   matched comparison.
10. **Eval_count mediation analysis** — formal test that ceiling truncation mediates
    the Qwen L dose-response effect.
11. **Source-controlled M analysis** — compare M to a mechanically shortened trace
    (no strong-model editing) to isolate compression from authorship.

## Status

- [x] Initial design
- [x] Tri-model brainstorm session
- [x] Tri-model audit of plan
- [x] Plan v1.1 (post-audit revision)
- [x] Infrastructure: ollama_client.py, condition_builder.py, trace_bank.py, score.py
- [x] Infrastructure: run_experiment.py (CLI runner)
- [x] Question generators (math, logic, spatial, factual, hard)
- [x] Calibration pool generated (740+ questions)
- [x] Ollama upgrade (0.20.2) + Gemma 4 E4B download
- [x] Gemma 4 think-mode verification (confirmed working)
- [x] Model identification: Gemma 4 E4B (4.5B effective / 8.0B total, Q4_K_M)
- [x] Tri-agent audit on infrastructure code (3 rounds: infra, validation, fixes)
- [x] Phase 1 calibration (A × 12 reps × 2 models)
- [x] Calibration analysis + item locking (103 items, Qwen 59%, Gemma 51%)
- [x] Validation scripts (analysis/validate.py, scripts/run-validation.sh)
- [x] Audit fixes: BPE token counting, Condition I protocol, Condition N, G provenance
- [x] Trace bank generation (2,472/2,472 complete)
- [x] Phase 1 validation (B/C/F/O × 4 reps × 20 items — 18/18 checks passed)
- [x] Phase 1 smoke tests: I/G/J × 4 reps × 20 items (scaffold-independent)
- [x] Scaffold generation (GPT 5.4 via Codex CLI, 103/103 questions)
- [x] Phase 1 smoke tests: D/E/H × 4 reps × 20 items (scaffold-dependent)
- [x] Fix Condition E: num_predict expansion + chat-mode redesign (was 2.5% acc → fixed)
- [x] Phase 2 confirmatory execution (complete — outputs/confirmatory/20260408_100418/)
- [x] Phase 2 analysis (outputs/results/phase2/)
- [x] Upgrade Ollama to v0.20.6
- [x] Phase 3 mechanism deep-dive (complete — outputs/mechanism/20260412_215554/)
- [x] Phase 3 analysis (outputs/results/phase3/, post-audit revision)
- [x] Phase 3 tri-agent audit (outputs/audits/phase3-analysis/, full convergence)
- [ ] Analysis + paper
