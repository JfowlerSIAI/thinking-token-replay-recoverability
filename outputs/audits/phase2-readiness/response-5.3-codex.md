[CRITICAL] [run_experiment.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py):75 — Early `_err(...)` returns (also at `:80,:85,:90,:96,:103,:111,:118,:126,:131,:137,:142`) are never logged  
  Impact: Missing-trace/missing-scaffold failures are silently absent from `inference_log.jsonl`, so Phase 2 denominators can be wrong and ITT accounting is broken at dataset level.  
  Fix: Replace each early `return _err(...)` with a helper that creates the error result and immediately calls `client.log_scored(result)` before returning.

[CRITICAL] [run_experiment.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py):212 — Condition I calibration lookup is hard-coded to `../outputs/pilot...`  
  Impact: If calibration logs live elsewhere, `_estimate_mean_a_tokens` falls back to `200.0`, silently changing `k` for all Condition I runs (token-matching no longer faithful).  
  Fix: Add a `--calibration-log` (or `--calibration-dir`) argument, pass it into `_run_condition_i`/`_estimate_mean_a_tokens`, and fail fast when Condition I is requested but calibration data is missing.

[CRITICAL] [run_experiment.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py):452 — `load_scaffolds` does unguarded `json.loads(...)`  
  Impact: One malformed scaffold JSON crashes the run before/at launch.  
  Fix: Wrap per-file parsing in `try/except json.JSONDecodeError`, emit a precise error with filename, and abort cleanly (or skip intentionally with explicit warning policy).

[IMPORTANT] [score.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py):21 — `extract_answer` takes the first `FINAL:` line, not the last  
  Impact: If reasoning contains an earlier `FINAL:` draft and a later corrected one, scoring can use the wrong answer silently.  
  Fix: Collect all `FINAL:` matches and use the last non-empty match.

[IMPORTANT] [score.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py):31 — `answer_is` fallback can truncate decimals / grab intermediate reasoning  
  Impact: Outputs like `the answer is 3.14` may be extracted as `3`; fallback may also capture non-final reasoning text.  
  Fix: Restrict fallback to line-bounded captures (not `.` terminator), and prefer last answer-like line.

[IMPORTANT] [run_experiment.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py):428 — Trace-bank generation scores B traces but never calls `client.log_scored(...)`  
  Impact: Those inferences are missing from JSONL, reducing auditability/reproducibility.  
  Fix: After `score_inference(...)` in trace-bank generation, call `client.log_scored(result)`.

[IMPORTANT] [ollama_client.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/ollama_client.py):22 — Prefill conditions inherit `num_predict=512` with no override  
  Impact: C/D/F/G/H/J continuations after long prefill can truncate before `FINAL:`, inflating extraction failures condition-specifically.  
  Fix: Set a larger `num_predict` override for prefill conditions (or detect `eval_count == num_predict` and retry once with higher cap).

[IMPORTANT] [run_experiment.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py):450 — `load_scaffolds` can silently overwrite duplicate `question_id` keys  
  Impact: If two files map to same `question_id`, scaffold selection is nondeterministic and can silently change condition D/E/H/M inputs.  
  Fix: Iterate deterministically (`sorted(...)`) and raise on duplicate key collisions.

No-finding checks:
- Condition dispatch for A-J/O is correct in current code; E is correctly chat-mode (`prefill: False`, `think: True`).
- Trace pairing works: `rep=9` maps to seed `10` with `SEED_GRID = [1..12]`.
- Confirmatory default `list("ABCDEFGHIJO")` is correct (11 conditions).
- `_g_donor_trace_id` is local-per-call and safe (no cross-inference state leak).

**CONDITIONAL PASS (launch after fixing CRITICALs).**