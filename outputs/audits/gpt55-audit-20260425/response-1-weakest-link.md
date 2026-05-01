**1. Per-Claim Weakest-Link Table**

| Claim | Weakest link | Severity |
|---|---|---|
| 1. C−F content, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:481) | F is a damaged control: shuffle/tokenizer mismatch causes extraction failure. But full-score E2E remains huge: Gemma C 901/1030 vs F 262/1030; Qwen C 766/1030 vs F 131/1030. | Low |
| 2. D−C scaffold, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:482) | Interpretation: D often contains the answer, so it is partly answer-extraction-from-context. Still large: Gemma D 1023/1030 vs C 901/1030; Qwen D 1004/1030 vs C 766/1030. | Medium |
| 3. Qwen B−C, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:483) | Mixed post-hoc corrections plus asymmetric B-only rerun. Full-corrected margin is only 59 rows: B 707/1030 vs C 766/1030. | Medium-high |
| 4. Gemma numeric B−C, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:484) | Post-hoc subset and small raw margin: B 485/510 vs C 472/510. But it survived exact-question clustering, template clustering, and leave-one-template-out. | Medium |
| 5. C−J filler, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:485) | J token-count mismatch weakens “same-length” wording, especially Qwen Part-2. Direction remains stable: Gemma C 901/1030 vs J 347/1030; Qwen C 766/1030 vs J 358/1030. | Medium |
| 6. G−F shape, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:486) | Depends on broken F; Gemma Part-2 null means only Qwen supports the positive shape claim. | Medium |
| 7. Qwen truncation, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:487) | Post-treatment selection and cross-version rerun. Also row-count provenance is off by one: see smell below. | Medium-high |
| 8. Gemma B−O, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:489) | Weakest. Effect is modest, family-driven, and vanishes under template/domain clustering. | High |

**2. The Single Weakest-Link Claim, Expanded**

Claim 8 is the weakest survivor.

The raw full-corrected E2E result is Gemma B 916/1030 vs O 876/1030, log-OR 0.345, p=.020. Part-2 is B 916/1021 vs O 876/1030, log-OR 0.413, p=.006, matching [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:444). That looks clean under `groups=question_id`.

But the inference depends heavily on the clustering unit. Re-fitting the same B−O contrast while clustering by generator template gives E2E p=.282 and Part-2 p=.218. Clustering by domain gives E2E p=.312 and Part-2 p=.267. Dropping numeric items dissolves it: E2E p=.395, Part-2 p=.308. By family, numeric supports B strongly, Cup goes the other way, and bool has separation.

This is not a scoring bug. It is a design/inference fragility: `condition_b` is the normal hidden-thinking chat prompt, while `condition_o` injects visible CoT text into the user prompt at [condition_builder.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/condition_builder.py:105). The effect is only 40 net successes. A symmetric adverse shift of 20 B/O rows erases the E2E count margin.

The clean dissolving analysis is already available: template-clustered or family-stratified B−O. The clean dissolving data would be a fresh B/O replication stratified by template family, with template as the planned cluster.

**3. Most Overstated Phrase In §4**

“robust to *all* our scoring corrections” in Claim 8, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:489).

It is true only in the narrow sense of template-strip + structured-label scoring, whose need follows from the regex scorer at [score.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py:23) and exact comparator at [score.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/score.py:102). It is not robust to reasonable clustering or family decomposition.

**4. Over-Disclaimed In §5**

The §5 claim “do not provide positive evidence for a distinct computational pathway,” [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:501), is too modest. The broad mechanism claim is unsupported, but there is positive evidence in narrower estimands: Qwen B−C Part-2 OR 1.43, p<.001, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:449), and Gemma numeric B−C OR 1.56, p=.001, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:392). Better wording: no broad E2E evidence across both models.

**5. Methodological Smell**

The paper/manifest say 367 Qwen-B reruns, [paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:95), [RUN_MANIFEST.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/RUN_MANIFEST.md:45). The actual rerun JSONL has 368 rows, and the original run has 368 Qwen-B `eval_count >= 8190` rows. Of those reruns: 164 finished below 16K, 149 were correct, and 204 still hit 16K. This does not flip Claim 7, but the provenance text is off.