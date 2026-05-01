# Replay Recoverability of Thinking-Token Benefits in Small Language Models

Companion repository for the paper of the same name. Contains the manuscript, all per-inference data, the question and scaffold banks, the experiment runner, the analysis code, and all audit reports.

**Author:** James Fowler
**Latest revision:** 2026-04-25 (post-audit)
**Manuscript:** [`paper/paper.md`](paper/paper.md)

## TL;DR

Tested whether "thinking tokens" (Qwen reasoning channel, Gemma `<think>` tag) provide value beyond what trace-replay-as-context recovers. Two small open models (Qwen 3.5 9B, Gemma 4 E4B), 11 conditions, 103 questions × 10 reps × 2 models = 22,660 inferences, plus a Phase 3 mechanism dive (~4.4k inferences) and a 16K-budget rescue rerun on Qwen-B ceiling-hit cases.

After seven audit rounds the surviving claims are substantially narrower than the pre-registered analysis would have implied. The most consequential finding for downstream practitioners is that on these two small models at an adequate budget with a fair scorer, trace replay matches or beats live thinking on the population-averaged estimand for both models — with per-domain heterogeneity (Gemma live thinking helps numeric reasoning; both models prefer trace replay on object/spatial tracking, partly mediated by truncation for Qwen).

## Why this repository exists

The paper has been through an unusually long audit chain (see §3.8–§3.15 of the manuscript and `outputs/audits/`). Several headline claims from the pre-registered analysis were retracted or substantially revised after scoring-pipeline bugs were discovered post-hoc. Publishing the full per-inference logs and the scoring code lets independent reviewers re-run any claim under any scoring regime. This is the point of the repo.

## Repository layout

```
paper/paper.md                       The manuscript.

ERRATA.md                            Issues found post-release and how each is addressed.

questions/
  selected.jsonl                     103 locked Phase 2 items with ground truth and answer_type.
  phase3-subset.jsonl                39 items used for Phase 3 mechanism deep-dive.
  calibration-pool.jsonl             740+ candidate items from procedural generators.
  generators/                        The procedural generators (math, logic, spatial, factual, hard).
  scaffolds/                         Per-question GPT-5.4 expert scaffolds, plus wrong_scaffold and compressed variants.

runner/
  run_experiment.py                  Main experiment loop (CLI: --phase calibration|validation|confirmatory|mechanism).
  ollama_client.py                   Ollama API wrapper with per-inference JSONL logging.
  condition_builder.py               Prompt construction for each condition (A through O, plus L25/L50/L75/L100).
  trace_bank.py                      B-trace bank management.
  score.py                           Answer extraction and grading. NOTE: paper §3.8/§3.10 and ERRATA.md
                                     document three bugs in this file (chat-template token leakage,
                                     missing Box N / Cup X aliasing, period-truncation in the
                                     "answer is" fallback). The scorer is shipped as-is for historical
                                     fidelity; reproductions of paper §3.10+ should use
                                     `analysis/full_correction.py`.

analysis/
  calibrate.py                       Phase 1 calibration analysis + item selection.
  validate.py                        Validation analysis: sanity checks, per-condition accuracy.
  analyze.py                         Pre-registered Phase 2 analysis: per-condition accuracy and marginal
                                     Haldane ORs with Wald CIs (descriptive ITT/PP tables only —
                                     it explicitly does NOT do GEE). Treats observations as independent.
  analyze_hierarchical.py            **Primary GEE analysis (paper Table 2 / §3.2 / §3.3).** Per-model
                                     GEE Binomial/Logit with question-clustered exchangeable working
                                     correlation and robust sandwich SEs; two-part hurdle decomposition;
                                     Holm-Bonferroni; trial-level dose-response. Imports loaders from
                                     analyze.py and analyze_mechanism.py.
  analyze_mechanism.py               Phase 3 mechanism analysis (K, L25/L50/L75/L100, M, N).
  full_correction.py                 **Full-correction analysis (paper §3.10, §3.13, §3.14, §3.15).**
                                     Applies all three scoring fixes documented in ERRATA, then re-runs
                                     the GEE contrasts under the corrected scorer, with question-family
                                     decomposition and cluster-robustness sensitivity.

scripts/
  merge_16k_rerun.py                 Reconstructs the 16K-merged Phase 2 dataset from the original
                                     Phase 2 log + the 16K-rerun log. Reproduces
                                     outputs/confirmatory_merged/20260415/inference_log.jsonl.gz.

outputs/
  osf-preregistration.md             Pre-registration text (committed to OSF before first inference).

  confirmatory/
    20260408_080415_inference_log.jsonl.gz    Phase 2 partial run (early seeds).
    20260408_100418_inference_log.jsonl.gz    Phase 2 full run (Ollama 0.20.2). Original raw data.

  confirmatory_16k/
    20260414_192703_qwen_b_rerun/
      inference_log.jsonl.gz                  16K-budget rerun of 368 Qwen-B ceiling-hit cases (Ollama 0.20.6).

  confirmatory_merged/
    20260415/
      inference_log.jsonl.gz                  Phase 2 merged dataset: original Phase 2 with the 368 Qwen-B
                                              ceiling-hit rows replaced by their 16K continuations. Used for
                                              all "16K-merged" analyses in the paper.

  mechanism/
    20260412_215554/
      inference_log.jsonl.gz                  Phase 3 mechanism conditions (K, L25/L50/L75/L100, M, N) under
                                              Ollama 0.20.6.

  trace_bank/
    trace_bank.jsonl                          Frozen B-condition traces used as prefill for C/F/G/J derivation.

  audits/
    paper-audit-20260415/                     2026-04-15 scoring-pipeline audit (gpt-5.3-codex + gpt-5.4).
                                              Found Box/Cup format drift and chat-template token leakage.
    paper-followup-20260425/                  2026-04-25 morning Sonnet-class follow-up.
                                              Closed deferred items, recovered Gemma numeric subgroup signal.
    gpt55-audit-20260425/                     2026-04-25 evening four-angle GPT-5.5 xhigh audit.
                                              Downgraded Claim 8, sharpened Claims 1/2/3/7, found 367→368
                                              provenance off-by-one.

PROJECT_NOTES.md                     Original project notes (was CLAUDE.md in the dev repo). Includes
                                     condition design rationale, deviations from the pre-reg, and known
                                     data anomalies.

RUN_MANIFEST.md                      Per-data-collection-run provenance: model digests, Ollama versions,
                                     row counts, file paths.
```

## Reading the data

All `inference_log.jsonl.gz` files are gzipped line-delimited JSON. Each line is one inference record. Schema:

```python
{
  "inference_id": str,                # 8-char hex
  "model_tag": str,                   # "qwen3.5:9b" or "gemma4"
  "model_digest": str,                # often blank (pre-registration gap)
  "quantization": str,                # "Q4_K_M"
  "ollama_version": str,              # "0.20.2" (Phase 2) or "0.20.6" (Phase 3 + 16K rerun)
  "condition": str,                   # "A" through "O", "L25"/"L50"/"L75"/"L100", "I_sub"
  "question_id": str,
  "rep_number": int,
  "seed": int,
  "think": bool,                      # whether think mode was enabled
  "prompt_eval_count": int,           # input tokens
  "eval_count": int,                  # generated tokens (incl. thinking_tokens)
  "total_duration": int,              # nanoseconds
  "load_duration": int,
  "prompt_eval_duration": int,
  "eval_duration": int,
  "raw_prompt": str,                  # full chat-messages JSON or raw prompt string
  "raw_response": str,                # full Ollama API response JSON
  "thinking_tokens": str,             # B/E only; visible-channel-equivalent of the hidden think
  "content": str,                     # visible content stream (post-thinking)
  "extracted_answer": str,            # output of score.extract_answer()
  "ground_truth": str,
  "correct": bool,                    # output of score.grade(extracted, ground_truth, answer_type)
  "extraction_failed": bool,
  "source_trace_id": str,             # for C/F/G/J/L conditions; the parent B-trace
  "source_trace_correct": bool|None,
  "parent_inference_id": str,
  "error": str,
  "timestamp": str
}
```

Quick load:

```python
import gzip, json
records = []
with gzip.open("outputs/confirmatory_merged/20260415/inference_log.jsonl.gz", "rt") as f:
    for line in f:
        records.append(json.loads(line))
```

## Reproducing the paper's contrasts

The paper's analyses are run on the **merged** dataset
(`outputs/confirmatory_merged/20260415/inference_log.jsonl.gz`). All analysis
scripts now handle `.jsonl.gz` transparently (see [`ERRATA.md`](ERRATA.md) E-4).

```bash
# Pre-registered analysis (Haldane marginal ORs, descriptive)
python analysis/analyze.py \
    --log outputs/confirmatory_merged/20260415/inference_log.jsonl.gz \
    --output-dir outputs/results/phase2/

# Primary GEE analysis (paper Table 2, §3.2, §3.3)
python analysis/analyze_hierarchical.py \
    --phase2-log outputs/confirmatory_merged/20260415/inference_log.jsonl.gz \
    --mechanism-log outputs/mechanism/20260412_215554/inference_log.jsonl.gz \
    --phase3-questions questions/phase3-subset.jsonl \
    --output-dir outputs/results/hierarchical/

# Full-correction analysis (paper §3.10, §3.13, §3.14, §3.15)
python analysis/full_correction.py \
    --merged-log outputs/confirmatory_merged/20260415/inference_log.jsonl.gz \
    --questions questions/selected.jsonl \
    --output-dir outputs/results/full_correction/

# Phase 3 mechanism analysis
python analysis/analyze_mechanism.py \
    --log outputs/mechanism/20260412_215554/inference_log.jsonl.gz \
    --questions questions/phase3-subset.jsonl \
    --output-dir outputs/results/phase3/

# Reconstruct the merged dataset from raw inputs
python scripts/merge_16k_rerun.py \
    --original outputs/confirmatory/20260408_100418_inference_log.jsonl.gz \
    --rerun outputs/confirmatory_16k/20260414_192703_qwen_b_rerun/inference_log.jsonl.gz \
    --output /tmp/reconstructed_merged.jsonl.gz
```

To reproduce a specific Robust Claim or sensitivity, the paper's §3.x sections
cite the relevant subset, scoring regime, and contrast specification.

## Known scorer issues (carried into the data)

`runner/score.py` as shipped has three documented issues that affect every
cell scored under it. All three are documented in [`ERRATA.md`](ERRATA.md)
and patched in `analysis/full_correction.py`:

1. **Chat-template token leakage.** `extract_answer()` does not strip
   `<end_of_turn>` (Gemma) or `<|endoftext|>`/`<|im_start|>user` (Qwen)
   before string-match. Affects 206/1030 Gemma-D rows and 80/1030 Qwen-C
   rows most prominently.

2. **No structured-label aliasing.** `grade()` does exact string equality
   for `answer_type: "exact"`. The benchmark contains 22/52 exact-answer
   items whose ground truth is `"Box N"` or `"Cup X"`; both models
   intermittently emit bare `"N"` answers. Affects Gemma rows broadly
   (+27 to +86 rescues per cell), Qwen modestly.

3. **Period-truncation in the "answer is" fallback regex.** The fallback
   regex `(?:the answer is|...)\s*(.+?)(?:\.|$)` is non-greedy and stops
   at any period, so `"the answer is 25.92"` extracts `"25"`. Affects
   ~48/39,550 records (0.12%), almost all profit-loss decimal answers.

The shipped scorer is preserved as the historical artifact;
`analysis/full_correction.py` applies all three fixes via
`strip_templates`, `canonical_match`, and `extract_answer_fixed`.

## License

MIT. See [`LICENSE`](LICENSE). The MIT license covers code, data, and the manuscript text. Citation appreciated but not required.

## Citation

If you use any of this:

```
Fowler, J. (2026). Replay Recoverability of Thinking-Token Benefits in Small Language Models.
github.com/JfowlerSIAI/thinking-token-replay-recoverability
```

## Status

This is a research artifact, not a maintained library. The scoring-pipeline bugs documented above are *deliberately not patched* in the shipped code so that the published data remains reproducible against the published `score.py`. A clean replication should patch the scorer per §3.15 of the paper, re-collect under a known Ollama version, and pre-register family-stratified contrasts.
