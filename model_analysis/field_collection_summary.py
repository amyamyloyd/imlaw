import json
import pandas as pd
from collections import Counter

# Set the input file here
INPUT_FILE = "model_analysis/results/run_20250603_143812/enriched_analysis_20250603_205126_fixed_value_info.json"
OUTPUT_XLSX = INPUT_FILE.replace('.json', '.xlsx')

# Read the enriched JSON
with open(INPUT_FILE, 'r') as f:
    fields = json.load(f)

# Prepare data for unique (persona, domain, value) combinations
combos = []
rows = []
for field in fields:
    persona = field.get('llm_persona') or field.get('persona')
    domain = field.get('llm_domain') or field.get('domain')
    value = None
    if isinstance(field.get('value_info'), dict):
        value = field['value_info'].get('value')
    name = field.get('name')
    tooltip = field.get('tooltip')
    form = field.get('form')
    combos.append((persona, domain, value))
    rows.append({
        'persona': persona,
        'domain': domain,
        'value': value,
        'name': name,
        'tooltip': tooltip,
        'form': form
    })

# Count unique combinations
combo_counter = Counter(combos)
unique_combos = list(combo_counter.keys())
print(f"Total unique (persona, domain, value) combinations: {len(unique_combos)}\n")
for combo, count in combo_counter.most_common():
    print(f"{combo}: {count}")

# Write Excel file
print(f"Writing Excel file to {OUTPUT_XLSX} ...")
df = pd.DataFrame([
    {
        'persona': row['persona'],
        'domain': row['domain'],
        'value': row['value'],
        'tooltip': row['tooltip'],
        'form': row['form'],
        'screen_label': fields[i].get('screen_label'),
        'name': row['name']
    }
    for i, row in enumerate(rows)
])
df = df.sort_values(by=['persona', 'domain', 'value'], na_position='last')
df.to_excel(OUTPUT_XLSX, index=False)
print("Done.") 