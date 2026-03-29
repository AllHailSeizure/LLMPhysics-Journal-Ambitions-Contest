import json
import os
import time
from pipeline_functions import prepare_document, score_paper

# Fixed noise floor paper set (randomly selected 2026-03-07)
NOISE_FLOOR_PAPERS = ["043", "041", "044", "029", "015", "018", "039", "010", "011", "020"]

MODELS = [
    "claude-sonnet-4-6",
    "gpt-5.2",
]

PAPERS_DIR = "papers"
RUNS_PER_PAPER = 5
OUTPUT_FILE = "noisefloor.json"


def main():
    records = []
    total = len(NOISE_FLOOR_PAPERS) * RUNS_PER_PAPER * len(MODELS)
    completed = 0

    for paper_id in NOISE_FLOOR_PAPERS:
        # Find the file for this paper_id
        filepath = None
        for fname in os.listdir(PAPERS_DIR):
            if fname.startswith(paper_id):
                filepath = os.path.join(PAPERS_DIR, fname)
                break

        if filepath is None:
            print(f"WARNING: No file found for paper {paper_id}, skipping.")
            continue

        prepared = prepare_document(filepath)

        for model in MODELS:
            for run in range(RUNS_PER_PAPER):
                print(f"Scoring {paper_id} | {model} | run {run + 1}/{RUNS_PER_PAPER} ({completed + 1}/{total})")
                record = score_paper(prepared, filepath, model, paper_id)
                record["run"] = run + 1
                records.append(record)
                completed += 1
                time.sleep(60)  # Respect Claude's 30K TPM rate limit

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"\nDone. {completed} records written to {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
