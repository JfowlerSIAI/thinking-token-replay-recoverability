**1. Claim-Evidence Consistency**
- Major mismatch: §3.1 first paragraph says “A ≈ 63% baseline, C ≈ 56–76%, D ≈ 72–98%.” Table 1 shows `A=82.8%/74.9%`, `C=80.5%/68.8%`, `D=82.5%/97.5%` for Gemma/Qwen. That paragraph reads like stale pre-revision prose.
- Major mismatch: §8 first paragraph says Gemma’s live-thinking premium is “+11.7 pp ITT.” Table 1 gives `B−C = 86.3% − 80.5% = +5.8 pp`, not `+11.7 pp`.
- Unsupported in the main results: §4 claim 1 says the PP `C−F` effect remains “OR≈7 in both models,” but §3 does not report those PP ORs.
- Unsupported/overstated: §5 first bullet says the “pooled B−O ITT effect is entirely a Qwen truncation artifact,” but §3 never shows the pooled interaction model, and “entirely” is too strong given Qwen B still has `20%` extraction failure at 16K.
- Overreach: §4 claim 2 calls the D−C pattern a “genuine cross-model architectural difference.” The paper shows a robust model-specific difference; it does not isolate architecture as the cause, especially given §2.1 and §7 acknowledge multiple model/stack confounds.
- Overreach: Abstract/§4 say Qwen is indistinguishable from replay “once the generation budget is adequate.” At 16K, Qwen B still truncates/extraction-fails nontrivially, so “adequate” is stronger than the evidence.
- Reporting inconsistency: Abstract/§4 use `p<10^-9` for `C−F`, while Table 2 only shows `p_adj<.001`. Harmonize exact vs adjusted p-value reporting.

**2. Statistical Rigor**
- The analysis is understandable, but not fully replicable from the paper alone. Missing details include exact formulas, factor coding/reference cells, software/packages, whether small-sample sandwich corrections were used, and the precise merge rule for the 16K rerun.
- “Hierarchical logistic regression (GEE)” is imprecise. GEE is a marginal population-averaged model, not a hierarchical/random-effects model.
- The cluster choice needs more defense. Dependence is not only by question; conditions are paired by seed/rep, and several conditions reuse the same B trace. A reviewer will ask for sensitivity to `question×rep` clustering or a mixed-effects model.
- The hurdle extraction model appears to hit separation (`OR≈10^16` in §3.3). That is fine as a qualitative sign of huge differences, but not as a stable quantitative estimate. Penalized logistic or risk differences would be cleaner.
- §6 says the 16K rerun criterion is “pre-treatment.” It is not; ceiling-hit status is post-treatment. That sentence should be corrected.
- The preregistered Bayesian-to-GEE switch is not adequately justified yet. “Dependencies/runtime” reads as convenience, not methodology. For a methods-heavy paper, you should run the preregistered Bayesian/GLMM sensitivity or a very close equivalent.

**3. Missing Analyses a Reviewer Will Ask For**
- Sensitivity to the 103-item calibration filter: ideally on the full 740 pool or a held-out slice. Right now the calibration story in §2.2 does not match the final A-condition rates in Table 1.
- Per-domain heterogeneity for the key contrasts (`B−C`, `D−C`, `C−F`) across math, logic, spatial, factual.
- Alternative dependence modeling: preregistered Bayesian hierarchy, GLMM, or at least small-sample-corrected clustered SEs.
- Length/budget diagnostics across all `B/C/O/I` comparisons, not just Qwen B. Table 1 shows Qwen C also has a `36%` ceiling-hit rate, which needs explanation.
- A concise extraction-error audit: how often failures are parser failures versus genuinely unfinished answers.

**4. Limitations Completeness**
- Missing limitation: question selection/calibration may bias effect sizes, and the calibration band described in §2.2 visibly drifted relative to final Table 1.
- Missing limitation: results are partly serving-stack-specific, not just model-specific. Ollama version, chat templates, think API behavior, and the raw-mode limitation already affected Condition E.
- Missing limitation: the 16K rerun is post-hoc and selective, so it reduces but does not remove researcher-degrees-of-freedom concerns.
- Missing limitation: compute is not actually matched across conditions; hidden thinking, replay, visible CoT, and self-consistency differ in both token placement and total inference cost.
- Missing limitation: D/H/M use GPT-5.4-authored text, which confounds “reasoning structure” with stronger-model style/knowledge.

**5. Writing Quality**
- The paper is generally well organized, but not clean enough for submission yet because the prose is not fully synchronized with the final tables.
- Fix 1: rewrite §3.1 first paragraph and §8 first paragraph after reconciling every numeric statement with Tables 1 and 2.
- Fix 2: rewrite §2.6 and §6 to use precise statistical language and to justify the prereg deviation on methodological grounds, not tooling/runtime grounds.
- Fix 3: tone down §4–§5 phrases like “genuine architectural difference,” “entirely artifact,” and “not a distinct computational mechanism.”

**6. Desk-Reject Risk**
- `3/5` for a workshop/second-tier venue.
- The likeliest trigger is not the idea; it is the obvious internal inconsistency between prose claims and the paper’s own tables.
- Fix it by doing a line-by-line claim audit and, ideally, auto-generating manuscript numbers from the analysis outputs.

**7. Bottom Line**
- Major revisions needed.
- One-sentence summary: the core experiment is interesting and probably workshop-worthy, but the draft is not submission-ready because several headline numbers and interpretations are internally inconsistent, and the preregistered-model deviation needs a real confirmatory sensitivity analysis.