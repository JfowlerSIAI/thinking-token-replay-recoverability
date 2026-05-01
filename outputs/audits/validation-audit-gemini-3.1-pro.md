Here is an audit of the validation infrastructure target files, categorized by the assessment areas and rated by severity.

### CORRECTNESS

**1. Does `validate.py` correctly parse InferenceResult JSONL?**
Yes. The script uses standard `json.loads` and accesses fields safely with `.get()`. All keys used in `validate.py` (e.g., `correct`, `extraction_failed`, `eval_count`, `condition`, `model_tag`, `thinking_tokens`, `source_trace_id`, `raw_prompt`) correctly map exactly to the `InferenceResult` dataclass fields defined in `ollama_client.py`.

**2. Are the sanity checks actually testing what they claim?**
Yes. The "F differs from C" check correctly joins the `F` inferences with the `C` inferences using the composite key `(question_id, model_tag, rep_number)`. This perfectly isolates the matched pairs so the unmodified trace prefill (C) can be directly compared against the word-level shuffled trace prefill (F).

**3. Is the ITT principle preserved?**
Yes. In `validate.py`'s `compute_condition_stats`, accuracy is calculated as `correct / max(n, 1)`, where `n` is the total length of `cond_results`. Because extraction failures will lack `r.get("correct") == True`, they appropriately lower the accuracy score without shrinking the denominator. Errors are also passed into `compute_condition_stats` without being filtered out first, satisfying the Intention-To-Treat principle.

**4. Are the comparative analysis deltas computed in the right direction?**
Yes. `_compare` calculates `delta = acc_a - acc_b`. For example, `_compare("B_vs_A", "B", "A", ...)` results in `delta = B_accuracy - A_accuracy`. If thinking helps, B will be higher than A, resulting in a positive delta. 

**5. Does the exit code logic correctly distinguish critical vs minor failures?**
Yes. `validate.py` explicitly builds a `failed_critical` list filtering for `not c.passed and c.critical`. It only exits with `1` if this list is populated.

---

### INTEGRATION

**6. Does run-validation.sh pass the right arguments to run_experiment.py?**
Yes. It correctly assembles the array, passing `--phase validation`, `--questions`, `--output-dir`, `--reps`, and `--conditions B C F O`. 

**7. Does the analysis script's `--min-reps` default make sense?**
* **MINOR (`analysis/validate.py:46`)**: The `--min-reps` parameter is defined and passed around, but it is **completely unused** inside the `compute_condition_stats` function. It performs no filtering on models or conditions that fail to meet this threshold.

**8. Does the shell script handle the case where the inference run fails?**
* **IMPORTANT (`scripts/run-validation.sh:58`)**: The script uses `set -e` at the top. If `run_experiment.py` fails and returns a non-zero exit code, the shell script will immediately abort. It will never reach Step 2 (`validate.py`), nor will it print the "VALIDATION FAILED" summary or return the intended `EXIT_CODE`. 

---

### COMPLETENESS

**9. Are there important validation checks missing?**
* **CRITICAL (`analysis/validate.py:98`)**: `validate.py` silently skips sanity checks if a condition is entirely missing. Because checks are wrapped in `if "C" in by_condition:`, an empty trace bank that causes Condition C and F to yield 0 inferences will simply skip the checks rather than failing them. The script should explicitly assert that all expected `DEFAULT_VALIDATION_CONDITIONS` are present.
* **IMPORTANT (`analysis/validate.py`)**: There are no checks to ensure `model_digest` or `ollama_version` remained consistent throughout the log. There is also no check ensuring that the expected number of total inferences (`reps * questions * models`) was actually reached.

**10. Does the comparative analysis cover all 8 pre-registered contrasts?**
It only partially covers them, but this is expected. It covers B-A, C-B, C-F, and B-O. It skips G-F, D-C, E-(B+D-A), and C-J. However, since this is a Phase 1 validation script specifically running only conditions `B, C, F, O`, it cannot compute the other contrasts.
* **MINOR (`analysis/validate.py:228`)**: The script attempts to compute `B_vs_A`, but since `A` is not in the validation condition list (`B C F O`), it will always silently abort and omit this comparison from the report.

**11. Should there be a check for Condition I sub-inference logging?**
Not for this specific `B C F O` validation script, but if `validate.py` is intended to be used generally on later phases, it will need a check to ensure `raw_response` contains the JSON list of sub-inferences for `I`.

---

### ROBUSTNESS

**12. What happens if the log file has mixed conditions from multiple runs?**
* **IMPORTANT (`scripts/run-validation.sh:42`)**: If `run-validation.sh` is executed multiple times, `run_experiment.py` will continuously append to the existing `inference_log.jsonl`. `validate.py` will then load the entire file, indiscriminately grouping the old and new inferences together. This will contaminate the `n` count and accuracy stats. The shell script should clear or backup the previous log before starting a new run.

**13. What if a condition has 0 inferences?**
As noted in finding #9, the script fails safely but silently. The sanity checks for that condition are entirely bypassed, leading to a misleading "PASS" verdict despite missing critical data.
