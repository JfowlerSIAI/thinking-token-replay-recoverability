# Errata and known issues

This file tracks issues found *after* the public release of this repository.
The original commit is preserved as the reproducibility artifact; fixes and
patches live in subsequent commits and in the dedicated full-correction
pipeline (`analysis/full_correction.py`).

## High-severity (audit findings, all addressed in commit history)

### E-1: README originally pointed at `analysis/analyze.py` for GEE; that script does Haldane marginal ORs only

`analysis/analyze.py` computes per-condition accuracies, marginal Haldane
odds ratios with Wald CIs, and a paper-stage TODO note saying hierarchical
modeling is required. The actual GEE / Binomial-Logit / exchangeable
working-correlation / question-clustered analyses that the paper's Robust
Claims rely on are in `analysis/analyze_hierarchical.py`. The README has
been updated to point at the right script.

The full-correction analyses (paper §3.10–§3.15) are now in
`analysis/full_correction.py` (added in the audit-response commit).

### E-2: Full-correction scorer was not committed

The paper's full-correction scoring (template-strip + structured-label
canonicalization) is implemented in `analysis/full_correction.py`, added in
the audit-response commit. The shipped `runner/score.py` is preserved as the
historical scorer; reproductions of paper §3.10 onward should use
`full_correction.py`. Three fixes are bundled there:

  1. `strip_templates()` — removes `<end_of_turn>`, `<|endoftext|>`,
     `<|im_start|>user`, etc. from the visible content stream before
     extraction (see paper §3.8 / §3.9).
  2. `canonical_match()` — accepts bare suffix as a match for `Box N` /
     `Cup X` ground truths (see paper §3.10).
  3. `extract_answer_fixed()` — fixes the regex period-truncation bug in
     the `answer_is` fallback (see E-3 below).

### E-3: `score.py` `answer_is` fallback truncates at any period

In `runner/score.py:33-40`, the regex
`(?:the answer is|answer:|therefore,? the answer is)\s*(.+?)(?:\.|$)` is
non-greedy and stops at the first `.` character. So `"the answer is 25.92"`
extracts `"25"` not `"25.92"`. This fallback only fires when the primary
`FINAL:` regex misses, which happens for ~536/39,550 records (1.4%) on the
merged Phase 2 dataset; of those, the period-truncation bug changes the
extraction in 48 records (0.12% of all records). Almost all are profit-loss
decimal answers.

The bug is not patched in `runner/score.py` to preserve the historical
scorer. The fixed extraction is implemented in
`analysis/full_correction.py` (`extract_answer_fixed`).

### E-4: Analysis loaders did not handle `.jsonl.gz`

The published data ships gzipped to fit GitHub's per-file size limit, but
the original loaders in `analysis/analyze.py` and `analysis/analyze_mechanism.py`
used plain `open()`. Both have been patched to handle `.jsonl.gz` transparently
via a `_open_log()` helper. `analysis/full_correction.py` and
`scripts/merge_16k_rerun.py` both natively handle `.gz`.

### E-5: 367 vs 368 rerun-row off-by-one

The original `RUN_MANIFEST.md` listed 367 Qwen-B rerun records; the actual
JSONL contains 368 (one row per ceiling-hit Qwen-B Phase 2 inference). The
paper's §3.15-K already documents this; `RUN_MANIFEST.md` has now been
fixed in the audit-response commit. All paper text uses 368.

### E-6: Merge script was not committed

`RUN_MANIFEST.md` referenced `scripts/merge_16k_rerun.py` but that script
was not committed in the original release. It is now committed at exactly
that path. Running it on the published `outputs/confirmatory/` and
`outputs/confirmatory_16k/` inputs reconstructs
`outputs/confirmatory_merged/20260415/inference_log.jsonl.gz` byte-for-byte
in record content (39,550 rows; 368 ceiling-hit Qwen-B rows replaced by
their 16K-rerun counterparts).

## Medium-severity (carried into the data; documented but not fixed)

### M-1: Endpoint asymmetry between B and C

Condition B uses Ollama's `/api/chat` endpoint with `think=true`. Condition C
uses `/api/generate` with `raw=true` and a manually-rendered chat template
because `/api/chat` did not reliably produce a continuation after an
assistant prefill. The B−C contrast is therefore not just "live thinking
vs trace replay" — it is also "chat-rendered think-mode generation vs
raw-generate assistant-prefill continuation."

This is a known design constraint of the Ollama-based experiment runner
and is not separable from the data as collected. A clean replication would
add an `A_raw` (no-think raw-generate baseline) or `C_chat` (assistant-prefill
via /api/chat with empty think) control to identify the endpoint contribution.

This caveat is added to the paper's §7 limitations in the audit-response
revision.

### M-2: Question independence is weaker than 103 implies

The 103 `selected.jsonl` items come from ~26 procedural-generator templates
(e.g., `compound_percentage_*`, `hard_tracking_*`, `long_object_tracking_*`).
Several "questions" are textually near-identical (especially in the math
generators). Question-level clustering treats them as independent, which
under-estimates uncertainty.

Mitigation: `analysis/full_correction.py` includes template-clustering as a
sensitivity (the §3.15-A Claim-8 fragility analysis already uses it). The
paper's Robust Claims are stable under template-clustering except for
Claim 8 (Gemma B−O), which is downgraded to exploratory-confirmatory
explicitly in §4 and §3.15-A. A clean replication should pre-register
template-clustering as the primary unit.

### M-3: Condition G "wrong-question" trace selection is loose

`runner/trace_bank.py` selects G traces by different `question_id`, same
domain, token-count tolerance, and crude word-overlap heuristics. With
templated questions, a G trace can be structurally close to the true trace
or even answer-compatible. Paper §4 Claim 6 ("generic reasoning shape has
value") inherits this caveat: the G−F effect is partly a "different but
structurally similar trace" effect, not a pure "wrong reasoning" effect.

### M-4: `shuffle_tokens` (Condition F) is not bijective

`shuffle_tokens()` shuffles BPE tokens then decodes/re-encodes; this is
not bijective and can change token count by a few percent. Paper §7
already notes the BPE-vs-native-tokenizer drift; this is a related
sub-issue. C−F remains a useful corruption contrast but is not a clean
"identical token length" control.

### M-5: Pre-registration says retry-up-to-3 on errors; runner does not retry

`runner/ollama_client.py` catches request errors and returns an error
result; `run_single_inference` then logs and scores it (typically as
extraction-failed). Pre-registration says failed inferences are retried
up to 3 times. This is a deviation; the impact depends on how many
errors actually occurred. Spot-check shows error counts are very low
(<0.1% of records), so the impact on claim numbers is minimal, but it
should be acknowledged.

### M-6: Per-inference provenance is incomplete

The pre-registration says generation parameters and model digests are
logged per inference. In practice, `model_digest` is blank in the published
logs and generation options were reconstructed from code, not logged. This
blocks bit-exact reproducibility and makes Ollama-version drift harder to
audit. `RUN_MANIFEST.md` documents this. A clean replication should log
both fields.

### M-7: 16K rerun is a sensitivity, not a clean counterfactual

Only Qwen-B ceiling-hit rows were rerun; selection is post-treatment;
rerun used a different Ollama version. This is acknowledged in paper
§2.7 and §7. Some headline phrasing in earlier paper drafts risked
over-interpretation; the current text in §4 Claim 7 reframes the
merged-dataset estimand as "adaptive Qwen-B rescue policy at 8K with 16K
rerun on ceiling-hit" rather than "Qwen-B at 16K."

## Verification

```bash
# Reproduce the paper's full-correction Table 2 / §3.13 / §3.15-A numbers:
python analysis/full_correction.py \
    --merged-log outputs/confirmatory_merged/20260415/inference_log.jsonl.gz \
    --questions questions/selected.jsonl \
    --output-dir outputs/results/full_correction/

# Reconstruct the merged dataset from the original Phase 2 + 16K rerun:
python scripts/merge_16k_rerun.py \
    --original outputs/confirmatory/20260408_100418_inference_log.jsonl.gz \
    --rerun outputs/confirmatory_16k/20260414_192703_qwen_b_rerun/inference_log.jsonl.gz \
    --output /tmp/reconstructed_merged.jsonl.gz

# The pre-registered analysis (Haldane marginal ORs):
python analysis/analyze.py \
    --log outputs/confirmatory_merged/20260415/inference_log.jsonl.gz \
    --output-dir outputs/results/phase2/

# The hierarchical/GEE primary analysis (paper Table 2):
python analysis/analyze_hierarchical.py \
    --phase2-log outputs/confirmatory_merged/20260415/inference_log.jsonl.gz \
    --mechanism-log outputs/mechanism/20260412_215554/inference_log.jsonl.gz \
    --phase3-questions questions/phase3-subset.jsonl \
    --output-dir outputs/results/hierarchical/
```
