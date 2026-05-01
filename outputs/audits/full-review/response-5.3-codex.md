**1) Overall Quality Grades**

| Area | Grade | Assessment |
|---|---|---|
| Experimental design | **B-** | Strong condition set and controls (A–O, pre-registered contrasts), but key manipulations are confounded for Qwen by context ceiling and some mechanism tests changed meaning (e.g., N deviation, M authorship confound). (Phase 2/3 reports + phase3 audits) |
| Infrastructure/execution | **C** | Major improvements happened, but audits still flag protocol-fidelity and provenance risks (token-match fidelity, stale token_count risk, run comparability/model digest gaps). (fixes-audit, infra-audit, validation-audit docs) |
| Statistical analysis | **C-** | Good transparency (ITT+PP, two-part extraction decomposition, Holm-adjusted p), but confirmatory inference is still marginal OR on clustered repeated measures; report itself says CIs are anti-conservative and hierarchical model is required. (Phase 2 report caveat) |
| Self-correction | **B+** | Strong response quality: per-model as primary, pooled downgraded, explicit “VOID” labels, mechanism caveats elevated, and confounds documented numerically. (Phase 2/3 revised reports) |

---

**2) Top 3 Remaining Reject-Level Issues**

1. **Primary confirmatory inference is still not the planned/appropriate model.**  
Evidence: repeated-measures design (`103 questions × 10 reps`) but marginal ORs treat rows as independent; report explicitly says final paper requires Bayesian hierarchical logistic with clustering/interactions. This alone is a desk-reject risk for a methods-heavy paper. (Phase 2 report statistical caveat)

2. **Core “thinking helps/hurts” contrasts are not identified for Qwen under current budget.**  
Evidence: Qwen B extraction failures `36%` in full Phase 2 (`367/1030`, all at 8192); in 39-item subset B is `62%` extraction failure. Phase 3 L/N have heavy ceiling pathology (Qwen L25–L100 ceiling `39–46%`; N extraction failure `64%`). So B-C/B-I/B-O/N-B are partly “room to answer” tests, not clean mechanism tests. (Phase 2 §1/§5; Phase 3 §1/§7)

3. **Manipulation fidelity remains incomplete for token-matched mechanism claims.**  
Evidence: fixes audits still report critical tokenization/fidelity problems (legacy `token_count` mismatch in bank, shuffle assertion non-bijectivity risk, Condition I `k` hardcoded denominator, M confounds compression with strong-model rewriting). That weakens causal interpretation of F/G/J/I/M contrasts. (fixes-audit-5.4, fixes-audit-5.3, Phase 3 M confound note)

---

**3) What The Data Actually Shows (Most Likely to Survive Hierarchical Modeling)**

1. **Semantic reasoning content matters a lot vs corrupted controls.**  
`C >> F` in both models: Gemma ITT `80.5% vs 23.5%` (OR `13.385`), Qwen ITT `68.8% vs 11.1%` (OR `17.664`); PP still huge in both.  
**Robustness: 5/5**. (Phase 2 §3)

2. **Reasoning text beats filler text, though magnitude is model-dependent.**  
`C >> J`: Gemma ITT `+50.1pp` (PP `+51.1pp`), Qwen ITT `+34.3pp` (PP `+14.2pp`).  
**Robustness: 4/5**. (Phase 2 §3)

3. **Expert scaffold effect is strongly model-specific.**  
Qwen `D-C`: `97.5% vs 68.8%` (OR `17.176`, huge); Gemma `82.5% vs 80.5%` (ns).  
**Robustness: 4/5**. (Phase 2 §3)

4. **Model heterogeneity is real and large; pooled conclusions can reverse.**  
`B-C` direction flips (Gemma `+5.8pp`, Qwen `-14.7pp` ITT); `B-O` also flips (Gemma `+3.9pp`, Qwen `-31.5pp`).  
**Robustness: 5/5**. (Phase 2 §3/§4)

5. **In Phase 3, externally compressed/edited traces (M) outperform raw full replay (L100), as a compound treatment.**  
Gemma `M-L100`: `+12.2pp`; Qwen `+36.9pp` (same-phase contrast). But this is “compression + stronger author” jointly, not pure compression.  
**Robustness: 3/5**. (Phase 3 §3 + M-confound note)

---

**4) What The Data Does NOT Show (Claims to Avoid)**

1. It does **not** show a universal statement that hidden “thinking tokens” inherently help or hurt across small LMs.  
2. It does **not** support “visible CoT beats hidden think” in general; pooled B-O is Qwen-truncation-driven.  
3. It does **not** establish super-additive think×scaffold synergy; per-model synergy is non-significant.  
4. It does **not** identify pure compression effects from M; M changes trace author quality too.  
5. It does **not** provide interpretable Qwen N-B mechanism evidence under the 8192 cap (both truncation-dominated).  
6. It does **not** justify monotonic dose-response claims from 4-point aggregate tau tests.

---

**5) Paper Readiness**

**Not submission-ready yet** (good internal draft quality, not publication-grade inference yet).

Must-complete before submission:
1. Run the planned **hierarchical model** (Bayesian logistic mixed model) for Phase 2 with question/seed clustering and `model × condition` interactions.  
2. Use **two-part modeling** (`P(extract)` and `P(correct | extracted)`) as primary sensitivity framing for B/F/J/L/N-affected contrasts.  
3. Add **run-comparability/provenance checks** (model digest/version/options) and lock single-run analysis scope.  
4. Re-run key Qwen contrasts with a protocol that removes cap pathology (or explicitly narrow claims to deployment-under-cap).  
5. For Phase 3 mechanism claims, add source-controlled ablations to separate **compression** from **trace-author quality**.

Estimated gap to submission-ready: **~35–45% remaining**, roughly **3–6 weeks** of focused reruns + modeling + rewrite.