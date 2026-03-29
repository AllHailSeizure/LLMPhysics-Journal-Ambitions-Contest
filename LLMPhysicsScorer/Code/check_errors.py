import json
import os

OUTPUT_DIR = "output"

total = 0
errors = 0
missing = 0

for fname in sorted(os.listdir(OUTPUT_DIR)):
    if not fname.endswith(".json"):
        continue
    filepath = os.path.join(OUTPUT_DIR, fname)
    with open(filepath, "r", encoding="utf-8") as f:
        records = json.load(f)
    for record in records:
        total += 1
        if record.get("error"):
            errors += 1
            print(f"ERROR: {fname} | {record['model']} | {record['error'][:80]}")

print(f"\n{total} records checked. {errors} errors found.")
