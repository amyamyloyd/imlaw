#!/usr/bin/env python3

"""
Generate CORRECT collection field mappings by grouping persona + value from field names.
"""

import os
import json
import logging
import re
from datetime import datetime
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class CorrectCollectionFieldMapper:
    def __init__(self):
        self.collection_mappings = {}
        
    def extract_value_from_field_name(self, field_name: str) -> str:
        """Extract value from field name like 'Pt2Line10_State[0]' -> 'State'"""
        # Remove the [0] suffix first
        clean_name = re.sub(r'\[\d+\]$', '', field_name)
        
        # Extract after the last underscore
        if '_' in clean_name:
            return clean_name.split('_')[-1]
        
        # Fallback: return the clean name if no underscore
        return clean_name
    
    def should_skip_field(self, field_name: str, field_data: dict) -> bool:
        """Determine if field should be skipped (form structure, etc.)"""
        # Skip form structure fields
        structure_patterns = [
            r'^#subform\[\d+\]$',
            r'^#pageSet\[\d+\]$', 
            r'^#area\[\d+\]$',
            r'^form1\[\d+\]$',
            r'^Page\d+\[\d+\]$',
            r'^PDF417BarCode',
            r'^sfTable\[\d+\]$'
        ]
        
        for pattern in structure_patterns:
            if re.match(pattern, field_name):
                return True
                
        # Skip if no persona assigned
        if not field_data.get('persona'):
            return True
            
        return False
    
    def generate_collection_name(self, persona: str, value: str) -> str:
        """Generate collection field name from persona and value"""
        # Capitalize persona for consistency
        persona_clean = persona.capitalize() if persona else 'Unknown'
        
        # Clean up value
        value_clean = value.strip() if value else 'Unknown'
        
        return f"{persona_clean}_{value_clean}"
    
    def determine_collection_type(self, field_data_list: list) -> str:
        """Determine collection type based on field patterns"""
        # Check if any field has specific collection type
        collection_types = set()
        for field_data in field_data_list:
            ctype = field_data.get('collection_type', 'standard')
            if ctype != 'standard':
                collection_types.add(ctype)
        
        # Return the most specific type found
        if 'one_to_many' in collection_types:
            return 'one_to_many'
        elif 'repeating' in collection_types:
            return 'repeating'
        elif 'grouped_checkboxes' in collection_types:
            return 'grouped_checkboxes'
        elif 'one_to_one' in collection_types:
            return 'one_to_one'
        else:
            return 'standard'
    
    def generate_collection_mappings(self, analyzed_fields_file: str) -> dict:
        """Generate collection field mappings from analyzed i485 fields"""
        logger.info(f"Loading analyzed fields from: {analyzed_fields_file}")
        
        with open(analyzed_fields_file, 'r') as f:
            all_fields = json.load(f)
        
        # Filter to only i485.pdf fields
        i485_fields = {name: data for name, data in all_fields.items() 
                      if data.get('form') == 'i485.pdf'}
        
        logger.info(f"Found {len(i485_fields)} i485.pdf fields to process")
        
        # Group fields by persona + value combination
        persona_value_groups = defaultdict(list)
        
        for field_name, field_data in i485_fields.items():
            # Skip structure fields and fields without persona
            if self.should_skip_field(field_name, field_data):
                continue
                
            # Extract persona and value
            persona = field_data.get('persona')
            value = self.extract_value_from_field_name(field_name)
            
            if persona and value:
                key = (persona, value)
                persona_value_groups[key].append((field_name, field_data))
        
        logger.info(f"Found {len(persona_value_groups)} unique persona + value combinations")
        
        # Create collection mappings
        for (persona, value), field_list in persona_value_groups.items():
            collection_name = self.generate_collection_name(persona, value)
            
            # Extract form field names and determine collection type
            form_fields = [field_name for field_name, _ in field_list]
            collection_type = self.determine_collection_type([field_data for _, field_data in field_list])
            
            # Get sample field data for metadata
            sample_field_data = field_list[0][1]
            
            self.collection_mappings[collection_name] = {
                'type': collection_type,
                'description': f'{persona.capitalize()} {value} data (collected across forms)',
                'persona': persona,
                'domain': sample_field_data.get('domain'),
                'value': value,
                'form_fields': sorted(form_fields),  # Sort for consistency
                'field_count': len(form_fields),
                'sample_screen_label': sample_field_data.get('screen_label'),
                'sample_tooltip': sample_field_data.get('tooltip')
            }
        
        logger.info(f"Generated {len(self.collection_mappings)} collection field mappings")
        return self.collection_mappings

def main():
    mapper = CorrectCollectionFieldMapper()
    
    # Find the most recent analyzed file
    extraction_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i485_extraction")
    analyzed_files = [f for f in os.listdir(extraction_dir) if f.startswith('i485_with_rules_') and f.endswith('.json')]
    if not analyzed_files:
        logger.error("No analyzed files found. Run apply_i485_rules.py first.")
        return
    
    latest_file = os.path.join(extraction_dir, sorted(analyzed_files)[-1])
    logger.info(f"Using analyzed file: {latest_file}")
    
    # Generate collection mappings
    collection_mappings = mapper.generate_collection_mappings(latest_file)
    
    # Save collection mappings
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(extraction_dir, f"correct_collection_mappings_{timestamp}.json")
    
    with open(output_file, 'w') as f:
        json.dump(collection_mappings, f, indent=2)
    
    print(f"Collection mappings saved to: {output_file}")
    print(f"Total collection fields: {len(collection_mappings)}")
    
    # Print summary by persona
    persona_summary = defaultdict(list)
    for collection_name, mapping in collection_mappings.items():
        persona = mapping['persona']
        value = mapping['value']
        field_count = mapping['field_count']
        collection_type = mapping['type']
        persona_summary[persona].append((value, field_count, collection_type))
    
    print(f"\n=== COLLECTION FIELDS BY PERSONA ===")
    for persona, collections in sorted(persona_summary.items()):
        print(f"\n{persona.upper()}:")
        for value, count, ctype in sorted(collections):
            print(f"  {persona.capitalize()}_{value}: {count} form fields ({ctype})")
    
    # Show examples
    print(f"\n=== EXAMPLES ===")
    example_count = 0
    for collection_name, mapping in collection_mappings.items():
        if example_count < 5:
            print(f"\nCollection: {collection_name}")
            print(f"  Value: {mapping['value']}")
            print(f"  Persona: {mapping['persona']}")
            print(f"  Domain: {mapping['domain']}")
            print(f"  Type: {mapping['type']}")
            print(f"  Form Fields: {mapping['form_fields'][:3]}{'...' if len(mapping['form_fields']) > 3 else ''}")
            example_count += 1

if __name__ == "__main__":
    main() 