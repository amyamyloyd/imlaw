"""
Script to create a sorted table of fields with their tooltips.
"""

import json
import os
from tabulate import tabulate

def create_tooltip_table():
    analysis_file = "/Users/claudiapitts/imlaw/Imlaw/generalscripts/field_analysis/complete_analysis.json"
    
    with open(analysis_file) as f:
        all_forms_data = json.load(f)
    
    # Create list to hold all rows
    table_data = []
    
    # Collect data for each field
    for form_name, form_data in all_forms_data.items():
        for field in form_data['fields']:
            if field.get('tooltip'):  # Only include fields with tooltips
                # Clean up tooltip text - remove extra whitespace and newlines
                tooltip = ' '.join(field.get('tooltip', '').split())
                # Truncate tooltip if too long
                if len(tooltip) > 80:
                    tooltip = tooltip[:77] + '...'
                table_data.append([
                    form_name,
                    tooltip,
                    field.get('name', '')
                ])
    
    # Sort by form name, then tooltip, then field name
    table_data.sort(key=lambda x: (x[0], x[1], x[2]))
    
    # Create and save the table
    headers = ['Form', 'Tooltip', 'Field Name']
    table = tabulate(table_data, headers=headers, tablefmt='simple', maxcolwidths=[20, 80, 40])
    
    # Save to file
    output_file = "/Users/claudiapitts/imlaw/Imlaw/generalscripts/field_analysis/field_tooltips.txt"
    with open(output_file, 'w') as f:
        f.write(table)
    
    print(f"\nTable has been saved to: {output_file}")
    print(f"Total fields with tooltips: {len(table_data)}")

if __name__ == '__main__':
    create_tooltip_table() 