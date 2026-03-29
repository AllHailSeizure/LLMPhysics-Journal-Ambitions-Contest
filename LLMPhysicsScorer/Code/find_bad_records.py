import json
import os

OUTPUT_DIR = "output"

for fname in sorted(os.listdir(OUTPUT_DIR)):
    if not fname.endswith(".json"):
        continue
    filepath = os.path.join(OUTPUT_DIR, fname)
    with open(filepath, "r", encoding="utf-8") as f:
        records = json.load(f)
    for i, record in enumerate(records):
        if not isinstance(record, dict):
            print(f"{fname} index {i}: {type(record)} -> {repr(record)[:150]}")

print("Done.")
