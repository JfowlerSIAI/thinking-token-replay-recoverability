Here is the Phase 2 Readiness Audit report based on a detailed review of the inference pipeline source code.

### [CRITICAL] File: run_experiment.py:100-155 — Missing logging for extraction errors
  **Impact:** Any inference that fails early due to a missing trace or missing scaffold triggers `return _err(...)`. However, `_err()` returns the `InferenceResult` object directly, entirely bypassing `client.log_scored(result)` which is called at the end of `run_single_inference`. These errors are silently dropped from the JSONL log instead of being recorded with `extraction_failed=True`, violating the ITT principle and corrupting matched-pair analysis by creating missing rows in the dataset.
  **Fix:** Capture the result of `_err()` and log it before returning. For example:
  ```python
  # Change early returns from:
  # return _err(...)
  # To:
  err_result = _err(...)
  client.log_scored(err_result)
  return err_result
  ```

### [CRITICAL] File: ollama_client.py:205-207 — Inadequate token budget for prefill conditions
  **Impact:** Conditions C, D, F, G, H, and J use raw mode with `think=False`. In `ollama_client.py`, when `think=False`, `num_predict` defaults to 512. For conditions like J (filler) or F (shuffled tokens), the model must generate entirely new reasoning from scratch after processing the prefill. A 512-token limit will truncate the reasoning before the model can output the `FINAL:` tag, causing massive artificial extraction failures for these conditions and ruining the data.
  **Fix:** In `run_experiment.py` inside `run_single_inference`, ensure that all prefill conditions receive the same token budget as thinking conditions:
  ```python
  if is_prefill and condition_options is None:
      condition_options = {"num_predict": THINKING_NUM_PREDICT}
  elif is_prefill:
      condition_options["num_predict"] = THINKING_NUM_PREDICT
  ```

### [IMPORTANT] File: run_experiment.py:378-384 — Scaffold ID type mismatch and crash risk
  **Impact:** In `load_scaffolds`, `q_id = data.get("question_id", f.stem)` can return an integer if the JSON file stores it as one. `scaffolds.get(q_id)` later looks up a string ID (e.g., `"7503"` vs `7503`), causing a silent dictionary miss and triggering the `_err()` data drop. Additionally, `json.loads` will crash the entire script at startup if a single scaffold file contains malformed JSON.
  **Fix:** Cast the extracted ID to a string and wrap the JSON parsing in a try/except block:
  ```python
  try:
      data = json.loads(f.read_text())
      q_id = str(data.get("question_id", f.stem))
      # ... proceed with assignment
  except json.JSONDecodeError:
      print(f"Warning: Skipping malformed scaffold {f.name}")
  ```

### [MINOR] File: run_experiment.py:207-210 — Hardcoded relative paths for calibration logs
  **Impact:** `_estimate_mean_a_tokens` uses paths hardcoded relative to the current working directory (e.g., `Path("../outputs/pilot/inference_log.jsonl")`). If the script is executed from the project root instead of the `runner/` directory, it won't find the calibration logs. It will safely fall back to the 200.0 token heuristic, but Condition I's `k` computation won't benefit from actual calibration data.
  **Fix:** Resolve paths relative to `__file__` (e.g., `Path(__file__).parent.parent / "outputs"...`) or accept the path dynamically.

---

### Answers to Specific Audit Questions

1. **Condition dispatch correctness:** Yes, correctly implemented. Condition E properly routes to `client.chat()` with `think=True`, and N overrides temperature to `0.0` inside `chat()`.
2. **Trace bank pairing:** Yes. `trace_bank.get_paired_trace` correctly indexes `SEED_GRID[rep]`. For Phase 2 with 10 reps, `rep=9` accurately fetches seed `10`. The out-of-bounds check (`if rep >= len(seed_grid)`) is safe.
3. **Condition I token budget:** Mostly correct, except for the path resolution bug noted in the MINOR finding above which causes a graceful fallback. `k` logic is solid.
4. **Condition E chat-mode redesign:** Yes. `CONDITION_REGISTRY` correctly specifies `prefill: False` and `think: True`. `condition_e` correctly returns `ChatMessages`, steering the dispatch to `client.chat()`.
5. **Scoring edge cases:** Yes. The regex `^\s*FINAL:\s*(.+)$` combined with `re.MULTILINE` successfully extracts the answer even if it is preceded by verbose reasoning in the `content` block.
6. **Logging completeness:** **No.** As noted in the CRITICAL finding, logic/retrieval errors caught by `_err()` are silently dropped because they bypass `client.log_scored()`.
7. **Confirmatory defaults:** Yes, `list("ABCDEFGHIJO")` evaluates to exactly the 11 pre-registered conditions (A-J and O).
8. **Token budget for prefill conditions:** **No.** As noted in the CRITICAL finding, defaulting to 512 tokens will catastrophically truncate responses in conditions that require the model to reason (F, G, J).
9. **Scaffold loading:** Partially. As noted in the IMPORTANT finding, it is susceptible to int/string key mismatches and crashes on malformed files.
10. **Race conditions / state leaks:** The `_g_donor_trace_id` pattern is safe. It is assigned inside an `if condition == "G":` block and only retrieved within a matching `if condition == "G":` block after the inference call. No state leaks across replicates or conditions were detected.

---
**SUMMARY:** **CONDITIONAL PASS** (Launch after fixing the 2 CRITICAL bugs and 1 IMPORTANT bug to prevent data loss and artificial truncation failures).
