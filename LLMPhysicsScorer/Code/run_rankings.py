import json
import sys
from pathlib import Path

INPUT_FILE  = Path("contest_descriptives.json")
OUTPUT_FILE = Path("contest_rankings.json")

MAX_RAW = 85.0


def compute_rankings(data: dict) -> dict:
    papers = data["per_paper"]
    categories = data["meta"]["categories"]
    models = data["meta"]["models"]

    ranked = []
    for paper in papers:
        entry = {
            "paper_id":  paper["paper_id"],
            "citation":  paper["citation"],
            "group":     paper["group"],
            "snorm_avg": paper["snorm_avg"],
            "models":    {},
        }

        for model in models:
            scores = paper["models"][model]["scores"]
            snorm  = paper["models"][model]["snorm"]
            entry["models"][model] = {
                "snorm":  snorm,
                "scores": scores,
            }

        # Per-category inter-model deltas (claude minus gpt)
        m0, m1 = models[0], models[1]
        deltas = {}
        for cat in categories:
            s0 = paper["models"][m0]["scores"][cat]
            s1 = paper["models"][m1]["scores"][cat]
            deltas[cat] = round(s0 - s1, 4)
        deltas["snorm"] = round(
            paper["models"][m0]["snorm"] - paper["models"][m1]["snorm"], 4
        )
        entry["inter_model_deltas"] = deltas

        ranked.append(entry)

    # Sort by snorm_avg descending
    ranked.sort(key=lambda x: x["snorm_avg"], reverse=True)

    # Attach rank
    for i, entry in enumerate(ranked, start=1):
        entry["rank"] = i

    # Reorder keys for readability
    ranked = [
        {
            "rank":                entry["rank"],
            "paper_id":            entry["paper_id"],
            "citation":            entry["citation"],
            "group":               entry["group"],
            "snorm_avg":           entry["snorm_avg"],
            "models":              entry["models"],
            "inter_model_deltas":  entry["inter_model_deltas"],
        }
        for entry in ranked
    ]

    return {
        "meta": {
            "description":   "Ranked contest results derived from contest_descriptives.json",
            "n_papers":      len(ranked),
            "categories":    categories,
            "models":        models,
            "max_raw_score": MAX_RAW,
            "rank_by":       "snorm_avg (mean of both models)",
        },
        "rankings": ranked,
        "summary":  data.get("summary", {}),
    }


def main():
    input_path  = Path(sys.argv[1]) if len(sys.argv) > 1 else INPUT_FILE
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else OUTPUT_FILE

    if not input_path.exists():
        print(f"Error: input file not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    output = compute_rankings(data)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Rankings written to {output_path}")
    print(f"  Papers ranked: {output['meta']['n_papers']}")
    print()
    print(f"  {'Rank':<6} {'Paper':<8} {'Avg Snorm':<12} {'Citation'}")
    print(f"  {'-'*4:<6} {'-'*5:<8} {'-'*9:<12} {'-'*20}")
    for entry in output["rankings"]:
        print(
            f"  {entry['rank']:<6} {entry['paper_id']:<8} "
            f"{entry['snorm_avg']:<12.2f} {entry['citation']}"
        )


if __name__ == "__main__":
    main()
