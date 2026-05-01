"""Phase 1 validation analysis: verify infrastructure and compute condition accuracy.

Reads the validation inference log (JSONL with InferenceResult fields),
runs sanity checks on the pipeline, and produces a formatted report with
per-condition and per-model accuracy breakdowns.

Usage:
    python validate.py --log ../outputs/pilot/validation/inference_log.jsonl
    python validate.py --log ../outputs/pilot/validation/inference_log.jsonl --output-json results.json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Optional


# Conditions that use prefill (routed through generate_raw, so raw_prompt is NOT a JSON array)
PREFILL_CONDITIONS = {"C", "D", "E", "F", "G", "H", "J", "K", "L", "M"}

# Conditions expected in a standard validation run
DEFAULT_VALIDATION_CONDITIONS = {"B", "C", "F", "O"}


def load_log(log_path: Path) -> list[dict]:
    """Load inference log JSONL into a list of dicts."""
    results = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def group_by(results: list[dict], *keys: str) -> dict:
    """Group results by one or more keys. Returns nested defaultdicts."""
    groups = defaultdict(list)
    for r in results:
        key = tuple(r.get(k, "") for k in keys)
        if len(keys) == 1:
            key = key[0]
        groups[key].append(r)
    return dict(groups)


# ---------------------------------------------------------------------------
# Per-condition accuracy
# ---------------------------------------------------------------------------

def compute_condition_stats(results: list[dict], min_reps: int = 2) -> dict:
    """Compute per-condition and per-model accuracy stats.

    Returns dict keyed by condition, each containing:
      - overall_accuracy, n, correct, extraction_failures, mean_eval_count
      - per_model: {model: {accuracy, n, correct, extraction_failures, mean_eval_count}}
    """
    by_condition = group_by(results, "condition")
    stats = {}

    for cond, cond_results in sorted(by_condition.items()):
        n = len(cond_results)
        correct = sum(1 for r in cond_results if r.get("correct"))
        ext_fail = sum(1 for r in cond_results if r.get("extraction_failed"))
        eval_counts = [r.get("eval_count", 0) for r in cond_results]
        mean_eval = sum(eval_counts) / max(n, 1)

        cond_stat = {
            "overall_accuracy": correct / max(n, 1),
            "n": n,
            "correct": correct,
            "extraction_failures": ext_fail,
            "extraction_failure_rate": ext_fail / max(n, 1),
            "mean_eval_count": mean_eval,
            "per_model": {},
        }

        by_model = group_by(cond_results, "model_tag")
        for model, model_results in sorted(by_model.items()):
            mn = len(model_results)
            mc = sum(1 for r in model_results if r.get("correct"))
            me = sum(1 for r in model_results if r.get("extraction_failed"))
            m_eval = [r.get("eval_count", 0) for r in model_results]
            cond_stat["per_model"][model] = {
                "accuracy": mc / max(mn, 1),
                "n": mn,
                "correct": mc,
                "extraction_failures": me,
                "extraction_failure_rate": me / max(mn, 1),
                "mean_eval_count": sum(m_eval) / max(mn, 1),
            }

        stats[cond] = cond_stat

    return stats


# ---------------------------------------------------------------------------
# Sanity checks
# ---------------------------------------------------------------------------

class SanityCheck:
    """Result of a single sanity check."""

    def __init__(self, name: str, passed: bool, detail: str, critical: bool = True):
        self.name = name
        self.passed = passed
        self.detail = detail
        self.critical = critical

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "passed": self.passed,
            "detail": self.detail,
            "critical": self.critical,
        }


def run_sanity_checks(results: list[dict]) -> list[SanityCheck]:
    """Run all sanity checks on the inference log. Returns list of SanityCheck."""
    checks = []
    by_condition = group_by(results, "condition")

    # --- Condition B: should have non-empty thinking_tokens ---
    if "B" in by_condition:
        b_results = by_condition["B"]
        b_with_thinking = [r for r in b_results if r.get("thinking_tokens", "").strip()]
        rate = len(b_with_thinking) / max(len(b_results), 1)
        checks.append(SanityCheck(
            "B_has_thinking_tokens",
            rate > 0.5,
            f"{len(b_with_thinking)}/{len(b_results)} B inferences have non-empty thinking_tokens ({rate:.0%})",
        ))

    # --- Condition C: should have source_trace_id set ---
    if "C" in by_condition:
        c_results = by_condition["C"]
        c_with_trace = [r for r in c_results if r.get("source_trace_id", "").strip()]
        rate = len(c_with_trace) / max(len(c_results), 1)
        checks.append(SanityCheck(
            "C_has_source_trace_id",
            rate > 0.5,
            f"{len(c_with_trace)}/{len(c_results)} C inferences have source_trace_id ({rate:.0%})",
        ))

    # --- Condition F: should have source_trace_id AND differ from C ---
    if "F" in by_condition:
        f_results = by_condition["F"]
        f_with_trace = [r for r in f_results if r.get("source_trace_id", "").strip()]
        rate = len(f_with_trace) / max(len(f_results), 1)
        checks.append(SanityCheck(
            "F_has_source_trace_id",
            rate > 0.5,
            f"{len(f_with_trace)}/{len(f_results)} F inferences have source_trace_id ({rate:.0%})",
        ))

        # Check that F's raw_prompt differs from C's for the same question/model/rep
        if "C" in by_condition:
            c_prompts = {}
            for r in by_condition["C"]:
                key = (r.get("question_id"), r.get("model_tag"), r.get("rep_number"))
                c_prompts[key] = r.get("raw_prompt", "")

            f_differs = 0
            f_comparable = 0
            for r in f_results:
                key = (r.get("question_id"), r.get("model_tag"), r.get("rep_number"))
                if key in c_prompts:
                    f_comparable += 1
                    if r.get("raw_prompt", "") != c_prompts[key]:
                        f_differs += 1

            if f_comparable > 0:
                diff_rate = f_differs / f_comparable
                checks.append(SanityCheck(
                    "F_prefill_differs_from_C",
                    diff_rate > 0.8,
                    f"{f_differs}/{f_comparable} F prompts differ from matched C prompts ({diff_rate:.0%})",
                ))

    # --- Condition O: NO thinking_tokens, but CoT in content ---
    if "O" in by_condition:
        o_results = by_condition["O"]
        o_no_think = [r for r in o_results if not r.get("thinking_tokens", "").strip()]
        no_think_rate = len(o_no_think) / max(len(o_results), 1)
        checks.append(SanityCheck(
            "O_no_thinking_tokens",
            no_think_rate > 0.8,
            f"{len(o_no_think)}/{len(o_results)} O inferences have empty thinking_tokens ({no_think_rate:.0%})",
        ))

        # Check that O's think field is False
        o_think_false = [r for r in o_results if not r.get("think", False)]
        think_false_rate = len(o_think_false) / max(len(o_results), 1)
        checks.append(SanityCheck(
            "O_think_is_false",
            think_false_rate > 0.8,
            f"{len(o_think_false)}/{len(o_results)} O inferences have think=false ({think_false_rate:.0%})",
        ))

        # Check that content shows reasoning (heuristic: content length > 100 chars or has step indicators)
        o_has_cot = 0
        for r in o_results:
            content = r.get("content", "")
            has_steps = any(indicator in content.lower() for indicator in [
                "step", "first", "then", "therefore", "because", "let's", "we need",
                "1.", "2.", "1)", "2)",
            ])
            long_enough = len(content) > 100
            if has_steps or long_enough:
                o_has_cot += 1
        cot_rate = o_has_cot / max(len(o_results), 1)
        checks.append(SanityCheck(
            "O_shows_visible_cot",
            cot_rate > 0.5,
            f"{o_has_cot}/{len(o_results)} O inferences show visible CoT in content ({cot_rate:.0%})",
            critical=False,
        ))

    # --- Prefill conditions should use generate_raw (raw_prompt is NOT a JSON array) ---
    for cond in sorted(PREFILL_CONDITIONS & set(by_condition.keys())):
        cond_results = by_condition[cond]
        non_json_array = 0
        for r in cond_results:
            rp = r.get("raw_prompt", "").strip()
            # Chat messages are logged as JSON arrays starting with [
            if rp and not rp.startswith("["):
                non_json_array += 1
        rate = non_json_array / max(len(cond_results), 1)
        checks.append(SanityCheck(
            f"{cond}_uses_raw_prompt",
            rate > 0.8,
            f"{non_json_array}/{len(cond_results)} {cond} inferences used raw prompt (not JSON array) ({rate:.0%})",
        ))

    # --- All conditions: non-zero eval_count ---
    for cond in sorted(by_condition.keys()):
        cond_results = by_condition[cond]
        nonzero = [r for r in cond_results if r.get("eval_count", 0) > 0]
        rate = len(nonzero) / max(len(cond_results), 1)
        checks.append(SanityCheck(
            f"{cond}_nonzero_eval_count",
            rate > 0.8,
            f"{len(nonzero)}/{len(cond_results)} {cond} inferences have eval_count > 0 ({rate:.0%})",
        ))

    # --- No condition should have >50% extraction failures ---
    for cond in sorted(by_condition.keys()):
        cond_results = by_condition[cond]
        ext_fail = sum(1 for r in cond_results if r.get("extraction_failed"))
        fail_rate = ext_fail / max(len(cond_results), 1)
        checks.append(SanityCheck(
            f"{cond}_extraction_failure_rate",
            fail_rate <= 0.50,
            f"{cond} extraction failure rate: {ext_fail}/{len(cond_results)} ({fail_rate:.0%})",
        ))

    return checks


# ---------------------------------------------------------------------------
# Comparative analysis
# ---------------------------------------------------------------------------

def compute_comparisons(stats: dict) -> list[dict]:
    """Compute key comparative contrasts between conditions.

    Returns list of comparison dicts with delta, interpretation, etc.
    """
    comparisons = []

    def _compare(name: str, cond_a: str, cond_b: str, description: str):
        if cond_a not in stats or cond_b not in stats:
            return
        acc_a = stats[cond_a]["overall_accuracy"]
        acc_b = stats[cond_b]["overall_accuracy"]
        delta = acc_a - acc_b
        comparisons.append({
            "name": name,
            "description": description,
            "condition_high": cond_a,
            "condition_low": cond_b,
            "accuracy_high": acc_a,
            "accuracy_low": acc_b,
            "delta": delta,
            "per_model": {},
        })

        # Per-model deltas
        models_a = stats[cond_a]["per_model"]
        models_b = stats[cond_b]["per_model"]
        for model in sorted(set(models_a.keys()) & set(models_b.keys())):
            m_acc_a = models_a[model]["accuracy"]
            m_acc_b = models_b[model]["accuracy"]
            comparisons[-1]["per_model"][model] = {
                "accuracy_high": m_acc_a,
                "accuracy_low": m_acc_b,
                "delta": m_acc_a - m_acc_b,
            }

    # B vs A: does thinking help?
    _compare("B_vs_A", "B", "A", "Does thinking help? (B-A = total think effect)")

    # C vs B: does trace replay match live thinking?
    _compare("C_vs_B", "B", "C", "Does trace replay match live thinking? (B-C = internal reasoning effect)")

    # F vs C: does shuffling degrade performance?
    _compare("C_vs_F", "C", "F", "Does shuffling degrade? (C-F = semantic content effect)")

    # O vs B: does visible CoT match hidden thinking?
    _compare("B_vs_O", "B", "O", "Think-mode vs visible CoT? (B-O = think-mode mechanism effect)")

    return comparisons


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_report(
    stats: dict,
    checks: list[SanityCheck],
    comparisons: list[dict],
    log_path: Path,
    total_records: int,
) -> str:
    """Format the full validation report for stdout."""
    lines = []
    lines.append("=" * 70)
    lines.append("  VALIDATION ANALYSIS REPORT")
    lines.append("=" * 70)
    lines.append(f"Log: {log_path}")
    lines.append(f"Total inference records: {total_records}")
    lines.append(f"Conditions found: {', '.join(sorted(stats.keys()))}")
    lines.append("")

    # --- Per-condition accuracy ---
    lines.append("-" * 70)
    lines.append("  PER-CONDITION ACCURACY")
    lines.append("-" * 70)
    for cond, s in sorted(stats.items()):
        lines.append(f"\n  Condition {cond}  (n={s['n']})")
        lines.append(f"    Overall accuracy:       {s['overall_accuracy']:.1%}  ({s['correct']}/{s['n']})")
        lines.append(f"    Extraction failures:    {s['extraction_failures']}  ({s['extraction_failure_rate']:.0%})")
        lines.append(f"    Mean eval_count:        {s['mean_eval_count']:.0f} tokens")
        for model, ms in sorted(s["per_model"].items()):
            lines.append(f"      {model:20s}  {ms['accuracy']:.1%}  ({ms['correct']}/{ms['n']})  "
                         f"ext_fail={ms['extraction_failures']}  eval={ms['mean_eval_count']:.0f}")
    lines.append("")

    # --- Sanity checks ---
    lines.append("-" * 70)
    lines.append("  SANITY CHECKS")
    lines.append("-" * 70)
    passed_count = sum(1 for c in checks if c.passed)
    failed_critical = [c for c in checks if not c.passed and c.critical]
    failed_minor = [c for c in checks if not c.passed and not c.critical]
    lines.append(f"  {passed_count}/{len(checks)} passed")
    if failed_critical:
        lines.append(f"  {len(failed_critical)} CRITICAL failures")
    if failed_minor:
        lines.append(f"  {len(failed_minor)} minor failures")
    lines.append("")

    for c in checks:
        status = "PASS" if c.passed else ("FAIL" if c.critical else "WARN")
        lines.append(f"  [{status:4s}] {c.name}")
        lines.append(f"         {c.detail}")
    lines.append("")

    # --- Comparative analysis ---
    if comparisons:
        lines.append("-" * 70)
        lines.append("  COMPARATIVE ANALYSIS")
        lines.append("-" * 70)
        for comp in comparisons:
            delta_str = f"{comp['delta']:+.1%}"
            lines.append(f"\n  {comp['name']}: {comp['description']}")
            lines.append(f"    {comp['condition_high']}: {comp['accuracy_high']:.1%}  vs  "
                         f"{comp['condition_low']}: {comp['accuracy_low']:.1%}  "
                         f"(delta={delta_str})")
            for model, md in sorted(comp["per_model"].items()):
                lines.append(f"      {model:20s}  {md['accuracy_high']:.1%} vs {md['accuracy_low']:.1%}  "
                             f"(delta={md['delta']:+.1%})")
        lines.append("")

    # --- Overall verdict ---
    lines.append("-" * 70)
    if failed_critical:
        lines.append("  VERDICT: FAIL — critical sanity check failures detected")
        for c in failed_critical:
            lines.append(f"    - {c.name}: {c.detail}")
    else:
        lines.append("  VERDICT: PASS — all critical sanity checks passed")
        if failed_minor:
            lines.append(f"  ({len(failed_minor)} minor warnings — see above)")
    lines.append("=" * 70)

    return "\n".join(lines)


def build_json_summary(
    stats: dict,
    checks: list[SanityCheck],
    comparisons: list[dict],
    log_path: str,
    total_records: int,
) -> dict:
    """Build structured JSON summary."""
    failed_critical = [c for c in checks if not c.passed and c.critical]
    return {
        "log_path": str(log_path),
        "total_records": total_records,
        "conditions": sorted(stats.keys()),
        "all_critical_passed": len(failed_critical) == 0,
        "condition_stats": stats,
        "sanity_checks": [c.to_dict() for c in checks],
        "comparisons": comparisons,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Validation analysis for the thinking-token experiment."
    )
    parser.add_argument(
        "--log", type=Path, required=True,
        help="Path to validation inference_log.jsonl",
    )
    parser.add_argument(
        "--output-json", type=Path, default=None,
        help="Optional path to write JSON summary",
    )
    parser.add_argument(
        "--min-reps", type=int, default=2,
        help="Minimum reps per condition/model to include (default: 2)",
    )
    parser.add_argument(
        "--expect-conditions", nargs="+", default=None,
        help="Conditions that MUST be present (e.g. B C F O). Fails if any are missing.",
    )
    parser.add_argument(
        "--run-id", type=str, default=None,
        help="Filter to a specific run (by timestamp prefix or inference_id pattern). "
             "Prevents stale data contamination from prior runs.",
    )
    args = parser.parse_args()

    if not args.log.exists():
        print(f"ERROR: Log file not found: {args.log}", file=sys.stderr)
        sys.exit(1)

    # Load data
    results = load_log(args.log)
    if not results:
        print("ERROR: Log file is empty.", file=sys.stderr)
        sys.exit(1)

    # Filter by run-id (timestamp prefix) to prevent stale data contamination
    if args.run_id:
        before = len(results)
        results = [r for r in results if r.get("timestamp", "").startswith(args.run_id)]
        print(f"NOTE: Filtered to run-id '{args.run_id}': {len(results)}/{before} records")
        if not results:
            print("ERROR: No records match --run-id filter.", file=sys.stderr)
            sys.exit(1)

    # Note error records (included in stats for ITT, just reported here)
    error_results = [r for r in results if r.get("error")]
    if error_results:
        error_conds = defaultdict(int)
        for r in error_results:
            error_conds[r.get("condition", "?")] += 1
        print(f"NOTE: {len(error_results)} error records in dataset (included per ITT): {dict(error_conds)}")

    # Compute stats (on all results, including errors, for ITT principle)
    stats = compute_condition_stats(results, min_reps=args.min_reps)

    # Sanity checks
    checks = run_sanity_checks(results)

    # Check expected conditions are present
    if args.expect_conditions:
        expected = set(args.expect_conditions)
        found = set(stats.keys())
        missing = expected - found
        if missing:
            checks.append(SanityCheck(
                "expected_conditions_present",
                False,
                f"Expected conditions {sorted(missing)} not found in log. "
                f"Found: {sorted(found)}. Trace bank may be empty or conditions failed silently.",
                critical=True,
            ))
        else:
            checks.append(SanityCheck(
                "expected_conditions_present",
                True,
                f"All expected conditions present: {sorted(expected)}",
            ))

    # Enforce min-reps: fail if any condition has fewer than min_reps per model
    for cond, s in stats.items():
        for model, ms in s["per_model"].items():
            if ms["n"] < args.min_reps:
                checks.append(SanityCheck(
                    f"{cond}_{model}_min_reps",
                    False,
                    f"{cond}/{model} has {ms['n']} inferences, need >= {args.min_reps}",
                    critical=True,
                ))

    # Comparisons
    comparisons = compute_comparisons(stats)

    # Report
    report = format_report(stats, checks, comparisons, args.log, len(results))
    print(report)

    # JSON output
    if args.output_json:
        summary = build_json_summary(stats, checks, comparisons, str(args.log), len(results))
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output_json, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"\nJSON summary written to {args.output_json}")

    # Exit code
    failed_critical = [c for c in checks if not c.passed and c.critical]
    if failed_critical:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
