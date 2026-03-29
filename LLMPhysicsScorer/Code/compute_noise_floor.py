"""
compute_noise_floor.py

Computes per-category noise variance from noisefloor.json per methodology v1.1 Section 4.3.

For each paper i, category c, model m:
    s²_i,m,c = sample variance of 5 repeated scores

Noise variance:
    σ²_noise,c = (1 / 2k) * sum over models and papers of s²_i,m,c
    where k = 10

Output: noise_floor_stats.json
"""

import json
import math
from collections import defaultdict

# --- Config ---
INPUT_FILE = "./output/noisefloor.json"
OUTPUT_FILE = "./output/noise_floor_stats.json"
CATEGORIES = ["hypothesis", "novelty", "scientific_humility", "engagement", "rigor", "citations"]
MAX_RAW = 85.0
MODELS = ["claude-sonnet-4-6", "gpt-5.2"]
K = 10  # number of papers in noise floor
RUNS_PER_PAPER = 5

# --- Helpers ---

def mean(vals):
    return sum(vals) / len(vals) if vals else None

def sample_variance(vals):
    if len(vals) < 2:
        return None
    m = mean(vals)
    return sum((v - m) ** 2 for v in vals) / (len(vals) - 1)

def compute_snorm(scores_dict):
    raw = sum(scores_dict[c]["score"] for c in CATEGORIES)
    return round((raw / MAX_RAW) * 100, 4)

# --- Load noisefloor.json ---

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    records = json.load(f)

print(f"Loaded {len(records)} noise floor records.")

# --- Organize by (paper_id, model) -> list of run records ---

grouped = defaultdict(list)  # (paper_id, model) -> [records]

for r in records:
    if r.get("error"):
        print(f"  WARNING: error record for paper {r['paper_id']} model {r['model']} run {r.get('run')} — skipping.")
        continue
    key = (r["paper_id"], r["model"])
    grouped[key].append(r)

# Verify we have 5 runs per (paper, model)
for key, runs in grouped.items():
    if len(runs) != RUNS_PER_PAPER:
        print(f"  WARNING: {key} has {len(runs)} runs (expected {RUNS_PER_PAPER})")

# --- Compute within-paper variances ---

# per_paper_variances[(paper_id, model)][category] = s²_i,m,c
per_paper_variances = {}

for key, runs in grouped.items():
    paper_id, model = key
    cat_var = {}
    for c in CATEGORIES:
        scores = [r["scores"][c]["score"] for r in runs]
        cat_var[c] = sample_variance(scores)
    # Also compute snorm variance
    snorms = [compute_snorm(r["scores"]) for r in runs]
    cat_var["snorm"] = sample_variance(snorms)
    per_paper_variances[key] = cat_var

# --- Compute σ²_noise,c per methodology eq. 3 ---
# σ²_noise,c = (1 / 2k) * sum over all (paper, model) of s²_i,m,c

all_cats = CATEGORIES + ["snorm"]
noise_variance = {}
noise_stddev = {}

for c in all_cats:
    variances = [per_paper_variances[key][c] for key in per_paper_variances if per_paper_variances[key][c] is not None]
    sigma2 = sum(variances) / (2 * K)
    noise_variance[c] = sigma2
    noise_stddev[c] = math.sqrt(sigma2)

# --- Per-model breakdown (informational, not used in methodology) ---

model_noise = {}
for model in MODELS:
    model_noise[model] = {}
    for c in all_cats:
        variances = [
            per_paper_variances[(pid, model)][c]
            for (pid, m) in per_paper_variances
            if m == model and per_paper_variances[(pid, model)][c] is not None
        ]
        sigma2 = sum(variances) / K if variances else None
        model_noise[model][c] = {
            "sigma2_noise": round(sigma2, 6) if sigma2 is not None else None,
            "sigma_noise": round(math.sqrt(sigma2), 6) if sigma2 is not None else None
        }

# --- Per-paper variance detail (for audit trail) ---

per_paper_detail = []
paper_ids = sorted(set(pid for (pid, _) in per_paper_variances))
for paper_id in paper_ids:
    entry = {"paper_id": paper_id, "models": {}}
    for model in MODELS:
        key = (paper_id, model)
        if key in per_paper_variances:
            entry["models"][model] = {
                c: round(per_paper_variances[key][c], 6) if per_paper_variances[key][c] is not None else None
                for c in all_cats
            }
    per_paper_detail.append(entry)

# --- Assemble output ---

output = {
    "meta": {
        "description": "Noise floor variance statistics per methodology v1.1 Section 4.3",
        "input_file": INPUT_FILE,
        "k": K,
        "runs_per_paper": RUNS_PER_PAPER,
        "n_models": len(MODELS),
        "models": MODELS,
        "total_runs": len(records),
        "categories": CATEGORIES
    },
    "noise_variance": {
        c: {
            "sigma2_noise": round(noise_variance[c], 6),
            "sigma_noise": round(noise_stddev[c], 6)
        }
        for c in all_cats
    },
    "per_model_breakdown": model_noise,
    "per_paper_variances": per_paper_detail
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"\nWritten: {OUTPUT_FILE}")
print(f"\n--- Noise Floor Results ---")
print(f"{'Category':<25} {'σ²_noise':>12} {'σ_noise':>12}")
print("-" * 51)
for c in all_cats:
    s2 = noise_variance[c]
    s = noise_stddev[c]
    print(f"{c:<25} {s2:>12.6f} {s:>12.6f}")
