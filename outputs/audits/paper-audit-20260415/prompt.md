# Audit task — scoring-pipeline artifacts in "Replay Recoverability" paper

## Your role

You are an independent methodological auditor. Read the full paper at the path below, read the scoring code and a sample of the data, and find **additional** claims in the paper that are undermined by extraction/scoring/data-pipeline artifacts analogous to what was discovered today. This is a forensic check, not a stylistic review.

## Today's discovery (2026-04-15, already patched into the paper's §3.8)

An audit of the Gemma D−C null in Table 2 found three compounding scoring-pipeline issues on condition D:

1. **Chat-template token leakage.** The scorer regex `^\s*FINAL:\s*(.+)$` in `runner/score.py` captures everything after `FINAL:` on that line. Gemma's Ollama chat completions frequently emit `<end_of_turn>` on the same line as the `FINAL:` answer; the extracted string becomes e.g. `"1<end_of_turn>"` and string-match against ground truth `"1"` fails. `normalize_answer()` strips `$` / `%` / trailing punctuation but NOT chat-template tokens. Affects 206/1030 Gemma D outputs (+8.4pp when stripped). Qwen is unaffected because Ollama strips `<|im_end|>` before emitting.

2. **Answer-format drift.** On nine `long_object_tracking_*` and `hard_tracking_*` questions the scaffold expects `"Box 3"`; the scaffold's stripped reasoning says "box 3" inline; Qwen echoes `"FINAL: Box 3"` (correct) while Gemma writes `"FINAL: 3"` (bare number). Worth another ~8.5pp when a semantic last-token scorer is used. This is a format-fidelity asymmetry, not reasoning.

3. **Qwen C truncation at 8K.** Qwen C has 30% ceiling hits; Qwen D has 0%. The comparison baseline for Qwen D is truncation-suppressed by ~10.7pp independent of anything D does.

The net effect: the paper's Qwen D−C OR=17.5 vs Gemma D−C OR=1.14 (a 14× asymmetry) shrinks to ~+17pp Qwen vs ~+12pp Gemma (a ~1.4× asymmetry) under fair scoring. Claim 2 in §4 has been revised and §3.8 now documents the decomposition.

## Separately discovered confound worth carrying through

**87% of scaffolds retain the ground-truth answer in their stripped reasoning text.** So condition D partially tests "can the model extract an answer already present in the context," not only "can the model use an expert scaffold." This is now documented in §3.8 but may ripple into other claims that rely on D being a pure reasoning probe.

## What to do

### Step 1 — Read

- The paper: `workflows/thinking-token-experiment/paper/paper.md`
- The scorer: `workflows/thinking-token-experiment/runner/score.py`
- The condition builder (to understand what each condition's prompt and prefill actually is): `workflows/thinking-token-experiment/runner/condition_builder.py`
- The CLAUDE.md for the experiment: `workflows/thinking-token-experiment/CLAUDE.md`
- Sample ~20–50 rows from `workflows/thinking-token-experiment/outputs/confirmatory_merged/20260415/inference_log.jsonl` across as many (model, condition) cells as you can spot-check — especially F, G, H, I, J, O, E where extraction behavior or scoring format could matter. The file is ~40k rows; use head/grep/`rg`/python rather than loading it all.
- The 103 questions: `workflows/thinking-token-experiment/questions/selected.jsonl` (check `answer_type` values — `mcq`, `exact`, `numeric` — and inspect a few ground-truth strings)

### Step 2 — Hunt for analogous issues

Look specifically for:

**A. Other chat-template / sentinel leakage.**
- Does Gemma emit `<start_of_turn>model` in the content stream of other conditions (B, E, H, C) and continue generating a second turn? If so, the scorer picks the LAST `FINAL:` line (regex uses `findall`), which may be from the re-generated turn. Check conditions where Gemma's `eval_count` or content length is long.
- Does any other model/condition pair have a template token that the scorer doesn't strip? (Check Qwen B's content for leaked `<|im_start|>` or `<|im_end|>`, Qwen C for same, etc.)

**B. Answer-format drift in other question families beyond "Box N".**
- Look at `questions/selected.jsonl` for `answer_type: "exact"` questions whose ground truth contains a prefix/suffix (e.g., letters around numbers, units, MCQ option letters with wordy continuations). Flag any systematic "model writes bare value, ground truth expects prefixed value" pattern.
- The scorer has numeric tolerance only for `answer_type: "numeric"`. Ground truths that are numbers stored as `answer_type: "exact"` (e.g., "25.93" vs "25.925") may be causing silent format-mismatch failures. Is this happening?

**C. Extraction-cliff conditions (F, G, J).**
- Paper §4 Claim 1 relies on C−F Part-2 hurdle OR ~7–9 after conditioning on extraction. §4 Claim 5 uses C−J. Are these Part-2 numbers safe from the `<end_of_turn>` / format-drift artifact? Spot-check Gemma F/G/J and Qwen F/G/J to see whether extracted-answer artifacts (not just extraction failures) are inflating the contrast.
- Is the shuffle scoring credible — are extraction failures in F really "model produced garbage" or sometimes "model produced a correct answer but with artifact/format issues"?

**D. Condition I (token-matched self-consistency) scoring.**
- I uses majority vote; check the vote-aggregation code path (is it in `run_experiment.py` or elsewhere?). Does it apply the same buggy regex to each sample before voting, then report the majority? If so, the vote could be corrupted by the same artifact pattern.

**E. Condition O (visible CoT) vs B (thinking).**
- §4 and §5 discuss B−O carefully. Gemma B−O is flagged as borderline (OR=1.34, p_adj=.089). If Gemma B has any hidden artifact suppressing B's accuracy, the B−O contrast could be meaningfully different under fair scoring. Check.

**F. Condition E (thinking + scaffold).**
- Gemma E reports 97.3% — near-perfect. Is this genuinely high, or is it inflated by a scoring artifact the reverse way (accepting too many things as correct)? Sanity check 10 Gemma E records to confirm extraction and scoring are clean.

**G. Phase 3 L-condition dose-response (§3.5).**
- If Gemma L25/L50/L75/L100 responses have similar `<end_of_turn>` artifacts, the reported dose slope β=+0.610 could have the wrong magnitude. Check a handful.

**H. The 16K-merged sensitivity (§3.4).**
- Does the merged Qwen-B dataset have any Ollama-0.20.6-vs-0.20.2 artifact that differentially affects scoring? E.g., different template handling in the 367 rerun records vs the 662 original records.

### Step 3 — Report

Produce a structured audit report with:

1. **Findings table.** One row per finding, columns: finding ID, location in paper, severity (CRITICAL / IMPORTANT / MINOR), mechanism, evidence (file:line or row counts), estimated magnitude impact on paper claims.

2. **For each CRITICAL finding:** recommend a specific fix (e.g., "strip `<end_of_turn>` and `<eos>` in `normalize_answer` at score.py:76") and quantify the estimated delta to the affected claim.

3. **Claims reassurance table.** For each of the 7 Robust Claims in §4 (and the conclusion bullets in §8), one-line verdict: ROBUST / MODESTLY_AFFECTED / NEEDS_REVISION, with one-line justification.

4. **Negative findings.** Anything you checked and confirmed is clean — especially the C−F and B−C contrasts for both models.

5. **Methodological recommendations** beyond the specific findings (e.g., "add a golden-sample extraction audit with 50 rows per cell manually adjudicated", "upgrade scorer to handle chat-template tokens").

Cite file paths and line numbers. Prefer raw data citations (row counts out of n) over impressions. Severity rubric:

- **CRITICAL** = would flip the direction or significance of a paper claim
- **IMPORTANT** = would change the magnitude by >3pp or demote significance to borderline
- **MINOR** = pedagogically worth mentioning but doesn't move a claim

Be direct. If you don't find additional issues, say so explicitly and explain what you checked. False-positive findings are worse than false-negative findings for this audit.

### Output constraints

- Plain Markdown.
- Under 1200 words in the main body; tables can be larger.
- No hedging about whether you have enough context — you have read access to the full repo. If a check requires data you couldn't access, say "I attempted X, the blocker was Y, recommend running Z."
- Do not propose stylistic changes. Only methodological findings.

Begin the report now.
