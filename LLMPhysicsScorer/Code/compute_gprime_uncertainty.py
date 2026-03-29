"""
compute_gprime_noise_sensitivity.py

Computes noise-floor-propagated sensitivity of g' to instrument noise
for each category and Snorm using error propagation (partial derivative).

    δg' = |(-1/2) · k · (s²_pooled)^(-3/2)| · σ²_noise

where k = J · (mean_contest - mean_baseline)

This is NOT a true uncertainty estimate — it quantifies how much the
point estimate of g' would shift if the pooled variance shifted by
σ²_noise. The noise floor is symmetric (scores can jitter up or down),
so it does not bias the effect size in expectation. This measure
characterizes instrument sensitivity, not estimation uncertainty.
True estimation uncertainty is captured by the bootstrap CIs.

Reported in parenthetical notation: g' = 1.33(04)

Reads from:
  - output/baseline_descriptives.json
  - output/noise_floor_stats.json
  - output/ *_contest.json files

Run from the llmphysics_scorer directory.
"""

import json
import os
import glob
import numpy as np

# ── CONFIG ──────────────────────────────────────────────────────────
OUTPUT_DIR          = "output"
BASELINE_DESC       = os.path.join(OUTPUT_DIR, "baseline_descriptives.json")
NOISE_STATS         = os.path.join(OUTPUT_DIR, "noise_floor_stats.json")
CONTEST_PATTERN     = os.path.join(OUTPUT_DIR, "*_contest.json")

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
            avg[cat] = np.mean([models[m]["scores"][cat] for m in model_keys])
        avg["snorm"] = np.mean([models[m]["snorm"] for m in model_keys])
        papers[pid] = avg

    return papers


def load_contest(pattern):
    """Load model-averaged per-paper scores from contest JSON files."""
    papers = {}
    for fpath in sorted(glob.glob(pattern)):
        with open(fpath, "r") as f:
            records = json.load(f)

        # Group by paper_id
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
                avg[cat] = np.mean([r["scores"][cat]["score"] for r in recs])
            raw_totals = []
            for r in recs:
                raw = sum(r["scores"][cat]["score"] for cat in CATEGORIES)
                raw_totals.append((raw / RUBRIC_MAX) * 100.0)
            avg["snorm"] = np.mean(raw_totals)
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


def to_arrays(paper_dict):
    """Convert dict of paper scores to per-category numpy arrays."""
    all_cats = CATEGORIES + ["snorm"]
    arrays = {cat: [] for cat in all_cats}
    for pid in sorted(paper_dict.keys()):
        for cat in all_cats:
            arrays[cat].append(paper_dict[pid][cat])
    return {cat: np.array(v) for cat, v in arrays.items()}


def format_parenthetical(g_prime, delta):
    """Format g' with parenthetical noise sensitivity like physics notation.
    e.g., g' = 1.3320 with delta = 0.004 -> '1.332(4)'
    """
    if delta <= 0 or not np.isfinite(delta):
        return f"{g_prime:.4f}(0)"

    # Determine decimal places needed to show delta as integer in last digits
    dec_places = max(0, -int(np.floor(np.log10(delta))) + 1)
    dec_places = min(dec_places, 6)  # cap at 6 decimal places

    # Round g' to that precision
    g_rounded = round(g_prime, dec_places)

    # Express delta in units of last decimal place
    delta_in_last = round(delta * (10 ** dec_places))
    if delta_in_last == 0:
        delta_in_last = 1  # minimum 1 unit

    return f"{g_rounded:.{dec_places}f}({delta_in_last})"


def main():
    print("Loading baseline descriptives...")
    baseline = load_baseline(BASELINE_DESC)
    print(f"  {len(baseline)} papers")

    print("Loading contest scores...")
    contest = load_contest(CONTEST_PATTERN)
    print(f"  {len(contest)} papers")

    print("Loading noise floor stats...")
    sigma2_noise = load_noise(NOISE_STATS)

    baseline_arr = to_arrays(baseline)
    contest_arr = to_arrays(contest)

    n1 = len(contest)
    n2 = len(baseline)
    J = 1.0 - 3.0 / (4.0 * (n1 + n2 - 2) - 1.0)

    all_cats = CATEGORIES + ["snorm"]

    print()
    print("=" * 70)
    print("  NOISE-FLOOR SENSITIVITY OF g'")
    print("  How much g' shifts per sigma2_noise of instrument jitter")
    print("  delta_g' = |(-1/2) * k * (s2_pooled)^(-3/2)| * sigma2_noise")
    print(f"  n_contest = {n1}, n_baseline = {n2}, J = {J:.4f}")
    print("=" * 70)

    results = []

    for cat in all_cats:
        x1 = contest_arr[cat]
        x2 = baseline_arr[cat]

        mean_diff = np.mean(x1) - np.mean(x2)
        s2_1 = np.var(x1, ddof=1)
        s2_2 = np.var(x2, ddof=1)
        s2_pooled = ((n1 - 1) * s2_1 + (n2 - 1) * s2_2) / (n1 + n2 - 2)
        sd_pooled = np.sqrt(s2_pooled)

        # Uncorrected g'
        g_raw = mean_diff / sd_pooled
        g_prime = J * g_raw

        # k = J * mean_diff
        k = J * mean_diff

        # Error propagation: dg'/d(s2) = (-1/2) * k * (s2)^(-3/2)
        s2n = sigma2_noise[cat]
        partial = abs(-0.5 * k * (s2_pooled ** (-1.5)))
        delta_gp = partial * s2n

        paren = format_parenthetical(g_prime, delta_gp)

        label = cat.replace("_", " ").title() if cat != "snorm" else "S_norm"

        results.append({
            "category": label,
            "mean_diff": mean_diff,
            "s2_pooled": s2_pooled,
            "sigma2_noise": s2n,
            "g_prime": g_prime,
            "delta_gprime": delta_gp,
            "formatted": paren
        })

        print(f"\n  {label}")
        print(f"    Mean diff:   {mean_diff:+.3f}")
        print(f"    s2_pooled:   {s2_pooled:.4f}")
        print(f"    sigma2_noise:{s2n:.6f}")
        print(f"    g' (uncorr): {g_prime:.4f}")
        print(f"    dg'/d(s2):   {partial:.6f}")
        print(f"    delta_g':    {delta_gp:.6f}")
        print(f"    --> g' = {paren}")

    # Summary table
    print("\n")
    print("=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    print(f"  {'Category':<22} {'g_prime':<18} {'delta_g_prime':<12}")
    print(f"  {'-'*22} {'-'*18} {'-'*12}")
    for r in results:
        print(f"  {r['category']:<22} {r['formatted']:<18} {r['delta_gprime']:<12.6f}")

    # Write JSON output
    output_path = os.path.join(OUTPUT_DIR, "gprime_noise_sensitivity.json")
    output_data = {
        "meta": {
            "description": "Noise-floor sensitivity of g' to instrument jitter via error propagation. This is NOT a true uncertainty — it quantifies how much g' shifts per sigma2_noise. Noise is symmetric and does not bias the point estimate. True estimation uncertainty is given by bootstrap CIs.",
            "method": "delta_g' = |(-1/2) * k * (s2_pooled)^(-3/2)| * sigma2_noise",
            "n_contest": n1,
            "n_baseline": n2,
            "J": round(J, 6)
        },
        "results": {
            r["category"].lower().replace(" ", "_"): {
                "g_prime": round(r["g_prime"], 6),
                "delta_gprime": round(r["delta_gprime"], 6),
                "formatted": r["formatted"],
                "mean_diff": round(r["mean_diff"], 6),
                "s2_pooled": round(r["s2_pooled"], 6),
                "sigma2_noise": round(r["sigma2_noise"], 6)
            }
            for r in results
        }
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"\n  Saved: {output_path}")


if __name__ == "__main__":
    main()