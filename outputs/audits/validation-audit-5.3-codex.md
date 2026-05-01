**Findings (severity-ordered)**

1. **CRITICAL**: Validation can silently analyze stale/mixed runs. The log path is fixed and reused, results are appended, and analysis loads the full file with no run boundary/filtering.  
[run-validation.sh#L28-L30](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/scripts/run-validation.sh#L28) [ollama_client.py#L313-L314](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/ollama_client.py#L313) [validate.py#L27-L35](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L27)

2. **CRITICAL**: Missing required-condition enforcement allows false PASS when a validation condition is absent. `DEFAULT_VALIDATION_CONDITIONS` is defined but never used; checks/comparisons skip missing conditions instead of failing.  
[validate.py#L24](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L24) [validate.py#L127](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L127) [validate.py#L276-L277](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L276) [validate.py#L488-L491](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L488)

3. **IMPORTANT**: `--min-reps` is effectively a no-op. It is parsed and passed through, but never used to filter/fail undersampled condition/model cells.  
[validate.py#L53](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L53) [validate.py#L467](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L467) [run-validation.sh#L76](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/scripts/run-validation.sh#L76)

4. **IMPORTANT**: Shell failure handling is inconsistent with intended summary flow. `set -e` causes immediate exit on Python failures, so `EXIT_CODE` capture and final PASS/FAIL banner are skipped on analysis failure.  
[run-validation.sh#L12](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/scripts/run-validation.sh#L12) [run-validation.sh#L78-L86](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/scripts/run-validation.sh#L78)

5. **IMPORTANT**: Key robustness checks are missing (trace-bank freshness/pairing integrity, model/version consistency, seed uniqueness/rep bijection). Schema has fields for this, but validator does not use them.  
[ollama_client.py#L35-L37](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/ollama_client.py#L35) [run_experiment.py#L169-L173](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py#L169) [validate.py#L122-L261](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L122)

6. **MINOR**: Message says error records are “excluded,” but stats/checks run on all records (which is ITT-correct). Wording is misleading.  
[validate.py#L457-L467](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L457)

7. **MINOR**: Comparative block covers only a subset (plus B-A exploratory), not all 8 preregistered contrasts; also `C_vs_B` naming is opposite its computed direction (B-C).  
[validate.py#L304-L314](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L304) [CLAUDE.md#L51-L60](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/CLAUDE.md#L51)

8. **MINOR**: No dedicated handling/check for Condition I sub-inference logging; if reused beyond Phase 1, I parent+sub rows can distort per-condition counts unless explicitly separated.  
[run_experiment.py#L251-L263](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py#L251) [run_experiment.py#L272-L287](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py#L272) [validate.py#L60](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L60)

**Criterion-by-criterion**

1. Field parsing compatibility: **Yes** (keys used by validator match `InferenceResult` fields).  
[validate.py#L65-L67](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L65) [ollama_client.py#L31-L67](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/ollama_client.py#L31)

2. “F differs from C” matching key correctness: **Yes** (matches `(question_id, model_tag, rep_number)`).  
[validate.py#L164-L171](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L164)

3. ITT preserved: **Yes** (failures/errors remain in denominator as incorrect).  
[score.py#L3-L4](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py#L3) [score.py#L145](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py#L145) [run_experiment.py#L314](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py#L314) [validate.py#L467](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L467)

4. Delta direction correctness: **Yes for implemented contrasts** (B-A, B-C, C-F, B-O are in intended sign direction).  
[validate.py#L305-L314](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L305)

5. Exit code critical vs minor: **Yes in `validate.py`** (only critical failures exit nonzero).  
[validate.py#L220](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L220) [validate.py#L488-L491](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L488)

6. `run-validation.sh` runner args: **Correct** (`--phase validation`, `--conditions B C F O`, `--trace-bank-dir`).  
[run-validation.sh#L34-L43](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/scripts/run-validation.sh#L34)

7. `--min-reps` default for 4-rep validation: **Conceptually fine, but currently ineffective** because unused.  
[validate.py#L442-L443](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L442) [validate.py#L53-L97](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L53)

8. Shell handling of inference non-zero exit: **Fail-fast works**, but no graceful/reporting path; analysis failure reporting path is broken by `set -e`.  
[run-validation.sh#L12](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/scripts/run-validation.sh#L12) [run-validation.sh#L68](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/scripts/run-validation.sh#L68) [run-validation.sh#L78-L79](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/scripts/run-validation.sh#L78)

9. Missing checks: **Yes** (trace-bank staleness/integrity, model consistency, seed uniqueness are missing).

10. Coverage of 8 preregistered contrasts: **No** (only subset testable in B/C/F/O phase, plus B-A exploratory).

11. Condition I sub-inference logging check: **Missing** (not needed for strict B/C/F/O Phase 1, but needed for broader reuse).

12. Mixed-condition/multi-run contamination risk: **High (critical)**.

13. Zero-inference condition behavior: **Unsafe** if condition absent (can still PASS); if condition emits only error rows, it will typically fail checks (good).  
[run_experiment.py#L73-L75](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py#L73) [validate.py#L139-L147](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/analysis/validate.py#L139)