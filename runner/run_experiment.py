"""Main experiment loop for the thinking-token experiment.

Routes non-prefill conditions through /api/chat and prefill conditions
through /api/generate (raw mode) for reliable assistant-prefill continuation.

Usage:
    python run_experiment.py --phase calibration --questions ../questions/calibration-pool.jsonl --output-dir ../outputs/pilot
    python run_experiment.py --phase validation --questions ../questions/calibration-pool.jsonl --output-dir ../outputs/pilot --conditions B C F O --reps 4
"""

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

from ollama_client import OllamaClient, InferenceResult, get_model_template_tokens, THINKING_NUM_PREDICT
from condition_builder import (
    condition_a, condition_b, condition_c, condition_d, condition_e,
    condition_f, condition_g, condition_h, condition_i, condition_j,
    condition_o, condition_k, condition_l, condition_m, condition_n,
    build_raw_prefill_prompt, PrefillSpec, CONDITION_REGISTRY,
)
from score import score_inference, normalize_answer, grade
from trace_bank import TraceBank, shuffle_tokens, count_tokens

SEED_GRID = list(range(1, 13))
MODELS = ["qwen3.5:9b", "gemma4"]
KEEP_ALIVE = "0"  # Override with --keep-alive for calibration speed


def load_questions(path: Path) -> list[dict]:
    questions = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                questions.append(json.loads(line))
    return questions


def run_single_inference(
    client: OllamaClient,
    model: str,
    condition: str,
    question: dict,
    rep: int,
    seed: int,
    template_tokens: dict,
    trace_bank: TraceBank = None,
    scaffolds: dict = None,
) -> InferenceResult:
    """Run a single inference. Routes to chat or raw mode based on condition."""
    q_id = question["id"]
    q_text = question["question"]
    q_answer = question["answer"]
    q_type = question.get("answer_type", "exact")
    q_domain = question.get("domain", "unknown")

    # L dose-response sub-conditions: L25, L50, L75, L100 → base condition L
    l_fraction = None
    base_condition = condition
    if condition.startswith("L") and condition != "L":
        try:
            l_fraction = int(condition[1:]) / 100.0
        except ValueError:
            pass
        base_condition = "L"

    reg = CONDITION_REGISTRY[base_condition]
    think = reg["think"]
    is_prefill = reg["prefill"]

    # --- Build prompt ---
    prompt_obj = None  # ChatMessages or PrefillSpec

    if condition == "A":
        prompt_obj = condition_a(q_text)
    elif condition == "B":
        prompt_obj = condition_b(q_text)
    elif condition == "C":
        entry = _get_trace(trace_bank, q_id, model, rep)
        if entry is None:
            return _err(model, condition, q_id, rep, seed, "no trace in bank", client)
        prompt_obj = condition_c(q_text, entry.thinking_tokens)
    elif condition == "D":
        scaffold = scaffolds.get(q_id, "") if scaffolds else ""
        if not scaffold:
            return _err(model, condition, q_id, rep, seed, "no scaffold", client)
        prompt_obj = condition_d(q_text, scaffold)
    elif condition == "E":
        scaffold = scaffolds.get(q_id, "") if scaffolds else ""
        if not scaffold:
            return _err(model, condition, q_id, rep, seed, "no scaffold", client)
        prompt_obj = condition_e(q_text, scaffold)
    elif condition == "F":
        entry = _get_trace(trace_bank, q_id, model, rep)
        if entry is None:
            return _err(model, condition, q_id, rep, seed, "no trace in bank", client)
        shuffled = shuffle_tokens(entry.thinking_tokens, seed=seed)
        prompt_obj = condition_f(q_text, shuffled)
    elif condition == "G":
        entry = _get_trace(trace_bank, q_id, model, rep)
        if entry is None:
            return _err(model, condition, q_id, rep, seed, "no trace in bank", client)
        wrong = trace_bank.get_wrong_question_trace(
            question_id=q_id, model_tag=model, seed=seed,
            target_token_count=entry.token_count, domain=q_domain,
            question_text=q_text, answer_text=q_answer,
        )
        if wrong is None:
            return _err(model, condition, q_id, rep, seed, "no matching wrong trace", client)
        prompt_obj = condition_g(q_text, wrong.thinking_tokens)
        # Store the donor trace ID (not the self-trace) for G provenance
        _g_donor_trace_id = wrong.trace_id
        _g_donor_correct = wrong.correct
    elif condition == "H":
        scaffold = scaffolds.get(f"{q_id}_wrong", "") if scaffolds else ""
        if not scaffold:
            return _err(model, condition, q_id, rep, seed, "no wrong scaffold", client)
        prompt_obj = condition_h(q_text, scaffold)
    elif condition == "I":
        return _run_condition_i(client, model, question, rep, seed, template_tokens, trace_bank)
    elif condition == "J":
        entry = _get_trace(trace_bank, q_id, model, rep)
        if entry is None:
            return _err(model, condition, q_id, rep, seed, "no trace bank for J length", client)
        prompt_obj = condition_j(q_text, entry.token_count)
    elif condition == "O":
        prompt_obj = condition_o(q_text)
    elif condition == "K":
        other = [m for m in MODELS if m != model][0]
        entry = trace_bank.get_cross_model_trace(q_id, other, seed) if trace_bank else None
        if entry is None:
            return _err(model, condition, q_id, rep, seed, "no cross-model trace", client)
        prompt_obj = condition_k(q_text, entry.thinking_tokens)
    elif base_condition == "L":
        entry = _get_trace(trace_bank, q_id, model, rep)
        if entry is None:
            return _err(model, condition, q_id, rep, seed, "no trace in bank", client)
        fraction = l_fraction if l_fraction is not None else question.get("l_fraction", 1.0)
        prompt_obj = condition_l(q_text, entry.thinking_tokens, fraction)
    elif condition == "M":
        scaffold = scaffolds.get(f"{q_id}_compressed", "") if scaffolds else ""
        if not scaffold:
            return _err(model, condition, q_id, rep, seed, "no compressed trace", client)
        prompt_obj = condition_m(q_text, scaffold)
    elif condition == "N":
        prompt_obj = condition_n(q_text)
    else:
        return _err(model, condition, q_id, rep, seed, "unknown condition", client)

    # --- Dispatch to correct endpoint ---
    # Condition N overrides temperature to 0.0 for deterministic (greedy) thinking.
    # This tests whether stochastic sampling in the think phase adds value over
    # greedy decoding, isolating the randomness variable.
    condition_options = None
    if condition == "N":
        condition_options = {"temperature": 0.0}
    elif condition == "O":
        # Condition O produces visible CoT in the content stream (not a separate
        # thinking channel), so it needs the same token budget as thinking conditions
        # to avoid truncation before the FINAL: tag.
        condition_options = {"num_predict": THINKING_NUM_PREDICT}

    # Prefill conditions (C/D/F/G/H/J) need a larger token budget than the 512
    # default. After a long prefill, the model must still generate its answer
    # (possibly with additional reasoning) + FINAL: tag. Use THINKING_NUM_PREDICT
    # to match the budget of thinking conditions.
    if is_prefill and condition not in ("N", "O"):
        if condition_options is None:
            condition_options = {}
        condition_options.setdefault("num_predict", THINKING_NUM_PREDICT)

    if isinstance(prompt_obj, PrefillSpec):
        raw_prompt = build_raw_prefill_prompt(prompt_obj, template_tokens)
        result = client.generate_raw(
            model=model, prompt=raw_prompt, think=think, seed=seed,
            options=condition_options,
            keep_alive=KEEP_ALIVE, condition=condition,
            question_id=q_id, rep_number=rep,
        )
        # Strip model-specific end-of-turn tokens from content
        result.content = _strip_turn_tokens(result.content, template_tokens)
    else:
        result = client.chat(
            model=model, messages=prompt_obj, think=think, seed=seed,
            options=condition_options,
            keep_alive=KEEP_ALIVE, condition=condition,
            question_id=q_id, rep_number=rep,
        )

    # Trace sourcing metadata
    if condition == "G":
        # G uses a donor trace from a different question — log the donor, not self
        result.source_trace_id = _g_donor_trace_id
        result.source_trace_correct = _g_donor_correct
    elif condition in ("C", "F", "J") and trace_bank:
        entry = _get_trace(trace_bank, q_id, model, rep)
        if entry:
            result.source_trace_id = entry.trace_id
            result.source_trace_correct = entry.correct

    score_inference(result, q_answer, q_type)
    client.log_scored(result)
    return result


def _get_trace(trace_bank, q_id, model, rep):
    if trace_bank is None:
        return None
    return trace_bank.get_paired_trace(q_id, model, rep, SEED_GRID)


_MEAN_A_CACHE: dict[str, float] = {}


def _estimate_mean_a_tokens(client: OllamaClient, model: str, q_id: str) -> float:
    """Estimate mean no-think response length from Condition A calibration data.

    Reads the calibration inference log (if it exists) to compute the actual mean
    eval_count for Condition A responses for this model.  Falls back to 200 tokens
    (calibrated from pilot data: Qwen ~213, Gemma ~297) if no data is available.
    The cache ensures we only read the file once per model per session.
    """
    if model in _MEAN_A_CACHE:
        return _MEAN_A_CACHE[model]

    # Try to find calibration data — check both CWD-relative and runner/-relative
    cal_paths = [
        Path("outputs/pilot/inference_log.jsonl"),
        Path("../outputs/pilot/inference_log.jsonl"),
        Path("outputs/pilot/calibration/inference_log.jsonl"),
        Path("../outputs/pilot/calibration/inference_log.jsonl"),
    ]
    eval_counts = []
    for cal_path in cal_paths:
        if not cal_path.exists():
            continue
        try:
            with open(cal_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    r = json.loads(line)
                    if r.get("condition") == "A" and r.get("model_tag") == model:
                        ec = r.get("eval_count", 0)
                        if ec > 0:
                            eval_counts.append(ec)
        except (OSError, json.JSONDecodeError):
            continue
        if eval_counts:
            break

    if eval_counts:
        mean_a = sum(eval_counts) / len(eval_counts)
    else:
        # Data-informed fallback: pilot observations show Qwen ~213, Gemma ~297 tokens
        mean_a = 200.0

    _MEAN_A_CACHE[model] = mean_a
    return mean_a


def _strip_turn_tokens(content: str, template_tokens: dict) -> str:
    """Remove model-specific end-of-turn tokens from generated content."""
    for key in ("assistant_end", "user_end"):
        token = template_tokens.get(key, "")
        if token and content.endswith(token):
            content = content[:-len(token)]
        if token:
            content = content.replace(token, "")
    return content.strip()


def _run_condition_i(client, model, question, rep, seed, template_tokens, trace_bank):
    """Condition I: Token-matched self-consistency with majority vote.

    Protocol (plan §3): Divide B's total output-token count (thinking + answer)
    by the mean no-think response length to get k attempts.  Run k independent
    no-think generations with different seeds.  Majority vote on extracted answers.

    k computation:
        mean_b_total_tokens = mean(count_tokens(thinking) + count_tokens(content))
                              across all B-traces for this question/model
        mean_a_tokens = estimated mean no-think response length (from Condition A
                        data if available, else heuristic of 50 tokens)
        k = max(2, min(20, round(mean_b_total_tokens / mean_a_tokens)))

    Tie-break: Lexicographic ordering of normalized answers.  The plan specifies
    logprob-then-lexicographic, but Ollama does not reliably expose per-token
    logprobs for chat completions (the `logprobs` field is absent or incomplete
    in most model backends).  Lexicographic is deterministic and reproducible,
    which is the key requirement.  This deviation is documented here and in the
    paper's methods section.

    Sub-inference logging: Each of the k sub-inferences is logged individually
    with a linked parent_inference_id so analysis can examine the full voting
    pattern, not just the majority-vote result.
    """
    q_id = question["id"]
    q_text = question["question"]
    q_answer = question["answer"]
    q_type = question.get("answer_type", "exact")

    # Compute k from B-trace token budget (plan §3)
    b_traces = trace_bank.get_all_for_question(q_id, model) if trace_bank else []
    if b_traces:
        mean_b_total_tokens = sum(
            count_tokens(t.thinking_tokens) + count_tokens(t.content)
            for t in b_traces
        ) / len(b_traces)
    else:
        mean_b_total_tokens = 250

    # Estimate mean no-think response length from Condition A calibration data.
    # Read the calibration log if available; otherwise use a data-informed default.
    mean_a_tokens = _estimate_mean_a_tokens(client, model, q_id)
    k = max(2, min(20, round(mean_b_total_tokens / mean_a_tokens)))

    parent_id = f"I_{q_id}_{model}_{rep}"
    messages = condition_i(q_text)
    sub_results = []
    answers = []

    for i in range(k):
        sub_seed = seed * 1000 + i
        sub = client.chat(
            model=model, messages=messages, think=False, seed=sub_seed,
            keep_alive=KEEP_ALIVE, condition="I_sub", question_id=q_id, rep_number=rep,
        )
        score_inference(sub, q_answer, q_type)
        sub.parent_inference_id = parent_id
        sub_results.append(sub)
        client.log_scored(sub)
        if not sub.extraction_failed:
            answers.append(sub.extracted_answer)

    voted, method = _majority_vote(answers)

    # Use grade() for correctness to respect answer_type (MCQ, numeric, exact)
    # instead of raw string equality.
    voted_correct = grade(voted, q_answer, q_type) if voted else False

    result = InferenceResult(
        inference_id=parent_id,
        model_tag=model, condition="I", question_id=q_id,
        rep_number=rep, seed=seed, think=False,
        prompt_eval_count=sum(r.prompt_eval_count for r in sub_results),
        eval_count=sum(r.eval_count for r in sub_results),
        total_duration=sum(r.total_duration for r in sub_results),
        raw_prompt=json.dumps(messages),
        raw_response=json.dumps([r.to_dict() for r in sub_results]),
        content=f"Majority vote ({method}): {voted}\nk={k}, answers={answers}",
        extracted_answer=voted, ground_truth=q_answer,
        correct=voted_correct,
        extraction_failed=not bool(voted),
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    )
    client.log_scored(result)
    return result


def _majority_vote(answers):
    """Majority vote with deterministic lexicographic tie-break.

    Tie-break rationale: The plan specifies logprob-then-lexicographic, but
    Ollama's chat API does not reliably expose per-token logprobs.  We use
    lexicographic ordering of normalized answers, which is deterministic and
    reproducible.  This is acceptable because (a) the tie-break only matters
    when k answers are evenly split, which is uncommon, and (b) the primary
    analysis uses the correctness of the voted answer, not the vote margin.
    """
    if not answers:
        return "", "no_answers"
    counts = Counter(answers)
    max_count = max(counts.values())
    winners = sorted(a for a, c in counts.items() if c == max_count)
    return winners[0], "majority" if len(winners) == 1 else "tie_lexicographic"


def _err(model, condition, q_id, rep, seed, error, client=None):
    result = InferenceResult(
        inference_id=f"err_{q_id}_{condition}_{rep}",
        model_tag=model, condition=condition, question_id=q_id,
        rep_number=rep, seed=seed, error=error,
        correct=False, extraction_failed=True,
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    )
    if client:
        client.log_scored(result)
    return result


# ---------------------------------------------------------------------------
# Phase runners
# ---------------------------------------------------------------------------

def run_calibration(client, questions, models, reps, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    total = len(questions) * len(models) * reps
    done = 0
    for model in models:
        tt = get_model_template_tokens(client, model)
        for question in questions:
            for rep in range(reps):
                seed = SEED_GRID[rep % len(SEED_GRID)]
                run_single_inference(client, model, "A", question, rep, seed, tt)
                done += 1
                if done % 25 == 0:
                    print(f"  Calibration: {done}/{total} ({done/total*100:.0f}%)", flush=True)
    print(f"  Calibration complete: {done} inferences")


def load_completed(log_path: Path) -> set[tuple[str, str, str, int]]:
    """Load (model, condition, question_id, rep) tuples already in the log.

    Used by --resume to skip completed inferences. Condition I parent records
    are keyed normally; I_sub records are ignored (they're children of the
    parent and will be re-run if the parent is missing).
    """
    completed = set()
    if not log_path.exists():
        return completed
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            cond = r.get("condition", "")
            if cond == "I_sub":
                continue  # only track parent I records
            key = (r.get("model_tag", ""), cond, r.get("question_id", ""), r.get("rep_number", -1))
            completed.add(key)
    return completed


def run_conditions(client, questions, models, conditions, reps, trace_bank=None, scaffolds=None, completed=None):
    total = len(questions) * len(models) * len(conditions) * reps
    skipped = done = errors = 0
    for model in models:
        tt = get_model_template_tokens(client, model)
        for question in questions:
            for cond in conditions:
                for rep in range(reps):
                    seed = SEED_GRID[rep % len(SEED_GRID)]
                    if completed and (model, cond, question["id"], rep) in completed:
                        skipped += 1
                        done += 1
                        continue
                    result = run_single_inference(
                        client, model, cond, question, rep, seed, tt,
                        trace_bank=trace_bank, scaffolds=scaffolds,
                    )
                    if result.error:
                        errors += 1
                    done += 1
                    if done % 25 == 0:
                        print(f"  Progress: {done}/{total} ({done/total*100:.0f}%) skipped={skipped} errors={errors}", flush=True)
    print(f"  Complete: {done} inferences, {skipped} skipped (resumed), {errors} errors")


def run_trace_bank_generation(client, questions, models, trace_bank, seeds=None):
    if seeds is None:
        seeds = SEED_GRID
    total = len(questions) * len(models) * len(seeds)
    done = 0
    for model in models:
        tt = get_model_template_tokens(client, model)
        for question in questions:
            for seed in seeds:
                q_id = question["id"]
                if trace_bank.get_trace(q_id, model, seed) is not None:
                    done += 1
                    continue
                messages = condition_b(question["question"])
                result = client.chat(
                    model=model, messages=messages, think=True, seed=seed,
                    keep_alive=KEEP_ALIVE, condition="B", question_id=q_id, rep_number=seed,
                )
                score_inference(result, question["answer"], question.get("answer_type", "exact"))
                trace_bank.add_trace(
                    question_id=q_id, model_tag=model, seed=seed,
                    thinking_tokens=result.thinking_tokens, content=result.content,
                    correct=result.correct, domain=question.get("domain", "unknown"),
                )
                done += 1
                if done % 10 == 0:
                    print(f"  Trace bank: {done}/{total} ({done/total*100:.0f}%)", flush=True)
    trace_bank.save()
    s = trace_bank.summary()
    print(f"  Trace bank: {s['total_traces']} traces, {s['correct_rate']:.1%} correct")


def load_scaffolds(path: Path) -> dict:
    scaffolds = {}
    if not path.exists():
        return scaffolds
    for f in sorted(path.iterdir()):
        if f.suffix == ".json":
            try:
                data = json.loads(f.read_text())
            except json.JSONDecodeError as e:
                print(f"ERROR: Malformed scaffold {f.name}: {e}", file=sys.stderr)
                sys.exit(1)
            q_id = str(data.get("question_id", f.stem))
            if q_id in scaffolds:
                print(f"ERROR: Duplicate scaffold question_id '{q_id}' in {f.name}", file=sys.stderr)
                sys.exit(1)
            scaffolds[q_id] = data.get("scaffold", "")
            if "wrong_scaffold" in data:
                scaffolds[f"{q_id}_wrong"] = data["wrong_scaffold"]
            if "compressed" in data:
                scaffolds[f"{q_id}_compressed"] = data["compressed"]
    return scaffolds


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["calibration", "validation", "trace-bank", "confirmatory", "smoke-test", "mechanism"], required=True)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--models", nargs="+", default=MODELS)
    parser.add_argument("--reps", type=int, default=12)
    parser.add_argument("--conditions", nargs="+", default=None)
    parser.add_argument("--trace-bank-dir", type=Path, default=None)
    parser.add_argument("--scaffold-dir", type=Path, default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--keep-alive", default="0", help="Model keep-alive (use '30m' for calibration speed)")
    parser.add_argument("--resume", action="store_true", help="Skip inferences already in the output log (for restart recovery)")
    args = parser.parse_args()

    global KEEP_ALIVE
    KEEP_ALIVE = args.keep_alive

    args.output_dir.mkdir(parents=True, exist_ok=True)
    log_path = args.output_dir / "inference_log.jsonl"
    client = OllamaClient(log_path=log_path)

    for model in args.models:
        try:
            info = client.get_model_info(model)
            print(f"Model: {info.tag} | {info.parameter_size} | {info.quantization}")
        except Exception as e:
            print(f"ERROR: {model}: {e}", file=sys.stderr)
            sys.exit(1)

    questions = load_questions(args.questions)
    if args.limit:
        questions = questions[:args.limit]
    print(f"Loaded {len(questions)} questions")

    trace_bank = TraceBank(args.trace_bank_dir) if args.trace_bank_dir else None
    scaffolds = load_scaffolds(args.scaffold_dir) if args.scaffold_dir else {}

    if args.phase == "calibration":
        print(f"=== Calibration (A × {args.reps} reps × {len(args.models)} models) ===")
        run_calibration(client, questions, args.models, args.reps, args.output_dir)
    elif args.phase == "trace-bank":
        if not trace_bank:
            trace_bank = TraceBank(args.output_dir / "trace_bank")
        print("=== Trace Bank Generation ===")
        run_trace_bank_generation(client, questions, args.models, trace_bank)
    else:
        defaults = {"validation": ["B", "C", "F", "O"], "smoke-test": ["D", "E", "H", "I", "J"],
                     "confirmatory": list("ABCDEFGHIJO"),
                     "mechanism": ["K", "L25", "L50", "L75", "L100", "M", "N"]}
        conditions = args.conditions or defaults[args.phase]
        completed = None
        if args.resume:
            completed = load_completed(log_path)
            print(f"Resume mode: {len(completed)} completed inferences found in log")
        print(f"=== {args.phase.title()} ({conditions} × {args.reps} reps) ===")
        run_conditions(client, questions, args.models, conditions, args.reps, trace_bank, scaffolds, completed=completed)

    print("Done.")


if __name__ == "__main__":
    main()
