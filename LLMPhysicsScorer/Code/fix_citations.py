import json
import os

OUTPUT_DIR = "output"
CITATIONS_FILE = "citations.txt"

# Load all citations
citations = {}
with open(CITATIONS_FILE, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split("--")
        if len(parts) == 2:
            paper_id = parts[0].strip()
            citation = parts[1].strip()
            citations[paper_id] = citation

fixed = 0
skipped = 0

for fname in sorted(os.listdir(OUTPUT_DIR)):
    if not fname.endswith(".json"):
        continue
    if not ("_baseline" in fname or "_contest" in fname or "noisefloor" in fname):
        continue

    filepath = os.path.join(OUTPUT_DIR, fname)
    with open(filepath, "r", encoding="utf-8") as f:
        records = json.load(f)

    changed = False
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("citation") is None:
            paper_id = record.get("paper_id")
            if paper_id and paper_id in citations:
                print(f"Fixing {fname} | {paper_id} | {record.get('model')} -> {citations[paper_id]}")
                record["citation"] = citations[paper_id]
                changed = True
                fixed += 1
            else:
                print(f"WARNING: No citation found for {paper_id} in {fname}")
                skipped += 1

    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)

print(f"\nDone. {fixed} citations fixed, {skipped} skipped.")
