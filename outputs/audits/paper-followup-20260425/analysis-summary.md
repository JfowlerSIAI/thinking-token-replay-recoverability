# Sonnet-class follow-up analysis (2026-04-25)

Closes deferred items from the 2026-04-15 scoring-pipeline audit.

## Deferred items closed

1. **Question-family heterogeneity decomposition** (paper §3.13). The aggregated
   Gemma B−C null under full correction concealed a formally significant
   interaction with question family. cond_B × is_boxcup interaction p = .031
   (Gemma), p < .001 (Qwen).

   Per-family Gemma B−C (full-correction GEE):
   - numeric (n=51): log-OR +0.446, p = .001 (OR 1.56) — significant premium
   - direction (n=15): −0.214, p = .072
   - Box (n=10): −0.981, p = .283
   - Cup (n=12): +0.067, p = .614
   - bool (n=13): +29.1 (separation, B at ceiling)

   Per-family Qwen B−C:
   - numeric (n=51): −0.031, p = .732 (null)
   - direction (n=15): −1.177, p = .002
   - Box (n=10): −0.955, p = .001
   - Cup (n=12): −0.807, p = .003

2. **Proper Part-2 hurdle GEE under full correction** (paper §3.14). Replaces
   the auditor-precision estimates ("OR ≈ 1.08, p ≈ .49") in the 2026-04-15
   §3.10. Notable results:
   - Gemma B−C Part-2: OR 1.06, p = .62 (confirms auditor estimate, null)
   - Qwen B−C Part-2: OR 1.43, p = .0001 (favors B; original §3.3 hurdle reading
     survives the scoring correction with smaller magnitude)
   - Gemma B−O Part-2: OR 1.51, p = .006 (significantly favors hidden thinking)
   - Qwen B−O Part-2: OR 0.91, p = .60 (null; visible-CoT advantage is purely
     extraction-channel for Qwen)

3. **Condition I re-aggregation with alias-aware voting** (paper §3.14).
   - Gemma I: 88.0% → 89.5% (+1.6 pp)
   - Qwen I: 91.5% → 88.5% (−3.0 pp; canonicalization collisions)
   - B−I direction and significance unchanged from paper for both models.

## New positive finding surfaced

**Gemma hidden thinking beats Gemma visible CoT under fair scoring.** Both E2E
(OR 1.41, p = .020) and Part-2 conditional-on-extraction (OR 1.51, p = .006).
This is the only within-model live-thinking signal in the dataset that is
robust to all scoring corrections in both reporting modes. Promoted to a new
Claim 8 in §4.

## Paper updates applied

- §3.13 added (question-family heterogeneity)
- §3.14 added (proper Part-2 hurdle + Condition I re-aggregation + B−I rerun)
- Claim 4 in §4 revised from full retraction to per-domain claim
- Claim 8 in §4 added
- §5 "Not visible CoT beats hidden thinking" updated to reflect Gemma reversal
- Abstract (iii) revised
- Conclusion bullet on Gemma live-thinking revised
- Date line and acknowledgments updated

## Method note

This analysis was performed by a single Sonnet-class pass on the cleaned
merged dataset. It is not a replacement for the multi-agent convergence
process used in earlier audit rounds. The findings are reported transparently
as such; reviewers should treat the per-family decomposition as a confirmed
heterogeneity finding warranting fresh pre-registered replication.
