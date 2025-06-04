#!/usr/bin/env python3

"""
Script to apply I-485 form rules (both existing and documented) to extracted fields.
"""

import os
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class I485RuleApplicator:
    def __init__(self):
        # Import existing rules from analyze_form_fields.py
        self.form_part_mappings = {
            'i485.pdf': {
                'Pt1': 'applicant',      # Information About You
                'Pt2': 'applicant',      # Application Type
                'Pt3': 'applicant',      # Additional Information About You
                'Pt4': 'family_member',  # Information About Your Parents
                'Pt5': 'family_member',  # Information About Your Marital History
                'Pt6': 'family_member',  # Information About Your Children
                'Pt7': 'applicant',      # Biographic Information
                'Pt8': 'applicant',      # General Eligibility and Inadmissibility Grounds
                'Pt9': 'interpreter',    # Interpreter's Contact Information
                'Pt10': 'preparer',      # Contact Information, Declaration, and Signature of the Person Preparing this Application
            }
        }
        
        # Form structure fields that don't need personas
        self.form_structure_patterns = [
            r'^#subform\[\d+\]$',
            r'^#pageSet\[\d+\]$', 
            r'^#area\[\d+\]$',
            r'^form1\[\d+\]$',
            r'^Page\d+\[\d+\]$',
            r'^PDF417BarCode2\[\d+\]$',
            r'^sfTable\[\d+\]$'
        ]

        # Personal information field patterns that indicate applicant
        self.personal_info_patterns = [
            r'.*(?:Family|Given|Middle)(?:Name)?.*',  # Match any name field
            r'.*(?:DOB|DateOfBirth|BirthDate).*',
            r'.*(?:BirthPlace|PlaceOfBirth).*',
            r'.*(?:CountryOfBirth|CityTownOfBirth).*',
            r'.*(?:Alien|Global_A|A)Number.*',
            r'.*(?:SSN|SocialSecurityNumber).*',
            r'.*(?:I94|Passport|Receipt|USCIS)Number.*',
            r'.*(?:DateOfEntry|PlaceOfEntry|PortOfEntry).*',
            r'.*(?:CurrentStatus|StatusExpiration).*',
            r'.*(?:MailingAddress|PhysicalAddress).*',
            r'.*(?:DaytimePhone|MobilePhone|EmailAddress).*',
            r'.*(?:Pt2Line4|Pt2Line11).*'  # Common personal info fields in Part 2
        ]

        # Medical examination field patterns that indicate applicant
        self.medical_patterns = [
            r'^Pt\d+Line\d+_(Medical|Health|Exam|Vaccine|Test|Treatment|Diagnosis|Doctor|Physician)',
            r'CompleteSeries',
            r'Immunization',
            r'MedicalExam',
            r'HealthScreening'
        ]

        # Domain/category patterns for field classification
        self.domain_patterns = {
            'personal': [
                r'.*(?:Family|Given|Middle)(?:Name)?.*',
                r'.*(?:DOB|DateOfBirth|BirthDate).*',
                r'.*(?:BirthPlace|PlaceOfBirth).*',
                r'.*(?:CountryOfBirth|CityTownOfBirth).*',
                r'.*(?:SSN|SocialSecurityNumber).*',
                r'.*(?:MailingAddress|PhysicalAddress).*',
                r'.*(?:DaytimePhone|MobilePhone|EmailAddress).*',
                r'.*(?:MaritalStatus|Marriage|Divorce).*',
                r'.*(?:Gender|Sex).*',
                r'.*(?:Height|Weight|EyeColor|HairColor).*',
                r'.*(?:Race|Ethnicity).*'
            ],
            'medical': [
                r'.*(?:Medical|Health|Exam|Vaccine|Test|Treatment|Diagnosis).*',
                r'.*(?:Doctor|Physician|Hospital|Clinic).*',
                r'.*(?:Disability|Condition|Illness).*',
                r'.*(?:Immunization|Vaccination).*',
                r'.*(?:Mental|Physical|Psychological).*',
                r'.*(?:Drug|Substance|Addiction).*'
            ],
            'criminal': [
                r'.*(?:Criminal|Arrest|Conviction|Offense).*',
                r'.*(?:Prison|Jail|Detention|Incarceration).*',
                r'.*(?:Court|Judge|Sentence|Probation).*',
                r'.*(?:Police|Law|Enforcement).*',
                r'.*(?:Felony|Misdemeanor|Crime).*',
                r'.*(?:Violation|Illegal|Unlawful).*'
            ],
            'immigration': [
                r'.*(?:Alien|Global_A|A)Number.*',
                r'.*(?:I94|Passport|Receipt|USCIS)Number.*',
                r'.*(?:DateOfEntry|PlaceOfEntry|PortOfEntry).*',
                r'.*(?:CurrentStatus|StatusExpiration).*',
                r'.*(?:Visa|Immigration|Naturalization).*',
                r'.*(?:Deportation|Removal|Exclusion).*',
                r'.*(?:Asylum|Refugee|Protection).*',
                r'.*(?:Citizenship|Nationality|Country).*'
            ],
            'office': [
                r'.*(?:Receipt|Filing|Processing).*',
                r'.*(?:Office|Administrative|Agency).*',
                r'.*(?:Form|Application|Petition).*',
                r'.*(?:Signature|Date|Certification).*',
                r'.*(?:Fee|Payment|Check).*',
                r'.*(?:Preparer|Attorney|Representative).*'
            ]
        }
        
        # Enhanced rules based on our documentation
        self.enhanced_rules = {
            # Office Section (Pre-Part 1)
            'office_section': {
                'persona': 'attorney',
                'domain': 'office',
                'patterns': [
                    r'volag',
                    r'g-28',
                    r'attorney.*state.*bar',
                    r'accredited.*representative',
                    r'uscis.*online.*account'
                ]
            },
            
            # Part 1 patterns
            'part1_patterns': {
                'current_names': {
                    'patterns': [r'Pt1Line1[abc]_.*Name'],
                    'persona': 'applicant',
                    'domain': 'personal',
                    'collection_type': 'one_to_many'
                },
                'previous_names': {
                    'patterns': [r'Pt1Line[234][abc]_.*Name'],
                    'persona': 'applicant', 
                    'domain': 'personal',
                    'collection_type': 'repeating'
                },
                'us_mailing_address': {
                    'patterns': [r'Pt1Line1[0-9]+.*(?:Address|Street|City|State|ZIP)'],
                    'persona': 'applicant',
                    'domain': 'personal', 
                    'collection_type': 'one_to_many'
                },
                'immigration_history': {
                    'patterns': [r'Pt1Line1[89].*', r'Pt1Line2[0-4].*'],
                    'persona': 'applicant',
                    'domain': 'immigration'
                },
                'character_fields': {
                    'patterns': [r'Pt1Line15_SSN', r'.*AlienNumber'],
                    'persona': 'applicant',
                    'domain': 'personal',
                    'field_type': 'character_sequence'
                }
            },
            
            # Part 2 patterns  
            'part2_patterns': {
                'immigration_category': {
                    'patterns': [r'Pt2Line1[a-g].*'],
                    'persona': 'applicant',
                    'domain': 'immigration',
                    'collection_type': 'grouped_checkboxes'
                },
                'principal_applicant': {
                    'patterns': [r'Pt2.*principal.*applicant'],
                    'persona': 'beneficiary',
                    'domain': 'immigration',
                    'collection_type': 'one_to_one'
                }
            },
            
            # Part 3 patterns
            'part3_patterns': {
                'current_address': {
                    'patterns': [r'Pt3.*current.*address'],
                    'persona': 'applicant',
                    'domain': 'personal',
                    'collection_type': 'one_to_many'
                },
                'previous_addresses': {
                    'patterns': [r'Pt3.*previous.*address'],
                    'persona': 'applicant', 
                    'domain': 'personal',
                    'collection_type': 'flagged_collection'
                },
                'employment': {
                    'patterns': [r'Pt3.*employ'],
                    'persona': 'applicant',
                    'domain': 'personal',
                    'collection_type': 'one_to_many'
                }
            },
            
            # Part 4 patterns
            'part4_patterns': {
                'parent_info': {
                    'patterns': [r'Pt4.*parent'],
                    'persona': 'family_member',
                    'domain': 'personal',
                    'collection_type': 'flagged_collection'
                }
            }
        }

    def _get_form_part_persona(self, field_id: str) -> str:
        """Determine persona based on form part number from field ID."""
        part_match = re.match(r'Pt(\d+)', field_id)
        if not part_match:
            return None
            
        part_num = f"Pt{part_match.group(1)}"
        return self.form_part_mappings.get('i485.pdf', {}).get(part_num)

    def _apply_office_section_rules(self, field: Dict) -> Dict:
        """Apply office section rules (pre-Part 1)"""
        field_name = field.get('name', '').lower()
        tooltip = field.get('tooltip', '').lower() if field.get('tooltip') else ''
        
        for pattern in self.enhanced_rules['office_section']['patterns']:
            if re.search(pattern, field_name) or re.search(pattern, tooltip):
                field['persona'] = self.enhanced_rules['office_section']['persona']
                field['domain'] = self.enhanced_rules['office_section']['domain']
                field['collection_type'] = 'one_to_one'
                field['rule_applied'] = 'office_section'
                return field
        return field

    def _apply_part_specific_rules(self, field: Dict) -> Dict:
        """Apply part-specific rules based on field patterns"""
        field_name = field.get('name', '')
        
        # Check Part 1 patterns
        for pattern_name, rules in self.enhanced_rules['part1_patterns'].items():
            for pattern in rules['patterns']:
                if re.search(pattern, field_name, re.IGNORECASE):
                    field['persona'] = rules['persona']
                    field['domain'] = rules['domain']
                    field['collection_type'] = rules.get('collection_type', 'standard')
                    field['rule_applied'] = f'part1_{pattern_name}'
                    return field
        
        # Check Part 2 patterns
        for pattern_name, rules in self.enhanced_rules['part2_patterns'].items():
            for pattern in rules['patterns']:
                if re.search(pattern, field_name, re.IGNORECASE):
                    field['persona'] = rules['persona']
                    field['domain'] = rules['domain']
                    field['collection_type'] = rules.get('collection_type', 'standard')
                    field['rule_applied'] = f'part2_{pattern_name}'
                    return field
        
        # Check Part 3 patterns
        for pattern_name, rules in self.enhanced_rules['part3_patterns'].items():
            for pattern in rules['patterns']:
                if re.search(pattern, field_name, re.IGNORECASE):
                    field['persona'] = rules['persona']
                    field['domain'] = rules['domain']
                    field['collection_type'] = rules.get('collection_type', 'standard')
                    field['rule_applied'] = f'part3_{pattern_name}'
                    return field
        
        # Check Part 4 patterns
        for pattern_name, rules in self.enhanced_rules['part4_patterns'].items():
            for pattern in rules['patterns']:
                if re.search(pattern, field_name, re.IGNORECASE):
                    field['persona'] = rules['persona']
                    field['domain'] = rules['domain'] 
                    field['collection_type'] = rules.get('collection_type', 'standard')
                    field['rule_applied'] = f'part4_{pattern_name}'
                    return field
        
        return field

    def _apply_legacy_rules(self, field: Dict) -> Dict:
        """Apply legacy rules from analyze_form_fields.py as fallback"""
        if field.get('persona') and field.get('domain'):
            return field  # Already assigned by enhanced rules
            
        field_name = field.get('name', '')
        tooltip = field.get('tooltip', '') if field.get('tooltip') else ''
        
        # Skip form structure fields
        if self._is_form_structure_field(field_name):
            field['persona'] = None
            field['domain'] = None
            field['rule_applied'] = 'form_structure_skip'
            return field
        
        # Apply persona logic
        if not field.get('persona'):
            # Medical fields indicate applicant persona
            if self._is_medical_field(field_name):
                field['persona'] = 'applicant'
                field['rule_applied'] = 'medical_pattern'
            # Personal info fields indicate applicant persona  
            elif self._is_personal_info_field(field_name):
                field['persona'] = 'applicant'
                field['rule_applied'] = 'personal_info_pattern'
            # Apply form part mapping as fallback
            else:
                part_persona = self._get_form_part_persona(field_name)
                if part_persona:
                    field['persona'] = part_persona
                    field['rule_applied'] = 'legacy_part_mapping'
        
        # Apply comprehensive domain patterns
        if not field.get('domain'):
            field['domain'] = self._apply_domain_patterns(field)
            if not field.get('rule_applied'):
                field['rule_applied'] = 'domain_pattern'
        
        # Override domain for certain personas
        if field.get('persona') in ['attorney', 'preparer'] and field.get('domain') != 'office':
            field['domain'] = 'office'
            field['rule_applied'] = f"{field.get('rule_applied', '')}_office_override"
                
        return field

    def _identify_field_patterns(self, field: Dict) -> Dict:
        """Identify special field patterns and collection strategies"""
        field_name = field.get('name', '')
        tooltip = field.get('tooltip', '') if field.get('tooltip') else ''
        
        # Dual checkbox pattern (Male/Female)
        if re.search(r'(male|female)', field_name, re.IGNORECASE) and field.get('type') == '/Btn':
            field['pattern_type'] = 'dual_checkbox'
            field['pattern_description'] = 'Either/or selection with separate checkboxes'
            
        # Yes/No button pattern
        elif re.search(r'(yes|no)', field_name, re.IGNORECASE) and field.get('type') == '/Btn':
            field['pattern_type'] = 'yes_no_button'
            field['pattern_description'] = 'Standard yes/no selection'
            
        # Character-by-character fields (SSN, Alien Number)
        elif re.search(r'(ssn|alien.*number)', field_name, re.IGNORECASE) and '_' in field_name:
            field['pattern_type'] = 'character_sequence'
            field['pattern_description'] = 'Individual character input boxes'
            
        # Checkbox + text combination
        elif 'checkbox' in tooltip.lower() and 'text' in tooltip.lower():
            field['pattern_type'] = 'checkbox_text_combo'
            field['pattern_description'] = 'Linked checkbox and text area'
            
        # Complex option pattern (Apt/Ste/Flr)
        elif re.search(r'(apt|ste|flr)', field_name, re.IGNORECASE):
            field['pattern_type'] = 'complex_option'
            field['pattern_description'] = 'Multiple checkboxes with conditional text'
            
        return field

    def apply_rules_to_field(self, field: Dict) -> Dict:
        """Apply all rules to a single field"""
        # 1. Apply office section rules first (highest priority)
        field = self._apply_office_section_rules(field)
        
        # 2. Apply part-specific enhanced rules
        field = self._apply_part_specific_rules(field)
        
        # 3. Apply legacy rules as fallback
        field = self._apply_legacy_rules(field)
        
        # 4. Identify field patterns
        field = self._identify_field_patterns(field)
        
        # 5. Set collection_type if not already set
        if not field.get('collection_type'):
            field['collection_type'] = 'standard'
            
        return field

    def process_i485_fields(self, fields_file: str) -> Dict:
        """Process all extracted i485 fields with enhanced rules"""
        logger.info(f"Loading fields from: {fields_file}")
        
        with open(fields_file, 'r') as f:
            fields = json.load(f)
        
        logger.info(f"Processing {len(fields)} fields with enhanced rules")
        
        processed_fields = {}
        rule_stats = {}
        
        for field_name, field_data in fields.items():
            processed_field = self.apply_rules_to_field(field_data)
            processed_fields[field_name] = processed_field
            
            # Track rule usage statistics
            rule_applied = processed_field.get('rule_applied', 'no_rule')
            rule_stats[rule_applied] = rule_stats.get(rule_applied, 0) + 1
        
        logger.info("Rule application statistics:")
        for rule, count in sorted(rule_stats.items()):
            logger.info(f"  {rule}: {count} fields")
            
        return processed_fields

    def _is_form_structure_field(self, field_id: str) -> bool:
        """Check if field is a form structure field that doesn't need a persona"""
        return any(re.match(pattern, field_id) for pattern in self.form_structure_patterns)

    def _is_personal_info_field(self, field_id: str) -> bool:
        """Check if field contains personal information about the applicant"""
        return any(re.search(pattern, field_id, re.IGNORECASE) for pattern in self.personal_info_patterns)

    def _is_medical_field(self, field_id: str) -> bool:
        """Check if field contains medical information about the applicant"""
        return any(re.match(pattern, field_id) for pattern in self.medical_patterns)

    def _apply_domain_patterns(self, field: Dict) -> str:
        """Apply domain patterns to determine field domain"""
        if field.get('domain'):
            return field['domain']  # Already set
            
        field_name = field.get('name', '')
        tooltip = field.get('tooltip', '') if field.get('tooltip') else ''
        
        # Check each domain pattern
        for domain, patterns in self.domain_patterns.items():
            for pattern in patterns:
                if re.search(pattern, field_name, re.IGNORECASE):
                    return domain
                if tooltip and re.search(pattern, tooltip, re.IGNORECASE):
                    return domain
        
        return 'personal'  # Default domain

def main():
    applicator = I485RuleApplicator()
    
    # Find the most recent extraction file
    extraction_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i485_extraction")
    extraction_files = [f for f in os.listdir(extraction_dir) if f.endswith('.json')]
    if not extraction_files:
        logger.error("No extraction files found. Run extract_i485_fields.py first.")
        return
    
    latest_file = os.path.join(extraction_dir, sorted(extraction_files)[-1])
    logger.info(f"Using extraction file: {latest_file}")
    
    # Process fields with rules
    processed_fields = applicator.process_i485_fields(latest_file)
    
    # Save processed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(extraction_dir, f"i485_with_rules_{timestamp}.json")
    
    with open(output_file, 'w') as f:
        json.dump(processed_fields, f, indent=2)
    
    print(f"Processed fields saved to: {output_file}")
    print(f"Total fields processed: {len(processed_fields)}")
    
    # Generate detailed analysis report
    personas = {}
    domains = {}
    collection_types = {}
    patterns = {}
    documented_vs_legacy = {
        'documented_sections': 0,
        'legacy_fallback': 0,
        'form_structure': 0
    }
    
    for field in processed_fields.values():
        # Filter out None values for sorting
        persona = field.get('persona') or 'None'
        domain = field.get('domain') or 'None'
        collection_type = field.get('collection_type') or 'None'
        pattern_type = field.get('pattern_type') or 'standard'
        rule_applied = field.get('rule_applied', 'no_rule')
        
        personas[persona] = personas.get(persona, 0) + 1
        domains[domain] = domains.get(domain, 0) + 1
        collection_types[collection_type] = collection_types.get(collection_type, 0) + 1
        patterns[pattern_type] = patterns.get(pattern_type, 0) + 1
        
        # Categorize by our documented rules vs legacy
        if rule_applied.startswith(('office_section', 'part1_', 'part2_', 'part3_', 'part4_')):
            documented_vs_legacy['documented_sections'] += 1
        elif rule_applied == 'form_structure_skip':
            documented_vs_legacy['form_structure'] += 1
        else:
            documented_vs_legacy['legacy_fallback'] += 1
    
    print(f"\n=== RULE EFFECTIVENESS ANALYSIS ===")
    print(f"Documented Sections (Office, Parts 1-4): {documented_vs_legacy['documented_sections']} fields")
    print(f"Legacy Fallback (Parts 5-14): {documented_vs_legacy['legacy_fallback']} fields") 
    print(f"Form Structure (Skipped): {documented_vs_legacy['form_structure']} fields")
    
    coverage = documented_vs_legacy['documented_sections'] / (len(processed_fields) - documented_vs_legacy['form_structure']) * 100
    print(f"Documented Rule Coverage: {coverage:.1f}% of content fields")
    
    print(f"\n=== SUMMARY REPORT ===")
    print(f"Personas: {dict(sorted(personas.items()))}")
    print(f"Domains: {dict(sorted(domains.items()))}")
    print(f"Collection Types: {dict(sorted(collection_types.items()))}")
    print(f"Pattern Types: {dict(sorted(patterns.items()))}")
    
    # Show examples of our documented rules working
    print(f"\n=== DOCUMENTED RULE EXAMPLES ===")
    examples_shown = 0
    for field_name, field in processed_fields.items():
        rule_applied = field.get('rule_applied', '')
        if rule_applied.startswith(('office_section', 'part1_', 'part2_', 'part3_', 'part4_')) and examples_shown < 10:
            print(f"{field_name}: {rule_applied} -> persona={field.get('persona')}, domain={field.get('domain')}, collection={field.get('collection_type')}")
            examples_shown += 1

if __name__ == "__main__":
    main() 