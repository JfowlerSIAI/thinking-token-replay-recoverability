## 1. B vs C Tracking Traces

C’s source trace is the frozen trace bank (`runner/trace_bank.py:47-55`), logged via `source_trace_id` (`runner/run_experiment.py:199-203`), not always the later merged B row.

For Qwen C on Box/Cup/direction tasks, I found 177/370 rows where `source_trace_correct=false` but C was correct: 107 direction, 45 Box, 25 Cup. In 173/177, the source trace’s visible `content` was blank, so the “wrong B trace” was usually not wrong reasoning; it was a hidden trace that never produced a visible answer.

Representative: `outputs/trace_bank/trace_bank/trace_bank.jsonl:124` feeds `outputs/confirmatory_merged/20260415/inference_log.jsonl:2115` (`d9edfbb1`, `hard_tracking_5128`). The trace tail is still re-listing swaps; C continues with a compact state ledger and emits `FINAL: Box 2`.

True correction after a wrong internal answer was rare: 4/177. Example: `inference_log.jsonl:2218` (`0c021db3`) follows a source trace ending `FINAL: West` for `rotation_tracking_6717`, then re-derives and outputs east. Interpretation: C mostly benefits by resuming an already-useful but unfinished state ledger; only a small slice is genuine “replay a wrong trace and fix it.”

## 2. Gemma Drops `Box`, Not `Cup`

On D-condition Box/Cup rows:

- Gemma: 86/220 bare labels, all Box; Box rows were 86/100 bare, Cup rows 0/120 bare.
- Qwen: 0/220 bare; all were prefixed.

Example Gemma bare: `inference_log.jsonl:27253` (`568c2566`) outputs `FINAL: 1` after scaffold `questions/scaffolds/long_object_tracking_7103.json:3` ends “The ball moves to Box 1.” Qwen on the same class consistently emits `FINAL: Box N`, e.g. `inference_log.jsonl:2123`.

This looks like semantic answer compression for numeric box labels, not generic scaffold misunderstanding: Gemma preserves `Cup C` but collapses `Box 1` to `1`. I could not directly verify Gemma’s native tokenizer: no local Gemma tokenizer/GGUF was present and Ollama API access was blocked. Local Qwen tokenizer inspection does not explain Gemma’s behavior.

## 3. Qwen B Truncation Triggers

Using the original 8K log, not the merged rerun file, I count 368/1030 Qwen-B rows at `eval_count=8192`; the rerun progress log also says 368 total (`outputs/confirmatory_16k/.../progress.log:2`). That conflicts with the paper’s 367 count.

Truncation is highly systematic:

- Cup: 111/120 = 93%
- Grid: 32/40 = 80%
- Box: 66/100 = 66%
- Direction: 82/150 = 55%
- Counting: 11/160 = 7%
- Modular arithmetic: 3/70 = 4%
- Multi-entity logic: 0/90 = 0%

Structured Box/Cup answers truncate 177/220 = 80%. Question-level ceiling rate correlates with prompt length (`r=.42`, Spearman `.40`) and with lower A-condition accuracy (`r=-.37`, Spearman `-.48`), but family dominates.

Example: `outputs/confirmatory/20260408_100418/inference_log.jsonl:4081` (`17f49217`, `object_tracking_6619`) ends in a loop about whether cup labels move or positions move, with no visible content. Interpretation: truncation is not random sampling noise; it is triggered by state-tracking ambiguity loops.

## 4. Gemma Empty Thinking

Trace bank: 15/1236 Gemma traces have empty `thinking_tokens`. The CLAUDE note says all modular, but I found 14 modular-arithmetic plus 1 system-of-equations trace.

Accuracy is not worse:

- Empty traces: 15/15 correct.
- Non-empty traces on the same 8 questions: 81/81 correct.
- Confirmatory Gemma-B empty-thinking rows: 15/1030, also 15/15 correct.

Example: `trace_bank.jsonl:2149` (`hard_modular_5060_gemma4_1`) has empty thinking but a correct visible modular solution. Interpretation: this is a free win on easy algebra/modular items, not a sampling failure mode.

## 5. Verbosity vs Accuracy

Length is not monotone-good.

Qwen B quartiles by `thinking_tokens` chars:

- 975-4,527: 73.2% correct
- 4,527-13,551: 88.4%
- 13,585-33,516: 96.1%
- 33,661-70,182: 17.1%, with 79.1% extraction failure

Qwen’s best decile is 13.6k-17.4k chars at 97.1%; worst is 49.1k-70.2k at 5.8%.

Gemma B shows the same “too long is bad” pattern without Qwen-scale truncation: top quartile drops to 69.0%, best decile 2.1k-2.5k chars at 95.1%, worst decile 3.7k-11.5k at 45.6%.

For C, long prefills also hurt: Qwen C top quartile is 53.9% vs 70-78% below; Gemma C top quartile is 66.7%. Interpretation: there is a usable middle band; runaway traces are both a truncation risk and a difficulty/rumination marker.

## 6. Scaffold Answer Leakage Location

Using the stripped D scaffold (`condition_builder.py:118-136`), raw substring matching reproduces the documented leak rate: 90/103 scaffolds contain the gold answer. But location is the new point:

- First gold occurrence: 39 early, 16 middle, 35 late.
- Last gold occurrence: 89 late, 1 middle.
- Median last occurrence position: 98.7% through the stripped scaffold.

D continuations look like immediate extraction from the scaffold tail:

- Qwen D with leaking scaffolds: 850/900 rows mention the answer within first 40 generated chars; 811/900 start directly with `FINAL:`.
- Gemma D with leaking scaffolds: 657/900 within first 40 chars; 593/900 direct `FINAL:`.

Example: `questions/scaffolds/object_tracking_6617.json:3` ends “Ball moves from Cup E to Cup B.” Qwen D `inference_log.jsonl:8496` outputs `Final Answer... FINAL: Cup B`; Gemma D `inference_log.jsonl:29303` outputs `FINAL: Cup B`.

## What This Implies

The mechanism story should be sharpened: C’s tracking advantage is mostly “resume and finalize a useful hidden ledger,” not evidence that models can generally repair bad reasoning. D is often tail-answer extraction, because the last gold mention sits at the end of the scaffold. Qwen truncation is family-triggered by state-tracking ambiguity loops, not random verbosity. Gemma’s Box-prefix issue is numeric-label compression, not a general structured-label failure.