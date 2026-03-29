"""
compile_contest_descriptives.py

Compiles all contest JSONs into a single structured descriptor file.
Output: contest_descriptives.json

Expected input: ./output/*_contest.json
Each file contains two records (one per model) with scores nested under "scores".
"""

import json
import os
import math
from glob import glob

# --- Config ---
OUTPUT_DIR = "./output"
OUTPUT_FILE = "./output/contest_descriptives.json"
CATEGORIES = ["hypothesis", "novelty", "scientific_humility", "engagement", "rigor", "citations"]
MAX_RAW = 85.0
MODELS = ["claude-sonnet-4-6", "gpt-5.2"]

# --- Helpers ---

def compute_snorm(scores_dict):
    raw = sum(scores_dict[c]["score"] for c in CATEGORIES)
    return round((raw / MAX_RAW) * 100, 1)

def mean(vals):
    return sum(vals) / len(vals) if vals else None

def variance(vals):
    if len(vals) < 2:
        return None
    m = mean(vals)
    return sum((v - m) ** 2 for v in vals) / (len(vals) - 1)

def stddev(vals):
    v = variance(vals)
    return math.sqrt(v) if v is not None else None

def median(vals):
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 != 0 else round((s[mid - 1] + s[mid]) / 2, 4)

def mode(vals):
    if not vals:
        return None
    from collections import Counter
    rounded = [round(v, 4) for v in vals]
    counts = Counter(rounded)
    max_count = max(counts.values())
    modes = sorted(k for k, v in counts.items() if v == max_count)
    return modes if len(modes) > 1 else modes[0]

# --- Load all contest files ---

contest_files = sorted(glob(os.path.join(OUTPUT_DIR, "*_contest.json")))
print(f"Found {len(contest_files)} contest files.")

papers = {}  # paper_id -> {citation, group, models: {model_name: {categories, snorm}}}

for filepath in contest_files:
    print(f"Loading: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        records = json.load(f)

    for record in records:
        paper_id = record["paper_id"]
        citation = record["citation"]
        group = record["group"]
        model = record["model"]
        scores = record["scores"]
        error = record.get("error")

        if paper_id not in papers:
            papers[paper_id] = {
                "paper_id": paper_id,
                "citation": citation,
                "group": group,
                "models": {}
            }

        if error:
            papers[paper_id]["models"][model] = {"error": error}
            continue

        category_scores = {c: scores[c]["score"] for c in CATEGORIES}
        snorm = compute_snorm(scores)

        papers[paper_id]["models"][model] = {
            "scores": category_scores,
            "snorm": snorm
        }

# --- Build per-paper records ---

per_paper = []

for paper_id in sorted(papers.keys()):
    p = papers[paper_id]
    record = {
        "paper_id": p["paper_id"],
        "citation": p["citation"],
        "group": p["group"],
        "models": {}
    }

    snorms = []
    for model in MODELS:
        if model in p["models"]:
            mdata = p["models"][model]
            if "error" in mdata:
                record["models"][model] = {"error": mdata["error"]}
            else:
                record["models"][model] = {
                    "scores": mdata["scores"],
                    "snorm": mdata["snorm"]
                }
                snorms.append(mdata["snorm"])

    # Average Snorm across models (if both present)
    record["snorm_avg"] = round(mean(snorms), 2) if len(snorms) == 2 else None

    per_paper.append(record)

# --- Build summary statistics ---

# Collect per-model per-category score lists and snorm lists
model_cat_scores = {m: {c: [] for c in CATEGORIES} for m in MODELS}
model_snorms = {m: [] for m in MODELS}
avg_snorms = []

for p in per_paper:
    snorms_this = []
    for model in MODELS:
        mdata = p["models"].get(model, {})
        if "scores" in mdata:
            for c in CATEGORIES:
                model_cat_scores[model][c].append(mdata["scores"][c])
            model_snorms[model].append(mdata["snorm"])
            snorms_this.append(mdata["snorm"])
    if len(snorms_this) == 2:
        avg_snorms.append(mean(snorms_this))

summary = {
    "n_papers": len(per_paper),
    "models": {}
}

for model in MODELS:
    cat_stats = {}
    for c in CATEGORIES:
        vals = model_cat_scores[model][c]
        cat_stats[c] = {
            "mean": round(mean(vals), 4) if vals else None,
            "median": median(vals),
            "mode": mode(vals),
            "variance": round(variance(vals), 4) if vals else None,
            "stddev": round(stddev(vals), 4) if vals else None,
            "min": min(vals) if vals else None,
            "max": max(vals) if vals else None,
            "n": len(vals)
        }
    snorm_vals = model_snorms[model]
    summary["models"][model] = {
        "categories": cat_stats,
        "snorm": {
            "mean": round(mean(snorm_vals), 4) if snorm_vals else None,
            "median": median(snorm_vals),
            "mode": mode(snorm_vals),
            "variance": round(variance(snorm_vals), 4) if snorm_vals else None,
            "stddev": round(stddev(snorm_vals), 4) if snorm_vals else None,
            "min": min(snorm_vals) if snorm_vals else None,
            "max": max(snorm_vals) if snorm_vals else None,
            "n": len(snorm_vals)
        }
    }

# Inter-model deltas per category (mean score difference: claude - gpt)
inter_model_deltas = {}
for c in CATEGORIES:
    vals_a = model_cat_scores[MODELS[0]][c]
    vals_b = model_cat_scores[MODELS[1]][c]
    paired = [(a - b) for a, b in zip(vals_a, vals_b)]
    inter_model_deltas[c] = {
        "mean_delta": round(mean(paired), 4) if paired else None,
        "stddev_delta": round(stddev(paired), 4) if paired else None,
        "note": f"{MODELS[0]} minus {MODELS[1]}"
    }

snorm_deltas = [
    p["models"][MODELS[0]]["snorm"] - p["models"][MODELS[1]]["snorm"]
    for p in per_paper
    if "snorm" in p["models"].get(MODELS[0], {}) and "snorm" in p["models"].get(MODELS[1], {})
]
inter_model_deltas["snorm"] = {
    "mean_delta": round(mean(snorm_deltas), 4) if snorm_deltas else None,
    "stddev_delta": round(stddev(snorm_deltas), 4) if snorm_deltas else None,
    "note": f"{MODELS[0]} minus {MODELS[1]}"
}

summary["inter_model_deltas"] = inter_model_deltas

# Averaged-model summary (across both models)
avg_cat_scores = {c: [] for c in CATEGORIES}
for p in per_paper:
    for c in CATEGORIES:
        vals = [
            p["models"][m]["scores"][c]
            for m in MODELS
            if "scores" in p["models"].get(m, {})
        ]
        if len(vals) == 2:
            avg_cat_scores[c].append(mean(vals))

summary["averaged_across_models"] = {
    "categories": {
        c: {
            "mean": round(mean(avg_cat_scores[c]), 4) if avg_cat_scores[c] else None,
            "median": median(avg_cat_scores[c]),
            "mode": mode(avg_cat_scores[c]),
            "variance": round(variance(avg_cat_scores[c]), 4) if avg_cat_scores[c] else None,
            "stddev": round(stddev(avg_cat_scores[c]), 4) if avg_cat_scores[c] else None,
        }
        for c in CATEGORIES
    },
    "snorm": {
        "mean": round(mean(avg_snorms), 4) if avg_snorms else None,
        "median": median(avg_snorms),
        "mode": mode(avg_snorms),
        "variance": round(variance(avg_snorms), 4) if avg_snorms else None,
        "stddev": round(stddev(avg_snorms), 4) if avg_snorms else None,
        "min": round(min(avg_snorms), 2) if avg_snorms else None,
        "max": round(max(avg_snorms), 2) if avg_snorms else None,
    }
}

# --- Assemble and write output ---

output = {
    "meta": {
        "description": "Compiled contest descriptives for LLMPhysics contest analysis",
        "n_files_loaded": len(contest_files),
        "n_papers": len(per_paper),
        "categories": CATEGORIES,
        "max_raw_score": MAX_RAW,
        "models": MODELS
    },
    "per_paper": per_paper,
    "summary": summary
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print(f"Written: {OUTPUT_FILE}")
print(f"Papers compiled: {len(per_paper)}")
print(f"\n--- Quick summary ---")
for model in MODELS:
    snorm_mean = summary["models"][model]["snorm"]["mean"]
    snorm_median = summary["models"][model]["snorm"]["median"]
    snorm_mode = summary["models"][model]["snorm"]["mode"]
    print(f"  {model} Snorm -> mean: {snorm_mean}, median: {snorm_median}, mode: {snorm_mode}")
avg = summary['averaged_across_models']['snorm']
print(f"  Averaged Snorm -> mean: {avg['mean']}, median: {avg['median']}, mode: {avg['mode']}")
print(f"\nInter-model deltas (claude - gpt):")
for c in CATEGORIES + ["snorm"]:
    d = inter_model_deltas[c]["mean_delta"]
    print(f"  {c}: {d:+.4f}")
