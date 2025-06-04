import json
import re

INPUT_FILE = "model_analysis/results/run_20250603_143812/enriched_analysis_20250603_205126.json"
OUTPUT_FILE = INPUT_FILE.replace('.json', '_fixed_value_info.json')

with open(INPUT_FILE, 'r') as f:
    fields = json.load(f)

updated_count = 0
for field in fields:
    if field.get('value_info') is None:
        name = field.get('name', '')
        # Match the value after the last underscore and before the bracket
        match = re.search(r'_([^_\[]+)\[\d+\]$', name)
        if match:
            value = match.group(1)
            field['value_info'] = {"type": "selection", "value": value}
            updated_count += 1

print(f"Updated value_info for {updated_count} records.")
with open(OUTPUT_FILE, 'w') as f:
    json.dump(fields, f, indent=2)
print(f"Wrote updated file to: {OUTPUT_FILE}") 