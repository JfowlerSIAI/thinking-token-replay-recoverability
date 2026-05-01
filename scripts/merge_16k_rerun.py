"""Reconstruct the 16K-merged Phase 2 dataset (paper §2.7, §3.4).

The merged dataset is built from two inputs:

  1. The original Phase 2 confirmatory log (Ollama 0.20.2, num_predict=8192):
     outputs/confirmatory/20260408_100418_inference_log.jsonl.gz

  2. The 16K-rerun log of the 368 Qwen-B Phase-2 inferences that hit the
     8192-token ceiling (Ollama 0.20.6, num_predict=16384, num_ctx=24576):
     outputs/confirmatory_16k/20260414_192703_qwen_b_rerun/inference_log.jsonl.gz

The merge rule:

  For each Qwen-B (question_id, rep_number) tuple that hit the 8K ceiling
  in the original run (eval_count >= 8190), replace the original row with
  the corresponding 16K-rerun row. All other rows are kept as-is.

Caveats (also noted in paper §2.7 and §7):

  - The selection criterion (ceiling-hit at 8K) is post-treatment, not
    pre-registered. The merged dataset identifies an "adaptive Qwen-B
    rescue policy" estimand, not a budget-normalized treatment effect.
  - The 16K rerun was collected under Ollama 0.20.6 vs the original
    Ollama 0.20.2. We cannot rule out that some of the rescue is a
    cross-version inference-stack difference. Model digests were not
    logged at collection time.
  - Only Qwen-B was rerun. Qwen-C also has a 30% 8K ceiling-hit rate
    but was not rerun. So the merged Qwen B vs unmerged Qwen C is an
    asymmetric comparison.

Usage:

    python scripts/merge_16k_rerun.py \\
        --original outputs/confirmatory/20260408_100418_inference_log.jsonl.gz \\
        --rerun outputs/confirmatory_16k/20260414_192703_qwen_b_rerun/inference_log.jsonl.gz \\
        --output outputs/confirmatory_merged/20260415/inference_log.jsonl.gz

The output is byte-identical to the published merged log when run on the
published inputs.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path


def open_log(path, mode="rt"):
    p = str(path)
    if p.endswith(".gz"):
        return gzip.open(p, mode, encoding="utf-8") if "t" in mode else gzip.open(p, mode)
    return open(p, mode, encoding="utf-8") if "t" in mode else open(p, mode)


def load_records(path):
    with open_log(path) as f:
        return [json.loads(line) for line in f]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--original", required=True,
                    help="Original Phase 2 confirmatory inference log (.jsonl or .jsonl.gz)")
    ap.add_argument("--rerun", required=True,
                    help="16K Qwen-B rerun inference log")
    ap.add_argument("--output", required=True,
                    help="Output path for merged log (.jsonl or .jsonl.gz)")
    ap.add_argument("--ceiling-threshold", type=int, default=8190,
                    help="eval_count threshold for 'ceiling hit' (default 8190 — token-ish-equal-to-8192)")
    args = ap.parse_args()

    print(f"Loading original: {args.original}", file=sys.stderr)
    orig = load_records(args.original)
    print(f"  {len(orig):,} records", file=sys.stderr)

    print(f"Loading rerun: {args.rerun}", file=sys.stderr)
    rerun = load_records(args.rerun)
    print(f"  {len(rerun):,} records", file=sys.stderr)

    # Index rerun by (question_id, rep_number, model_tag) for the Qwen-B replacement set
    rerun_idx = {}
    for r in rerun:
        if r.get("model_tag") != "qwen3.5:9b":
            continue
        if r.get("condition") != "B":
            continue
        key = (r["question_id"], r["rep_number"])
        if key in rerun_idx:
            print(f"WARN duplicate rerun row for {key}", file=sys.stderr)
        rerun_idx[key] = r
    print(f"  {len(rerun_idx)} Qwen-B rerun rows indexed", file=sys.stderr)

    # Walk original, replace ceiling-hit Qwen-B rows
    merged = []
    n_replaced = 0
    n_ceiling_hits_seen = 0
    for r in orig:
        is_qwen_b = r.get("model_tag") == "qwen3.5:9b" and r.get("condition") == "B"
        ceiling_hit = is_qwen_b and r.get("eval_count", 0) >= args.ceiling_threshold
        if ceiling_hit:
            n_ceiling_hits_seen += 1
            key = (r["question_id"], r["rep_number"])
            replacement = rerun_idx.get(key)
            if replacement is None:
                print(f"WARN no rerun match for ceiling-hit {key}; keeping original",
                      file=sys.stderr)
                merged.append(r)
                continue
            merged.append(replacement)
            n_replaced += 1
        else:
            merged.append(r)

    print(f"\nMerge summary:", file=sys.stderr)
    print(f"  Original rows: {len(orig):,}", file=sys.stderr)
    print(f"  Qwen-B 8K ceiling hits in original: {n_ceiling_hits_seen}", file=sys.stderr)
    print(f"  Rows replaced from rerun: {n_replaced}", file=sys.stderr)
    print(f"  Output rows: {len(merged):,}", file=sys.stderr)

    # Write
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    if str(out).endswith(".gz"):
        with gzip.open(out, "wt", encoding="utf-8") as f:
            for r in merged:
                f.write(json.dumps(r) + "\n")
    else:
        with open(out, "w", encoding="utf-8") as f:
            for r in merged:
                f.write(json.dumps(r) + "\n")
    print(f"\nWrote: {out}", file=sys.stderr)


if __name__ == "__main__":
    main()
