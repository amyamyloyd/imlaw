import os
import json
from collections import defaultdict

INPUT_FILE = "model_analysis/collection_mapping_llm.json"
OUTPUT_DIR = "model_analysis/llm_batches"

os.makedirs(OUTPUT_DIR, exist_ok=True)

with open(INPUT_FILE, "r") as f:
    data = json.load(f)

batches = defaultdict(list)
for rec in data:
    persona = rec.get("persona")
    if persona:
        batches[persona].append(rec)

for persona, records in batches.items():
    out_file = os.path.join(OUTPUT_DIR, f"{persona}_llm.json")
    with open(out_file, "w") as f:
        json.dump(records, f, indent=2)
    print(f"Wrote {len(records)} records to {out_file}")

print(f"Personas found: {list(batches.keys())}") 