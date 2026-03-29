"""
run_analysis.py

Implements the full statistical analysis per LLMPhysics Methodology v1.1.
Reads: baseline_descriptives.json, contest_descriptives.json, noise_floor_stats.json
Writes: analysis_results.json

Steps per category and Snorm:
  1. Observed pooled SD (Eq. 5)
  2. Noise-corrected pooled SD (Eq. 6)
  3. Raw effect size g (Eq. 7)
  4. Hedges' small-sample correction J (Eq. 8-9)
  5. Bootstrap CIs (B=10,000, fixed noise floor, percentile method) (Sec. 6)
  6. Decision framework (Sec. 7)
"""

import json
import math
import random
from datetime import datetime, timezone

# --- Config ---
BASELINE_FILE = "./output/baseline_descriptives.json"
CONTEST_FILE  = "./output/contest_descriptives.json"
NOISE_FILE    = "./output/noise_floor_stats.json"
OUTPUT_FILE   = "./output/analysis_results.json"

CATEGORIES = ["hypothesis", "novelty", "scientific_humility", "engagement", "rigor", "citations"]
METRICS = CATEGORIES + ["snorm"]

B = 10_000           # bootstrap iterations
SEED = 42            # reproducibility
INVALID_THRESHOLD = 0.10  # >10% invalid iterations -> CI declared unreliable

random.seed(SEED)

# --- Helpers ---

def sample_variance(vals):
    """Sample variance (ddof=1)."""
    n = len(vals)
    if n < 2:
        return 0.0
    m = sum(vals) / n
    return sum((v - m) ** 2 for v in vals) / (n - 1)

def mean(vals):
    return sum(vals) / len(vals) if vals else None

def observed_pooled_sd(s2_1, n1, s2_2, n2):
    """Eq. 5: observed pooled SD."""
    pooled_var = ((n1 - 1) * s2_1 + (n2 - 1) * s2_2) / (n1 + n2 - 2)
    return math.sqrt(pooled_var), pooled_var

def noise_corrected_sd(pooled_var, sigma2_noise):
    """Eq. 6: noise-corrected pooled SD. Returns (sd, valid)."""
    corrected_var = pooled_var - sigma2_noise
    if corrected_var <= 0:
        return None, False
    return math.sqrt(corrected_var), True

def hedges_j(n1, n2):
    """Eq. 8: Hedges' small-sample correction factor."""
    df = n1 + n2 - 2
    return 1 - (3 / (4 * df - 1))

def classify_magnitude(g_prime):
    """Returns magnitude classification string per Sec. 7.2 / 7.3."""
    ag = abs(g_prime)
    if g_prime >= 0.8:
        return "large_improvement"
    elif g_prime >= 0.5:
        return "medium_improvement"
    elif g_prime >= 0.2:
        return "small_improvement"
    elif g_prime <= -0.8:
        return "large_regression"
    elif g_prime <= -0.5:
        return "medium_regression"
    elif g_prime <= -0.2:
        return "small_regression"
    else:
        return "null"

def decision_outcome(g_prime, valid):
    """Returns outcome label per Sec. 7.2."""
    if not valid:
        return "invalid"
    if g_prime >= 0.2:
        return "H1_supported"
    elif g_prime <= -0.2:
        return "H0_rejected_regression"
    else:
        return "H0_not_rejected"

def resample(vals):
    """Resample with replacement (bootstrap)."""
    n = len(vals)
    return [vals[int(random.random() * n)] for _ in range(n)]

def bootstrap_ci(contest_vals, baseline_vals, sigma2_noise, n1, n2, J):
    """
    B=10,000 bootstrap iterations per Sec. 6.2.
    sigma2_noise held fixed (Sec. 6.3).
    Returns (ci_low, ci_high, invalid_fraction, valid_count).
    """
    g_prime_boot = []
    invalid_count = 0

    for _ in range(B):
        b_contest  = resample(contest_vals)
        b_baseline = resample(baseline_vals)

        m1 = mean(b_contest)
        m2 = mean(b_baseline)
        s2_1 = sample_variance(b_contest)
        s2_2 = sample_variance(b_baseline)

        _, pooled_var = observed_pooled_sd(s2_1, n1, s2_2, n2)
        sd_corr, valid = noise_corrected_sd(pooled_var, sigma2_noise)

        if not valid:
            invalid_count += 1
            continue

        g_raw = (m1 - m2) / sd_corr
        g_prime_boot.append(g_raw * J)

    total = B
    invalid_frac = invalid_count / total
    valid_count = len(g_prime_boot)

    if valid_count == 0:
        return None, None, invalid_frac, valid_count

    g_prime_boot.sort()
    lo_idx = int(math.floor(0.025 * valid_count))
    hi_idx = int(math.ceil(0.975 * valid_count)) - 1
    hi_idx = min(hi_idx, valid_count - 1)

    return (
        round(g_prime_boot[lo_idx], 6),
        round(g_prime_boot[hi_idx], 6),
        round(invalid_frac, 6),
        valid_count
    )

# --- Load data ---

print("Loading data...")

with open(BASELINE_FILE, "r", encoding="utf-8") as f:
    baseline = json.load(f)

with open(CONTEST_FILE, "r", encoding="utf-8") as f:
    contest = json.load(f)

with open(NOISE_FILE, "r", encoding="utf-8") as f:
    noise = json.load(f)

# Extract per-paper score lists from per_paper records
# Use snorm_avg for snorm, category scores averaged across both models

def extract_scores(descriptives, metric):
    """
    Extract per-paper scores for a given metric.
    For categories: average of both models' scores per paper.
    For snorm: snorm_avg field.
    Returns list of floats (one per paper), skipping papers with errors.
    """
    vals = []
    for paper in descriptives["per_paper"]:
        models = paper.get("models", {})
        if metric == "snorm":
            v = paper.get("snorm_avg")
            if v is not None:
                vals.append(v)
        else:
            # average both models
            scores = []
            for mdata in models.values():
                if "scores" in mdata:
                    scores.append(mdata["scores"][metric])
            if len(scores) == 2:
                vals.append(sum(scores) / 2)
    return vals

baseline_scores = {m: extract_scores(baseline, m) for m in METRICS}
contest_scores  = {m: extract_scores(contest,  m) for m in METRICS}

n2 = len(baseline_scores["snorm"])  # should be 50
n1 = len(contest_scores["snorm"])   # should be 10

print(f"Baseline papers: {n2}, Contest papers: {n1}")

J = hedges_j(n1, n2)
print(f"Hedges' J correction: {J:.6f}")

# --- Run analysis per metric ---

results = {}

for metric in METRICS:
    print(f"\nAnalyzing: {metric}")

    c_vals = contest_scores[metric]
    b_vals = baseline_scores[metric]

    sigma2_noise = noise["noise_variance"][metric]["sigma2_noise"]

    m1 = mean(c_vals)
    m2 = mean(b_vals)
    s2_1 = sample_variance(c_vals)
    s2_2 = sample_variance(b_vals)

    sd_obs, pooled_var = observed_pooled_sd(s2_1, n1, s2_2, n2)
    sd_corr, valid = noise_corrected_sd(pooled_var, sigma2_noise)

    if valid:
        g_raw = (m1 - m2) / sd_corr
        g_prime = g_raw * J
    else:
        g_raw = None
        g_prime = None

    # Bootstrap CI
    ci_lo, ci_hi, invalid_frac, valid_boot = bootstrap_ci(
        c_vals, b_vals, sigma2_noise, n1, n2, J
    )

    ci_reliable = (invalid_frac <= INVALID_THRESHOLD) and (ci_lo is not None)

    outcome = decision_outcome(g_prime, valid and ci_reliable)
    magnitude = classify_magnitude(g_prime) if (valid and g_prime is not None) else None

    results[metric] = {
        "n1": n1,
        "n2": n2,
        "mean_contest": round(m1, 6),
        "mean_baseline": round(m2, 6),
        "mean_diff": round(m1 - m2, 6),
        "s2_contest": round(s2_1, 6),
        "s2_baseline": round(s2_2, 6),
        "sigma2_noise": sigma2_noise,
        "sd_observed": round(sd_obs, 6),
        "pooled_var_observed": round(pooled_var, 6),
        "pooled_var_corrected": round(pooled_var - sigma2_noise, 6),
        "sd_corrected": round(sd_corr, 6) if sd_corr else None,
        "valid": valid,
        "J": round(J, 6),
        "g_raw": round(g_raw, 6) if g_raw is not None else None,
        "g_prime": round(g_prime, 6) if g_prime is not None else None,
        "bootstrap": {
            "B": B,
            "seed": SEED,
            "ci_95_lo": ci_lo,
            "ci_95_hi": ci_hi,
            "invalid_iterations": round(invalid_frac * B),
            "invalid_fraction": invalid_frac,
            "valid_iterations": valid_boot,
            "ci_reliable": ci_reliable
        },
        "outcome": outcome,
        "magnitude": magnitude
    }

    print(f"  mean_diff: {m1 - m2:+.4f}")
    sd_corr_str = f"{sd_corr:.4f}" if sd_corr else "INVALID"
    g_prime_str = f"{g_prime:.4f}" if g_prime is not None else "INVALID"
    print(f"  sd_observed: {sd_obs:.4f}, sd_corrected: {sd_corr_str}")
    print(f"  g_prime: {g_prime_str}")
    print(f"  CI 95%: [{ci_lo}, {ci_hi}] (reliable: {ci_reliable})")
    print(f"  outcome: {outcome} | magnitude: {magnitude}")

# --- Write output ---

output = {
    "meta": {
        "description": "LLMPhysics contest analysis results per methodology v1.1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_file": BASELINE_FILE,
        "contest_file": CONTEST_FILE,
        "noise_file": NOISE_FILE,
        "n1": n1,
        "n2": n2,
        "B": B,
        "seed": SEED,
        "J": round(J, 6),
        "methodology_sha256": "D8E0F7BA894902B613773FB40A50BD7F135747A2ED5AB81AA606A0FAF4984304"
    },
    "results": results
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"\nWritten: {OUTPUT_FILE}")
print("\n=== SUMMARY ===")
for metric in METRICS:
    r = results[metric]
    gp = f"{r['g_prime']:.4f}" if r['g_prime'] is not None else "INVALID"
    ci = f"[{r['bootstrap']['ci_95_lo']}, {r['bootstrap']['ci_95_hi']}]" if r['bootstrap']['ci_reliable'] else "[UNRELIABLE]"
    print(f"  {metric:22s} g'={gp:>8}  CI={ci}  -> {r['outcome']}")
