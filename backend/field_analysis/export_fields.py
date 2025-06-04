import json
import csv
from pathlib import Path
from typing import List, Dict
import re

def normalize_field_type(field_type: str) -> str:
    """Normalize the field type from various formats."""
    field_type = field_type.lower() if field_type else ''
    
    # Common field types
    if field_type == 'tx':
        return 'text'
    elif field_type == 'btn':
        return 'button'
    elif field_type == 'ch':
        return 'checkbox'
    elif any(x in field_type for x in ['date', 'month', 'year', 'day']):
        return 'date'
    elif field_type.endswith('number'):
        return 'number'
    elif 'yn' in field_type or 'yesno' in field_type:
        return 'checkbox'
    else:
        return 'text'

def extract_form_id(form_text: str) -> str:
    """Extract form ID from the Form column, PDF filename, or field name.
    
    Examples:
    - From PDF name: "i-485.pdf" -> "i485"
    - From field name: "i485_Part1_Line5" -> "i485"
    - From form text: "Form I-485" -> "i485"
    """
    if not form_text:
        return 'unknown'
    
    # Try to extract from PDF filename first
    pdf_match = re.search(r'[iI]-?(\d+)\.pdf', form_text)
    if pdf_match:
        return f"i{pdf_match.group(1)}"
    
    # Try to extract from field name pattern
    field_match = re.search(r'^[iI][-]?(\d+)(?:_|$)', form_text)
    if field_match:
        return f"i{field_match.group(1)}"
    
    # Try to extract from form text (e.g., "Form I-485")
    form_match = re.search(r'[fF]orm\s+[iI]-?(\d+)', form_text)
    if form_match:
        return f"i{form_match.group(1)}"
    
    # If it's already in the correct format (i485, i693, etc.)
    clean_match = re.search(r'^[iI](\d+)$', form_text.strip())
    if clean_match:
        return f"i{clean_match.group(1)}"
    
    return form_text.lower().strip()

def convert_fields_to_json(input_csv: Path) -> List[Dict]:
    """Convert fields from CSV to JSON format with form IDs and tooltips."""
    fields = []
    
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip header row if field_type is 'Type'
            if row.get('Type', '') == 'Type':
                continue
            
            # Try to get form ID from Form column first
            form_id = extract_form_id(row.get('Form', ''))
            
            # If form_id is unknown, try to extract from field name
            if form_id == 'unknown':
                field_name = row.get('Field Name', '')
                form_id = extract_form_id(field_name)
            
            # Get other values
            field_type = row.get('Type', '')
            tooltip = row.get('Tooltip', '')
                
            # Normalize the field type
            normalized_type = normalize_field_type(field_type)
            
            field = {
                'form_id': form_id,
                'name': row.get('Field Name', ''),
                'type': normalized_type,
                'tooltip': tooltip,
                'base_type': field_type,
                'page': row.get('Page', ''),
                'field_rule': row.get('FieldRule', ''),
                'keywords': row.get('KeyWords', '')
            }
            
            fields.append(field)
    
    return fields

def main():
    """Main function to export fields."""
    base_dir = Path(__file__).parent
    input_file = base_dir / "fieldswrules.csv"
    output_file = base_dir / "extracted_fields.json"
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} not found")
        return
    
    fields = convert_fields_to_json(input_file)
    
    # Print type distribution before saving
    type_counts = {}
    form_counts = {}
    for field in fields:
        field_type = field['type']
        form_id = field['form_id']
        type_counts[field_type] = type_counts.get(field_type, 0) + 1
        form_counts[form_id] = form_counts.get(form_id, 0) + 1
    
    print("\nField Type Distribution:")
    for field_type, count in sorted(type_counts.items()):
        print(f"{field_type}: {count} fields")
        
    print("\nForm Distribution:")
    for form_id, count in sorted(form_counts.items()):
        print(f"{form_id}: {count} fields")
    
    with open(output_file, 'w') as f:
        json.dump(fields, f, indent=2)
    
    print(f"\nExported {len(fields)} fields to {output_file}")

if __name__ == '__main__':
    main() 