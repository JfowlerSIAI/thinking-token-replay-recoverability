"""Phase 3 mechanism deep-dive analysis for the thinking-token experiment.

Post-audit revision (tri-agent audit 2026-04-14). Key changes:
- Cross-phase comparisons downgraded to historical-control (different Ollama
  versions, rep counts, dates). Stronger caveats throughout.
- "Simpson's paradox" relabeled as crossover interaction / model heterogeneity.
- M vs L100 reframed: trace-source quality confound (M uses strong-model
  compressed traces, not just mechanical compression).
- Qwen L/N reframed as context-window pathology, not mechanism evidence.
- Qwen N-B explicitly voided (both arms truncation-dominated).
- Within-phase L pairwise contrasts added (L100 vs L25, etc.).
- "Monotone" label removed for non-significant 4-point tau.

Analyzes conditions K, L25, L50, L75, L100, M, N against Phase 2 reference
conditions (A, B, C, D) on the same 39-item subset. Produces:

1. Per-condition accuracy table (ITT + PP) by model
2. Two-part extraction decomposition
3. Mechanism contrasts with audit caveats
4. Within-phase L pairwise contrasts
5. Dose-response trend analysis (aggregate + trial-level note)
6. Key findings summary

Usage:
    python analyze_mechanism.py \
        --mechanism-log ../outputs/mechanism/20260412_215554/inference_log.jsonl \
        --phase2-log ../outputs/confirmatory/20260408_100418/inference_log.jsonl \
        --phase3-questions ../questions/phase3-subset.jsonl \
        --output-dir ../outputs/results/phase3/
"""

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as sp_stats

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MECHANISM_CONDITIONS = ["K", "L25", "L50", "L75", "L100", "M", "N"]
PHASE2_REFERENCE = ["A", "B", "C", "D"]  # loaded from Phase 2 on same subset
L_DOSES = [("L25", 0.25), ("L50", 0.50), ("L75", 0.75), ("L100", 1.00)]

# Mechanism contrasts: (name, high_cond, low_cond, description, high_source, low_source)
# source = "p3" or "p2" indicating which dataset the condition comes from
MECHANISM_CONTRASTS = [
    ("K-C",   "K",    "C",    "Cross-model trace vs self-trace (verbosity confound)",  "p3", "p2"),
    ("M-L100","M",    "L100", "Strong-model compressed vs raw full trace",             "p3", "p3"),
    ("M-C",   "M",    "C",    "Strong-model compressed vs self-trace",                 "p3", "p2"),
    ("M-D",   "M",    "D",    "Strong-model compressed vs expert scaffold",            "p3", "p2"),
    ("N-B",   "N",    "B",    "Deterministic think vs stochastic think",               "p3", "p2"),
    ("L100-C","L100", "C",    "Full dose trace vs Phase 2 self-trace (replication)",   "p3", "p2"),
    ("L25-A", "L25",  "A",    "Quarter trace vs baseline (any signal?)",               "p3", "p2"),
]

# Within-phase L pairwise contrasts (no cross-phase confound)
L_PAIRWISE_CONTRASTS = [
    ("L100-L25", "L100", "L25", "Full vs quarter trace (within-phase)"),
    ("L100-L50", "L100", "L50", "Full vs half trace (within-phase)"),
    ("L75-L25",  "L75",  "L25", "Three-quarter vs quarter trace"),
    ("L50-L25",  "L50",  "L25", "Half vs quarter trace"),
]

# Contrasts where Qwen is truncation-dominated and interpretation is void
QWEN_VOID_CONTRASTS = {"N-B"}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_jsonl(path: Path) -> list[dict]:
    results = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                results.append(json.loads(line))
    return results


def load_phase3_qids(path: Path) -> set[str]:
    """Load question IDs from phase3-subset.jsonl (field is 'id')."""
    qids = set()
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                qids.add(json.loads(line)["id"])
    return qids


def group_by(records: list[dict], *keys: str) -> dict:
    groups = defaultdict(list)
    for r in records:
        key = tuple(r.get(k, "") for k in keys)
        if len(keys) == 1:
            key = key[0]
        groups[key].append(r)
    return dict(groups)


# ---------------------------------------------------------------------------
# Accuracy computation
# ---------------------------------------------------------------------------

def compute_accuracy(records: list[dict]) -> dict:
    n = len(records)
    if n == 0:
        return {"n": 0, "correct": 0, "acc_itt": 0.0,
                "ext_fail": 0, "ext_fail_rate": 0.0,
                "n_pp": 0, "correct_pp": 0, "acc_pp": 0.0,
                "mean_eval_count": 0.0, "ceiling_hits": 0}
    correct = sum(1 for r in records if r.get("correct"))
    ext_fail = sum(1 for r in records if r.get("extraction_failed"))
    n_pp = n - ext_fail
    correct_pp = sum(1 for r in records if r.get("correct") and not r.get("extraction_failed"))
    eval_counts = [r.get("eval_count", 0) for r in records]
    ceiling_hits = sum(1 for r in records if r.get("eval_count", 0) >= 8190)
    return {
        "n": n,
        "correct": correct,
        "acc_itt": correct / n,
        "ext_fail": ext_fail,
        "ext_fail_rate": ext_fail / n,
        "n_pp": n_pp,
        "correct_pp": correct_pp,
        "acc_pp": correct_pp / max(n_pp, 1),
        "mean_eval_count": sum(eval_counts) / n,
        "ceiling_hits": ceiling_hits,
    }


def build_accuracy_table(records: list[dict], conditions: list[str]) -> dict:
    by_cond = group_by(records, "condition")
    table = {}
    for cond in conditions:
        if cond not in by_cond:
            continue
        cond_recs = by_cond[cond]
        overall = compute_accuracy(cond_recs)
        by_model = group_by(cond_recs, "model_tag")
        models = {}
        for model, mrecs in sorted(by_model.items()):
            models[model] = compute_accuracy(mrecs)
        overall["per_model"] = models
        table[cond] = overall
    return table


# ---------------------------------------------------------------------------
# Odds ratio + CI
# ---------------------------------------------------------------------------

def odds_ratio_ci(n1_correct, n1_total, n2_correct, n2_total, alpha=0.05):
    a = n1_correct + 0.5
    b = (n1_total - n1_correct) + 0.5
    c = n2_correct + 0.5
    d = (n2_total - n2_correct) + 0.5
    log_or = math.log(a * d) - math.log(b * c)
    se = math.sqrt(1/a + 1/b + 1/c + 1/d)
    z_crit = sp_stats.norm.ppf(1 - alpha / 2)
    return {
        "or": math.exp(log_or),
        "log_or": log_or,
        "se": se,
        "ci_lower": math.exp(log_or - z_crit * se),
        "ci_upper": math.exp(log_or + z_crit * se),
        "p_value": 2 * sp_stats.norm.sf(abs(log_or / se)),
    }


def _sig(p):
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"


# ---------------------------------------------------------------------------
# Holm-Bonferroni
# ---------------------------------------------------------------------------

def holm_bonferroni(p_values: list[float]) -> list[float]:
    n = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted = [0.0] * n
    cummax = 0.0
    for rank, (orig_idx, p) in enumerate(indexed):
        adj = p * (n - rank)
        cummax = max(cummax, adj)
        adjusted[orig_idx] = min(cummax, 1.0)
    return adjusted


# ---------------------------------------------------------------------------
# Dose-response analysis
# ---------------------------------------------------------------------------

def dose_response_analysis(records: list[dict], model: str) -> dict:
    """Analyze L dose-response for a single model.

    Returns per-dose stats, Jonckheere-Terpstra trend test approximation,
    and logistic regression coefficient.
    """
    doses = {}
    for dose_label, dose_frac in L_DOSES:
        recs = [r for r in records
                if r["condition"] == dose_label and r["model_tag"] == model]
        if not recs:
            continue
        stats = compute_accuracy(recs)
        doses[dose_label] = {
            "fraction": dose_frac,
            "n": stats["n"],
            "acc_itt": stats["acc_itt"],
            "acc_pp": stats["acc_pp"],
            "ext_fail_rate": stats["ext_fail_rate"],
            "ceiling_hits": stats["ceiling_hits"],
        }

    # Jonckheere-Terpstra approximation via Mann-Kendall on dose vs accuracy
    fractions = []
    accuracies_itt = []
    accuracies_pp = []
    for dl, df in L_DOSES:
        if dl in doses:
            fractions.append(df)
            accuracies_itt.append(doses[dl]["acc_itt"])
            accuracies_pp.append(doses[dl]["acc_pp"])

    # Kendall's tau as monotonicity test
    tau_itt, p_tau_itt = sp_stats.kendalltau(fractions, accuracies_itt) if len(fractions) >= 3 else (0, 1)
    tau_pp, p_tau_pp = sp_stats.kendalltau(fractions, accuracies_pp) if len(fractions) >= 3 else (0, 1)

    # Logistic regression (dose -> correct) via statsmodels-free approach
    # Simple: aggregate proportion at each dose, weighted least squares on logit
    log_reg = _simple_logistic_trend(records, model)

    return {
        "doses": doses,
        "kendall_tau_itt": tau_itt,
        "kendall_p_itt": p_tau_itt,
        "kendall_tau_pp": tau_pp,
        "kendall_p_pp": p_tau_pp,
        "logistic_trend": log_reg,
    }


def _simple_logistic_trend(records: list[dict], model: str) -> dict:
    """Fit dose -> P(correct) via weighted logistic regression on aggregates."""
    xs = []
    ys = []
    ns = []
    for dose_label, dose_frac in L_DOSES:
        recs = [r for r in records
                if r["condition"] == dose_label and r["model_tag"] == model]
        if not recs:
            continue
        n = len(recs)
        k = sum(1 for r in recs if r.get("correct"))
        xs.append(dose_frac)
        ys.append(k / n)
        ns.append(n)

    if len(xs) < 2:
        return {"beta": 0, "se": 0, "p": 1, "direction": "insufficient data"}

    # Iteratively reweighted least squares on logit(p) = a + b*dose
    # Simplified: use numpy lstsq on logit-transformed proportions
    xs = np.array(xs)
    ys = np.array(ys)
    ns = np.array(ns)

    # Clamp to avoid log(0)
    ys_c = np.clip(ys, 0.01, 0.99)
    logits = np.log(ys_c / (1 - ys_c))
    weights = np.sqrt(ns * ys_c * (1 - ys_c))  # approx information weights

    # Weighted least squares: logit(p) = a + b * dose
    X = np.column_stack([np.ones_like(xs), xs])
    W = np.diag(weights)
    try:
        beta = np.linalg.solve(X.T @ W @ X, X.T @ W @ logits)
        residuals = logits - X @ beta
        mse = np.sum(weights**2 * residuals**2) / max(len(xs) - 2, 1)
        var_beta = mse * np.linalg.inv(X.T @ W @ X)
        se_slope = np.sqrt(max(var_beta[1, 1], 1e-10))
        z = beta[1] / se_slope
        p = 2 * sp_stats.norm.sf(abs(z))
    except np.linalg.LinAlgError:
        return {"beta": 0, "se": 0, "p": 1, "direction": "singular"}

    return {
        "beta": float(beta[1]),
        "se": float(se_slope),
        "p": float(p),
        "direction": "increasing" if beta[1] > 0 else "decreasing",
    }


# ---------------------------------------------------------------------------
# Per-question dose-response detail
# ---------------------------------------------------------------------------

def per_question_dose_response(records: list[dict], model: str) -> dict:
    """For each question, compute accuracy at each dose level."""
    by_q = group_by(records, "question_id")
    q_results = {}
    for qid, qrecs in sorted(by_q.items()):
        qmodel = [r for r in qrecs if r["model_tag"] == model
                  and r["condition"].startswith("L")]
        if not qmodel:
            continue
        row = {}
        for dose_label, dose_frac in L_DOSES:
            drecs = [r for r in qmodel if r["condition"] == dose_label]
            if drecs:
                row[dose_label] = sum(1 for r in drecs if r.get("correct")) / len(drecs)
            else:
                row[dose_label] = None
        q_results[qid] = row
    return q_results


# ---------------------------------------------------------------------------
# Contrast computation
# ---------------------------------------------------------------------------

def compute_mechanism_contrast(name, cond_hi, cond_lo, desc,
                                hi_source, lo_source,
                                p3_table, p2_table):
    """Compute a mechanism contrast between two conditions (possibly from different phases)."""
    hi_tbl = p3_table if hi_source == "p3" else p2_table
    lo_tbl = p3_table if lo_source == "p3" else p2_table

    if cond_hi not in hi_tbl or cond_lo not in lo_tbl:
        return None

    hi = hi_tbl[cond_hi]
    lo = lo_tbl[cond_lo]

    # ITT overall
    or_itt = odds_ratio_ci(hi["correct"], hi["n"], lo["correct"], lo["n"])
    or_pp = odds_ratio_ci(hi["correct_pp"], hi["n_pp"], lo["correct_pp"], lo["n_pp"])

    result = {
        "name": name,
        "description": desc,
        "cond_high": cond_hi,
        "cond_low": cond_lo,
        "hi_source": hi_source,
        "lo_source": lo_source,
        # Overall ITT
        "acc_high_itt": hi["acc_itt"],
        "acc_low_itt": lo["acc_itt"],
        "delta_itt": hi["acc_itt"] - lo["acc_itt"],
        "or_itt": or_itt["or"],
        "or_itt_ci": (or_itt["ci_lower"], or_itt["ci_upper"]),
        "or_itt_p": or_itt["p_value"],
        # Overall PP
        "acc_high_pp": hi["acc_pp"],
        "acc_low_pp": lo["acc_pp"],
        "delta_pp": hi["acc_pp"] - lo["acc_pp"],
        "or_pp": or_pp["or"],
        "or_pp_ci": (or_pp["ci_lower"], or_pp["ci_upper"]),
        "or_pp_p": or_pp["p_value"],
        # Per model
        "per_model": {},
    }

    models_hi = hi["per_model"]
    models_lo = lo["per_model"]
    for model in sorted(set(models_hi.keys()) & set(models_lo.keys())):
        mhi = models_hi[model]
        mlo = models_lo[model]
        m_or_itt = odds_ratio_ci(mhi["correct"], mhi["n"], mlo["correct"], mlo["n"])
        m_or_pp = odds_ratio_ci(mhi["correct_pp"], mhi["n_pp"], mlo["correct_pp"], mlo["n_pp"])
        result["per_model"][model] = {
            "acc_high_itt": mhi["acc_itt"],
            "acc_low_itt": mlo["acc_itt"],
            "delta_itt": mhi["acc_itt"] - mlo["acc_itt"],
            "or_itt": m_or_itt["or"],
            "or_itt_ci": (m_or_itt["ci_lower"], m_or_itt["ci_upper"]),
            "or_itt_p": m_or_itt["p_value"],
            "acc_high_pp": mhi["acc_pp"],
            "acc_low_pp": mlo["acc_pp"],
            "delta_pp": mhi["acc_pp"] - mlo["acc_pp"],
            "or_pp": m_or_pp["or"],
            "or_pp_ci": (m_or_pp["ci_lower"], m_or_pp["ci_upper"]),
            "or_pp_p": m_or_pp["p_value"],
            "ext_fail_high": mhi["ext_fail_rate"],
            "ext_fail_low": mlo["ext_fail_rate"],
            "ceiling_high": mhi["ceiling_hits"],
            "ceiling_low": mlo["ceiling_hits"],
        }

    return result


# ---------------------------------------------------------------------------
# Two-part decomposition
# ---------------------------------------------------------------------------

def two_part_decomposition(records: list[dict], conditions: list[str]) -> dict:
    by_cm = group_by(records, "condition", "model_tag")
    results = {}
    for (cond, model), recs in sorted(by_cm.items()):
        if cond not in conditions:
            continue
        n = len(recs)
        extracted = [r for r in recs if not r.get("extraction_failed")]
        correct_given_extracted = sum(1 for r in extracted if r.get("correct"))
        ceiling = sum(1 for r in recs if r.get("eval_count", 0) >= 8190)
        results[(cond, model)] = {
            "n": n,
            "p_extract": len(extracted) / max(n, 1),
            "n_extracted": len(extracted),
            "p_correct_given_extract": correct_given_extracted / max(len(extracted), 1),
            "ceiling_truncated": ceiling,
            "ceiling_rate": ceiling / max(n, 1),
        }
    return results


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_report(p3_table, p2_table, contrasts, dose_resp, per_q_dose,
                  two_part_p3, two_part_p2, total_p3, total_p2_subset,
                  mech_log_path, p2_log_path):
    lines = []
    w = 78

    lines.append("=" * w)
    lines.append("  PHASE 3 MECHANISM DEEP-DIVE ANALYSIS")
    lines.append("=" * w)
    lines.append(f"  Mechanism log: {mech_log_path}")
    lines.append(f"  Phase 2 log:   {p2_log_path}")
    lines.append(f"  Phase 3 records: {total_p3}")
    lines.append(f"  Phase 2 subset records (same 39 questions): {total_p2_subset}")
    lines.append(f"  Phase 3 conditions: {', '.join(sorted(p3_table.keys()))}")
    lines.append(f"  Phase 2 references: {', '.join(sorted(p2_table.keys()))}")
    models = sorted({m for t in [p3_table, p2_table] for s in t.values() for m in s["per_model"]})
    lines.append(f"  Models: {', '.join(models)}")
    lines.append("")
    lines.append("  NOTE: Phase 3 is explicitly exploratory (post-audit revision).")
    lines.append("  CROSS-PHASE CAVEAT: Phase 2 references are HISTORICAL CONTROLS,")
    lines.append("  not same-run counterfactuals. Ollama version changed (0.20.2 ->")
    lines.append("  0.20.6), rep counts differ (10 vs 8), model digests blank. Only")
    lines.append("  M-L100 and within-L contrasts are same-phase.")
    lines.append("  QWEN CONTEXT-WINDOW PATHOLOGY: Qwen's verbose B-traces (~6370")
    lines.append("  tokens) consume the 8192 budget when replayed as prefill, leaving")
    lines.append("  no room for the answer. L/N conditions for Qwen primarily measure")
    lines.append("  'room to answer' not 'value of trace'. Qwen N-B is VOID (both")
    lines.append("  arms truncation-dominated). Marginal ORs are anti-conservative")
    lines.append("  (clustering ignored).")
    lines.append("  M TRACE-SOURCE CONFOUND: M traces were compressed by a strong")
    lines.append("  external model, not just mechanically shortened. M vs L100 tests")
    lines.append("  trace authorship + compression jointly, not compression alone.")
    lines.append("")

    # --- 1. Accuracy table ---
    lines.append("=" * w)
    lines.append("  1. PER-CONDITION ACCURACY (ITT + PP)")
    lines.append("=" * w)
    lines.append("")

    all_conds = PHASE2_REFERENCE + MECHANISM_CONDITIONS
    for label, tbl, conds in [("Overall", None, all_conds)]:
        lines.append(f"  {'Cond':5s}  {'Src':3s}  {'N':>5s}  {'ITT':>6s}  {'PP':>6s}  {'ExtF':>5s}  {'Ceil':>5s}  {'Eval':>6s}")
        lines.append("  " + "-" * 55)
        for cond in conds:
            src = "P2" if cond in PHASE2_REFERENCE else "P3"
            t = p2_table if cond in PHASE2_REFERENCE else p3_table
            if cond not in t:
                continue
            s = t[cond]
            lines.append(f"  {cond:5s}  {src:3s}  {s['n']:5d}  {s['acc_itt']:6.1%}  {s['acc_pp']:6.1%}  "
                          f"{s['ext_fail_rate']:5.0%}  {s['ceiling_hits']/max(s['n'],1):5.0%}  {s['mean_eval_count']:6.0f}")
        lines.append("")

    for model in models:
        short = model.replace(":latest", "").replace(":9b", "")
        lines.append(f"  --- {short} ---")
        lines.append(f"  {'Cond':5s}  {'Src':3s}  {'N':>5s}  {'ITT':>6s}  {'PP':>6s}  {'ExtF':>5s}  {'Ceil':>5s}  {'Eval':>6s}")
        lines.append("  " + "-" * 55)
        for cond in all_conds:
            src = "P2" if cond in PHASE2_REFERENCE else "P3"
            t = p2_table if cond in PHASE2_REFERENCE else p3_table
            if cond not in t or model not in t[cond]["per_model"]:
                continue
            ms = t[cond]["per_model"][model]
            lines.append(f"  {cond:5s}  {src:3s}  {ms['n']:5d}  {ms['acc_itt']:6.1%}  {ms['acc_pp']:6.1%}  "
                          f"{ms['ext_fail_rate']:5.0%}  {ms['ceiling_hits']/max(ms['n'],1):5.0%}  {ms['mean_eval_count']:6.0f}")
        lines.append("")

    # --- 2. Two-part decomposition ---
    lines.append("=" * w)
    lines.append("  2. TWO-PART DECOMPOSITION: P(extract) and P(correct|extracted)")
    lines.append("=" * w)
    lines.append("")
    lines.append(f"  {'Cond/Model':25s}  {'Src':3s}  {'P(ext)':>7s}  {'P(c|e)':>7s}  {'Ceil%':>6s}  {'N':>5s}")
    lines.append("  " + "-" * 60)
    all_two_part = {}
    all_two_part.update({(k, "P2"): v for k, v in two_part_p2.items()})
    all_two_part.update({(k, "P3"): v for k, v in two_part_p3.items()})
    for ((cond, model), src), tp in sorted(all_two_part.items()):
        if tp["ceiling_rate"] < 0.01 and tp["p_extract"] > 0.95:
            continue
        short = model.replace(":latest", "").replace(":9b", "")
        key = f"{cond}/{short}"
        lines.append(f"  {key:25s}  {src:3s}  {tp['p_extract']:7.1%}  {tp['p_correct_given_extract']:7.1%}  "
                      f"{tp['ceiling_rate']:6.1%}  {tp['n']:5d}")
    lines.append("")

    # --- 3. Mechanism contrasts (per-model PRIMARY) ---
    lines.append("=" * w)
    lines.append("  3. MECHANISM CONTRASTS (per-model PRIMARY)")
    lines.append("=" * w)
    lines.append("")

    for model in models:
        short = model.replace(":latest", "").replace(":9b", "")
        lines.append(f"  === {short} ===")
        lines.append("")

        model_ps_itt = []
        valid_contrasts = []
        for c in contrasts:
            if c and model in c["per_model"]:
                model_ps_itt.append(c["per_model"][model]["or_itt_p"])
                valid_contrasts.append(c)

        adj_itt = holm_bonferroni(model_ps_itt) if model_ps_itt else []

        for i, c in enumerate(valid_contrasts):
            md = c["per_model"][model]
            trunc = ""
            if md["ceiling_high"] > 0 or md["ceiling_low"] > 0:
                trunc = " [TRUNC]"
            # Void Qwen N-B explicitly
            is_void = (c["name"] in QWEN_VOID_CONTRASTS and "qwen" in model.lower()
                        and md["ext_fail_high"] > 0.5 and md["ext_fail_low"] > 0.5)
            if is_void:
                trunc = " [VOID: both arms truncation-dominated]"
            lines.append(f"  {c['name']}{trunc}: {c['description']}")
            lines.append(f"    ITT: {md['acc_high_itt']:.1%} vs {md['acc_low_itt']:.1%}"
                          f"  delta={md['delta_itt']:+.1%}"
                          f"  OR={md['or_itt']:.3f} [{md['or_itt_ci'][0]:.3f},{md['or_itt_ci'][1]:.3f}]"
                          f"  p={md['or_itt_p']:.4f}{_sig(md['or_itt_p'])}"
                          f"  p_adj={adj_itt[i]:.4f}{_sig(adj_itt[i])}")
            lines.append(f"    PP:  {md['acc_high_pp']:.1%} vs {md['acc_low_pp']:.1%}"
                          f"  delta={md['delta_pp']:+.1%}"
                          f"  OR={md['or_pp']:.3f} [{md['or_pp_ci'][0]:.3f},{md['or_pp_ci'][1]:.3f}]"
                          f"  p={md['or_pp_p']:.4f}{_sig(md['or_pp_p'])}")
            if md["ext_fail_high"] > 0.01 or md["ext_fail_low"] > 0.01:
                lines.append(f"    ExtFail: {c['cond_high']}={md['ext_fail_high']:.0%}  {c['cond_low']}={md['ext_fail_low']:.0%}")
            lines.append("")

    # --- 4. Pooled contrasts (SECONDARY) ---
    lines.append("=" * w)
    lines.append("  4. POOLED CONTRASTS (SECONDARY — exploratory)")
    lines.append("=" * w)
    lines.append("")

    pooled_ps = [c["or_itt_p"] for c in contrasts if c]
    adj_pooled = holm_bonferroni(pooled_ps) if pooled_ps else []

    for i, c in enumerate(contrasts):
        if not c:
            continue
        lines.append(f"  {c['name']}: {c['description']}")
        lines.append(f"    ITT: {c['acc_high_itt']:.1%} vs {c['acc_low_itt']:.1%}  delta={c['delta_itt']:+.1%}"
                      f"  OR={c['or_itt']:.3f} [{c['or_itt_ci'][0]:.3f},{c['or_itt_ci'][1]:.3f}]"
                      f"  p={c['or_itt_p']:.4f}{_sig(c['or_itt_p'])}"
                      f"  p_adj={adj_pooled[i]:.4f}{_sig(adj_pooled[i])}")
        lines.append(f"    PP:  {c['acc_high_pp']:.1%} vs {c['acc_low_pp']:.1%}  delta={c['delta_pp']:+.1%}"
                      f"  OR={c['or_pp']:.3f} [{c['or_pp_ci'][0]:.3f},{c['or_pp_ci'][1]:.3f}]"
                      f"  p={c['or_pp_p']:.4f}{_sig(c['or_pp_p'])}")

        # Crossover interaction check (not "Simpson's paradox" — that term is reserved
        # for same-sign subgroup effects that reverse on aggregation)
        model_dirs = [(m, md["delta_itt"]) for m, md in c["per_model"].items()]
        if len(model_dirs) >= 2:
            dirs = [d > 0 for _, d in model_dirs]
            if not all(d == dirs[0] for d in dirs):
                lines.append(f"    >> CROSSOVER INTERACTION: " +
                              ", ".join(f"{m.replace(':latest','').replace(':9b','')}={d:+.1%}" for m, d in model_dirs))
        lines.append("")

    # --- 5. Within-phase L pairwise contrasts ---
    lines.append("=" * w)
    lines.append("  5. WITHIN-PHASE L PAIRWISE CONTRASTS (no cross-phase confound)")
    lines.append("=" * w)
    lines.append("")
    for model in models:
        short = model.replace(":latest", "").replace(":9b", "")
        lines.append(f"  === {short} ===")
        for name, hi, lo, desc in L_PAIRWISE_CONTRASTS:
            if hi in p3_table and lo in p3_table:
                mhi = p3_table[hi]["per_model"].get(model)
                mlo = p3_table[lo]["per_model"].get(model)
                if mhi and mlo:
                    m_or = odds_ratio_ci(mhi["correct"], mhi["n"], mlo["correct"], mlo["n"])
                    trunc = " [TRUNC]" if mhi["ceiling_hits"] > 0 or mlo["ceiling_hits"] > 0 else ""
                    lines.append(f"  {name}{trunc}: {desc}")
                    lines.append(f"    ITT: {mhi['acc_itt']:.1%} vs {mlo['acc_itt']:.1%}"
                                  f"  delta={mhi['acc_itt']-mlo['acc_itt']:+.1%}"
                                  f"  OR={m_or['or']:.3f} [{m_or['ci_lower']:.3f},{m_or['ci_upper']:.3f}]"
                                  f"  p={m_or['p_value']:.4f}{_sig(m_or['p_value'])}")
        lines.append("")

    # --- 6. Dose-response analysis ---
    lines.append("=" * w)
    lines.append("  6. DOSE-RESPONSE ANALYSIS (L25 → L100)")
    lines.append("=" * w)
    lines.append("  NOTE: Aggregate Kendall tau on 4 points cannot reach p<0.05 even")
    lines.append("  with perfect monotonicity. These are descriptive only. Trial-level")
    lines.append("  mixed-effects models on all 1248 obs/model are needed for power.")
    lines.append("  Qwen dose-response is dominated by context-window exhaustion:")
    lines.append("  higher doses = longer prefill = more ceiling truncation.")
    lines.append("")

    for model in models:
        short = model.replace(":latest", "").replace(":9b", "")
        dr = dose_resp.get(model)
        if not dr:
            continue

        lines.append(f"  === {short} ===")
        lines.append(f"  {'Dose':5s}  {'Frac':5s}  {'ITT':>6s}  {'PP':>6s}  {'ExtF':>5s}  {'Ceil':>5s}")
        lines.append("  " + "-" * 40)
        for dl, df in L_DOSES:
            if dl in dr["doses"]:
                d = dr["doses"][dl]
                lines.append(f"  {dl:5s}  {d['fraction']:5.0%}  {d['acc_itt']:6.1%}  {d['acc_pp']:6.1%}  "
                              f"{d['ext_fail_rate']:5.0%}  {d['ceiling_hits']:5d}")
        lines.append("")
        lines.append(f"  Monotonicity (Kendall's tau):")
        lines.append(f"    ITT: tau={dr['kendall_tau_itt']:+.3f}  p={dr['kendall_p_itt']:.4f} {_sig(dr['kendall_p_itt'])}")
        lines.append(f"    PP:  tau={dr['kendall_tau_pp']:+.3f}  p={dr['kendall_p_pp']:.4f} {_sig(dr['kendall_p_pp'])}")
        lt = dr["logistic_trend"]
        lines.append(f"  Logistic trend (dose -> P(correct)):")
        lines.append(f"    beta={lt['beta']:+.3f}  se={lt['se']:.3f}  p={lt['p']:.4f} {_sig(lt['p'])}  ({lt['direction']})")
        lines.append("")

    # Per-question dose-response summary
    for model in models:
        short = model.replace(":latest", "").replace(":9b", "")
        pq = per_q_dose.get(model, {})
        if not pq:
            continue

        lines.append(f"  --- {short}: Per-question dose-response pattern ---")
        # Classify each question's pattern
        monotone_up = 0
        monotone_down = 0
        non_monotone = 0
        flat = 0
        for qid, row in pq.items():
            vals = [row.get(dl) for dl, _ in L_DOSES if row.get(dl) is not None]
            if len(vals) < 3:
                continue
            diffs = [vals[i+1] - vals[i] for i in range(len(vals)-1)]
            if all(d >= -0.01 for d in diffs) and max(diffs) > 0.1:
                monotone_up += 1
            elif all(d <= 0.01 for d in diffs) and min(diffs) < -0.1:
                monotone_down += 1
            elif max(vals) - min(vals) < 0.15:
                flat += 1
            else:
                non_monotone += 1
        lines.append(f"    Monotone increasing: {monotone_up}")
        lines.append(f"    Monotone decreasing: {monotone_down}")
        lines.append(f"    Non-monotone:        {non_monotone}")
        lines.append(f"    Flat (<15pp range):   {flat}")
        lines.append("")

    # --- 7. Key findings ---
    lines.append("=" * w)
    lines.append("  7. KEY FINDINGS (post-audit)")
    lines.append("=" * w)
    lines.append("")

    lines.append("  Robust findings (both models, same-phase or consistent cross-phase):")
    lines.append("  - M >> L100 >> C: Strong-model compressed traces massively outperform")
    lines.append("    raw self-traces. CONFOUND: M traces authored/edited by stronger model,")
    lines.append("    so this tests trace quality + compression jointly, not compression alone.")
    lines.append("    Gemma: M~D (73.4% vs 72.3% ns), Qwen: M<D (88.8% vs 98.2%).")
    lines.append("  - L100 ~ C: Full dose-response endpoint matches Phase 2 self-trace")
    lines.append("    for both models (replication check passes, cross-phase).")
    lines.append("  - Gemma L25 < A: Quarter-trace hurts vs baseline (-9.7pp, p_adj=.040).")
    lines.append("    Partial/truncated reasoning context may confuse the model. Suggestive")
    lines.append("    (cross-phase), but confirmed within-phase: L25 < L100 by -11.2pp.")
    lines.append("")

    lines.append("  Cross-model transfer (K) — crossover interaction, not 'paradox':")
    for model in models:
        short = model.replace(":latest", "").replace(":9b", "")
        k_c = next((c for c in contrasts if c and c["name"] == "K-C"), None)
        if k_c and model in k_c["per_model"]:
            md = k_c["per_model"][model]
            direction = "better" if md["delta_itt"] > 0 else "worse"
            lines.append(f"    {short}: K={md['acc_high_itt']:.1%} vs C={md['acc_low_itt']:.1%} — "
                          f"cross-model {direction} than self-trace {_sig(md['or_itt_p'])}")
    lines.append("    CONFOUND: Reversal likely driven by donor trace verbosity mismatch.")
    lines.append("    Qwen gets short Gemma traces (room to answer), Gemma gets long Qwen")
    lines.append("    traces (overwhelms context). Not evidence for cross-model incompatibility.")
    lines.append("")

    lines.append("  Deterministic thinking (N vs B):")
    lines.append("    Gemma: N ~ B (70.2% vs 68.5% ns) — greedy decoding works fine.")
    lines.append("    Qwen: VOID — both arms truncation-dominated (N: 64% ext_fail,")
    lines.append("    B: 62% ext_fail). ITT tie reflects shared truncation, not mechanism.")
    lines.append("")

    lines.append("  Dose-response pattern (aggregate, underpowered):")
    for model in models:
        short = model.replace(":latest", "").replace(":9b", "")
        dr = dose_resp.get(model)
        if dr:
            accs = [dr["doses"][dl]["acc_itt"] for dl, _ in L_DOSES if dl in dr["doses"]]
            pattern = " → ".join(f"{a:.0%}" for a in accs)
            lines.append(f"    {short}: {pattern} (tau={dr['kendall_tau_itt']:+.2f}, ns)")
    lines.append("    Gemma: weakly increasing, all non-significant.")
    lines.append("    Qwen: decreasing — driven by context-window exhaustion (higher")
    lines.append("    dose = longer prefill = more ceiling truncation), NOT cognitive effect.")
    lines.append("")

    lines.append("  Context-window pathology (Qwen):")
    lines.append("    Qwen ceiling hits: " +
                  ", ".join(f"{c}={p3_table[c]['per_model'].get('qwen3.5:9b', {}).get('ceiling_hits', 0)}"
                            for c in MECHANISM_CONDITIONS if c in p3_table))
    lines.append("    Qwen B-traces average ~6370 tokens. When replayed as prefill,")
    lines.append("    they consume the 8192 budget leaving no room for FINAL:.")
    lines.append("    All Qwen L/N ITT results primarily reflect 'room to answer'.")
    lines.append("    N-B comparison is VOID for Qwen (both ~60% extraction failure).")
    lines.append("")

    lines.append("=" * w)
    lines.append("  STATISTICAL CAVEAT: Phase 3 is exploratory. All results are")
    lines.append("  hypothesis-generating, not confirmatory. Cross-phase comparisons")
    lines.append("  are historical controls (Ollama 0.20.2→0.20.6, 10→8 reps). Marginal")
    lines.append("  ORs are anti-conservative (clustering ignored). Qwen L/N are context-")
    lines.append("  window pathology, not mechanism evidence. M confounds compression with")
    lines.append("  trace authorship. Trial-level mixed-effects models needed for power.")
    lines.append("=" * w)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Phase 3 mechanism analysis.")
    parser.add_argument("--mechanism-log", type=Path, required=True,
                        help="Path to Phase 3 mechanism inference_log.jsonl")
    parser.add_argument("--phase2-log", type=Path, required=True,
                        help="Path to Phase 2 confirmatory inference_log.jsonl")
    parser.add_argument("--phase3-questions", type=Path, required=True,
                        help="Path to phase3-subset.jsonl")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    for p in [args.mechanism_log, args.phase2_log, args.phase3_questions]:
        if not p.exists():
            print(f"ERROR: Not found: {p}", file=sys.stderr)
            sys.exit(1)

    # Load data
    p3_records = load_jsonl(args.mechanism_log)
    p2_all = load_jsonl(args.phase2_log)
    p3_qids = load_phase3_qids(args.phase3_questions)

    print(f"Phase 3 records: {len(p3_records)}")
    print(f"Phase 2 total records: {len(p2_all)}")
    print(f"Phase 3 question IDs: {len(p3_qids)}")

    # Filter Phase 2 to same 39-item subset, exclude I_sub
    p2_subset = [r for r in p2_all
                 if r.get("condition") != "I_sub"
                 and r.get("question_id") in p3_qids
                 and r.get("condition") in PHASE2_REFERENCE]
    print(f"Phase 2 subset (A/B/C/D on 39 items): {len(p2_subset)}")

    # Build accuracy tables
    p3_table = build_accuracy_table(p3_records, MECHANISM_CONDITIONS)
    p2_table = build_accuracy_table(p2_subset, PHASE2_REFERENCE)

    # Compute mechanism contrasts
    contrasts = []
    for name, hi, lo, desc, hi_src, lo_src in MECHANISM_CONTRASTS:
        c = compute_mechanism_contrast(name, hi, lo, desc, hi_src, lo_src, p3_table, p2_table)
        contrasts.append(c)

    # Dose-response analysis
    models = sorted({m for t in [p3_table, p2_table] for s in t.values() for m in s["per_model"]})
    dose_resp = {}
    per_q_dose = {}
    for model in models:
        dose_resp[model] = dose_response_analysis(p3_records, model)
        per_q_dose[model] = per_question_dose_response(p3_records, model)

    # Two-part decomposition
    two_part_p3 = two_part_decomposition(p3_records, MECHANISM_CONDITIONS)
    two_part_p2 = two_part_decomposition(p2_subset, PHASE2_REFERENCE)

    # Format report
    report = format_report(
        p3_table, p2_table, contrasts, dose_resp, per_q_dose,
        two_part_p3, two_part_p2, len(p3_records), len(p2_subset),
        args.mechanism_log, args.phase2_log,
    )
    print(report)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

        report_path = args.output_dir / "phase3_report.txt"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\nReport written to {report_path}")

        # JSON summary
        json_path = args.output_dir / "phase3_summary.json"

        def _serialize(obj):
            if isinstance(obj, tuple):
                return list(obj)
            if isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            raise TypeError(f"Not serializable: {type(obj)}")

        summary = {
            "total_p3_records": len(p3_records),
            "total_p2_subset": len(p2_subset),
            "p3_questions": len(p3_qids),
            "p3_accuracy": {
                cond: {k: v for k, v in s.items() if k != "per_model"}
                for cond, s in p3_table.items()
            },
            "p3_accuracy_by_model": {
                cond: s["per_model"] for cond, s in p3_table.items()
            },
            "p2_ref_accuracy": {
                cond: {k: v for k, v in s.items() if k != "per_model"}
                for cond, s in p2_table.items()
            },
            "p2_ref_accuracy_by_model": {
                cond: s["per_model"] for cond, s in p2_table.items()
            },
            "contrasts": [c for c in contrasts if c],
            "dose_response": dose_resp,
            "per_question_dose_response": per_q_dose,
        }

        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2, default=_serialize)
        print(f"JSON summary written to {json_path}")


if __name__ == "__main__":
    main()
