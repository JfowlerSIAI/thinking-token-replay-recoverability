"""Phase 2 confirmatory analysis for the thinking-token experiment.

Computes per-condition accuracy (ITT + per-protocol), all 8 pre-registered
confirmatory contrasts with odds ratios and 95% CIs, synergy test on
log-odds scale, two-part extraction decomposition, and Holm-Bonferroni
correction.

Post-audit (tri-agent, 2026-04-12): per-model contrasts are PRIMARY.
Pooled contrasts are SECONDARY with explicit caveat about Simpson's paradox
and model heterogeneity. B-involving contrasts flag truncation confound.

Usage:
    python analyze.py --log ../outputs/confirmatory/20260408_100418/inference_log.jsonl
    python analyze.py --log ... --output-dir ../outputs/results/phase2/
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

PRIMARY_CONDITIONS = list("ABCDEFGHIJO")

# 8 pre-registered confirmatory contrasts (CLAUDE.md §Pre-registered Contrasts)
PAIRWISE_CONTRASTS = [
    ("B-C",  "B", "C", "Internal-reasoning effect (live think vs trace replay)"),
    ("C-F",  "C", "F", "Rationale-content effect (coherent vs shuffled)"),
    ("G-F",  "G", "F", "Generic reasoning-shape (wrong-Q trace vs shuffled)"),
    ("D-C",  "D", "C", "Expert-scaffold premium"),
    ("B-I",  "B", "I", "Compute-allocation (think vs k-attempt voting)"),
    ("B-O",  "B", "O", "Think-mode vs visible-CoT"),
    ("C-J",  "C", "J", "Semantic reasoning vs filler tokens"),
]

# Contrasts where B truncation confounds interpretation
B_INVOLVED_CONTRASTS = {"B-C", "B-I", "B-O", "E-(B+D-A)"}

# SESOI for equivalence testing (odds ratio scale)
SESOI_LOWER = 0.85
SESOI_UPPER = 1.18


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_primary(log_path: Path) -> list[dict]:
    """Load JSONL, exclude I_sub records."""
    results = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                d = json.loads(line)
                if d.get("condition") != "I_sub":
                    results.append(d)
    return results


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
    """Compute ITT and per-protocol accuracy."""
    n = len(records)
    if n == 0:
        return {"n": 0, "correct": 0, "acc_itt": 0.0,
                "ext_fail": 0, "ext_fail_rate": 0.0,
                "n_pp": 0, "correct_pp": 0, "acc_pp": 0.0,
                "errors": 0, "mean_eval_count": 0.0,
                "ceiling_hits": 0}
    correct = sum(1 for r in records if r.get("correct"))
    ext_fail = sum(1 for r in records if r.get("extraction_failed"))
    errors = sum(1 for r in records if r.get("error"))
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
        "errors": errors,
        "n_pp": n_pp,
        "correct_pp": correct_pp,
        "acc_pp": correct_pp / max(n_pp, 1),
        "mean_eval_count": sum(eval_counts) / n,
        "ceiling_hits": ceiling_hits,
    }


def build_accuracy_table(records: list[dict]) -> dict:
    by_cond = group_by(records, "condition")
    table = {}
    for cond in PRIMARY_CONDITIONS:
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
    """Marginal odds ratio with Wald CI on log scale. Haldane correction (+0.5)."""
    a = n1_correct + 0.5
    b = (n1_total - n1_correct) + 0.5
    c = n2_correct + 0.5
    d = (n2_total - n2_correct) + 0.5

    log_or = math.log(a * d) - math.log(b * c)
    se = math.sqrt(1/a + 1/b + 1/c + 1/d)
    z_crit = sp_stats.norm.ppf(1 - alpha/2)

    return {
        "or": math.exp(log_or),
        "log_or": log_or,
        "se_log_or": se,
        "ci_lower": math.exp(log_or - z_crit * se),
        "ci_upper": math.exp(log_or + z_crit * se),
        "p_value": 2 * sp_stats.norm.sf(abs(log_or / se)),
        "z_stat": log_or / se,
    }


def logit(p):
    p = max(min(p, 1 - 1e-6), 1e-6)
    return math.log(p / (1 - p))


def inv_logit(x):
    return 1 / (1 + math.exp(-x))


# ---------------------------------------------------------------------------
# Holm-Bonferroni correction
# ---------------------------------------------------------------------------

def holm_bonferroni(p_values: list[float]) -> list[float]:
    """Apply Holm-Bonferroni step-down correction. Returns adjusted p-values."""
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
# Pre-registered contrasts
# ---------------------------------------------------------------------------

def compute_pairwise_contrast(name, cond_hi, cond_lo, desc, table, records):
    """Compute a single pairwise contrast — ITT + PP, overall + per model."""
    if cond_hi not in table or cond_lo not in table:
        return None

    hi = table[cond_hi]
    lo = table[cond_lo]

    # ITT
    or_itt = odds_ratio_ci(hi["correct"], hi["n"], lo["correct"], lo["n"])
    # PP
    or_pp = odds_ratio_ci(hi["correct_pp"], hi["n_pp"], lo["correct_pp"], lo["n_pp"])

    truncation_warning = name in B_INVOLVED_CONTRASTS

    result = {
        "name": name,
        "description": desc,
        "cond_high": cond_hi,
        "cond_low": cond_lo,
        "truncation_warning": truncation_warning,
        # ITT
        "acc_high_itt": hi["acc_itt"],
        "acc_low_itt": lo["acc_itt"],
        "delta_itt": hi["acc_itt"] - lo["acc_itt"],
        "or_itt": or_itt["or"],
        "or_itt_ci": (or_itt["ci_lower"], or_itt["ci_upper"]),
        "or_itt_p": or_itt["p_value"],
        # PP
        "acc_high_pp": hi["acc_pp"],
        "acc_low_pp": lo["acc_pp"],
        "delta_pp": hi["acc_pp"] - lo["acc_pp"],
        "or_pp": or_pp["or"],
        "or_pp_ci": (or_pp["ci_lower"], or_pp["ci_upper"]),
        "or_pp_p": or_pp["p_value"],
        # SESOI
        "in_sesoi_itt": SESOI_LOWER <= or_itt["or"] <= SESOI_UPPER,
        "in_sesoi_pp": SESOI_LOWER <= or_pp["or"] <= SESOI_UPPER,
        # Per-model (PRIMARY)
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
            "acc_high_itt": mhi["acc_itt"], "acc_low_itt": mlo["acc_itt"],
            "delta_itt": mhi["acc_itt"] - mlo["acc_itt"],
            "or_itt": m_or_itt["or"],
            "or_itt_ci": (m_or_itt["ci_lower"], m_or_itt["ci_upper"]),
            "or_itt_p": m_or_itt["p_value"],
            "acc_high_pp": mhi["acc_pp"], "acc_low_pp": mlo["acc_pp"],
            "delta_pp": mhi["acc_pp"] - mlo["acc_pp"],
            "or_pp": m_or_pp["or"],
            "or_pp_ci": (m_or_pp["ci_lower"], m_or_pp["ci_upper"]),
            "or_pp_p": m_or_pp["p_value"],
            "ext_fail_high": mhi["ext_fail_rate"],
            "ext_fail_low": mlo["ext_fail_rate"],
        }

    return result


def compute_synergy(table):
    """Synergy contrast: E − (B + D − A) on log-odds scale. ITT + PP."""
    needed = {"A", "B", "D", "E"}
    if not needed.issubset(table.keys()):
        return None

    result = {"name": "E-(B+D-A)", "description": "Synergy (scaffold+think vs additive prediction)",
              "truncation_warning": True}

    all_models = sorted(
        set(table["A"]["per_model"].keys()) & set(table["B"]["per_model"].keys()) &
        set(table["D"]["per_model"].keys()) & set(table["E"]["per_model"].keys())
    )

    for scope, get_stats in [("overall", lambda t: t),
                              *[("model:" + m, lambda t, m=m: t["per_model"].get(m))
                                for m in all_models]]:
        sa = get_stats(table["A"])
        sb = get_stats(table["B"])
        sd = get_stats(table["D"])
        se_ = get_stats(table["E"])
        if not all([sa, sb, sd, se_]):
            continue

        for label_suffix, acc_key, n_key, correct_key in [("_itt", "acc_itt", "n", "correct"),
                                                            ("_pp", "acc_pp", "n_pp", "correct_pp")]:
            pA, nA = sa[acc_key], sa[n_key]
            pB, nB = sb[acc_key], sb[n_key]
            pD, nD = sd[acc_key], sd[n_key]
            pE, nE = se_[acc_key], se_[n_key]

            if any(n == 0 for n in [nA, nB, nD, nE]):
                continue

            lA, lB, lD, lE = logit(pA), logit(pB), logit(pD), logit(pE)
            additive_logit = lB + lD - lA
            additive_prob = inv_logit(additive_logit)
            synergy_logit = lE - additive_logit

            def logit_se(p, n):
                p = max(min(p, 1 - 1e-6), 1e-6)
                return 1 / (p * (1 - p) * math.sqrt(n))

            se_synergy = math.sqrt(
                logit_se(pE, nE)**2 + logit_se(pB, nB)**2 +
                logit_se(pD, nD)**2 + logit_se(pA, nA)**2
            )
            z_crit = sp_stats.norm.ppf(0.975)
            ci_lower = synergy_logit - z_crit * se_synergy
            ci_upper = synergy_logit + z_crit * se_synergy
            p_value = 2 * sp_stats.norm.sf(abs(synergy_logit / se_synergy))

            result[scope + label_suffix] = {
                "p_E": pE, "p_B": pB, "p_D": pD, "p_A": pA,
                "additive_prob": additive_prob,
                "synergy_logit": synergy_logit,
                "synergy_ci": (ci_lower, ci_upper),
                "synergy_p": p_value,
                "direction": "super-additive" if synergy_logit > 0 else "sub-additive",
            }

    return result


def compute_all_contrasts(table, records):
    contrasts = []
    for name, hi, lo, desc in PAIRWISE_CONTRASTS:
        c = compute_pairwise_contrast(name, hi, lo, desc, table, records)
        if c:
            contrasts.append(c)
    synergy = compute_synergy(table)
    if synergy:
        contrasts.append(synergy)
    return contrasts


# ---------------------------------------------------------------------------
# Two-part extraction decomposition
# ---------------------------------------------------------------------------

def two_part_decomposition(records: list[dict]) -> dict:
    """Decompose into P(extract FINAL:) and P(correct | extracted) per condition/model."""
    by_cm = group_by(records, "condition", "model_tag")
    results = {}
    for (cond, model), recs in sorted(by_cm.items()):
        if cond not in PRIMARY_CONDITIONS:
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
# Extraction failure analysis
# ---------------------------------------------------------------------------

def extraction_failure_analysis(records: list[dict]) -> dict:
    by_cond_model = group_by(records, "condition", "model_tag")
    analysis = {}
    for (cond, model), recs in sorted(by_cond_model.items()):
        if cond not in PRIMARY_CONDITIONS:
            continue
        fails = [r for r in recs if r.get("extraction_failed")]
        if not fails:
            continue
        fail_eval = [r.get("eval_count", 0) for r in fails]
        nonfail_eval = [r.get("eval_count", 0) for r in recs if not r.get("extraction_failed")]
        key = f"{cond}/{model}"
        analysis[key] = {
            "n_fail": len(fails), "n_total": len(recs),
            "fail_rate": len(fails) / len(recs),
            "mean_eval_fail": np.mean(fail_eval) if fail_eval else 0,
            "mean_eval_ok": np.mean(nonfail_eval) if nonfail_eval else 0,
            "max_eval_fail": max(fail_eval) if fail_eval else 0,
        }
    return analysis


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def _sig(p):
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "ns"


def format_report(table, contrasts, ext_analysis, two_part, total_records, log_path):
    lines = []
    w = 78

    lines.append("=" * w)
    lines.append("  PHASE 2 CONFIRMATORY ANALYSIS (post-audit revision)")
    lines.append("=" * w)
    lines.append(f"  Log: {log_path}")
    lines.append(f"  Total primary records: {total_records} (excluding I_sub)")
    lines.append(f"  Conditions: {', '.join(sorted(table.keys()))}")
    models = sorted({m for s in table.values() for m in s["per_model"]})
    lines.append(f"  Models: {', '.join(models)}")
    lines.append("")
    lines.append("  AUDIT NOTE: Per-model contrasts are PRIMARY. Pooled contrasts are")
    lines.append("  SECONDARY due to Simpson's paradox (model heterogeneity reverses")
    lines.append("  several pooled effects). All B-involving contrasts are confounded")
    lines.append("  by Qwen 8192-token truncation (36% extraction failure). ITT and PP")
    lines.append("  are reported side-by-side. Final paper requires hierarchical model.")
    lines.append("")

    # --- 1. Per-condition accuracy ---
    lines.append("=" * w)
    lines.append("  1. PER-CONDITION ACCURACY (ITT + PP)")
    lines.append("=" * w)
    lines.append("")
    lines.append(f"  {'Cond':4s}  {'N':>5s}  {'ITT':>6s}  {'PP':>6s}  {'ExtF':>5s}  {'Ceil':>5s}  {'Eval':>6s}")
    lines.append("  " + "-" * 48)
    for cond in PRIMARY_CONDITIONS:
        if cond not in table:
            continue
        s = table[cond]
        lines.append(f"  {cond:4s}  {s['n']:5d}  {s['acc_itt']:6.1%}  {s['acc_pp']:6.1%}  "
                      f"{s['ext_fail_rate']:5.0%}  {s['ceiling_hits']/s['n']:5.0%}  {s['mean_eval_count']:6.0f}")
    lines.append("")

    for model in models:
        short = model.replace(":latest", "").replace(":9b", "")
        lines.append(f"  --- {short} ---")
        lines.append(f"  {'Cond':4s}  {'N':>5s}  {'ITT':>6s}  {'PP':>6s}  {'ExtF':>5s}  {'Ceil':>5s}  {'Eval':>6s}")
        lines.append("  " + "-" * 48)
        for cond in PRIMARY_CONDITIONS:
            if cond not in table or model not in table[cond]["per_model"]:
                continue
            ms = table[cond]["per_model"][model]
            lines.append(f"  {cond:4s}  {ms['n']:5d}  {ms['acc_itt']:6.1%}  {ms['acc_pp']:6.1%}  "
                          f"{ms['ext_fail_rate']:5.0%}  {ms['ceiling_hits']/ms['n']:5.0%}  {ms['mean_eval_count']:6.0f}")
        lines.append("")

    # --- 2. Two-part decomposition ---
    lines.append("=" * w)
    lines.append("  2. TWO-PART DECOMPOSITION: P(extract) and P(correct|extracted)")
    lines.append("=" * w)
    lines.append("")
    lines.append(f"  {'Cond/Model':25s}  {'P(ext)':>7s}  {'P(c|e)':>7s}  {'Ceil%':>6s}")
    lines.append("  " + "-" * 50)
    for (cond, model), tp in sorted(two_part.items()):
        short = model.replace(":latest", "").replace(":9b", "")
        key = f"{cond}/{short}"
        if tp["ceiling_rate"] > 0.01 or tp["p_extract"] < 0.95:
            lines.append(f"  {key:25s}  {tp['p_extract']:7.1%}  {tp['p_correct_given_extract']:7.1%}  {tp['ceiling_rate']:6.1%}")
    lines.append("")

    # --- 3. Per-model PRIMARY contrasts ---
    lines.append("=" * w)
    lines.append("  3. PER-MODEL CONTRASTS (PRIMARY)")
    lines.append("=" * w)
    lines.append(f"  SESOI: OR {SESOI_LOWER}–{SESOI_UPPER}")
    lines.append("")

    # Collect per-model p-values for Holm-Bonferroni
    pairwise = [c for c in contrasts if c["name"] != "E-(B+D-A)"]
    for model in models:
        short = model.replace(":latest", "").replace(":9b", "")
        lines.append(f"  === {short} ===")
        lines.append("")

        # Gather p-values for this model
        model_ps_itt = []
        model_ps_pp = []
        for c in pairwise:
            md = c["per_model"].get(model)
            if md:
                model_ps_itt.append(md["or_itt_p"])
                model_ps_pp.append(md["or_pp_p"])

        adj_itt = holm_bonferroni(model_ps_itt) if model_ps_itt else []
        adj_pp = holm_bonferroni(model_ps_pp) if model_ps_pp else []

        for i, c in enumerate(pairwise):
            md = c["per_model"].get(model)
            if not md:
                continue
            trunc = " [!TRUNC]" if c.get("truncation_warning") else ""
            lines.append(f"  {c['name']}{trunc}: {c['description']}")

            # ITT
            lines.append(f"    ITT: {md['acc_high_itt']:.1%} vs {md['acc_low_itt']:.1%}"
                          f"  (delta={md['delta_itt']:+.1%})"
                          f"  OR={md['or_itt']:.3f} [{md['or_itt_ci'][0]:.3f},{md['or_itt_ci'][1]:.3f}]"
                          f"  p={md['or_itt_p']:.4f}{_sig(md['or_itt_p'])}"
                          f"  p_adj={adj_itt[i]:.4f}{_sig(adj_itt[i])}")
            # PP
            lines.append(f"    PP:  {md['acc_high_pp']:.1%} vs {md['acc_low_pp']:.1%}"
                          f"  (delta={md['delta_pp']:+.1%})"
                          f"  OR={md['or_pp']:.3f} [{md['or_pp_ci'][0]:.3f},{md['or_pp_ci'][1]:.3f}]"
                          f"  p={md['or_pp_p']:.4f}{_sig(md['or_pp_p'])}"
                          f"  p_adj={adj_pp[i]:.4f}{_sig(adj_pp[i])}")
            # Extraction failure rates
            if md["ext_fail_high"] > 0.05 or md["ext_fail_low"] > 0.05:
                lines.append(f"    ExtFail: {c['cond_high']}={md['ext_fail_high']:.0%}  {c['cond_low']}={md['ext_fail_low']:.0%}")
            lines.append("")

        # Synergy per model
        synergy = next((c for c in contrasts if c["name"] == "E-(B+D-A)"), None)
        if synergy:
            for suffix, label in [("_itt", "ITT"), ("_pp", "PP")]:
                key = f"model:{model}{suffix}"
                if key in synergy:
                    s = synergy[key]
                    lines.append(f"  Synergy [!TRUNC] ({label}): E={s['p_E']:.1%}  pred={s['additive_prob']:.1%}"
                                  f"  syn={s['synergy_logit']:+.3f} [{s['synergy_ci'][0]:+.3f},{s['synergy_ci'][1]:+.3f}]"
                                  f"  {s['direction']} {_sig(s['synergy_p'])}")
            lines.append("")

    # --- 4. Pooled contrasts (SECONDARY) ---
    lines.append("=" * w)
    lines.append("  4. POOLED CONTRASTS (SECONDARY — Simpson's paradox warning)")
    lines.append("=" * w)
    lines.append("  CAUTION: Pooled ORs are non-collapsible and can reverse per-model effects.")
    lines.append("  These are descriptive only — not confirmatory.")
    lines.append("")

    pooled_ps_itt = [c["or_itt_p"] for c in pairwise]
    adj_pooled_itt = holm_bonferroni(pooled_ps_itt)

    for i, c in enumerate(pairwise):
        trunc = " [!TRUNC]" if c.get("truncation_warning") else ""
        lines.append(f"  {c['name']}{trunc}: {c['description']}")
        lines.append(f"    ITT: {c['acc_high_itt']:.1%} vs {c['acc_low_itt']:.1%}  delta={c['delta_itt']:+.1%}"
                      f"  OR={c['or_itt']:.3f} [{c['or_itt_ci'][0]:.3f},{c['or_itt_ci'][1]:.3f}]"
                      f"  p={c['or_itt_p']:.4f}{_sig(c['or_itt_p'])}"
                      f"  p_adj={adj_pooled_itt[i]:.4f}{_sig(adj_pooled_itt[i])}")
        lines.append(f"    PP:  {c['acc_high_pp']:.1%} vs {c['acc_low_pp']:.1%}  delta={c['delta_pp']:+.1%}"
                      f"  OR={c['or_pp']:.3f} [{c['or_pp_ci'][0]:.3f},{c['or_pp_ci'][1]:.3f}]"
                      f"  p={c['or_pp_p']:.4f}{_sig(c['or_pp_p'])}")

        # Flag direction reversal between models
        model_dirs = []
        for model, md in c["per_model"].items():
            model_dirs.append((model, md["delta_itt"]))
        if len(model_dirs) >= 2:
            dirs = [d > 0 for _, d in model_dirs]
            if not all(d == dirs[0] for d in dirs):
                lines.append(f"    >> DIRECTION REVERSAL: " +
                              ", ".join(f"{m.replace(':latest','').replace(':9b','')}={d:+.1%}" for m, d in model_dirs))
        lines.append("")

    # Synergy pooled
    synergy = next((c for c in contrasts if c["name"] == "E-(B+D-A)"), None)
    if synergy:
        lines.append(f"  Synergy [!TRUNC]: logit(E) - logit(B) - logit(D) + logit(A)")
        for suffix, label in [("_itt", "ITT"), ("_pp", "PP")]:
            key = f"overall{suffix}"
            if key in synergy:
                s = synergy[key]
                lines.append(f"    {label}: E={s['p_E']:.1%}  pred={s['additive_prob']:.1%}"
                              f"  syn={s['synergy_logit']:+.3f} [{s['synergy_ci'][0]:+.3f},{s['synergy_ci'][1]:+.3f}]"
                              f"  {s['direction']} {_sig(s['synergy_p'])}")
        lines.append("")

    # --- 5. Extraction failure spotlight ---
    lines.append("=" * w)
    lines.append("  5. EXTRACTION FAILURE ANALYSIS")
    lines.append("=" * w)
    lines.append("")
    sorted_ext = sorted(ext_analysis.items(), key=lambda x: -x[1]["fail_rate"])
    for key, ea in sorted_ext:
        if ea["fail_rate"] < 0.01:
            continue
        lines.append(f"  {key:25s}  {ea['n_fail']:4d}/{ea['n_total']} ({ea['fail_rate']:.0%})"
                      f"  eval_fail={ea['mean_eval_fail']:.0f}  eval_ok={ea['mean_eval_ok']:.0f}"
                      f"  max_eval_fail={ea['max_eval_fail']}")
    lines.append("")

    # --- 6. Key findings ---
    lines.append("=" * w)
    lines.append("  6. KEY FINDINGS (per-model primary)")
    lines.append("=" * w)
    lines.append("")
    lines.append("  Robust findings (consistent across models):")
    lines.append("  - C >> F: Semantic content of reasoning is critical (both models, OR >13)")
    lines.append("  - C >> J: Reasoning content beats filler tokens (both models)")
    lines.append("  - G > F: Even wrong-question traces help vs shuffled (both models)")
    lines.append("")
    lines.append("  Model-specific findings:")
    lines.append("  - Gemma: B > C > A (thinking helps, live > replay > baseline)")
    lines.append("  - Gemma: B > O (hidden thinking beats visible CoT)")
    lines.append("  - Qwen: D >> C (expert scaffold massively helps)")
    lines.append("  - Qwen: I > B-PP (voting beats thinking even per-protocol)")
    lines.append("  - Gemma: D ~ C ~ A (expert scaffold has no effect)")
    lines.append("")
    lines.append("  Confounded findings (require hierarchical model to resolve):")
    lines.append("  - Pooled B-C, B-I, B-O: reversed by Qwen truncation artifact")
    lines.append("  - Pooled synergy: aggregation artifact (neither model significant)")
    lines.append("")

    lines.append("=" * w)
    lines.append("  STATISTICAL CAVEAT: Marginal ORs treat observations as independent.")
    lines.append("  The design is repeated-measures (103 Q x 10 reps). CIs are anti-")
    lines.append("  conservative. The final paper requires Bayesian hierarchical logistic")
    lines.append("  regression with question/seed clustering and model interactions.")
    lines.append("=" * w)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Phase 2 confirmatory analysis (post-audit).")
    parser.add_argument("--log", type=Path, required=True, help="Path to inference_log.jsonl")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for JSON + report output")
    args = parser.parse_args()

    if not args.log.exists():
        print(f"ERROR: Log not found: {args.log}", file=sys.stderr)
        sys.exit(1)

    records = load_primary(args.log)
    print(f"Loaded {len(records)} primary records (I_sub excluded)")

    primary = [r for r in records if r.get("condition") in PRIMARY_CONDITIONS]
    print(f"Primary condition records: {len(primary)}")

    table = build_accuracy_table(primary)
    contrasts = compute_all_contrasts(table, primary)
    ext_analysis = extraction_failure_analysis(primary)
    two_part = two_part_decomposition(primary)

    report = format_report(table, contrasts, ext_analysis, two_part, len(primary), args.log)
    print(report)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

        report_path = args.output_dir / "phase2_report.txt"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\nReport written to {report_path}")

        json_path = args.output_dir / "phase2_summary.json"
        summary = {
            "total_primary_records": len(primary),
            "conditions": sorted(table.keys()),
            "accuracy_table": {
                cond: {k: v for k, v in s.items() if k != "per_model"}
                for cond, s in table.items()
            },
            "accuracy_by_model": {
                cond: s["per_model"] for cond, s in table.items()
            },
            "two_part_decomposition": {
                f"{cond}/{model}": tp for (cond, model), tp in two_part.items()
            },
        }

        def _serialize(obj):
            if isinstance(obj, tuple):
                return list(obj)
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.integer):
                return int(obj)
            raise TypeError(f"Not serializable: {type(obj)}")

        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2, default=_serialize)
        print(f"JSON summary written to {json_path}")


if __name__ == "__main__":
    main()
