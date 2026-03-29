"""
compute_gprime_perturbation.py

Computes scorer noise sensitivity of g' via direct perturbation of V_p,
replacing the linearized partial-derivative approach.

Instead of:
    δg' = |∂g'/∂V_p| · σ²_noise          (first-order Taylor, symmetric)

We evaluate g' at perturbed pooled variance directly:
    g'_low  = K / √(V_p + σ²_noise)       (noise inflates V_p -> g' shrinks)
    g'_high = K / √(V_p - σ²_noise)       (noise deflates V_p -> g' grows)

    Δ+ = g'_high - g'_obs
    Δ- = g'_obs - g'_low

This captures the nonlinearity of g' ∝ V_p^(-1/2) and produces
asymmetric bounds. It is NOT a confidence interval — it represents
sensitivity of g' to scorer-induced variability.

Reads:
  - output/baseline_descriptives.json
  - output/noise_floor_stats.json
  - output/*_contest.json

Run from the llmphysics_scorer directory.
"""

import json
import os
import glob
import math

# ── CONFIG ──────────────────────────────────────────────────────────
OUTPUT_DIR      = "output"
BASELINE_DESC   = os.path.join(OUTPUT_DIR, "baseline_descriptives.json")
NOISE_STATS     = os.path.join(OUTPUT_DIR, "noise_floor_stats.json")
CONTEST_PATTERN = os.path.join(OUTPUT_DIR, "*_contest.json")

CATEGORIES = ["hypothesis", "novelty", "scientific_humility",
              "engagement", "rigor", "citations"]
RUBRIC_MAX = 85.0
# ────────────────────────────────────────────────────────────────────


def load_baseline(path):
    """Load model-averaged per-paper scores from baseline_descriptives.json."""
    with open(path, "r") as f:
        data = json.load(f)

    papers = {}
    for entry in data["per_paper"]:
        pid = entry["paper_id"]
        models = entry["models"]
        model_keys = list(models.keys())
        if len(model_keys) < 2:
            continue

        avg = {}
        for cat in CATEGORIES:
            vals = [models[m]["scores"][cat] for m in model_keys]
            avg[cat] = sum(vals) / len(vals)
        snorm_vals = [models[m]["snorm"] for m in model_keys]
        avg["snorm"] = sum(snorm_vals) / len(snorm_vals)
        papers[pid] = avg

    return papers


def load_contest(pattern):
    """Load model-averaged per-paper scores from contest JSON files."""
    papers = {}
    for fpath in sorted(glob.glob(pattern)):
        with open(fpath, "r") as f:
            records = json.load(f)

        by_paper = {}
        for rec in records:
            pid = rec["paper_id"]
            if rec.get("error"):
                continue
            if pid not in by_paper:
                by_paper[pid] = []
            by_paper[pid].append(rec)

        for pid, recs in by_paper.items():
            if len(recs) < 2:
                continue
            avg = {}
            for cat in CATEGORIES:
                vals = [r["scores"][cat]["score"] for r in recs]
                avg[cat] = sum(vals) / len(vals)
            raw_totals = []
            for r in recs:
                raw = sum(r["scores"][cat]["score"] for cat in CATEGORIES)
                raw_totals.append((raw / RUBRIC_MAX) * 100.0)
            avg["snorm"] = sum(raw_totals) / len(raw_totals)
            papers[pid] = avg

    return papers


def load_noise(path):
    """Load sigma2_noise per category from noise_floor_stats.json."""
    with open(path, "r") as f:
        data = json.load(f)

    sigma2 = {}
    for cat in CATEGORIES + ["snorm"]:
        sigma2[cat] = data["noise_variance"][cat]["sigma2_noise"]
    return sigma2


def sample_variance(vals):
    """Sample variance (ddof=1)."""
    n = len(vals)
    if n < 2:
        return 0.0
    m = sum(vals) / n
    return sum((v - m) ** 2 for v in vals) / (n - 1)


def main():
    print("Loading data...")

    baseline = load_baseline(BASELINE_DESC)
    print(f"  Baseline: {len(baseline)} papers")

    contest = load_contest(CONTEST_PATTERN)
    print(f"  Contest:  {len(contest)} papers")

    sigma2_noise = load_noise(NOISE_STATS)

    # Build per-category arrays
    all_cats = CATEGORIES + ["snorm"]
    baseline_arr = {cat: [] for cat in all_cats}
    contest_arr = {cat: [] for cat in all_cats}

    for pid in sorted(baseline.keys()):
        for cat in all_cats:
            baseline_arr[cat].append(baseline[pid][cat])

    for pid in sorted(contest.keys()):
        for cat in all_cats:
            contest_arr[cat].append(contest[pid][cat])

    n1 = len(contest)   # contest (treatment)
    n2 = len(baseline)   # baseline (control)
    J = 1.0 - 3.0 / (4.0 * (n1 + n2 - 2) - 1.0)

    print(f"\n  n_contest={n1}, n_baseline={n2}, J={J:.6f}")

    # ── Headers ─────────────────────────────────────────────────────
    print()
    print("=" * 78)
    print("  SCORER NOISE SENSITIVITY — DIRECT PERTURBATION")
    print("  g'_low  = K / sqrt(V_p + sigma2_noise)")
    print("  g'_high = K / sqrt(V_p - sigma2_noise)   [if V_p > sigma2_noise]")
    print("=" * 78)

    results = []

    for cat in all_cats:
        x_c = contest_arr[cat]
        x_b = baseline_arr[cat]

        mean_c = sum(x_c) / len(x_c)
        mean_b = sum(x_b) / len(x_b)
        mean_diff = mean_c - mean_b

        s2_c = sample_variance(x_c)
        s2_b = sample_variance(x_b)
        V_p = ((n1 - 1) * s2_c + (n2 - 1) * s2_b) / (n1 + n2 - 2)

        K = J * mean_diff
        s2n = sigma2_noise[cat]

        # Observed g'
        g_obs = K / math.sqrt(V_p)

        # Perturbed: noise inflates V_p (g' shrinks)
        g_low = K / math.sqrt(V_p + s2n)

        # Perturbed: noise deflates V_p (g' grows)
        # Clamp: V_p - s2n must be > 0
        if V_p > s2n:
            g_high = K / math.sqrt(V_p - s2n)
            high_valid = True
        else:
            g_high = None
            high_valid = False

        # Deltas
        delta_minus = g_obs - g_low
        delta_plus = (g_high - g_obs) if high_valid else None

        # Old linearized delta for comparison
        partial = abs(-0.5 * K * (V_p ** (-1.5)))
        delta_linear = partial * s2n

        label = cat.replace("_", " ").title() if cat != "snorm" else "S_norm"

        results.append({
            "category": cat,
            "label": label,
            "K": K,
            "V_p": V_p,
            "sigma2_noise": s2n,
            "g_obs": g_obs,
            "g_low": g_low,
            "g_high": g_high,
            "high_valid": high_valid,
            "delta_plus": delta_plus,
            "delta_minus": delta_minus,
            "delta_linear": delta_linear,
        })

        print(f"\n  {label}")
        print(f"    K (J·mean_diff): {K:+.6f}")
        print(f"    V_p:             {V_p:.6f}")
        print(f"    sigma2_noise:    {s2n:.6f}")
        print(f"    V_p / sigma2:    {V_p / s2n:.2f}x")
        print(f"    g'_obs:          {g_obs:+.4f}")
        print(f"    g'_low:          {g_low:+.4f}   (V_p + sigma2)")
        if high_valid:
            print(f"    g'_high:         {g_high:+.4f}   (V_p - sigma2)")
        else:
            print(f"    g'_high:         INVALID (V_p <= sigma2_noise)")
        print(f"    Δ-:              {delta_minus:.6f}")
        print(f"    Δ+:              {f'{delta_plus:.6f}' if delta_plus is not None else 'N/A'}")
        print(f"    (old linear δ):  {delta_linear:.6f}")

    # ── Summary table ───────────────────────────────────────────────
    print("\n")
    print("=" * 78)
    print("  SUMMARY")
    print("=" * 78)
    print(f"  {'Category':<22} {'g_obs':>8} {'g_low':>8} {'g_high':>8}   {'Δ-':>8} {'Δ+':>8}   {'old δ':>8}")
    print(f"  {'-'*22} {'-'*8} {'-'*8} {'-'*8}   {'-'*8} {'-'*8}   {'-'*8}")
    for r in results:
        g_hi_str = f"{r['g_high']:+.4f}" if r['high_valid'] else "  N/A  "
        dp_str = f"{r['delta_plus']:.4f}" if r['delta_plus'] is not None else "  N/A  "
        print(
            f"  {r['label']:<22} {r['g_obs']:+.4f}  {r['g_low']:+.4f}  {g_hi_str}"
            f"   {r['delta_minus']:.4f}  {dp_str}"
            f"   {r['delta_linear']:.4f}"
        )

    # ── Asymmetry check ─────────────────────────────────────────────
    print(f"\n  Asymmetry (Δ+ / Δ- ratio, >1 means upside is larger):")
    for r in results:
        if r['delta_plus'] is not None and r['delta_minus'] > 0:
            ratio = r['delta_plus'] / r['delta_minus']
            print(f"    {r['label']:<22} {ratio:.3f}")
        else:
            print(f"    {r['label']:<22} N/A")

    # ── Save JSON ───────────────────────────────────────────────────
    output_path = os.path.join(OUTPUT_DIR, "gprime_perturbation.json")
    output_data = {
        "meta": {
            "description": (
                "Scorer noise sensitivity of g' via direct perturbation of V_p. "
                "g'_low = K/sqrt(V_p + sigma2_noise), g'_high = K/sqrt(V_p - sigma2_noise). "
                "Asymmetric bounds. NOT a confidence interval."
            ),
            "method": "direct_perturbation",
            "n_contest": n1,
            "n_baseline": n2,
            "J": round(J, 6),
        },
        "results": {
            r["category"]: {
                "g_obs": round(r["g_obs"], 6),
                "g_low": round(r["g_low"], 6),
                "g_high": round(r["g_high"], 6) if r["high_valid"] else None,
                "delta_plus": round(r["delta_plus"], 6) if r["delta_plus"] is not None else None,
                "delta_minus": round(r["delta_minus"], 6),
                "delta_linear_old": round(r["delta_linear"], 6),
                "K": round(r["K"], 6),
                "V_p": round(r["V_p"], 6),
                "sigma2_noise": round(r["sigma2_noise"], 6),
            }
            for r in results
        }
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\n  Saved: {output_path}")


if __name__ == "__main__":
    main()
