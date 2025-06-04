#!/usr/bin/env python3

import json
import csv
from pathlib import Path
from typing import Dict, List

def format_field_name(field_type: str, persona: str) -> str:
    """Format the collection field name"""
    return f"{field_type}_{persona}"

def format_mapping(form_id: str, field_id: str) -> str:
    """Format the form mapping identifier"""
    return f"{form_id}/{field_id}"

def convert_to_table(input_file: str, output_file: str):
    # Load the collection fields
    with open(input_file, 'r') as f:
        collection_fields = json.load(f)
    
    # Prepare the CSV data
    csv_data = []
    headers = ['collection_field_name', 'form_mapping', 'domain', 'persona', 'biographical_subcategory', 'reuse_category']
    
    # Convert each collection field to rows
    for field_key, field_data in collection_fields.items():
        field_type = field_data['field_type']
        persona = field_data['persona']
        collection_field_name = format_field_name(field_type, persona)
        
        # Create a row for each mapping
        for mapping in field_data['mappings']:
            form_mapping = format_mapping(mapping['form_id'], mapping['field_id'])
            
            row = {
                'collection_field_name': collection_field_name,
                'form_mapping': form_mapping,
                'domain': mapping.get('domains', [''])[0] if mapping.get('domains') else '',
                'persona': mapping.get('personas', [''])[0] if mapping.get('personas') else '',
                'biographical_subcategory': mapping.get('biographical_subcategories', [''])[0] if mapping.get('biographical_subcategories') else '',
                'reuse_category': mapping.get('reuse_category', '')
            }
            csv_data.append(row)
    
    # Sort by collection field name and form mapping
    csv_data.sort(key=lambda x: (x['collection_field_name'], x['form_mapping']))
    
    # Write to CSV
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(csv_data)

def main():
    # Find the most recent results directory
    model_results_dir = Path("../")
    results_dirs = list(model_results_dir.glob("model_results_*"))
    if not results_dirs:
        print("No model results directories found!")
        return
    
    latest_dir = max(results_dirs)
    input_file = latest_dir / "collection_fields.json"
    output_file = latest_dir / "collection_fields_table.csv"
    
    print(f"Converting {input_file} to table format...")
    convert_to_table(input_file, output_file)
    print(f"Table saved to {output_file}")

if __name__ == "__main__":
    main() 