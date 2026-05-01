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
  score.py                           Answer extraction and grading. NOTE: §3.8/§3.10 of the paper document
                                     two scoring-pipeline bugs in this file (chat-template token leakage and
                                     missing structured-label aliasing). The scorer is shipped as-is for
                                     historical fidelity; reproductions should patch it per §3.15.

analysis/
  calibrate.py                       Phase 1 calibration analysis + item locking.
  validate.py                        Validation analysis: sanity checks, per-condition accuracy.
  analyze.py                         Phase 2 confirmatory analysis (per-model GEE, ITT/PP, Holm-Bonferroni).
  analyze_mechanism.py               Phase 3 mechanism analysis.

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

The paper's analyses are run on the **merged** dataset (`outputs/confirmatory_merged/20260415/inference_log.jsonl.gz`). Use `analysis/analyze.py` for the per-model GEE contrasts and the two-part hurdle decomposition. Phase 3 dose-response and mechanism contrasts are in `analysis/analyze_mechanism.py`.

To reproduce a specific Robust Claim or sensitivity, the paper's §3.x sections cite the relevant subset, scoring regime, and contrast specification. The full-correction scoring used in §3.10 onward is *not* implemented in `runner/score.py` as shipped (see "Known scorer issues" below); a small canonicalization layer is needed.

## Known scorer issues (carried into the data)

`runner/score.py` as shipped has two documented issues that affect every cell scored under it. Both are documented in §3.8–§3.10 of the paper, with row counts and impacted claims:

1. **Chat-template token leakage.** `extract_answer()` does not strip `<end_of_turn>` (Gemma) or `<|endoftext|>`/`<|im_start|>user` (Qwen) before string-match. Affects 206/1030 Gemma-D rows and 80/1030 Qwen-C rows most prominently.

2. **No structured-label aliasing.** `grade()` does exact string equality for `answer_type: "exact"`. The benchmark contains 22/52 exact-answer items whose ground truth is `"Box N"` or `"Cup X"`; both models intermittently emit bare `"N"` answers. Affects Gemma rows broadly (+27 to +86 rescues per cell), Qwen modestly.

Reproductions should patch these. The paper's §3.15 archived audit reports include reference fix code.

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
