import json
import os
import time
from pipeline_functions import prepare_document, score_paper

PAPERS_DIR = "papers"
NOISEFLOOR_FILE = "./output/noisefloor.json"


def main():
    with open(NOISEFLOOR_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    # Find all failed records by index
    failures = []
    for i, record in enumerate(records):
        if record.get("error"):
            failures.append((i, record["paper_id"], record["model"], record.get("run")))

    print(f"Found {len(failures)} failed noise floor records to re-run.\n")

    for index, paper_id, model, run in failures:
        # Find the paper file
        filepath = None
        for pname in os.listdir(PAPERS_DIR):
            if pname.startswith(paper_id):
                filepath = os.path.join(PAPERS_DIR, pname)
                break

        if filepath is None:
            print(f"WARNING: No file found for paper {paper_id}, skipping.")
            continue

        print(f"Re-scoring {paper_id} | {model} | run {run}")
        prepared = prepare_document(filepath)
        new_record = score_paper(prepared, filepath, model, paper_id)

        # Preserve the original run number and group
        new_record["run"] = run
        new_record["group"] = records[index]["group"]

        # Overwrite the failed record in place
        records[index] = new_record

        with open(NOISEFLOOR_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

        if new_record["error"]:
            print(f"  Still failing: {new_record['error'][:80]}")
        else:
            print(f"  Success.")

        time.sleep(30)  # Respect Claude's 30K TPM rate limit

    print("\nDone.")


if __name__ == "__main__":
    main()
