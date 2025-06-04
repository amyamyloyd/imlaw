#!/usr/bin/env python3

"""
Generate collection field mappings from analyzed i485 fields.
"""

import os
import json
import logging
from datetime import datetime
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class CollectionFieldMapper:
    def __init__(self):
        self.collection_mappings = {}
        
    def generate_collection_name(self, base_name: str, collection_type: str, persona: str, domain: str) -> str:
        """Generate a standardized collection field name"""
        # Clean up base name
        clean_base = base_name.replace('Name', '').replace('Address', '').strip()
        
        # Add persona prefix for clarity
        persona_prefix = {
            'applicant': 'Applicant',
            'attorney': 'Attorney', 
            'family_member': 'Family',
            'beneficiary': 'Beneficiary',
            'preparer': 'Preparer',
            'interpreter': 'Interpreter'
        }.get(persona, 'Unknown')
        
        # Add domain context if needed
        domain_suffix = ''
        if domain == 'immigration':
            domain_suffix = '_Immigration'
        elif domain == 'medical':
            domain_suffix = '_Medical'
        elif domain == 'criminal':
            domain_suffix = '_Criminal'
        elif domain == 'office':
            domain_suffix = '_Office'
            
        return f"{persona_prefix}_{clean_base}{domain_suffix}"

    def process_one_to_many_fields(self, fields_by_type):
        """Process fields that map one collection field to many form fields"""
        logger.info("Processing one-to-many collection fields...")
        
        # Group by logical collection (e.g., names, addresses)
        name_fields = []
        address_fields = []
        other_fields = []
        
        for field_name, field_data in fields_by_type['one_to_many']:
            if 'Name' in field_name:
                name_fields.append((field_name, field_data))
            elif any(addr in field_name for addr in ['Address', 'Street', 'City', 'State', 'ZIP']):
                address_fields.append((field_name, field_data))
            else:
                other_fields.append((field_name, field_data))
        
        # Create collection for current names
        if name_fields:
            collection_name = "Applicant_Current_Name"
            self.collection_mappings[collection_name] = {
                'type': 'one_to_many',
                'description': 'Applicant current legal name (reused across forms)',
                'persona': 'applicant',
                'domain': 'personal',
                'form_fields': [field[0] for field in name_fields],
                'components': {
                    'family_name': [f for f in [field[0] for field in name_fields] if 'Family' in f],
                    'given_name': [f for f in [field[0] for field in name_fields] if 'Given' in f], 
                    'middle_name': [f for f in [field[0] for field in name_fields] if 'Middle' in f]
                }
            }
            
        # Create collection for mailing address
        if address_fields:
            collection_name = "Applicant_Mailing_Address"
            self.collection_mappings[collection_name] = {
                'type': 'one_to_many',
                'description': 'Applicant mailing address (reused across forms)',
                'persona': 'applicant',
                'domain': 'personal',
                'form_fields': [field[0] for field in address_fields],
                'components': {
                    'street': [f for f in [field[0] for field in address_fields] if 'Street' in f],
                    'city': [f for f in [field[0] for field in address_fields] if 'City' in f],
                    'state': [f for f in [field[0] for field in address_fields] if 'State' in f],
                    'zip': [f for f in [field[0] for field in address_fields] if 'ZIP' in f]
                }
            }

    def process_repeating_fields(self, fields_by_type):
        """Process repeating fields (0-3 occurrences)"""
        logger.info("Processing repeating collection fields...")
        
        # Group previous names by occurrence (2, 3, 4)
        previous_name_groups = defaultdict(list)
        
        for field_name, field_data in fields_by_type['repeating']:
            if 'Name' in field_name:
                # Extract line number (2, 3, 4)
                if 'Line2' in field_name:
                    previous_name_groups['previous_name_1'].append((field_name, field_data))
                elif 'Line3' in field_name:
                    previous_name_groups['previous_name_2'].append((field_name, field_data))
                elif 'Line4' in field_name:
                    previous_name_groups['previous_name_3'].append((field_name, field_data))
        
        # Create collection for each previous name slot
        for i, (group_key, fields) in enumerate(previous_name_groups.items(), 1):
            collection_name = f"Applicant_Previous_Name_{i}"
            self.collection_mappings[collection_name] = {
                'type': 'repeating',
                'description': f'Applicant previous name #{i} (optional)',
                'persona': 'applicant',
                'domain': 'personal',
                'form_fields': [field[0] for field in fields],
                'occurrence': i,
                'components': {
                    'family_name': [f for f in [field[0] for field in fields] if 'Family' in f],
                    'given_name': [f for f in [field[0] for field in fields] if 'Given' in f],
                    'middle_name': [f for f in [field[0] for field in fields] if 'Middle' in f]
                }
            }

    def process_one_to_one_fields(self, fields_by_type):
        """Process one-to-one collection fields (mostly office/attorney)"""
        logger.info("Processing one-to-one collection fields...")
        
        for field_name, field_data in fields_by_type['one_to_one']:
            # Create individual collection field for each
            collection_name = self.generate_collection_name(
                field_name.replace('[0]', ''), 
                'one_to_one',
                field_data.get('persona', 'unknown'),
                field_data.get('domain', 'unknown')
            )
            
            # Safely extract value_type
            value_info = field_data.get('value_info') or {}
            value_type = value_info.get('type', 'unknown') if isinstance(value_info, dict) else 'unknown'
            
            self.collection_mappings[collection_name] = {
                'type': 'one_to_one',
                'description': f'Single field collection for {field_name}',
                'persona': field_data.get('persona'),
                'domain': field_data.get('domain'),
                'form_fields': [field_name],
                'screen_label': field_data.get('screen_label'),
                'value_type': value_type
            }

    def process_grouped_checkboxes(self, fields_by_type):
        """Process grouped checkbox collections"""
        logger.info("Processing grouped checkbox collections...")
        
        for field_name, field_data in fields_by_type['grouped_checkboxes']:
            collection_name = "Applicant_Immigration_Category"
            if collection_name not in self.collection_mappings:
                self.collection_mappings[collection_name] = {
                    'type': 'grouped_checkboxes',
                    'description': 'Immigration category selection (Part 2)',
                    'persona': 'applicant',
                    'domain': 'immigration',
                    'form_fields': [],
                    'sub_categories': {}
                }
            
            self.collection_mappings[collection_name]['form_fields'].append(field_name)

    def generate_collection_mappings(self, analyzed_fields_file: str) -> dict:
        """Generate collection field mappings from analyzed fields"""
        logger.info(f"Loading analyzed fields from: {analyzed_fields_file}")
        
        with open(analyzed_fields_file, 'r') as f:
            fields = json.load(f)
        
        # Group fields by collection type
        fields_by_type = defaultdict(list)
        
        for field_name, field_data in fields.items():
            collection_type = field_data.get('collection_type', 'standard')
            if collection_type != 'standard':
                fields_by_type[collection_type].append((field_name, field_data))
        
        logger.info(f"Found fields by collection type:")
        for ctype, fields_list in fields_by_type.items():
            logger.info(f"  {ctype}: {len(fields_list)} fields")
        
        # Process each collection type
        self.process_one_to_many_fields(fields_by_type)
        self.process_repeating_fields(fields_by_type)
        self.process_one_to_one_fields(fields_by_type)
        self.process_grouped_checkboxes(fields_by_type)
        
        logger.info(f"Generated {len(self.collection_mappings)} collection field mappings")
        return self.collection_mappings

def main():
    mapper = CollectionFieldMapper()
    
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
    output_file = os.path.join(extraction_dir, f"collection_mappings_{timestamp}.json")
    
    with open(output_file, 'w') as f:
        json.dump(collection_mappings, f, indent=2)
    
    print(f"Collection mappings saved to: {output_file}")
    print(f"Total collection fields: {len(collection_mappings)}")
    
    # Print summary
    print(f"\n=== COLLECTION FIELD SUMMARY ===")
    for collection_name, mapping in collection_mappings.items():
        field_count = len(mapping['form_fields'])
        ctype = mapping['type']
        persona = mapping.get('persona', 'unknown')
        print(f"{collection_name}: {ctype} -> {field_count} form fields (persona: {persona})")
    
    # Show detailed example
    if collection_mappings:
        print(f"\n=== EXAMPLE COLLECTION MAPPING ===")
        example_name = list(collection_mappings.keys())[0]
        example = collection_mappings[example_name]
        print(f"Collection: {example_name}")
        print(f"Type: {example['type']}")
        print(f"Description: {example['description']}")
        print(f"Form Fields: {example['form_fields']}")
        if 'components' in example:
            print(f"Components: {example['components']}")

if __name__ == "__main__":
    main() 