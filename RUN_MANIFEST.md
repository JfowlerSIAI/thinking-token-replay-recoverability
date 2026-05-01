# Run Manifest — Thinking-Token Experiment

Frozen provenance record for all data collection runs backing the paper. Every
reported number in `paper/paper.md` traces to one or more of the logs listed
below. Model digests are captured from the Ollama registry at manifest time
(2026-04-15) because the per-inference log `model_digest` field was left blank
during collection — a limitation discussed in the paper's `§7 Limitations`.

## Models

| Model | Ollama tag | Digest (as of 2026-04-15) | Quantization | Modified |
|------|-----------|---------------------------|--------------|----------|
| Gemma 4 E4B | `gemma4:latest` | `c6eb396dbd5992bb...` | Q4_K_M | 2026-04-06 |
| Qwen 3.5 9B | `qwen3.5:9b` | `6488c96fa5faab64...` | Q4_K_M | 2026-03-05 |

Parameter sizes reported by Ollama `/api/show`:
- Gemma 4 E4B: 8.0 B total (4.5 B effective via PLE)
- Qwen 3.5 9B: 9.7 B (dense)

## Inference runs

### Run 1 — Phase 2 confirmatory (original)

- **Path:** `outputs/confirmatory/20260408_100418/inference_log.jsonl`
- **Records:** 39,550
- **Primary records (excluding I_sub):** 22,660
- **I-subsample records:** 16,890
- **Conditions:** A, B, C, D, E, F, G, H, I, I_sub, J, O (11 primary + I_sub)
- **Ollama version at collection:** 0.20.2 (from 37,472/39,550 records)
- **Models × records:** gemma4 15,790; qwen3.5:9b 23,760 (Qwen extra due to I_sub)
- **Collection date:** 2026-04-08

### Run 2 — Phase 3 mechanism

- **Path:** `outputs/mechanism/20260412_215554/inference_log.jsonl`
- **Records:** 4,368
- **Conditions:** K, L25, L50, L75, L100, M, N
- **Ollama version:** 0.20.6
- **Models × records:** gemma4 2,184; qwen3.5:9b 2,184
- **Collection date:** 2026-04-12 → 2026-04-13

### Run 3 — Qwen B 16K sensitivity rerun

- **Path:** `outputs/confirmatory_16k/20260414_192703_qwen_b_rerun/inference_log.jsonl`
- **Records:** 368 (Qwen B only, 16K ceiling-hit sensitivity)
- **Conditions:** B (Qwen 3.5 only)
- **Ollama version:** 0.20.6
- **num_predict:** 16384 (doubled from Run 1's 8192)
- **num_ctx:** 24576
- **Selection:** records from Run 1 where Qwen B `eval_count ≥ 8190`
- **Collection date:** 2026-04-14 → 2026-04-15 (13.2 hours wall clock)
- **Outcome:** 164 records extracted within 16K (91.4% correct); 204 still hit ceiling

## Merged dataset (used by primary analyses)

The primary analyses in the paper use the 16K-merged Phase 2 dataset:

- **Path:** `outputs/confirmatory_merged/20260415/inference_log.jsonl`
- **Records:** 39,550 (same count as Run 1)
- **Construction:** Run 1 records where Qwen B did NOT hit the 8K ceiling (662 kept unchanged) + 368 replacement records from Run 3 at 16K cap + all non-Qwen-B records from Run 1 unchanged
- **Script:** `scripts/merge_16k_rerun.py`

## Cross-phase version drift (known limitation)

Ollama updated from 0.20.2 → 0.20.6 between Phase 2 (Run 1) and Phase 3
(Run 2). Phase 3 analyses that reference Phase 2 conditions (e.g., comparing K
or L100 to Phase 2 C as a historical control) inherit this drift as a
potential confound. The paper reports these as historical controls rather than
same-run counterfactuals. The 16K sensitivity rerun (Run 3) was collected
under the same Ollama version as Phase 3 (0.20.6), so the merged Qwen B data
contains Ollama version heterogeneity within a single condition (662 records
at 0.20.2, 368 at 0.20.6). A sensitivity analysis on the 662 unchanged Phase 2
non-ceiling Qwen B records alone would test this; we have not run it.

## Missing provenance fields (known limitation)

- Per-inference `model_digest` field: blank in all three log files
  (inference_log JSONL schema has the field, but the runner did not populate
  it at collection time). Digests above are from a live Ollama query on
  2026-04-15 and should be identical to the values during collection if the
  model files were not re-pulled; no evidence of re-pull in shell history.
- Generation-option audit: the raw `options` dict sent to Ollama (temperature,
  top_p, top_k, num_ctx, num_predict, repeat_penalty, seed) is reconstructed
  from code constants and per-condition overrides in
  `runner/run_experiment.py` and `runner/ollama_client.py`, not logged per
  inference. Reviewers who want bit-exact provenance would need to re-run
  under instrumentation.

## Analysis artifacts (current vs superseded)

| Artifact | Status | Path |
|----------|--------|------|
| Phase 2 descriptive (merged 16K) | **Current** | `outputs/results/phase2_16k/` |
| Phase 2 descriptive (original 8K) | **Superseded** | `outputs/results/phase2/` (has `SUPERSEDED.md`) |
| Hierarchical GEE (merged 16K) | **Current** | `outputs/results/hierarchical_16k/` |
| Hierarchical GEE (original 8K) | **Superseded** | `outputs/results/hierarchical/` (has `SUPERSEDED.md`) |
| Phase 3 mechanism | **Current** | `outputs/results/phase3/` |
| Paper | **Current** | `paper/paper.md` |
| Pre-registration | **Reference** | `outputs/osf-preregistration.md` |

## Tri-agent audit history

| Round | Target | Date | Reports |
|-------|--------|------|---------|
| 1 | Infrastructure code | Pre-Phase 2 | `outputs/audits/infra-audit-*.md` |
| 2 | Validation results | Pre-Phase 2 | `outputs/audits/validation-audit-*.md` |
| 3 | Fixes applied | Pre-Phase 2 | `outputs/audits/fixes-audit-*.md` |
| 4 | Model identification (Gemma 4 E4B) | Pre-Phase 2 | `outputs/audits/gemma4-id-*.md` |
| 5 | Phase 2 readiness | Pre-Phase 2 | `outputs/audits/phase2-readiness/` |
| 6 | Phase 2 analysis | Post-Phase 2 | `outputs/audits/phase2-analysis/` |
| 7 | Phase 3 analysis | Post-Phase 3 | `outputs/audits/phase3-analysis/` |
| 8 | Full review (all artifacts) | Post-hierarchical | `outputs/audits/full-review/` |
| 9 | Final review (post-hierarchical) | Post-hierarchical | `outputs/audits/final-review/` |
| 10 | Paper draft audit | Post-paper v1 | `outputs/audits/paper-audit/` |
| 11 | All-results audit | Post-paper v1 | `outputs/audits/all-results-audit/` |

## Reproducibility checklist

- [x] Inference logs retained (per-record JSONL, all three runs)
- [x] Analysis scripts version-controlled (`analysis/*.py`, `scripts/*.py`)
- [x] Paper version-controlled (`paper/paper.md`)
- [x] Model digests captured at manifest time
- [x] Superseded artifacts clearly labeled
- [x] Ollama versions per run documented
- [x] Tri-agent audit reports archived verbatim
- [ ] Per-inference model digest logged at collection time (for next project)
- [ ] Per-inference generation-options logged at collection time (for next project)
