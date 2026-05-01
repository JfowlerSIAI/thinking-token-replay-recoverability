"""Phase 1 calibration analysis: select items in 30-70% accuracy band.

Reads the calibration inference log, computes per-item accuracy for each model,
and selects items that fall in the target band for BOTH models.

Usage:
    python calibrate.py --log ../outputs/pilot/inference_log.jsonl --output ../questions/selected.jsonl
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_results(log_path: Path) -> dict:
    """Load inference results grouped by (model, question_id)."""
    results = defaultdict(lambda: defaultdict(list))
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            model = r["model_tag"]
            q_id = r["question_id"]
            correct = 1 if r.get("correct") else 0
            results[model][q_id].append(correct)
    return results


def compute_accuracy(scores: list) -> float:
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def select_items(
    results: dict,
    questions_path: Path,
    low: float = 0.30,
    high: float = 0.70,
    min_reps: int = 3,
) -> tuple[list[dict], dict]:
    """Select items in the target accuracy band for all models.

    Returns (selected_questions, stats_dict).
    """
    models = sorted(results.keys())
    all_question_ids = set()
    for model_qs in results.values():
        all_question_ids |= set(model_qs.keys())

    # Load original questions for metadata
    q_lookup = {}
    with open(questions_path) as f:
        for line in f:
            q = json.loads(line.strip())
            q_lookup[q["id"]] = q

    # Compute per-model accuracy for each question
    per_item = {}
    for q_id in sorted(all_question_ids):
        item = {"id": q_id, "accuracies": {}}
        in_band_all = True
        for model in models:
            scores = results[model].get(q_id, [])
            if len(scores) < min_reps:
                in_band_all = False
                continue
            acc = compute_accuracy(scores)
            item["accuracies"][model] = {
                "accuracy": acc,
                "n": len(scores),
                "correct": sum(scores),
            }
            if not (low <= acc <= high):
                in_band_all = False
        item["in_band"] = in_band_all
        per_item[q_id] = item

    # Select in-band items
    selected = []
    for q_id, item in per_item.items():
        if item["in_band"] and q_id in q_lookup:
            q = q_lookup[q_id].copy()
            q["calibration"] = item["accuracies"]
            selected.append(q)

    # Statistics
    domain_counts = defaultdict(int)
    for q in selected:
        domain_counts[q["domain"]] += 1

    stats = {
        "total_items": len(all_question_ids),
        "models": models,
        "min_reps": min_reps,
        "band": f"{low:.0%}-{high:.0%}",
        "in_band": len(selected),
        "by_domain": dict(domain_counts),
        "per_model_overall": {},
    }
    for model in models:
        all_scores = [s for q_scores in results[model].values() for s in q_scores]
        stats["per_model_overall"][model] = compute_accuracy(all_scores) if all_scores else 0

    return selected, stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--low", type=float, default=0.30)
    parser.add_argument("--high", type=float, default=0.70)
    parser.add_argument("--min-reps", type=int, default=3)
    args = parser.parse_args()

    results = load_results(args.log)
    selected, stats = select_items(results, args.questions, args.low, args.high, args.min_reps)

    print(f"=== Calibration Analysis ===")
    print(f"Total items tested: {stats['total_items']}")
    print(f"Models: {stats['models']}")
    print(f"Band: {stats['band']}")
    print(f"Items in band (both models): {stats['in_band']}")
    print(f"By domain: {stats['by_domain']}")
    for model, acc in stats["per_model_overall"].items():
        print(f"  {model} overall: {acc:.1%}")

    if selected:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            for q in selected:
                f.write(json.dumps(q) + "\n")
        print(f"\nSelected {len(selected)} items written to {args.output}")
    else:
        print("\nWARNING: No items in target band. Consider relaxing the band or adding harder questions.")

    # Detailed report
    print(f"\n=== Per-model accuracy distribution ===")
    for model in stats["models"]:
        accs = []
        for q_id in sorted(results[model].keys()):
            scores = results[model][q_id]
            accs.append(compute_accuracy(scores))
        if accs:
            bins = [0] * 11
            for a in accs:
                bins[min(10, int(a * 10))] += 1
            print(f"\n{model}:")
            for i, count in enumerate(bins):
                lo = i * 10
                hi = lo + 10
                bar = "#" * count
                marker = " ***" if 3 <= i <= 7 else ""
                print(f"  {lo:3d}-{hi:3d}%: {count:3d} {bar}{marker}")


if __name__ == "__main__":
    main()
