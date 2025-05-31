import os
import json
from jira import JIRA
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to Jira
jira = JIRA(
    server=os.getenv('JIRA_URL'),
    basic_auth=(os.getenv('JIRA_USERNAME'), os.getenv('JIRA_API_TOKEN'))
)

# Load i485 field map
with open('i485_fill_map.json', 'r') as f:
    field_map = json.load(f)

# Extract all field_id -> (field_name, pdf info)
field_lookup = []
for item in field_map:
    for field in item['jira_source_fields']:
        field_lookup.append({
            'field_id': field['id'],
            'field_name': field['name'],
            'pdf_internal_id': item['pdf_internal_id'],
            'source_i485_label': item['source_i485_label'],
            'source_i485_field_original': item['source_i485_field_original']
        })

# Jira issues to fetch
issue_keys = ['CF-16', 'CF-3']
results = {}

for issue_key in issue_keys:
    issue = jira.issue(issue_key)
    populated_fields = []
    for entry in field_lookup:
        value = getattr(issue.fields, entry['field_id'], None)
        if value not in [None, '', [], {}]:
            populated_fields.append({
                'pdf_internal_id': entry['pdf_internal_id'],
                'source_i485_label': entry['source_i485_label'],
                'source_i485_field_original': entry['source_i485_field_original'],
                'jira_field_id': entry['field_id'],
                'jira_field_name': entry['field_name'],
                'value': str(value)
            })
    results[issue_key] = populated_fields

# Save to JSON
with open('i485_filled_output.json', 'w') as f:
    json.dump(results, f, indent=2)

print("✅ Output saved to i485_filled_output.json")
