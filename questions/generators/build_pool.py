"""Build the full calibration question pool (250+ questions).

Generates questions across all 4 domains and writes to calibration-pool.jsonl.
"""

import json
import sys
from pathlib import Path

from math_generator import generate_math_questions
from logic_generator import generate_logic_questions
from factual_generator import generate_factual_questions
from spatial_generator import generate_spatial_questions
from hard_generator import generate_hard_questions


def build_pool(output_path: Path, target_per_domain: int = 50) -> None:
    """Generate the calibration pool.

    Target: ~360 questions (50 per original domain + 160 hard supplementary).
    """
    print(f"Generating {target_per_domain} questions per domain + hard supplement...")

    math_qs = generate_math_questions(target_per_domain)
    print(f"  Math: {len(math_qs)} questions")

    logic_qs = generate_logic_questions(target_per_domain)
    print(f"  Logic: {len(logic_qs)} questions")

    factual_qs = generate_factual_questions(target_per_domain)
    print(f"  Factual: {len(factual_qs)} questions")

    spatial_qs = generate_spatial_questions(target_per_domain)
    print(f"  Spatial: {len(spatial_qs)} questions")

    hard_qs = generate_hard_questions(160)
    print(f"  Hard supplement: {len(hard_qs)} questions")

    all_qs = math_qs + logic_qs + factual_qs + spatial_qs + hard_qs
    print(f"\nTotal: {len(all_qs)} questions")

    # Verify all questions have required fields
    required = {"id", "question", "answer", "answer_type", "domain", "steps", "template", "seed"}
    for q in all_qs:
        missing = required - set(q.keys())
        if missing:
            print(f"  WARNING: {q['id']} missing fields: {missing}", file=sys.stderr)

    # Verify unique IDs
    ids = [q["id"] for q in all_qs]
    dupes = [x for x in ids if ids.count(x) > 1]
    if dupes:
        print(f"  WARNING: duplicate IDs: {set(dupes)}", file=sys.stderr)

    # Write
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        for q in all_qs:
            f.write(json.dumps(q) + "\n")

    print(f"\nWritten to {output_path}")

    # Domain breakdown
    from collections import Counter
    domains = Counter(q["domain"] for q in all_qs)
    for domain, count in sorted(domains.items()):
        print(f"  {domain}: {count}")


if __name__ == "__main__":
    output = Path(__file__).parent.parent / "calibration-pool.jsonl"
    build_pool(output)
