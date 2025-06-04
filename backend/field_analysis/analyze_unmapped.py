import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List
import re
from tabulate import tabulate

def load_latest_mappings() -> Dict:
    """Load the most recent generated mappings file."""
    base_dir = Path(__file__).parent
    mapping_files = sorted(
        [f for f in base_dir.glob("generated_mappings_*.json")],
        key=lambda x: x.name,
        reverse=True
    )
    if not mapping_files:
        raise FileNotFoundError("No mapping files found!")
    
    with open(mapping_files[0], 'r') as f:
        return json.load(f)

def analyze_field_patterns(field_name: str) -> Dict:
    """Analyze patterns in field names."""
    patterns = {
        'has_part': bool(re.search(r'P(?:art)?(\d+)', field_name)),
        'has_line': bool(re.search(r'Line(\d+)', field_name)),
        'has_checkbox': field_name.startswith('Checkbox'),
        'has_barcode': 'BarCode' in field_name,
        'base_type': field_name.split('[')[0].split('_')[-1] if '_' in field_name else field_name.split('[')[0]
    }
    return patterns

def group_by_pattern(unmapped_fields: List[Dict]) -> Dict:
    """Group unmapped fields by common patterns."""
    pattern_groups = defaultdict(list)
    base_type_groups = defaultdict(list)
    
    for field in unmapped_fields:
        field_name = field['field_name']
        patterns = analyze_field_patterns(field_name)
        
        # Create pattern key
        pattern_key = f"{'Part+' if patterns['has_part'] else ''}" \
                     f"{'Line+' if patterns['has_line'] else ''}" \
                     f"{'Checkbox+' if patterns['has_checkbox'] else ''}" \
                     f"{'Barcode+' if patterns['has_barcode'] else ''}"
        
        if not pattern_key:
            pattern_key = "No common pattern"
        
        pattern_groups[pattern_key].append(field)
        base_type_groups[patterns['base_type']].append(field)
    
    return {
        'by_pattern': pattern_groups,
        'by_base_type': base_type_groups
    }

def analyze_unmapped_fields(mappings: Dict) -> None:
    """Analyze and display information about unmapped fields."""
    # Get unmapped fields
    unmapped = [
        {
            'field_name': field_name,
            **field_data,
            'base_type': analyze_field_patterns(field_name)['base_type']
        }
        for field_name, field_data in mappings['field_mappings'].items()
        if not field_data['collection_field']
    ]
    
    # Group fields
    groups = group_by_pattern(unmapped)
    
    # Print pattern summary
    print("\n=== Unmapped Fields Pattern Summary ===")
    pattern_summary = [
        [pattern, len(fields), f"{len(fields)/len(unmapped)*100:.1f}%"]
        for pattern, fields in groups['by_pattern'].items()
    ]
    print(tabulate(
        pattern_summary,
        headers=['Pattern', 'Count', '% of Unmapped'],
        tablefmt='grid'
    ))
    
    # Print base type summary
    print("\n=== Unmapped Fields Base Type Summary ===")
    base_type_summary = [
        [base_type, len(fields), f"{len(fields)/len(unmapped)*100:.1f}%"]
        for base_type, fields in groups['by_base_type'].items()
    ]
    base_type_summary.sort(key=lambda x: x[1], reverse=True)
    print(tabulate(
        base_type_summary[:20],  # Show top 20 base types
        headers=['Base Type', 'Count', '% of Unmapped'],
        tablefmt='grid'
    ))
    
    # Print sample fields for top patterns
    print("\n=== Sample Unmapped Fields by Pattern ===")
    for pattern, fields in groups['by_pattern'].items():
        print(f"\nPattern: {pattern}")
        sample = fields[:5]  # Show 5 examples per pattern
        sample_data = [
            [f.get('field_name'), f.get('base_type'), f.get('persona', 'unknown')]
            for f in sample
        ]
        print(tabulate(
            sample_data,
            headers=['Field Name', 'Base Type', 'Persona'],
            tablefmt='grid'
        ))

def main():
    """Main execution function."""
    try:
        mappings = load_latest_mappings()
        analyze_unmapped_fields(mappings)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 