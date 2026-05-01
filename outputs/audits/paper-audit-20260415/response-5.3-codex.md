## Audit Report — Additional Pipeline Artifacts

### 1) Findings table

| ID | Paper location | Severity | Mechanism | Evidence | Estimated impact |
|---|---|---|---|---|---|
| F-01 | §4 Claim 3, §8 bullet 2 ([paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md):257, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md):334) | **CRITICAL** | Qwen C/G extracted answers leak `"<|endoftext|><|im_start|>user"` suffix; scorer does exact match after `FINAL:` and does not strip these sentinels ([score.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py):23, [score.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py):70, [score.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py):119). | 45/1030 Qwen C and 52/1030 Qwen G rows have this suffix; 39 C + 37 G rows flip wrong→correct when truncating answer at first `<`. Example rows: [inference_log.jsonl](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/confirmatory_merged/20260415/inference_log.jsonl):661, :2917, :2674. | Refit GEE with only this fix (76 rows): Qwen B−C moves from log-OR **−0.009** (p=.899, 90% CI [−0.126,+0.108], TOST p=.016) to **−0.192** (p=.009, 90% CI [−0.314,−0.071], TOST p=.658). Equivalence claim fails. |
| F-02 | §4 Claim 4, §8 bullet 3 ([paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md):258, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md):335) | **CRITICAL** | “Box/Cup” format drift is not limited to D: many exact-answer rows are semantically correct bare tokens (`"1"` vs `"Box 1"`, `"c"` vs `"Cup C"`), scored wrong by exact equality ([score.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py):119). | Conservative Box/Cup-only mismatches: Gemma B=27, **Gemma C=71**, Gemma I=39, Gemma J=34; Qwen C=18, Qwen G=22. Example rows: Gemma C [inference_log.jsonl](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/confirmatory_merged/20260415/inference_log.jsonl):27243, :30055; Gemma B :27237. | GEE with Box/Cup-only canonicalization: Gemma B−C shifts from log-OR **+0.424** (OR 1.53, p=.0007) to **+0.149** (OR 1.16, p=.163; 90% CI [−0.026,+0.324]). Claim 4 loses statistical support. |
| F-03 | Condition I interpretation around B−I ([paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md):259, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md):272) | IMPORTANT | I-majority vote uses same extracted-answer strings and exact grading path as all conditions ([run_experiment.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py):334, :341, :345), so Box/Cup/knight phrasing drift propagates into voted outcomes. | Parent-I semantic rescues: Gemma 39/1030 (+3.79pp), Qwen 7/1030 (+0.68pp). I_sub has 184 Gemma and 156 Qwen semantic false-negatives. | B−I effect size shifts (mostly Gemma), but direction does not reverse. |

---

### 2) CRITICAL fixes (specific)

- **Fix for F-01 (template suffix leakage):**  
  In [score.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py):70, strip/truncate chat sentinels before grading, eg split at first sentinel token (`<|endoftext|>`, `<|im_start|>`, `<end_of_turn>`, `<start_of_turn>`, `<channel|>`, `<eos>`).  
  **Estimated delta:** Qwen C +3.79pp, Qwen G +3.59pp; Qwen B−C equivalence claim flips to non-equivalence/significant C advantage.

- **Fix for F-02 (Box/Cup canonicalization):**  
  In [score.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py):102–119, add exact-answer canonical rules: accept bare `N` for truth `Box N`, and bare letter for truth `Cup X`.  
  **Estimated delta:** Gemma B−C significance drops (p=.0007 → p=.163 under conservative Box/Cup-only correction).

---

### 3) Claims reassurance table (7 robust claims)

| Claim (§4) | Verdict | One-line justification |
|---|---|---|
| 1. C−F content effect | ROBUST | After fixes, C−F remains large/significant (Qwen/Gemma), usually stronger. |
| 2. D−C expert scaffold benefit | MODESTLY_AFFECTED | Qwen C under-scoring (F-01) inflates table-scale D−C magnitude; direction stays strongly positive. |
| 3. Qwen B−C equivalence (TOST) | **NEEDS_REVISION** | F-01 removes equivalence: corrected B−C log-OR −0.192, p=.009, TOST fails. |
| 4. Gemma live-thinking premium (B−C) | **NEEDS_REVISION** | F-02 shows C is disproportionately penalized by Box/Cup exact-format scoring; B−C no longer significant under conservative canonicalization. |
| 5. C−J reasoning vs filler | ROBUST | Direction and significance survive; magnitude increases when C leakage is corrected. |
| 6. Qwen-only residual G−F Part-2 value | ROBUST | F-01 raises Qwen G; inference direction unchanged. |
| 7. Qwen truncation as dominant mediator | MODESTLY_AFFECTED | Truncation remains important, but B−C “equivalence” wording is not sustainable after F-01. |

---

### 4) Conclusion bullets (§8) reassurance

| §8 bullet | Verdict |
|---|---|
| Content beats shuffled/filler | ROBUST |
| Qwen hidden-thinking ≈ replay (equivalent) | **NEEDS_REVISION** |
| Gemma live-thinking premium is robust | **NEEDS_REVISION** |
| Expert scaffold helps both, asymmetry mostly artifact | MODESTLY_AFFECTED |

---

### 5) Negative findings (checked clean)

- F/G/J extraction cliffs are mostly real generation failures, not parser misses: permissive failed-row rescue is small (Qwen: F 2/590, G 0/87, J 0/415; Gemma: F 2/347, G 6/29, J 1/15).
- B−O is not materially driven by template leakage; token-strip effect on B/O is negligible.
- Gemma E near-perfect is not inflated by permissive scoring; extraction is clean (0 extraction failures, no sentinel-leak pattern in extracted answers).
- Gemma Phase-3 L25/L50/L75/L100 shows no sentinel leakage or split-rescues (0/1248), so §3.5 Gemma dose slope is not affected by this artifact family.
- For 16K-merged Qwen-B (§3.4), I found no extracted-answer sentinel leakage differential by Ollama version; version-drift remains a separate (already documented) concern.

---

### 6) Methodological recommendations

1. Add scorer canonicalization layer for known structured exact families (`Box N`, `Cup X`, yes/no/direction labels) before strict equality.
2. Add sentinel scrub at extraction (`FINAL:` payload truncated at first chat-template token).
3. Add a mandatory “50-row per cell” human adjudication audit before final claims.
4. Record and report both first and last `FINAL:` candidates to detect self-correction vs template-loop artifacts.