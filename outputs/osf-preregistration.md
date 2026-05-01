# OSF Pre-registration: Thinking Token Experiment

**Template:** OSF Preregistration (Standard)

---

## Study Information

### Title

Replay Recoverability of Thinking-Token Benefits in Small Language Models: A Mechanistic Case Study

### Description

When small language models use "thinking tokens" — chain-of-thought reasoning tokens generated in a dedicated thinking phase before the final answer — they often perform better on reasoning tasks. This experiment decomposes the sources of that improvement through 15 conditions that systematically vary thinking mode, reasoning content, reasoning quality, reasoning source, and raw token count. Two local models (Qwen 3.5 9B and Gemma 4 E4B) are tested on 103 calibrated questions spanning math, logical deduction, factual MCQ, and spatial/pattern domains.

The core question is **replay recoverability**: how much of think-mode's benefit can be recovered by replaying the visible reasoning trace as context, without engaging the model's thinking mechanism? This framing acknowledges that replaying a trace as context is not identical to the model's internal thinking state — the estimand is recovery, not replication.

### Contributors

James Fowler

### Hypotheses

**8 Pre-registered Confirmatory Contrasts** (each tested directionally on the log-odds scale):

1. **B − C > 0 (Internal-reasoning effect):** Thinking mode provides benefit beyond what replaying the visible trace as context achieves. The thinking mechanism contributes something that the visible trace alone does not capture.

2. **C − F > 0 (Rationale-content effect):** The semantic content of reasoning traces matters — coherent self-reasoning as context improves accuracy more than shuffled tokens of identical length.

3. **G − F > 0 (Generic reasoning-shape effect):** Reasoning-shaped text from a different question helps more than shuffled tokens, even though the reasoning is for the wrong problem. Tests whether structured reasoning has generic value.

4. **D − C > 0 (Expert-scaffold premium):** Expert-quality reasoning (from GPT 5.4) as context improves accuracy more than the model's own reasoning trace.

5. **E − (B + D − A) > 0 on log-odds (Synergy):** Combining thinking mode with expert scaffold context produces super-additive improvement — the benefits compound rather than merely adding.

6. **B − I > 0 (Compute-allocation):** Thinking mode is more effective than spending the same token budget on multiple independent no-think attempts with majority voting (self-consistency).

7. **B − O > 0 (Think-mode vs visible-CoT):** Native think-mode outperforms explicit chain-of-thought prompting ("Think step by step...") without the thinking mechanism enabled.

8. **C − J > 0 (Semantic reasoning vs filler):** Reasoning content as context improves accuracy more than semantically neutral filler text of identical length.

**Equivalence test:** Two one-sided tests (TOST) on B − C with SESOI defined as odds ratio 0.85–1.18 (approximately ±3 percentage points at 50% baseline, specified on the log-odds scale). If B − C falls within this interval, we claim practical equivalence of thinking mode and trace replay.

**Direction of expected effects:** We expect B > A (thinking helps), C > F > J ≈ A (semantic reasoning content drives improvement, not token count), D > C (expert reasoning is better than self-reasoning), and B ≈ C or B > C (replay recovery is substantial but possibly incomplete).

---

## Design Plan

### Study Type

Computational experiment — systematic evaluation of language model inference conditions. No human participants are involved; the "subjects" are model inference instances.

### Blinding

Automated execution with no researcher-in-the-loop during data collection. Seed assignment is fixed and deterministic. Answer extraction and scoring are automated via regex pattern matching with an intention-to-treat (ITT) principle: extraction failures are scored as incorrect. The analysis pipeline runs on logged data without manual intervention.

### Study Design

**Within-subject fully-crossed design.** Each of 103 locked questions is tested under all 11 primary conditions (A–J, O) with 8–12 replications per condition per question per model, using both Qwen 3.5 9B and Gemma 4 E4B.

**Models under test:**

| Property | Qwen 3.5 | Gemma 4 E4B |
|----------|----------|-------------|
| Ollama tag | `qwen3.5:9b` | `gemma4:latest` |
| Architecture | qwen35 (dense) | gemma4 (Per-Layer Embeddings / PLE) |
| Total parameters | 9.7B | 8.0B |
| Effective parameters | 9.7B | 4.5B |
| Quantization | Q4_K_M | Q4_K_M |
| Ollama digest | (locked before Phase 2) | c6eb396dbd59 |

**Asymmetry note:** Gemma 4 E4B uses Per-Layer Embeddings, reducing active compute to ~4.5B effective parameters per forward pass vs Qwen's full 9.7B dense parameters. This asymmetry is a limitation for cross-model comparisons, but the primary contrasts are within-model.

**Primary Conditions (11):**

| ID | Name | Thinking | Extra Context | Key Contrast |
|----|------|----------|---------------|--------------|
| A | Baseline | Off | None | — |
| B | Standard thinking | On | None | B−A: total think effect |
| C | Self-trace replay | Off | B's thinking tokens (prefill) | B−C: internal reasoning effect |
| D | Expert scaffold | Off | GPT 5.4 reasoning (prefill) | D−C: expert premium |
| E | Thinking + scaffold | On | GPT 5.4 scaffold (context + think) | Synergy test |
| F | Shuffled tokens | Off | Shuffled B tokens (prefill) | C−F: semantic content effect |
| G | Wrong-question trace | Off | B from different question (prefill) | G−F: reasoning shape effect |
| H | Wrong scaffold | Off | Minimally-wrong GPT 5.4 (prefill) | Suggestibility test |
| I | Token-matched SC | Off | k no-think attempts, majority vote | B−I: think vs compute |
| J | Filler tokens | Off | Neutral filler (prefill) | C−J: reasoning vs filler |
| O | Visible-CoT | Off | None (prompted CoT) | B−O: think-mode vs explicit CoT |

**Implementation notes:**
- Conditions C/D/F/G/H/J use assistant prefill via Ollama's `/api/generate` raw mode
- Condition E uses `/api/chat` with scaffold as explicit context in the user message and `think=true` (see Deviations section)
- Conditions A/B/I/N/O use Ollama's `/api/chat` endpoint
- All prefill conditions share identical template structure per model

### Randomization

- Fixed seed grid: seeds 1–12, paired 1:1 with replications
- Temperature: 0.7 (stochastic regime)
- KV cache cleared between every inference (`keep_alive: 0`)
- Trace bank pairing: each C/F/G/J replicate r uses the B-trace from seed r (deterministic 1:1 mapping)

---

## Sampling Plan

### Existing Data

**Registration prior to collection of Phase 2 data.** Phase 1 pilot data has been collected for calibration and infrastructure validation purposes:
- Calibration: Condition A × 12 reps × 103 questions × 2 models (used to lock question set)
- Trace bank: Condition B × 12 seeds × 103 questions × 2 models (2,472 traces, frozen)
- Validation: Conditions B/C/F/O × 4 reps × 20 questions × 2 models
- Smoke tests: All 11 primary conditions × 4 reps × 20 questions × 2 models

Phase 1 data informed question selection and rep count determination. No Phase 2 confirmatory inferences have been run at the time of pre-registration.

### Data Collection Procedures

All inferences are run locally via Ollama (version 0.20.2+) on a single GPU. Each inference call logs: model tag, model digest, Ollama version, condition label, question ID, replication number, seed, full prompt, raw API response, thinking tokens, content, answer extraction result, correctness, token counts (prompt_eval_count, eval_count), timing data (total_duration, eval_duration), and all generation parameters.

Data is logged as append-only JSONL files with one record per inference.

### Sample Size

- 103 locked questions × 11 primary conditions × 8–12 reps × 2 models
- Condition I: each cell requires k ≈ 3–7 sub-inferences (token-budget-matched to B), so ~3,200 cells × ~5 mean sub-inferences = ~16,000 additional inferences
- **Total: approximately 34,000–48,000 model inferences** (exact count depends on final rep count)

### Sample Size Rationale

Rep count determined by Phase 1 variance component estimation and simulation-based power analysis. Target: 80% power to detect the SESOI (OR 0.85–1.18) for the B−C equivalence test, and 80% power to detect a 5 percentage-point accuracy difference for the directional contrasts, at the Holm-corrected alpha level.

### Stopping Rule

Data collection ends when all 103 questions × 11 conditions × target reps × 2 models have been completed. No interim analysis or early stopping.

---

## Variables

### Manipulated Variables

1. **Condition** (11 levels: A–J, O): The primary experimental manipulation, varying thinking mode, reasoning context type, and reasoning quality.
2. **Model** (2 levels: Qwen 3.5 9B, Gemma 4 E4B): Between-architecture comparison.
3. **Seed** (12 levels: fixed grid 1–12): Controls stochastic variation across replications.

### Measured Variables

1. **Accuracy** (binary: correct/incorrect): Primary outcome. Answer extracted via regex pattern matching on `FINAL:` tag. ITT principle: extraction failures scored as incorrect.
2. **eval_count** (integer): Total tokens generated by the model per inference.
3. **prompt_eval_count** (integer): Tokens evaluated in the prompt (includes prefill).
4. **Thinking token count** (integer): BPE tokens in the thinking phase (via cl100k_base).
5. **Content token count** (integer): BPE tokens in the answer content.
6. **Extraction method** (categorical): How the answer was extracted (regex_final, regex_answer, failed).
7. **Wall-clock time** (milliseconds): total_duration, eval_duration, prompt_eval_duration.

### Indices

- **Accuracy per 1,000 total evaluated tokens**: Primary efficiency metric.
- **Condition I voted accuracy**: Majority vote across k sub-inferences per cell.
- **Answer entropy**: Normalized entropy of extracted answers across reps for a single question-condition-model cell.

---

## Analysis Plan

### Statistical Models

**Primary model:** Bayesian hierarchical logistic regression.

```
correct ~ condition + model + task_type + condition:model + condition:task_type
        + (1 | question_id)
```

Random intercept by question captures item difficulty variation. Fixed-effect interactions capture condition × model and condition × task_type patterns.

**Implementation:** `brms` (R) or `bambi` (Python) with default weakly informative priors. Report posterior means, 95% credible intervals, and posterior probability for each directional contrast (e.g., P(B > C)).

**Design rationale:**
- `trace_length_z` excluded from primary model: it is a post-treatment variable (trace length is caused by condition), so including it would bias the contrasts being tested. Moved to exploratory mediation analysis.
- `(1 | seed)` excluded: seeds are unique per run, making this effect unidentifiable.
- Random slopes `(1 + condition | question_id)` excluded from primary model due to convergence risk with 11 conditions × 103 items. Estimated in separate exploratory per-contrast models.

### Transformations

All contrasts computed on the log-odds scale (natural scale of the logistic regression). Marginal means extracted via `emmeans` (R) or equivalent.

### Inference Criteria

- **Directional contrasts (#1–#8):** Holm correction across all 8 contrasts. Report both Bayesian posterior probability P(contrast > 0) and frequentist Holm-adjusted p-values. Declare significance at Bayesian P > 0.975 (equivalent to two-sided α = 0.05) or Holm-adjusted p < 0.05.
- **Equivalence test (B−C):** TOST with SESOI OR 0.85–1.18. Declare practical equivalence if both one-sided tests reject at α = 0.05.
- **Secondary estimand families:** Per-model and per-task-type contrasts, each separately Holm-corrected within their family.

### Data Exclusion

**No data exclusion for the primary analysis.** ITT principle: all inferences are included regardless of extraction success. Extraction failures are scored as incorrect.

**Sensitivity analysis:** Re-run primary model excluding extraction failures. Report whether conclusions change.

### Missing Data

No missing data expected — every cell in the design matrix will have the target number of inferences. If an inference fails due to timeout or API error, it is re-run with the same seed until successful or exhausts 3 retries (then scored as incorrect).

### Exploratory Analysis (not pre-registered as confirmatory)

- Condition × task_type deep-dive interactions
- Backtracking/error-correction frequency in B traces vs correctness
- Trace-length mediation analysis (causal mediation)
- Source-trace quality moderation (does C's benefit depend on whether the source B trace was correct?)
- Random-slope variance estimation per contrast
- Attention-displacement analysis (do long scaffolds hurt on short-answer questions?)

---

## Other

### Deviations from Original Protocol

Documented deviations from the original experiment plan (v1.1):

1. **Condition N:** Implemented as deterministic thinking (temperature 0, greedy decoding) instead of empty-trace think mode. Ollama has no reliable mechanism to force an empty thinking trace.

2. **Token counting:** Uses cl100k_base (tiktoken) as a consistent BPE proxy across both models, rather than model-native tokenizers. Produces counts within ~10% of native tokenizers.

3. **Condition I tie-break:** Lexicographic only (not logprob-then-lexicographic). Ollama does not reliably expose per-token logprobs for chat completions.

4. **Question pool:** 103 items from 740+ candidates (not 120–160 from 260). Additional hard generators were needed; stricter calibration yielded 103 in-band for both models.

5. **Condition E:** Uses `/api/chat` with scaffold as explicit context in the user message (not raw-mode assistant prefill). Ollama's raw `/api/generate` mode does not support thinking token generation. The scaffold is presented as "An expert provided the following step-by-step reasoning..." The synergy contrast E − (B + D − A) remains valid.

6. **Scaffold source:** GPT 5.4 via Codex CLI at medium reasoning effort (not Claude Sonnet 4.6 as originally planned). Produces comparable quality expert reasoning.

### Phase 1 Pilot Results (informing but not constraining Phase 2)

Calibration accuracy: Qwen 59%, Gemma 51% (mean across 103 selected items in Condition A).

Smoke test condition-level accuracy (20-item subset, 4 reps, pooled across models — informative, not confirmatory):
- A (baseline): ~55%, B (thinking): ~63%, C (self-trace): ~56%, D (expert scaffold): ~92%, E (scaffold + think): ~87%, F (shuffled): ~14%, G (wrong-question): ~19%, H (wrong scaffold): ~51%, I (self-consistency): ~86%, J (filler): ~29%, O (visible-CoT): ~78%

### Known Data Anomalies

- **Gemma 4 empty-thinking traces:** 15/1,236 B-condition traces have empty thinking tokens despite `think: true`. All are correct answers to modular arithmetic questions. Root cause: model genuinely skips thinking at certain sampling paths. These traces are flagged but not excluded.

### Reproducibility

All code, data, generation parameters, model digests, and raw inference logs will be published alongside the paper. The experiment runs entirely on local hardware via Ollama with fixed seeds, enabling exact reproduction.
