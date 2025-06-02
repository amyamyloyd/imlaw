"""
Script to find family-related fields in the pattern analysis.
"""

import json
import os

def find_family_fields():
    analysis_file = "/Users/claudiapitts/imlaw/Imlaw/generalscripts/field_analysis/pattern_analysis.json"
    
    with open(analysis_file) as f:
        data = json.load(f)
    
    print("Fields Related to Family Members:\n")
    
    for form_name, form_data in data.items():
        print(f"\n{form_name}:")
        
        for pattern_type, groups in form_data['patterns'].items():
            for group in groups:
                # Find groups with family-related fields
                family_fields = [
                    field for field in group['fields']
                    if field['context']['subject'] in ['spouse', 'child', 'parent', 'sibling']
                ]
                
                if family_fields:
                    print(f"\nGroup Type: {pattern_type}")
                    print("Fields:")
                    for field in family_fields:
                        print(f"  - {field['name']}")
                        print(f"    Subject: {field['context']['subject']}")
                        print(f"    Temporal: {field['context']['temporal']}")
                        print(f"    Info Type: {field['context']['info_type']}")
                        print(f"    Is Repeated: {field['context']['is_repeated']}")
                        print()

if __name__ == '__main__':
    find_family_fields() 