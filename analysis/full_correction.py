"""Full-correction scoring analysis for paper §3.10, §3.13, §3.14, §3.15.

The shipped runner/score.py has three documented bugs (see paper §3.8 / §3.10
and ERRATA.md):

1. Chat-template token leakage: `<end_of_turn>` (Gemma) and
   `<|endoftext|>`/`<|im_start|>user` (Qwen) leak into the extracted
   answer string and break exact-match grading.
2. No structured-label aliasing: ground-truth `Box 3` requires the model
   to write exactly `Box 3`; bare `3` is silently scored wrong, even
   though Gemma in particular drops the prefix systematically.
3. The "answer is X" fallback regex truncates at any period: `the answer
   is 25.92` extracts `25` (impacts ~48/39,550 records under exact match,
   ~0.1%; nearly all are profit-loss decimal answers).

This script:
  - Implements `aggressive_strip()` for chat-template tokens
  - Implements `canonical_match()` for `Box N` / `Cup X` aliasing
  - Re-scores every (model, condition) cell on the merged Phase 2 dataset
  - Runs the full set of GEE contrasts the paper reports under the
    "full correction" scoring regime, including:
      • Per-model B−C, C−F, G−F, D−C, B−O, C−J E2E and Part-2
      • TOST equivalence for Qwen B−C
      • Question-family heterogeneity decomposition (§3.13)
      • Cluster-robustness sensitivity (question vs template vs domain)

The original `runner/score.py` is preserved as-shipped for historical
fidelity; this script applies the corrections in a separate scoring layer
without modifying the underlying logs.

Usage:
    python full_correction.py \\
        --merged-log ../outputs/confirmatory_merged/20260415/inference_log.jsonl.gz \\
        --questions ../questions/selected.jsonl \\
        --output-dir ../outputs/results/full_correction/
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

# Reuse the shipped scorer for the baseline comparison
sys.path.insert(0, str(Path(__file__).parent.parent / "runner"))
from score import extract_answer, grade, normalize_answer  # type: ignore


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def open_log(path):
    """Open a JSONL file, transparently handling .gz suffix."""
    p = str(path)
    if p.endswith(".gz"):
        return gzip.open(p, "rt", encoding="utf-8")
    return open(p, "r", encoding="utf-8")


def load_records(path):
    with open_log(path) as f:
        return [json.loads(line) for line in f]


def load_questions(path):
    qmeta = {}
    with open_log(path) as f:
        for line in f:
            q = json.loads(line)
            qmeta[q["id"]] = q
    return qmeta


# ---------------------------------------------------------------------------
# Full-correction scoring
# ---------------------------------------------------------------------------

# Chat-template tokens that leak into the visible content stream after a
# prefilled assistant turn. Any of these appearing on the same line as
# FINAL: corrupts the exact-string match.
TURN_BOUNDARIES = (
    r"<start_of_turn>", r"</start_of_turn>",
    r"<\|im_start\|>", r"<\|endoftext\|>",
)
SENTINELS = (
    r"<end_of_turn>", r"</end_of_turn>", r"<eos>", r"<bos>",
    r"<\|im_end\|>", r"<\|channel\|>",
)
_TURN_RE = re.compile("|".join(TURN_BOUNDARIES))
_SENT_RE = re.compile("|".join(SENTINELS))


def strip_templates(content: str) -> str:
    """Truncate at any second-turn boundary and remove sentinels."""
    if not content:
        return content
    parts = _TURN_RE.split(content, maxsplit=1)
    head = parts[0]
    return _SENT_RE.sub("", head)


_BOX_PREFIX = re.compile(r"^(box|cup)\s+", re.IGNORECASE)


def canonical_match(extracted: str, ground_truth: str, answer_type: str) -> bool:
    """Exact match, falling back to 'Box N' / 'Cup X' alias matching.

    Accepts bare suffix as a match when the ground truth is a structured
    label. e.g. extracted="3" matches ground_truth="Box 3".
    """
    if not extracted:
        return False
    if grade(extracted, ground_truth, answer_type):
        return True
    gt_n = normalize_answer(ground_truth)
    ex_n = normalize_answer(extracted)
    return _BOX_PREFIX.sub("", gt_n) == _BOX_PREFIX.sub("", ex_n)


# Fix for the "answer is X" fallback regex period-truncation bug (ERRATA #3).
# Original (buggy): r"(?:the answer is|answer:|...)\s*(.+?)(?:\.|$)"
# Replacement: stop at sentence boundary (period+space) or newline, not any period.
_ANSWER_IS_FIXED = re.compile(
    r"(?:the answer is|answer:|therefore,? the answer is)\s*([^\n]+?)(?:\.\s|$)",
    re.IGNORECASE | re.MULTILINE,
)
_FINAL_RE = re.compile(r"^\s*FINAL:\s*(.+)$", re.MULTILINE | re.IGNORECASE)


def extract_answer_fixed(content: str):
    """Re-implementation of `runner.score.extract_answer` with the period-truncation
    bug in the answer_is fallback fixed. All other extraction logic is unchanged.

    Returns (normalized_answer, extraction_failed, method).
    """
    if not content or not content.strip():
        return "", True, "empty"
    final_matches = _FINAL_RE.findall(content)
    if final_matches:
        ans = final_matches[-1].strip()
        if ans:
            return normalize_answer(ans), False, "final_tag"
    m = _ANSWER_IS_FIXED.search(content)
    if m:
        ans = m.group(1).strip()
        if ans:
            return normalize_answer(ans), False, "answer_is"
    # Defer to the rest of the shipped scorer's fallback chain
    return extract_answer(content)


def correct_full(record: dict, qmeta: dict) -> int:
    """Score one record under the full-correction regime.

    Applies all three fixes documented in ERRATA.md:
      1. Strip chat-template tokens before extraction.
      2. Use `extract_answer_fixed` to avoid period-truncation in fallback.
      3. Use `canonical_match` for `Box N` / `Cup X` aliasing.

    Note: condition I's content is a synthesized majority-vote string, not a
    model output. We cannot re-extract it the same way; per paper §3.14 we
    leave I scoring as-shipped (the proper fix is to re-aggregate I_sub
    answers under canonical_match, which is a separate pipeline).
    """
    if record.get("condition") == "I":
        return int(record.get("correct", False))
    q = qmeta.get(record["question_id"])
    atype = q.get("answer_type", "exact") if q else "exact"
    content = strip_templates(record.get("content", "") or "")
    extracted, failed, _ = extract_answer_fixed(content)
    if failed:
        return 0
    return 1 if canonical_match(extracted, record["ground_truth"], atype) else 0


def correct_paper(record: dict, qmeta: dict) -> int:
    """Score one record under the as-shipped paper regime (for comparison)."""
    return int(record.get("correct", False))


# ---------------------------------------------------------------------------
# Question family decomposition (paper §3.13)
# ---------------------------------------------------------------------------

def question_family(qid: str, qmeta: dict) -> str:
    q = qmeta.get(qid)
    if not q:
        return "unknown"
    gt = str(q["answer"])
    if re.match(r"^Box \d+$", gt):
        return "Box"
    if re.match(r"^Cup [A-Za-z]$", gt):
        return "Cup"
    if gt.lower() in {"true", "false"}:
        return "bool"
    if gt.lower() in {"north", "south", "east", "west", "up", "down", "left", "right"}:
        return "direction"
    if re.match(r"^[a-zA-Z]$", gt):
        return "letter"
    if re.match(r"^-?\d", gt):
        return "numeric"
    return "other"


def question_template(qid: str) -> str:
    """Strip trailing _NNNN to get the procedural-generator template name."""
    return re.sub(r"_\d+$", "", qid)


def question_domain(qid: str) -> str:
    """Coarse domain bucket — used for cluster-robustness sensitivity."""
    t = question_template(qid)
    if any(k in t for k in ("tracking", "rotation", "object", "spatial", "grid")):
        return "spatial"
    if any(k in t for k in ("logic", "knight", "multi_entity", "long_chain")):
        return "logic"
    if any(k in t for k in ("modular", "crt", "profit", "compound", "percentage", "system_of",
                            "bat_ball", "math", "work_rate", "counting")):
        return "math"
    return "other"


# ---------------------------------------------------------------------------
# GEE wrappers
# ---------------------------------------------------------------------------

def fit_gee(df: pd.DataFrame, formula: str, groups: str) -> dict:
    """Fit a Binomial/Logit GEE with exchangeable working correlation.

    Returns dict with coefs, robust SEs, p-values. None on failure.
    """
    try:
        m = smf.gee(
            formula, groups=groups, data=df,
            family=sm.families.Binomial(),
            cov_struct=sm.cov_struct.Exchangeable(),
        ).fit()
        return {
            "coefs": m.params.to_dict(),
            "ses": m.bse.to_dict(),
            "ps": m.pvalues.to_dict(),
            "n_clusters": df[groups].nunique(),
            "n_obs": len(df),
        }
    except Exception as e:
        return {"error": repr(e)}


def contrast(records, qmeta, model_tag: str, hi: str, lo: str, scorer, groups="qid",
             question_filter=None, ceiling_only=False, exclude_ceiling=False,
             part2_only=False):
    """Run a per-model GEE B−C-style contrast under a given scorer.

    `scorer` is a function `record -> 0/1`.
    `groups` is "qid", "tpl", or "dom" (clustering choice).
    Returns dict with {log_or, se, p, n}.
    """
    rows = []
    for r in records:
        if r["model_tag"] != model_tag:
            continue
        if r["condition"] not in (hi, lo):
            continue
        if question_filter is not None and not question_filter(r["question_id"]):
            continue
        eval_count = r.get("eval_count", 0)
        if exclude_ceiling and eval_count >= 8190:
            continue
        if ceiling_only and eval_count < 8190:
            continue
        if part2_only and r.get("extraction_failed", False):
            continue
        rows.append({
            "qid": r["question_id"],
            "tpl": question_template(r["question_id"]),
            "dom": question_domain(r["question_id"]),
            "cond_hi": int(r["condition"] == hi),
            "y": scorer(r, qmeta),
        })
    if not rows:
        return None
    df = pd.DataFrame(rows)
    res = fit_gee(df, "y ~ cond_hi", groups=groups)
    if "error" in res:
        return res
    return {
        "log_or": res["coefs"].get("cond_hi"),
        "se": res["ses"].get("cond_hi"),
        "p": res["ps"].get("cond_hi"),
        "n": res["n_obs"],
        "n_clusters": res["n_clusters"],
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

CONTRASTS = [("B", "C"), ("C", "F"), ("G", "F"), ("D", "C"),
             ("B", "I"), ("B", "O"), ("C", "J")]


def report_table_2_full_correction(records, qmeta) -> str:
    out = ["# Table 2-equivalent under full-correction scoring",
           "",
           "Per-model GEE pairwise contrasts; question-clustered, exchangeable, robust SEs.",
           "Values: log-OR (SE) p — note: Holm correction not re-applied here.",
           ""]
    for model in ["gemma4", "qwen3.5:9b"]:
        out.append(f"## {model}")
        out.append("")
        out.append(f"| Contrast | log-OR | SE | OR | p |")
        out.append(f"|----------|-------:|---:|---:|--:|")
        for hi, lo in CONTRASTS:
            r = contrast(records, qmeta, model, hi, lo, correct_full)
            if r is None or "error" in (r or {}):
                out.append(f"| {hi}−{lo} | — | — | — | — |")
                continue
            try:
                or_ = math.exp(r["log_or"])
            except Exception:
                or_ = float("nan")
            out.append(f"| {hi}−{lo} | {r['log_or']:+.3f} | {r['se']:.3f} | {or_:.2f} | {r['p']:.4f} |")
        out.append("")
    return "\n".join(out)


def report_qwen_bc_tost(records, qmeta) -> str:
    """Reproduces the §3.10 Qwen B−C TOST result."""
    out = ["# Qwen B−C — full-correction TOST",
           "",
           "SESOI: log-OR (−0.162, +0.166)",
           ""]
    r = contrast(records, qmeta, "qwen3.5:9b", "B", "C", correct_full)
    if r:
        log_or = r["log_or"]
        se = r["se"]
        lo = log_or - 1.645 * se
        hi = log_or + 1.645 * se
        # B−C is the negation
        bc_log = -log_or
        bc_lo, bc_hi = -hi, -lo
        in_sesoi = -0.162 <= bc_lo and bc_hi <= 0.166
        out.append(f"Qwen B−C log-OR (full-corrected): {bc_log:+.3f}")
        out.append(f"SE: {se:.3f}")
        out.append(f"90% CI: [{bc_lo:+.3f}, {bc_hi:+.3f}]")
        out.append(f"Both bounds within SESOI (TOST equivalence): {in_sesoi}")
        out.append(f"Directional p (favoring C if negative): {r['p']:.4f}")
    return "\n".join(out)


def report_question_family_heterogeneity(records, qmeta) -> str:
    """Reproduces §3.13 numbers."""
    out = ["# Question-family heterogeneity in B−C (paper §3.13)",
           "",
           "Per-family GEE B−C under full-correction scoring, question-clustered.",
           ""]
    for model in ["gemma4", "qwen3.5:9b"]:
        out.append(f"## {model}")
        out.append("")
        out.append("| Family | n_q | log-OR | SE | p |")
        out.append("|--------|----:|-------:|---:|--:|")
        for fam in ["numeric", "direction", "Box", "Cup", "bool", "letter", "other"]:
            qf = lambda qid, fam=fam: question_family(qid, qmeta) == fam
            r = contrast(records, qmeta, model, "B", "C", correct_full, question_filter=qf)
            if r is None or "error" in (r or {}):
                continue
            n_q = r.get("n_clusters", 0)
            if n_q < 5:
                continue
            out.append(f"| {fam} | {n_q} | {r['log_or']:+.3f} | {r['se']:.3f} | {r['p']:.4f} |")
        out.append("")
    return "\n".join(out)


def report_cluster_robustness(records, qmeta) -> str:
    """Reproduces §3.15-A — Claim 8 fragility under cluster-choice."""
    out = ["# Cluster-choice robustness for Gemma B−O (paper §3.15-A / Claim 8)",
           "",
           "Same B−O contrast under different cluster definitions.",
           "",
           "| Cluster unit | log-OR | SE | p |",
           "|--------------|-------:|---:|--:|"]
    for groups in ["qid", "tpl", "dom"]:
        r = contrast(records, qmeta, "gemma4", "B", "O", correct_full, groups=groups)
        if r is None or "error" in (r or {}):
            continue
        out.append(f"| {groups} (n={r.get('n_clusters', '?')}) | {r['log_or']:+.3f} | {r['se']:.3f} | {r['p']:.4f} |")
    out.append("")
    return "\n".join(out)


def report_qwen_tracking_budget(records, qmeta) -> str:
    """Reproduces §3.15-B — Qwen tracking C>B budget mediation."""
    out = ["# Qwen tracking B−C — budget mediation (paper §3.15-B)",
           "",
           "On the tracking subset (Box+Cup+direction), under different conditioning.",
           "",
           "| Conditioning | log-OR(B-C) | SE | p |",
           "|--------------|-----------:|---:|--:|"]
    qf = lambda qid: question_family(qid, qmeta) in {"Box", "Cup", "direction"}

    r1 = contrast(records, qmeta, "qwen3.5:9b", "B", "C", correct_full, question_filter=qf)
    out.append(f"| All rows (E2E) | {r1['log_or']:+.3f} | {r1['se']:.3f} | {r1['p']:.4f} |")

    r2 = contrast(records, qmeta, "qwen3.5:9b", "B", "C", correct_full, question_filter=qf, exclude_ceiling=True)
    out.append(f"| Exclude ceiling | {r2['log_or']:+.3f} | {r2['se']:.3f} | {r2['p']:.4f} |")

    r3 = contrast(records, qmeta, "qwen3.5:9b", "B", "C", correct_full, question_filter=qf, part2_only=True)
    out.append(f"| Part-2 (extracted) | {r3['log_or']:+.3f} | {r3['se']:.3f} | {r3['p']:.4f} |")
    out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--merged-log", required=True,
                    help="Path to the 16K-merged Phase 2 inference log (gzipped or plain).")
    ap.add_argument("--questions", required=True,
                    help="Path to questions/selected.jsonl.")
    ap.add_argument("--output-dir", default=".",
                    help="Where to write output reports.")
    args = ap.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.merged_log} ...", file=sys.stderr)
    records = load_records(args.merged_log)
    print(f"  {len(records)} records loaded", file=sys.stderr)

    print(f"Loading {args.questions} ...", file=sys.stderr)
    qmeta = load_questions(args.questions)
    print(f"  {len(qmeta)} questions loaded", file=sys.stderr)

    sections = [
        ("table_2_full_correction.md", report_table_2_full_correction(records, qmeta)),
        ("qwen_bc_tost.md", report_qwen_bc_tost(records, qmeta)),
        ("question_family_heterogeneity.md", report_question_family_heterogeneity(records, qmeta)),
        ("cluster_robustness_b_o.md", report_cluster_robustness(records, qmeta)),
        ("qwen_tracking_budget.md", report_qwen_tracking_budget(records, qmeta)),
    ]
    for name, body in sections:
        path = out / name
        path.write_text(body + "\n")
        print(f"  wrote {path}", file=sys.stderr)

    # Combined report
    combined = "\n\n---\n\n".join(body for _, body in sections)
    (out / "FULL_CORRECTION_REPORT.md").write_text(combined + "\n")
    print(f"  wrote {out / 'FULL_CORRECTION_REPORT.md'}", file=sys.stderr)


if __name__ == "__main__":
    main()
