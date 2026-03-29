import json
import os

CONTEST_DIR = "./output"
OUTPUT_FILE = "./contest_justifications.json"
MODELS = ["claude-sonnet-4-6", "gpt-5.2"]
CATEGORIES = ["hypothesis", "novelty", "scientific_humility", "engagement", "rigor", "citations"]

results = []

for i in range(101, 111):
    paper_id = str(i)
    filename = os.path.join(CONTEST_DIR, f"{paper_id}_contest.json")

    if not os.path.exists(filename):
        print(f"WARNING: {filename} not found, skipping.")
        continue

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    entry = {
        "paper_id": paper_id,
        "citation": data[0].get("citation", ""),
        "scores": {}
    }

    for record in data:
        model = record.get("model")
        if model not in MODELS:
            print(f"WARNING: Unexpected model '{model}' in {filename}, skipping.")
            continue

        scores = record.get("scores", {})
        entry["scores"][model] = {}

        for cat in CATEGORIES:
            if cat in scores:
                entry["scores"][model][cat] = {
                    "score": scores[cat].get("score"),
                    "justification": scores[cat].get("justification")
                }
            else:
                print(f"WARNING: Category '{cat}' missing for {model} in {filename}.")
                entry["scores"][model][cat] = {
                    "score": None,
                    "justification": None
                }

    results.append(entry)

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nDone. {len(results)} papers extracted to {OUTPUT_FILE}")
