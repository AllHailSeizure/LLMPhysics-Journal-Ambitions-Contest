import json
import os
import time
from pipeline_functions import prepare_document, score_paper

PAPERS_DIR = "papers"
OUTPUT_DIR = "output"


def main():
    # Find all failed records
    failures = []
    for fname in sorted(os.listdir(OUTPUT_DIR)):
        if not fname.endswith(".json"):
            continue
        if not ("_baseline" in fname or "_contest" in fname or "noisefloor" in fname):
            continue
        filepath = os.path.join(OUTPUT_DIR, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            records = json.load(f)
        for i, record in enumerate(records):
            if record.get("error"):
                failures.append((fname, i, record["paper_id"], record["model"]))

    print(f"Found {len(failures)} failed records to re-run.\n")

    for fname, index, paper_id, model in failures:
        # Find the paper file
        filepath = None
        for pname in os.listdir(PAPERS_DIR):
            if pname.startswith(paper_id):
                filepath = os.path.join(PAPERS_DIR, pname)
                break

        if filepath is None:
            print(f"WARNING: No file found for paper {paper_id}, skipping.")
            continue

        print(f"Re-scoring {paper_id} | {model}")
        prepared = prepare_document(filepath)
        new_record = score_paper(prepared, filepath, model, paper_id)

        # Overwrite the failed record in place
        output_file = os.path.join(OUTPUT_DIR, fname)
        with open(output_file, "r", encoding="utf-8") as f:
            records = json.load(f)

        records[index] = new_record

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

        if new_record["error"]:
            print(f"  Still failing: {new_record['error'][:80]}")
        else:
            print(f"  Success.")

        time.sleep(30)  # Respect Claude's 30K TPM rate limit

    print("\nDone.")


if __name__ == "__main__":
    main()
