"""Hierarchical statistical analyses for the thinking-token experiment.

Addresses the four analyses required by tri-agent audit for paper submission:

1. Hierarchical logistic model (GEE with question clustering + robust SEs)
2. Two-part hurdle model (extraction failure vs correctness|extracted)
3. Token-length covariate analysis (eval_count mediation of truncation)
4. Trial-level dose-response (replaces underpowered 4-point Kendall tau)

Uses statsmodels GEE (Binomial/Logit/Exchangeable) as the population-averaged
analog of GLMM correct ~ condition * model + (1|question_id). Robust sandwich
SEs provide valid inference even if correlation structure is mis-specified.

Usage:
    python analyze_hierarchical.py \\
        --phase2-log ../outputs/confirmatory/20260408_100418/inference_log.jsonl \\
        --mechanism-log ../outputs/mechanism/20260412_215554/inference_log.jsonl \\
        --phase3-questions ../questions/phase3-subset.jsonl \\
        --output-dir ../outputs/results/hierarchical/
"""

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from statsmodels.genmod.cov_struct import Exchangeable, Independence
from statsmodels.genmod.families import Binomial
from statsmodels.genmod.families.links import Logit
from statsmodels.genmod.generalized_estimating_equations import GEE

# Import shared utilities from existing analysis scripts
sys.path.insert(0, str(Path(__file__).parent))
from analyze import (
    B_INVOLVED_CONTRASTS,
    PAIRWISE_CONTRASTS,
    PRIMARY_CONDITIONS,
    _sig,
    holm_bonferroni,
    load_primary,
)
from analyze_mechanism import L_DOSES, load_jsonl, load_phase3_qids

def _open_log(path):
    """Open a JSONL file, transparently handling .gz suffix."""
    import gzip
    p = str(path)
    if p.endswith(".gz"):
        return gzip.open(p, "rt", encoding="utf-8")
    return open(p, "r", encoding="utf-8")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MODELS = ["gemma4", "qwen3.5:9b"]

# Pairwise contrasts as (name, high, low) — synergy handled separately
PAIRWISE = [(name, hi, lo) for name, hi, lo, _desc in PAIRWISE_CONTRASTS]

# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------

def prepare_dataframe(records: list[dict]) -> pd.DataFrame:
    """Convert JSONL records to DataFrame for GEE. Sorted by question_id."""
    rows = []
    for r in records:
        cond = r.get("condition", "")
        if cond not in PRIMARY_CONDITIONS:
            continue
        rows.append({
            "correct": int(bool(r.get("correct"))),
            "extraction_failed": int(bool(r.get("extraction_failed"))),
            "condition": cond,
            "model_tag": r.get("model_tag", ""),
            "question_id": r.get("question_id", ""),
            "seed": r.get("seed", 0),
            "rep_number": r.get("rep_number", 0),
            "eval_count": r.get("eval_count", 0),
        })
    df = pd.DataFrame(rows)
    df["ceiling_hit"] = (df["eval_count"] >= 8190).astype(int)
    df = df.sort_values("question_id").reset_index(drop=True)
    return df


def prepare_dose_dataframe(records: list[dict]) -> pd.DataFrame:
    """Prepare Phase 3 L-condition data for dose-response GEE."""
    dose_map = {"L25": 0.25, "L50": 0.50, "L75": 0.75, "L100": 1.00}
    rows = []
    for r in records:
        cond = r.get("condition", "")
        if cond not in dose_map:
            continue
        rows.append({
            "correct": int(bool(r.get("correct"))),
            "extraction_failed": int(bool(r.get("extraction_failed"))),
            "condition": cond,
            "dose": dose_map[cond],
            "model_tag": r.get("model_tag", ""),
            "question_id": r.get("question_id", ""),
            "eval_count": r.get("eval_count", 0),
            "ceiling_hit": int(r.get("eval_count", 0) >= 8190),
        })
    df = pd.DataFrame(rows)
    df = df.sort_values("question_id").reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# GEE fitting
# ---------------------------------------------------------------------------

def fit_gee(df, formula, groups_col="question_id", cov_struct=None):
    """Fit a GEE model with Binomial/Logit. Returns results or None on failure."""
    if cov_struct is None:
        cov_struct = Exchangeable()
    try:
        model = GEE.from_formula(
            formula,
            groups=groups_col,
            data=df,
            family=Binomial(link=Logit()),
            cov_struct=cov_struct,
        )
        result = model.fit(maxiter=200, cov_type="robust")
        return result
    except Exception as e:
        # Fall back to independence if exchangeable fails
        try:
            model = GEE.from_formula(
                formula,
                groups=groups_col,
                data=df,
                family=Binomial(link=Logit()),
                cov_struct=Independence(),
            )
            result = model.fit(maxiter=200, cov_type="robust")
            result._fallback_note = f"Exchangeable failed ({e}), used Independence + robust SEs"
            return result
        except Exception as e2:
            print(f"  GEE FAILED: {e2}", file=sys.stderr)
            return None


def extract_contrast(result, param_hi, param_lo):
    """Extract a pairwise contrast from GEE results.

    For Treatment('A') coding: param_hi = 'C(condition, Treatment("A"))[T.B]'
    Contrast = beta_hi - beta_lo, SE from robust VCV.
    """
    params = result.params
    vcov = result.cov_params()
    pnames = list(params.index)

    def _find(cond):
        target = f'C(condition, Treatment("A"))[T.{cond}]'
        if target in pnames:
            return target
        # Reference level (A) has no parameter — coefficient is 0
        if cond == "A":
            return None
        return None

    hi_name = _find(param_hi)
    lo_name = _find(param_lo)

    # Get betas (reference = 0)
    beta_hi = params[hi_name] if hi_name else 0.0
    beta_lo = params[lo_name] if lo_name else 0.0
    diff = beta_hi - beta_lo

    # SE from robust VCV
    if hi_name and lo_name:
        var = vcov.loc[hi_name, hi_name] + vcov.loc[lo_name, lo_name] - 2 * vcov.loc[hi_name, lo_name]
    elif hi_name:
        var = vcov.loc[hi_name, hi_name]
    elif lo_name:
        var = vcov.loc[lo_name, lo_name]
    else:
        return None  # A vs A

    se = math.sqrt(max(var, 1e-12))
    z = diff / se
    p = 2 * sp_stats.norm.sf(abs(z))
    ci_lo = diff - 1.96 * se
    ci_hi = diff + 1.96 * se

    return {
        "log_or": diff,
        "or": math.exp(diff),
        "se": se,
        "z": z,
        "p": p,
        "ci_lower": math.exp(ci_lo),
        "ci_upper": math.exp(ci_hi),
    }


def extract_synergy(result):
    """Extract synergy contrast E-(B+D-A) from GEE results.

    With A as reference: synergy = beta_E - beta_B - beta_D.
    """
    params = result.params
    vcov = result.cov_params()

    def _get(cond):
        name = f'C(condition, Treatment("A"))[T.{cond}]'
        return name if name in params.index else None

    e_name = _get("E")
    b_name = _get("B")
    d_name = _get("D")

    if not all([e_name, b_name, d_name]):
        return None

    syn = params[e_name] - params[b_name] - params[d_name]

    # Variance: Var(E - B - D) = V_EE + V_BB + V_DD - 2V_EB - 2V_ED + 2V_BD
    var = (vcov.loc[e_name, e_name] + vcov.loc[b_name, b_name] + vcov.loc[d_name, d_name]
           - 2 * vcov.loc[e_name, b_name] - 2 * vcov.loc[e_name, d_name]
           + 2 * vcov.loc[b_name, d_name])
    se = math.sqrt(max(var, 1e-12))
    z = syn / se
    p = 2 * sp_stats.norm.sf(abs(z))

    return {
        "synergy_logit": syn,
        "se": se,
        "z": z,
        "p": p,
        "ci_lower": syn - 1.96 * se,
        "ci_upper": syn + 1.96 * se,
        "direction": "super-additive" if syn > 0 else "sub-additive",
    }


# ---------------------------------------------------------------------------
# Analysis 1: Per-model GEE contrasts
# ---------------------------------------------------------------------------

def run_analysis1(df):
    """GEE per-model contrasts (PRIMARY) + pooled (SECONDARY)."""
    results = {}

    for model in MODELS:
        mdf = df[df["model_tag"] == model].copy()
        if len(mdf) < 100:
            continue

        gee_result = fit_gee(mdf, 'correct ~ C(condition, Treatment("A"))')
        if gee_result is None:
            continue

        # Extract rho
        try:
            rho = gee_result.cov_struct.summary()
        except Exception:
            rho = "N/A"

        contrasts = {}
        for name, hi, lo in PAIRWISE:
            c = extract_contrast(gee_result, hi, lo)
            if c:
                contrasts[name] = c

        synergy = extract_synergy(gee_result)

        # Holm-Bonferroni on pairwise
        pairwise_names = [name for name, _, _ in PAIRWISE]
        ps = [contrasts[n]["p"] for n in pairwise_names if n in contrasts]
        adj_ps = holm_bonferroni(ps)
        for i, n in enumerate(pairwise_names):
            if n in contrasts:
                contrasts[n]["p_adj"] = adj_ps[i]

        results[model] = {
            "gee_result": gee_result,
            "rho": rho,
            "contrasts": contrasts,
            "synergy": synergy,
            "n": len(mdf),
            "fallback": getattr(gee_result, "_fallback_note", None),
        }

    return results


# ---------------------------------------------------------------------------
# Analysis 2: Two-part hurdle model
# ---------------------------------------------------------------------------

def run_analysis2(df):
    """Two-part hurdle: Part 1 = P(extraction_failed), Part 2 = P(correct|extracted)."""
    results = {}

    for model in MODELS:
        mdf = df[df["model_tag"] == model].copy()
        if len(mdf) < 100:
            continue

        # Part 1: extraction failure
        part1_result = fit_gee(mdf, 'extraction_failed ~ C(condition, Treatment("A"))')
        part1_contrasts = {}
        if part1_result:
            for name, hi, lo in PAIRWISE:
                c = extract_contrast(part1_result, hi, lo)
                if c:
                    part1_contrasts[name] = c

        # Part 2: correct | not extraction_failed
        pp_df = mdf[mdf["extraction_failed"] == 0].copy()
        pp_df = pp_df.sort_values("question_id").reset_index(drop=True)
        part2_result = fit_gee(pp_df, 'correct ~ C(condition, Treatment("A"))')
        part2_contrasts = {}
        if part2_result:
            for name, hi, lo in PAIRWISE:
                c = extract_contrast(part2_result, hi, lo)
                if c:
                    part2_contrasts[name] = c

        results[model] = {
            "part1": {"result": part1_result, "contrasts": part1_contrasts, "n": len(mdf)},
            "part2": {"result": part2_result, "contrasts": part2_contrasts, "n": len(pp_df)},
        }

    return results


# ---------------------------------------------------------------------------
# Analysis 3: Token-length covariate
# ---------------------------------------------------------------------------

def run_analysis3(df):
    """Token-length covariate analysis."""
    results = {}

    for model in MODELS:
        mdf = df[df["model_tag"] == model].copy()
        if len(mdf) < 100:
            continue

        # Standardize eval_count for numerical stability
        mdf = mdf.copy()
        mdf["eval_count_z"] = (mdf["eval_count"] - mdf["eval_count"].mean()) / max(mdf["eval_count"].std(), 1)

        # Model 1: correct ~ eval_count_z + condition
        m1 = fit_gee(mdf, 'correct ~ eval_count_z + C(condition, Treatment("A"))')

        # Model 2: extraction_failed ~ eval_count_z + condition
        m2 = fit_gee(mdf, 'extraction_failed ~ eval_count_z + C(condition, Treatment("A"))')

        # Model 3: correct ~ ceiling_hit + condition
        m3 = fit_gee(mdf, 'correct ~ ceiling_hit + C(condition, Treatment("A"))')

        # Model 4 (baseline, no covariate): correct ~ condition
        m4 = fit_gee(mdf, 'correct ~ C(condition, Treatment("A"))')

        # Extract eval_count coefficients
        def _get_coef(res, name):
            if res is None or name not in res.params.index:
                return None
            p = res.params[name]
            se = math.sqrt(res.cov_params().loc[name, name])
            z = p / se
            return {"beta": p, "se": se, "z": z, "p": 2 * sp_stats.norm.sf(abs(z))}

        # Compare B-involving contrasts with and without covariate
        b_contrasts_with = {}
        b_contrasts_without = {}
        if m1:
            for name, hi, lo in PAIRWISE:
                if name in B_INVOLVED_CONTRASTS:
                    c = extract_contrast(m1, hi, lo)
                    if c:
                        b_contrasts_with[name] = c
        if m4:
            for name, hi, lo in PAIRWISE:
                if name in B_INVOLVED_CONTRASTS:
                    c = extract_contrast(m4, hi, lo)
                    if c:
                        b_contrasts_without[name] = c

        results[model] = {
            "eval_count_on_correct": _get_coef(m1, "eval_count_z") if m1 else None,
            "eval_count_on_extraction": _get_coef(m2, "eval_count_z") if m2 else None,
            "ceiling_on_correct": _get_coef(m3, "ceiling_hit") if m3 else None,
            "b_contrasts_with_covariate": b_contrasts_with,
            "b_contrasts_without_covariate": b_contrasts_without,
            "eval_count_mean": float(mdf["eval_count"].mean()),
            "eval_count_sd": float(mdf["eval_count"].std()),
        }

    return results


# ---------------------------------------------------------------------------
# Analysis 4: Trial-level dose-response
# ---------------------------------------------------------------------------

def run_analysis4(dose_df):
    """Trial-level dose-response GEE on Phase 3 L data."""
    results = {}

    # Per-model
    for model in MODELS:
        mdf = dose_df[dose_df["model_tag"] == model].copy()
        mdf = mdf.sort_values("question_id").reset_index(drop=True)
        if len(mdf) < 50:
            continue

        gee_result = fit_gee(mdf, "correct ~ dose")
        if gee_result and "dose" in gee_result.params.index:
            beta = gee_result.params["dose"]
            se = math.sqrt(gee_result.cov_params().loc["dose", "dose"])
            z = beta / se
            p = 2 * sp_stats.norm.sf(abs(z))
            results[model] = {
                "beta_dose": float(beta),
                "se": float(se),
                "z": float(z),
                "p": float(p),
                "ci_lower": float(beta - 1.96 * se),
                "ci_upper": float(beta + 1.96 * se),
                "direction": "increasing" if beta > 0 else "decreasing",
                "n": len(mdf),
            }

    # Interaction model: dose * model
    if len(dose_df) > 100:
        interaction_df = dose_df.copy().sort_values("question_id").reset_index(drop=True)
        gee_int = fit_gee(interaction_df, 'correct ~ dose * C(model_tag, Treatment("gemma4"))')
        if gee_int:
            # Find interaction term
            int_name = None
            for n in gee_int.params.index:
                if "dose:" in n and "model_tag" in n:
                    int_name = n
                    break
            if int_name:
                beta_int = gee_int.params[int_name]
                se_int = math.sqrt(gee_int.cov_params().loc[int_name, int_name])
                z_int = beta_int / se_int
                p_int = 2 * sp_stats.norm.sf(abs(z_int))
                results["interaction"] = {
                    "beta": float(beta_int),
                    "se": float(se_int),
                    "z": float(z_int),
                    "p": float(p_int),
                    "n": len(interaction_df),
                }

    return results


# ---------------------------------------------------------------------------
# Report formatting
# ---------------------------------------------------------------------------

def format_report(a1, a2, a3, a4, total_p2, total_dose,
                  p2_log_path, mech_log_path):
    lines = []
    w = 78

    lines.append("=" * w)
    lines.append("  HIERARCHICAL ANALYSES (GEE — post-audit)")
    lines.append("=" * w)
    lines.append(f"  Phase 2 log: {p2_log_path}")
    lines.append(f"  Mechanism log: {mech_log_path}")
    lines.append(f"  Phase 2 primary records: {total_p2}")
    lines.append(f"  Dose-response records: {total_dose}")
    lines.append(f"  Method: GEE, Binomial(Logit), Exchangeable correlation,")
    lines.append(f"  robust (sandwich) SEs, grouped by question_id.")
    lines.append(f"  Software: statsmodels {__import__('statsmodels').__version__}")
    lines.append("")

    # --- Section 1: Per-model contrasts ---
    lines.append("=" * w)
    lines.append("  1. GEE PER-MODEL CONTRASTS (PRIMARY)")
    lines.append("=" * w)
    lines.append("")

    for model in MODELS:
        if model not in a1:
            continue
        m = a1[model]
        short = model.replace(":latest", "").replace(":9b", "")
        lines.append(f"  === {short} (n={m['n']}) ===")
        lines.append(f"  Within-question correlation (rho): {m['rho']}")
        if m.get("fallback"):
            lines.append(f"  NOTE: {m['fallback']}")
        lines.append("")

        for name, hi, lo in PAIRWISE:
            c = m["contrasts"].get(name)
            if not c:
                continue
            trunc = " [!TRUNC]" if name in B_INVOLVED_CONTRASTS else ""
            lines.append(f"  {name}{trunc}:")
            lines.append(f"    log-OR={c['log_or']:+.3f}  OR={c['or']:.3f} [{c['ci_lower']:.3f},{c['ci_upper']:.3f}]"
                          f"  z={c['z']:+.2f}  p={c['p']:.4f}{_sig(c['p'])}"
                          f"  p_adj={c.get('p_adj', c['p']):.4f}{_sig(c.get('p_adj', c['p']))}")
        lines.append("")

        syn = m.get("synergy")
        if syn:
            lines.append(f"  Synergy E-(B+D-A) [!TRUNC]:")
            lines.append(f"    syn={syn['synergy_logit']:+.3f} [{syn['ci_lower']:+.3f},{syn['ci_upper']:+.3f}]"
                          f"  z={syn['z']:+.2f}  p={syn['p']:.4f}{_sig(syn['p'])}"
                          f"  {syn['direction']}")
        lines.append("")

    # --- Section 2: Two-part hurdle ---
    lines.append("=" * w)
    lines.append("  2. TWO-PART HURDLE MODEL")
    lines.append("=" * w)
    lines.append("  Part 1: P(extraction_failed) ~ condition  (what causes format failure)")
    lines.append("  Part 2: P(correct | extracted) ~ condition (reasoning quality)")
    lines.append("")

    for model in MODELS:
        if model not in a2:
            continue
        short = model.replace(":latest", "").replace(":9b", "")
        p1 = a2[model]["part1"]
        p2 = a2[model]["part2"]

        lines.append(f"  === {short} ===")
        lines.append(f"  Part 1 (extraction failure, n={p1['n']}):")
        for name, _, _ in PAIRWISE:
            c = p1["contrasts"].get(name)
            if c:
                lines.append(f"    {name}: log-OR={c['log_or']:+.3f}  OR={c['or']:.3f}"
                              f"  p={c['p']:.4f}{_sig(c['p'])}")
        lines.append(f"  Part 2 (correct|extracted, n={p2['n']}):")
        for name, _, _ in PAIRWISE:
            c = p2["contrasts"].get(name)
            if c:
                lines.append(f"    {name}: log-OR={c['log_or']:+.3f}  OR={c['or']:.3f}"
                              f"  p={c['p']:.4f}{_sig(c['p'])}")
        lines.append("")

    # --- Section 3: Token-length covariate ---
    lines.append("=" * w)
    lines.append("  3. TOKEN-LENGTH COVARIATE ANALYSIS")
    lines.append("=" * w)
    lines.append("  Does eval_count / ceiling_hit explain accuracy after condition?")
    lines.append("")

    for model in MODELS:
        if model not in a3:
            continue
        short = model.replace(":latest", "").replace(":9b", "")
        m = a3[model]
        lines.append(f"  === {short} (eval_count mean={m['eval_count_mean']:.0f}, sd={m['eval_count_sd']:.0f}) ===")

        ec = m.get("eval_count_on_correct")
        if ec:
            lines.append(f"  eval_count_z -> correct: beta={ec['beta']:+.3f}  z={ec['z']:+.2f}  p={ec['p']:.4f}{_sig(ec['p'])}")
        ee = m.get("eval_count_on_extraction")
        if ee:
            lines.append(f"  eval_count_z -> ext_fail: beta={ee['beta']:+.3f}  z={ee['z']:+.2f}  p={ee['p']:.4f}{_sig(ee['p'])}")
        ch = m.get("ceiling_on_correct")
        if ch:
            lines.append(f"  ceiling_hit -> correct:   beta={ch['beta']:+.3f}  z={ch['z']:+.2f}  p={ch['p']:.4f}{_sig(ch['p'])}")
        lines.append("")

        # B-contrast mediation
        bw = m.get("b_contrasts_with_covariate", {})
        bwo = m.get("b_contrasts_without_covariate", {})
        if bw and bwo:
            lines.append(f"  B-involving contrasts: with vs without eval_count covariate:")
            lines.append(f"  {'Contrast':8s}  {'Without':>12s}  {'With':>12s}  {'Change':>8s}")
            lines.append("  " + "-" * 46)
            for name in sorted(set(bw.keys()) | set(bwo.keys())):
                wo = bwo.get(name, {})
                wi = bw.get(name, {})
                if wo and wi:
                    change = wi["log_or"] - wo["log_or"]
                    lines.append(f"  {name:8s}  {wo['log_or']:+12.3f}  {wi['log_or']:+12.3f}  {change:+8.3f}")
            lines.append("")

    # --- Section 4: Dose-response ---
    lines.append("=" * w)
    lines.append("  4. TRIAL-LEVEL DOSE-RESPONSE (Phase 3 L conditions)")
    lines.append("=" * w)
    lines.append("  GEE: correct ~ dose, Binomial/Logit, groups=question_id")
    lines.append(f"  Total dose-response records: {total_dose}")
    lines.append("")

    for model in MODELS:
        if model not in a4:
            continue
        short = model.replace(":latest", "").replace(":9b", "")
        d = a4[model]
        lines.append(f"  {short} (n={d['n']}):")
        lines.append(f"    beta_dose={d['beta_dose']:+.3f}  SE={d['se']:.3f}"
                      f"  z={d['z']:+.2f}  p={d['p']:.4f}{_sig(d['p'])}"
                      f"  [{d['ci_lower']:+.3f},{d['ci_upper']:+.3f}]"
                      f"  ({d['direction']})")

    if "interaction" in a4:
        i = a4["interaction"]
        lines.append(f"\n  Model x dose interaction (n={i['n']}):")
        lines.append(f"    beta={i['beta']:+.3f}  SE={i['se']:.3f}"
                      f"  z={i['z']:+.2f}  p={i['p']:.4f}{_sig(i['p'])}")
    lines.append("")

    # --- Section 5: Key findings ---
    lines.append("=" * w)
    lines.append("  5. KEY FINDINGS — WHAT CHANGED FROM MARGINAL ANALYSIS")
    lines.append("=" * w)
    lines.append("")
    lines.append("  Compare these GEE results to phase2_report.txt marginal ORs.")
    lines.append("  GEE CIs should be wider (clustering correction). If any")
    lines.append("  contrast flips significance, that indicates the marginal")
    lines.append("  analysis was anti-conservative for that contrast.")
    lines.append("")

    # Check rho values
    for model in MODELS:
        if model in a1:
            short = model.replace(":latest", "").replace(":9b", "")
            lines.append(f"  {short} rho: {a1[model]['rho']}")
    lines.append("  (rho > 0 confirms within-question correlation; marginal ORs were anti-conservative)")
    lines.append("")

    lines.append("=" * w)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Hierarchical analyses (GEE) for paper submission.")
    parser.add_argument("--phase2-log", type=Path, required=True)
    parser.add_argument("--mechanism-log", type=Path, required=True)
    parser.add_argument("--phase3-questions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    for p in [args.phase2_log, args.mechanism_log, args.phase3_questions]:
        if not p.exists():
            print(f"ERROR: Not found: {p}", file=sys.stderr)
            sys.exit(1)

    # Load Phase 2
    p2_records = load_primary(args.phase2_log)
    print(f"Phase 2 records: {len(p2_records)}")
    df = prepare_dataframe(p2_records)
    print(f"Phase 2 DataFrame: {len(df)} rows, {df['condition'].nunique()} conditions, "
          f"{df['model_tag'].nunique()} models, {df['question_id'].nunique()} questions")

    # Load Phase 3 dose-response
    p3_records = load_jsonl(args.mechanism_log)
    dose_df = prepare_dose_dataframe(p3_records)
    print(f"Dose-response DataFrame: {len(dose_df)} rows")

    # Run analyses
    print("\n--- Analysis 1: GEE per-model contrasts ---")
    a1 = run_analysis1(df)
    for model in MODELS:
        if model in a1:
            short = model.replace(":latest", "").replace(":9b", "")
            print(f"  {short}: {len(a1[model]['contrasts'])} contrasts, rho={a1[model]['rho']}")

    print("\n--- Analysis 2: Two-part hurdle ---")
    a2 = run_analysis2(df)
    for model in MODELS:
        if model in a2:
            short = model.replace(":latest", "").replace(":9b", "")
            print(f"  {short}: Part1 {len(a2[model]['part1']['contrasts'])} contrasts, "
                  f"Part2 {len(a2[model]['part2']['contrasts'])} contrasts")

    print("\n--- Analysis 3: Token-length covariate ---")
    a3 = run_analysis3(df)
    for model in MODELS:
        if model in a3:
            short = model.replace(":latest", "").replace(":9b", "")
            ec = a3[model].get("eval_count_on_correct")
            print(f"  {short}: eval_count beta={ec['beta']:+.3f} p={ec['p']:.4f}" if ec else f"  {short}: no result")

    print("\n--- Analysis 4: Dose-response ---")
    a4 = run_analysis4(dose_df)
    for model in MODELS:
        if model in a4:
            short = model.replace(":latest", "").replace(":9b", "")
            print(f"  {short}: beta_dose={a4[model]['beta_dose']:+.3f} p={a4[model]['p']:.4f}")

    # Format report
    report = format_report(a1, a2, a3, a4, len(df), len(dose_df),
                           args.phase2_log, args.mechanism_log)
    print("\n" + report)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)

        report_path = args.output_dir / "hierarchical_report.txt"
        with open(report_path, "w") as f:
            f.write(report)
        print(f"\nReport written to {report_path}")

        # JSON summary
        def _clean(obj):
            if isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            if isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            if isinstance(obj, tuple):
                return list(obj)
            raise TypeError(f"Not serializable: {type(obj)}")

        def _strip_gee(d):
            """Remove non-serializable GEE result objects."""
            if isinstance(d, dict):
                return {k: _strip_gee(v) for k, v in d.items()
                        if not k.endswith("_result") and k != "gee_result" and k != "result"}
            return d

        summary = {
            "analysis1_contrasts": _strip_gee(a1),
            "analysis2_hurdle": _strip_gee(a2),
            "analysis3_token_covariate": _strip_gee(a3),
            "analysis4_dose_response": _strip_gee(a4),
        }

        json_path = args.output_dir / "hierarchical_summary.json"
        with open(json_path, "w") as f:
            json.dump(summary, f, indent=2, default=_clean)
        print(f"JSON summary written to {json_path}")


if __name__ == "__main__":
    main()
