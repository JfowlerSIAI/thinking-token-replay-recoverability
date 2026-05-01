I ran corrected rescoring over `outputs/confirmatory_merged/20260415/inference_log.jsonl` and GEE Binomial/Logit tests clustered by `question_id`.

**1. C-F Content Effect**
Paper: coherent replay content beats shuffled tokens ([paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:480)).

Alternatives tested:
- Extraction-channel only: REJECTED. F does break extraction: Gemma F fail 351/1030 vs C 18/1030; Qwen F fail 590/1030 vs C 47/1030. But conditional-on-extraction C-F remains large: Gemma OR 14.1, p=2.4e-33; Qwen OR 7.5, p=1.3e-13.
- F degrades into copy/repeat/runaway: SUPPORTED as a partial mechanism. F had no `FINAL:` in 383/1030 Gemma and 838/1030 Qwen rows; ceiling hits 196/1030 and 320/1030. Example Qwen F copy/runaway at [inference_log.jsonl](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/confirmatory_merged/20260415/inference_log.jsonl:47).
- C mostly benefits from correct source traces: SUPPORTED for Gemma, only partial for Qwen. When `source_trace_correct=False`, Gemma C-F vanishes: E2E OR 1.23, p=.57; Part-2 OR 0.70, p=.35. Qwen still shows C-F when source trace was wrong: E2E OR 10.15, p=1.1e-17; Part-2 OR 3.74, p=2.0e-5.

Implication: Claim 1 is robust, but for Gemma it is closer to “replaying a correct solved trace beats shuffled tokens” than a pure semantic-coherence result.  
Recommendation: add caveat about source-trace correctness dependence.

**2. Gemma B-C Numeric Premium**
Paper: Gemma live thinking helps numeric items ([paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:387)).

Alternatives tested:
- Dominated by `compound_percentage`, `profit_loss_chain`, `bat_ball_variant`: REJECTED. Those are 18/51 numeric questions, not a majority. Interaction `isB × named3` was negative and ns: OR 0.55, p=.126. Leave-one-template-out GEE stayed significant every time, including leaving out `bat_ball_variant`: OR 2.19, p=.003.
- Numeric C truncation-prone for Gemma: REJECTED. Gemma numeric C had 1/510 ceiling hit; B had 0/510. C median eval count was 6 tokens vs B 917.
- Better Gemma math-trace quality: CONSISTENT but not independently identified. Numeric B was 485/510 correct vs C 472/510; this fits the paper’s reading but does not explain why without trace-quality annotation.

Implication: the numeric premium is not a template-composition artifact or truncation artifact.  
Recommendation: leave claim, but avoid mechanistic overstatement.

**3. Qwen Tracking C > B**
Paper: trace replay beats live thinking on tracking ([paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:398)).

Alternatives tested:
- Live tracking traces are longer/truncate more: SUPPORTED. Tracking all-family B-C: OR 0.48, p=4.7e-8 favoring C. After excluding ceiling rows, B-C disappears: OR 0.89, p=.423. Conditional on extraction, B actually wins: OR 1.60, p=.0045. Qwen B Cup ceiling/fail was 80/120; C Cup fail was 1/120. Example ceiling row: [inference_log.jsonl](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/outputs/confirmatory_merged/20260415/inference_log.jsonl:39206).
- C has one fixed trace for all 10 reps: REJECTED. Implementation pairs each replicate to its seed-matched trace ([trace_bank.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/trace_bank.py:135); [run_experiment.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py:82)).
- Box/Cup tokenizer-specific issue: REJECTED as primary. Direction questions, which are not Box/Cup labels, also favor C: B 117/150 vs C 138/150.

Implication: tracking C>B is mostly a termination-budget effect, not direct evidence that replayed tracking reasoning is intrinsically better.  
Recommendation: weaken mechanism language.

**4. Gemma B-O Hidden > Visible CoT**
Paper: hidden thinking beats visible CoT for Gemma ([paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:489)).

Alternatives tested:
- Visible-CoT prompt suboptimal: CONSISTENT, not testable without rerun. O uses one prompt: “Think step by step...” ([condition_builder.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/condition_builder.py:31), [condition_builder.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/condition_builder.py:105)).
- `num_predict` differs: REJECTED. O is explicitly set to `THINKING_NUM_PREDICT` ([run_experiment.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/run_experiment.py:161)); B also gets it when `think=True` ([ollama_client.py](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/runner/ollama_client.py:162)).
- O does not trigger Gemma `<think>` path: SUPPORTED. Gemma B had nonempty `thinking_tokens` in 1015/1030 rows; O had 0/1030. B-O is not budget/extraction: B fail 9/1030, O fail 0/1030, no ceiling hits.

Implication: claim is valid only as “Gemma think-mode API beats this visible-CoT prompt,” not hidden text vs visible text in isolation.  
Recommendation: add prompt/API-path caveat.

**5. Master Claim: Replay Recovers Most Benefit**
Alternative: benchmark too easy for live-thinking advantage.

Test: split by corrected A accuracy. The ease premise is true: paper reports realized A accuracy 82.8%/82.6% ([paper.md](/home/james-fowler/github/Workflows/workflows/thinking-token-experiment/paper/paper.md:53)). But the predicted hard-subset B>C pattern fails. On A<=.5 questions: Gemma B 99/140 vs C 101/140, OR 0.93, p=.73; Qwen B 69/140 vs C 81/140, OR 0.71, p=.041 favoring C. Hardness interactions were ns for both models.

Implication: ceiling compression is real, but harder items do not reveal a larger live-thinking advantage.  
Recommendation: keep title claim, add benchmark-ease limitation.