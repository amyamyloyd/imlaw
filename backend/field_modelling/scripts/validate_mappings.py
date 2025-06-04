#!/usr/bin/env python3

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def validate_collection_field_structure(collection_fields: Dict) -> List[Dict]:
    """Validate that collection fields follow the persona_fieldtype structure"""
    structural_issues = []
    
    for collection_key, data in collection_fields.items():
        # Check key format
        parts = collection_key.split('_')
        if len(parts) < 2:  # Must have at least persona_fieldtype
            structural_issues.append({
                'collection_field': collection_key,
                'issue': 'Invalid key format - must be persona_fieldtype[_repeating_category]',
                'details': f"Found {len(parts)} parts, expected at least 2"
            })
            continue
            
        # Verify parts match the data
        persona = parts[0]
        field_type = parts[1]
        
        if data.get('persona') != persona:
            structural_issues.append({
                'collection_field': collection_key,
                'issue': 'Persona mismatch',
                'details': f"Key persona '{persona}' doesn't match data persona '{data.get('persona')}'"
            })
            
        if data.get('field_type') != field_type:
            structural_issues.append({
                'collection_field': collection_key,
                'issue': 'Field type mismatch',
                'details': f"Key field_type '{field_type}' doesn't match data field_type '{data.get('field_type')}'"
            })
    
    return structural_issues

def analyze_form_field_usage(collection_fields: Dict) -> Tuple[Dict, Dict]:
    """Analyze how form fields are being mapped to collection fields"""
    # Track form field usage
    form_field_usage = defaultdict(list)  # {form_id/field_id: [(collection_field, persona)]}
    
    # Track collection patterns
    collection_patterns = defaultdict(lambda: {'personas': set(), 'forms': set()})
    
    for collection_key, data in collection_fields.items():
        persona = data['persona']
        field_type = data['field_type']
        
        for mapping in data['mappings']:
            form_key = f"{mapping['form_id']}/{mapping['field_id']}"
            
            # Track this usage
            form_field_usage[form_key].append({
                'collection_field': collection_key,
                'persona': persona,
                'field_type': field_type
            })
            
            # Track patterns
            collection_patterns[field_type]['personas'].add(persona)
            collection_patterns[field_type]['forms'].add(mapping['form_id'])
    
    return dict(form_field_usage), dict(collection_patterns)

def validate_mappings(collection_fields_file: Path):
    """Validate collection fields and their form field mappings"""
    with open(collection_fields_file) as f:
        collection_fields = json.load(f)
    
    # Validate basic structure
    structural_issues = validate_collection_field_structure(collection_fields)
    
    # Analyze usage patterns
    form_field_usage, collection_patterns = analyze_form_field_usage(collection_fields)
    
    # Find problematic mappings
    duplicate_mappings = {
        form_key: usages 
        for form_key, usages in form_field_usage.items() 
        if len(usages) > 1
    }
    
    # Print report
    print("\nCollection Fields Validation Report")
    print("=" * 50)
    
    if structural_issues:
        print("\n⚠️  Structural Issues Found:")
        for issue in structural_issues:
            print(f"\nCollection Field: {issue['collection_field']}")
            print(f"Issue: {issue['issue']}")
            print(f"Details: {issue['details']}")
    else:
        print("\n✅ All collection fields follow the correct persona_fieldtype structure")
    
    if duplicate_mappings:
        print("\n⚠️  Form Fields Mapped Multiple Times:")
        for form_key, usages in duplicate_mappings.items():
            print(f"\nForm Field: {form_key}")
            print("Mapped to:")
            for usage in usages:
                print(f"  - {usage['collection_field']} (Persona: {usage['persona']}, Type: {usage['field_type']})")
    else:
        print("\n✅ No duplicate form field mappings found")
    
    # Report on field type patterns
    print("\nField Type Usage Patterns:")
    print("=" * 50)
    for field_type, data in sorted(collection_patterns.items()):
        print(f"\nField Type: {field_type}")
        print(f"Used for {len(data['personas'])} personas: {', '.join(sorted(data['personas']))}")
        print(f"Appears in {len(data['forms'])} forms: {', '.join(sorted(data['forms']))}")
    
    # Print statistics
    print("\nCollection Field Statistics:")
    print("=" * 50)
    personas = {data['persona'] for data in collection_fields.values()}
    field_types = {data['field_type'] for data in collection_fields.values()}
    print(f"Total collection fields: {len(collection_fields)}")
    print(f"Unique personas: {len(personas)}")
    print(f"Unique field types: {len(field_types)}")
    
    # Return whether validation passed
    validation_passed = len(structural_issues) == 0 and len(duplicate_mappings) == 0
    
    if validation_passed:
        print("\n✅ All validations passed")
    else:
        print("\n❌ Some validations failed")
        if structural_issues:
            print("- Found structural issues in collection fields")
        if duplicate_mappings:
            print("- Found duplicate form field mappings")
    
    return validation_passed

def main():
    # Find most recent results directory
    model_results_dir = Path("../")
    latest_dir = max(model_results_dir.glob("model_results_*"))
    collection_fields_file = latest_dir / "collection_fields.json"
    
    print(f"Validating mappings in {collection_fields_file}")
    is_valid = validate_mappings(collection_fields_file)
    
    if not is_valid:
        print("\nPlease review and fix the issues above")
        exit(1)

if __name__ == "__main__":
    main() 