**1) Consistency Matrix (7 robust claims in §4)**

| Claim | Check vs reports | Verdict | Issue flagged |
|---|---|---|---|
| 1. `C−F` semantic content effect | Hierarchical: Gemma OR `13.430`, Qwen OR `17.747`; both highly significant. PP in Phase 2: Gemma `8.230`, Qwen `7.370`. | Supported | Minor wording drift: paper says PP “≈7 in both”; Gemma is closer to `8.23`. |
| 2. `D−C` expert premium is model-specific | Hierarchical: Gemma `1.145` (ns), Qwen `17.483` (sig). | Supported | None. |
| 3. Qwen `B−C` null at 16K | Hierarchical: Qwen `B−C OR=0.991`, `p_adj=.899` (null). | Supported with caveat | “Adequate budget” is a bit strong; Qwen `B` still has ~`20%` extraction failure at 16K. |
| 4. Gemma live-thinking premium (`B−C`) | Hierarchical: Gemma `OR=1.529`, `p_adj=.0027`. | Supported | None. |
| 5. `C−J` content >> filler | Hierarchical ITT: Gemma `9.448`, Qwen `4.182`, both sig. | Supported | Mechanistically smaller in Qwen conditional model (`OR=1.778`), so “>>” is mainly ITT-scale. |
| 6. `G−F` residual structure value | Hierarchical ITT significant in both models (`1.818`, `5.667`). | Partially supported | Gemma conditional (`correct|extracted`) is ns (`OR=1.138`), so effect is partly extraction-channel. |
| 7. Qwen truncation mediates outcomes | Length/cap mediation is strong: negative `eval_count` and `ceiling_hit`; B-involving contrasts shift materially with length covariate; 8K→16K rerun raises Qwen B `54.2%→68.6%`. | Supported | None. |

**Critical global inconsistency (not just §4):**
`paper.md` Table 1 / §3.1 has multiple hard mismatches against `phase2_16k` (for example Qwen A `0.749` vs report `82.6%`; Gemma E `0.897` vs `97.3%`; Qwen H `0.826` vs `40.4%`; paper text says “A ≈ 63% baseline” while phase2_16k A is ~`82.7%` pooled). This is a major manuscript-report sync error.

**2) Audit-Response Trace**

- Phase 2 audit demanded hierarchical + hurdle: delivered.
  - GEE clustered by question with robust SEs is implemented.
  - Two-part hurdle (`P(extraction_failed)` and `P(correct|extracted)`) is implemented and used in interpretation.
- Phase 3 audit confounds (K verbosity, M authorship, Qwen L/N pathology): handled explicitly.
  - K framed as verbosity/context-budget mismatch, not compatibility claim.
  - M explicitly framed as compression+author confound.
  - Qwen L/N explicitly framed as context-window pathology; N-B marked VOID for Qwen.
- Final-review truncation fix demand: partially delivered.
  - 16K rerun fixed the key Qwen B-C reversal artifact.
  - Not fully sufficient experimentally: Qwen B still truncates (~20%), and Phase 3 L/N were not rerun under higher cap.

**3) Final Grade Update (vs final-review)**

| Area | Final-review baseline | Now | Change |
|---|---|---|---|
| Design | `B-` | `B-` | 16K rerun improved one core estimand, but residual cap/pathology and Phase 3 confounds remain. |
| Infrastructure | `C` | `C-` | Downgrade due manuscript/report numeric desync plus still-weak provenance closure. |
| Statistics | `B+` | `B+` | Strong GEE+hurdle+mediation remains solid; no major new statistical regression. |
| Self-correction | `A` | `A-` | Strong responsiveness, but unresolved fidelity/provenance closure and Table 1 drift keep it below A. |

**4) Single Biggest Remaining Concern**

Manuscript internal numeric integrity: Table 1 and §3.1 are inconsistent with the underlying post-audit Phase 2 16K report on multiple cells. That directly threatens credibility of all downstream claims, even where the hierarchical contrast table is correct.

**5) Replication Risk (biggest missing piece)**

Lack of an immutable run-provenance manifest tying every reported table to exact model build and run config.
Current artifacts still note cross-phase version drift and blank model digests; without fixed digests/options/hash mapping, independent replication can only be approximate.

**6) Submission Verdict**

**Major revisions.** The core inferential arc is much stronger now (hierarchical GEE, hurdle decomposition, truncation sensitivity), and most robust claims are supportable. But submission is premature until the manuscript’s descriptive tables are reconciled to the released reports and provenance/reproducibility metadata is tightened. Fix those, and this becomes defensible as a careful, scope-limited paper.

Key sources: [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md), [phase2_16k report](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/results/phase2_16k/phase2_report.txt), [hierarchical_16k report](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/results/hierarchical_16k/hierarchical_report.txt), [phase3 report](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/results/phase3/phase3_report.txt), [phase2 audit 5.4](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/audits/phase2-analysis/response-5.4.md), [phase3 audit 5.4](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/audits/phase3-analysis/response-5.4.md), [final-review 5.4](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/audits/final-review/response-5.4.md), [full-review 5.4](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/audits/full-review/response-5.4.md).