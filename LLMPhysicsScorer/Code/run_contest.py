import json
import os
import time
from pipeline_functions import prepare_document, score_paper

MODELS = [
    "claude-sonnet-4-6",
    "gpt-5.2",
]

PAPERS_DIR = "papers"
OUTPUT_DIR = "output"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Build list of contest papers (101+)
    papers = []
    for fname in sorted(os.listdir(PAPERS_DIR)):
        paper_id = fname.split(".")[0]
        try:
            if int(paper_id) >= 101:
                papers.append((paper_id, os.path.join(PAPERS_DIR, fname)))
        except ValueError:
            continue

    if not papers:
        print("No contest papers found in papers/ folder.")
        return

    total = len(papers) * len(MODELS)
    completed = 0

    for paper_id, filepath in papers:
        prepared = prepare_document(filepath)

        for model in MODELS:
            print(f"Scoring {paper_id} | {model} ({completed + 1}/{total})")
            record = score_paper(prepared, filepath, model, paper_id)

            output_file = os.path.join(OUTPUT_DIR, f"{paper_id}_contest.json")
            if os.path.exists(output_file):
                with open(output_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            else:
                existing = []

            existing.append(record)

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)

            completed += 1

        time.sleep(5)  # Respect Claude's 30K TPM rate limit

    print(f"\nDone. {completed} records written to {OUTPUT_DIR}/.")


if __name__ == "__main__":
    main()
