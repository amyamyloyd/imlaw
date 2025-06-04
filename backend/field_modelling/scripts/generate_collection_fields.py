#!/usr/bin/env python3

import json
import os
import csv
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import re
from pathlib import Path

class CollectionFieldGenerator:
    def __init__(self):
        self.collection_fields = {}
        self.form_field_mappings = {}
        
    def analyze_field_patterns(self, fields_data: List[Dict]) -> Dict:
        """Group fields by persona+field_type as these represent unique data points"""
        field_patterns = defaultdict(list)
        
        for field in fields_data:
            # Extract key identifiers
            field_type = field.get('field_type', '')
            form_id = field.get('form_id', '')
            field_id = field.get('field_name', '')
            is_repeating = field.get('is_repeating', False)
            repeating_category = field.get('repeating_category', '')
            
            # Extract classification and context data
            personas = field.get('personas', [])
            domains = field.get('domains', [])
            biographical_subcategories = field.get('biographical_subcategories', [])
            reuse_category = field.get('reuse_category', '')
            
            # Process each persona this field applies to
            if not personas:
                # Default to applicant if no persona specified
                personas = ["('applicant', 1.0)"]
            
            for persona in personas:
                # Extract persona value from tuple string format "('persona', score)"
                persona_match = re.match(r"\('([^']+)',", persona)
                if not persona_match:
                    continue
                persona_value = persona_match.group(1)
                
                # Create unique collection field key combining persona and field type
                collection_key = f"{persona_value}_{field_type}"
                if is_repeating:
                    collection_key += f"_{repeating_category}"
                
                # Store mapping info
                mapping_info = {
                    'form_id': form_id,
                    'field_id': field_id,
                    'is_repeating': is_repeating,
                    'repeating_category': repeating_category,
                    'domains': domains,
                    'biographical_subcategories': biographical_subcategories,
                    'reuse_category': reuse_category
                }
                
                field_patterns[collection_key].append(mapping_info)
            
        return field_patterns
    
    def generate_collection_fields(self, fields_data: List[Dict]) -> Dict:
        """Generate collection fields where each field represents a unique persona+field combination"""
        print("Analyzing field patterns...")
        field_patterns = self.analyze_field_patterns(fields_data)
        
        collection_fields = {}
        
        print("Generating collection fields and mappings...")
        for collection_key, mappings in field_patterns.items():
            # Parse the collection key
            parts = collection_key.split('_')
            persona = parts[0]
            field_type = parts[1]
            repeating_info = parts[2:] if len(parts) > 2 else []
            
            # Create collection field
            collection_field = {
                'persona': persona,  # Now part of the core identity
                'field_type': field_type,
                'is_repeating': len(repeating_info) > 0,
                'repeating_category': repeating_info[0] if repeating_info else None,
                'mappings': mappings
            }
            
            collection_fields[collection_key] = collection_field
        
        return collection_fields
    
    def generate_mapping_table(self, collection_fields: Dict, output_file: Path):
        """Generate CSV table showing how form fields map to our persona-specific collection fields"""
        rows = []
        headers = ['collection_field', 'persona', 'field_type', 'form_mapping', 'domains', 'biographical_category', 'reuse_category']
        
        for collection_key, field_data in collection_fields.items():
            persona = field_data['persona']
            field_type = field_data['field_type']
            
            # Create a row for each form field that maps to this collection field
            for mapping in field_data['mappings']:
                form_mapping = f"{mapping['form_id']}/{mapping['field_id']}"
                
                # Format the contextual data
                domains = '; '.join([d.strip("()' ").split(',')[0] for d in mapping.get('domains', [])])
                bio_cat = '; '.join([b.strip("()' ").split(',')[0] for b in mapping.get('biographical_subcategories', [])])
                reuse_cat = mapping.get('reuse_category', '')
                
                row = {
                    'collection_field': collection_key,
                    'persona': persona,
                    'field_type': field_type,
                    'form_mapping': form_mapping,
                    'domains': domains,
                    'biographical_category': bio_cat,
                    'reuse_category': reuse_cat
                }
                rows.append(row)
        
        # Sort by collection field name
        rows.sort(key=lambda x: x['collection_field'])
        
        # Write to CSV
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
    
    def save_results(self, collection_fields: Dict, output_dir: Path):
        """Save collection fields and mappings"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(output_dir) / f"model_results_{timestamp}"
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Save collection fields JSON
        with open(output_dir / "collection_fields.json", 'w') as f:
            json.dump(collection_fields, f, indent=2)
            
        # Generate and save summary
        summary = self.generate_summary(collection_fields)
        with open(output_dir / "summary.txt", 'w') as f:
            f.write(summary)
            
        # Generate and save mapping table
        self.generate_mapping_table(collection_fields, output_dir / "collection_field_mappings.csv")
            
    def generate_summary(self, collection_fields: Dict) -> str:
        """Generate human-readable summary of our persona-specific collection fields"""
        summary = []
        summary.append("Collection Fields Summary")
        summary.append("=" * 50)
        
        # Group by persona for better organization
        persona_fields = defaultdict(list)
        for key, field in collection_fields.items():
            persona_fields[field['persona']].append((key, field))
        
        # Output organized by persona
        for persona in sorted(persona_fields.keys()):
            summary.append(f"\nPersona: {persona}")
            summary.append("=" * 20)
            
            for collection_key, field in sorted(persona_fields[persona]):
                summary.append(f"\nCollection Field: {collection_key}")
                if field['is_repeating']:
                    summary.append(f"Repeating Category: {field['repeating_category']}")
                summary.append("\nMaps to Form Fields:")
                for mapping in field['mappings']:
                    summary.append(f"- {mapping['form_id']}: {mapping['field_id']}")
                    if mapping.get('domains'):
                        summary.append(f"  Domains: {', '.join(d.strip('()').split(',')[0] for d in mapping['domains'])}")
                    if mapping.get('biographical_subcategories'):
                        summary.append(f"  Categories: {', '.join(b.strip('()').split(',')[0] for b in mapping['biographical_subcategories'])}")
                    if mapping.get('reuse_category'):
                        summary.append(f"  Reuse: {mapping['reuse_category']}")
                summary.append("-" * 30)
        
        return "\n".join(summary)

def main():
    generator = CollectionFieldGenerator()
    
    # Find latest analysis results
    analysis_dir = Path("../../field_analysis")
    latest_results = max(analysis_dir.glob("analysis_results_*/field_analysis_results_*.json"))
    
    print(f"Loading analysis results from {latest_results}")
    with open(latest_results) as f:
        fields_data = json.load(f)
    
    collection_fields = generator.generate_collection_fields(fields_data)
    generator.save_results(collection_fields, Path("../"))
    print("Collection fields and mappings generated successfully")

if __name__ == "__main__":
    main() 