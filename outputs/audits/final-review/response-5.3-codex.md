**1) Did hierarchical GEE resolve prior top audit concerns?**

1. **Clustering (repeated measures): mostly yes.**  
GEE now models clustering by `question_id` with robust SEs, and intra-cluster correlation is nonzero (`rho=0.143` Gemma, `0.118` Qwen), confirming the old independence assumption was wrong. One borderline result dropped after correction (`gemma B-O p_adj: 0.0468 -> 0.0885`), which is exactly the anti-conservative issue audits flagged.

2. **Truncation mediation: substantially yes (diagnosis), partially no (identification).**  
The hurdle model cleanly separates extraction vs reasoning:
- **Qwen B-C:** extraction failure explodes (`OR=11.577`, `p<0.001`), but among extracted answers B is better (`OR=1.889`, `p=0.0001`).
- **Qwen B-O:** extraction failure dominates (`OR≈3.11e16`, `p<0.001`), while conditional accuracy is ns (`OR=0.810`, `p=0.2319`).
- **Qwen B-I:** both pathways matter (failure `OR=27.954`, `p<0.001`; conditional accuracy still worse `OR=0.446`, `p=0.0252`).

3. **Dose-response power: yes (statistically).**  
Trial-level GEE (not 4-point aggregate) is now powered:
- Gemma dose slope `+0.610`, `p=0.0027`
- Qwen dose slope `-0.641`, `p=0.0001`
- model×dose interaction `-1.251`, `p<0.001`  
So ambiguity from underpowered Kendall tau is resolved statistically.

4. **Two-part decomposition: yes.**  
This is now explicitly implemented for both models (`P(extraction fail)` and `P(correct|extracted)`), directly addressing a core audit requirement.

---

**2) What changed vs marginal OR analysis?**

1. **Primary contrast directions:** no direction flips in the 7 per-model primary contrasts (`B-C`, `C-F`, `G-F`, `D-C`, `B-I`, `B-O`, `C-J`).

2. **Significance changes:**  
- `gemma B-O` lost Holm-adjusted significance (`p_adj 0.0468 -> 0.0885`).  
- `gemma` synergy changed from ns to significant: `+1.757 [0.980, 2.533], p<0.001` (was `+1.757 [-0.685, 4.199], ns`).

3. **Does hurdle resolve B truncation confound?**  
Yes for **B-C** and **B-O** (mostly extraction-mediated), only partly for **B-I** (extraction + residual conditional deficit).

4. **Does token-length covariate confirm truncation mediation?**  
For Qwen, yes:
- `eval_count_z -> ext_fail: +1.072`, `p<0.001`
- `eval_count_z -> correct: -0.587`, `p<0.001`
- `ceiling_hit -> correct: -1.771`, `p<0.001`
- `B-O` log-OR shrinks from `-1.618` to `-0.924` after adjustment (large attenuation).  
`B-C` attenuates modestly (`-0.625 -> -0.500`), `B-I` does not (`-1.998 -> -2.128`).

5. **Does trial-level dose-response resolve ambiguity?**  
Yes on statistical existence of trend; no on full mechanism for Qwen (still intertwined with context exhaustion).

---

**3) Remaining submission blockers**

1. **Claim scope vs estimand mismatch remains** if the paper claims “inherent thinking-token value.” Qwen key cells are still cap-pathology heavy (`B` ext fail `36%`; Phase 3 `L` ceiling `39–46%`, `N` ext fail `64%`).

2. **Phase 3 mechanism identification remains weak** for causal claims: `M` still conflates compression + stronger-trace authorship; cross-phase references remain historical controls (`Ollama 0.20.2 -> 0.20.6`, reps `10 -> 8`, blank model digests).

3. **Protocol-fidelity/provenance issues from prior infra audits** (token-count bank staleness, `I` token-match implementation, etc.) still need explicit closure evidence in the final methods artifact, or reruns if unresolved.

4. **If prereg strictly required Bayesian hierarchical mixed model**, GEE is strong but may still need a Bayesian sensitivity appendix.

---

**4) Paper-ready claims now (with robustness)**

1. **Coherent reasoning beats shuffled tokens massively in both models.**  
Gemma `C-F OR=13.430 [9.520,18.945]`; Qwen `17.747 [11.541,27.291]`; both `p_adj<0.001`.  
**Robustness: 5/5**

2. **Coherent reasoning beats filler tokens in both models.**  
Gemma `C-J OR=9.448 [6.283,14.206]`; Qwen `4.182 [2.883,6.066]`; both `p_adj<0.001`.  
**Robustness: 4/5**

3. **Expert scaffold benefit is strongly model-dependent.**  
Qwen `D-C OR=17.483 [8.275,36.937], p_adj<0.001`; Gemma `1.145 [0.832,1.576], ns`.  
**Robustness: 5/5**

4. **Qwen B-related ITT deficits are largely truncation-mediated (especially B-C, B-O).**  
Hurdle part 1 huge failure ORs; part 2 shows B-C benefit and B-O parity among extracted outputs.  
**Robustness: 4/5**

5. **Length/ceiling mechanics are major causal mediators in Qwen outcomes.**  
`eval_count_z` increases failure and lowers correctness; `ceiling_hit` strongly lowers correctness (`z=-13.89`).  
**Robustness: 5/5**

6. **Dose-response diverges by model at trial level.**  
Gemma positive slope, Qwen negative slope, strong interaction (`p<0.001`).  
**Robustness: 4/5**

---

**5) Grade update**

- **Experimental design: B** (was ~B-). Better defensibility after hierarchical/mediation analysis, but mechanism confounds remain.
- **Infrastructure/execution: C+** (was ~C). Analysis improved; core runtime/provenance concerns are not fully closed in docs shown.
- **Statistical analysis: B+** (was ~C-/C+). Major upgrade: clustered GEE, hurdle decomposition, length mediation, powered trial-level dose modeling.
- **Self-correction: A** (was ~B+/A-). The team addressed the exact audit failure modes with targeted reanalysis and explicit caveats.