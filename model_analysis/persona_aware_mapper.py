#!/usr/bin/env python3
"""
Persona-Aware Field Mapper for USCIS Form Fields
Creates collection fields like applicant_given_name, beneficiary_address_street, etc.
"""

import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder
import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PersonaCollectionField:
    """Represents a persona-aware collection field"""
    name: str  # e.g., "applicant_given_name"
    persona: str  # e.g., "applicant"
    field_type: str  # e.g., "given_name"
    data_type: str  # text, date, selection
    description: str

@dataclass
class PersonaFieldMapping:
    """Represents a mapping between form field and persona-aware collection field"""
    form_field_id: str
    form_name: str
    persona_collection_field: str  # e.g., "applicant_given_name"
    confidence: float
    detected_persona: str
    detected_field_type: str
    context: str

class PersonaAwareMapper:
    """Creates persona-specific collection fields for each field type"""
    
    def __init__(self):
        self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.persona_encoder = LabelEncoder()
        self.field_type_encoder = LabelEncoder()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        
        # Define field types that need persona-specific collection
        self.field_types = {
            'given_name': 'text',
            'family_name': 'text', 
            'middle_name': 'text',
            'full_name': 'text',
            'date_of_birth': 'date',
            'country_of_birth': 'text',
            'alien_number': 'text',
            'social_security_number': 'text',
            'gender': 'selection',
            'address_street': 'text',
            'address_city': 'text',
            'address_state': 'text',
            'address_zipcode': 'text',
            'address_country': 'text',
            'phone_number': 'text',
            'email_address': 'text',
            'employer_name': 'text',
            'occupation': 'text',
            'marriage_date': 'date',
            'marital_status': 'selection',
            'height': 'text',
            'weight': 'text',
            'eye_color': 'selection',
            'hair_color': 'selection'
        }
        
        # Define personas
        self.personas = ['applicant', 'beneficiary', 'spouse', 'family_member', 'parent', 'preparer', 'employer']
        
    def _predict_field_type_rule_based(self, field_data: Dict) -> Optional[str]:
        """Determine the field type based on field name and tooltip"""
        field_name = field_data.get('name', '').lower()
        tooltip = field_data.get('tooltip', '').lower()
        
        # Name patterns
        if re.search(r'(given|first).*name', field_name) or re.search(r'(given|first).*name', tooltip):
            return 'given_name'
        if re.search(r'(family|last|surname).*name', field_name) or re.search(r'(family|last|surname).*name', tooltip):
            return 'family_name'
        if re.search(r'middle.*name', field_name) or re.search(r'middle.*name', tooltip):
            return 'middle_name'
        if re.search(r'full.*name', field_name) or re.search(r'full.*name', tooltip):
            return 'full_name'
            
        # Date patterns
        if re.search(r'(date.*birth|birth.*date|dob)', field_name) or re.search(r'(date.*birth|birth.*date|dob)', tooltip):
            return 'date_of_birth'
        if re.search(r'(marriage|married)', field_name) or re.search(r'(marriage|married)', tooltip):
            return 'marriage_date'
            
        # Address patterns
        if re.search(r'street.*address', field_name) or re.search(r'street.*address', tooltip):
            return 'address_street'
        if re.search(r'(^city|[^a-z]city)', field_name) or re.search(r'(^city|[^a-z]city)', tooltip):
            return 'address_city'
        if re.search(r'(^state|[^a-z]state)', field_name) or re.search(r'(^state|[^a-z]state)', tooltip):
            return 'address_state'
        if re.search(r'(zip|postal)', field_name) or re.search(r'(zip|postal)', tooltip):
            return 'address_zipcode'
        if re.search(r'country', field_name) or re.search(r'country', tooltip):
            return 'address_country'
            
        # Contact information
        if re.search(r'(phone|telephone)', field_name) or re.search(r'(phone|telephone)', tooltip):
            return 'phone_number'
        if re.search(r'email', field_name) or re.search(r'email', tooltip):
            return 'email_address'
            
        # Physical characteristics
        if re.search(r'height', field_name) or re.search(r'height', tooltip):
            return 'height'
        if re.search(r'weight', field_name) or re.search(r'weight', tooltip):
            return 'weight'
        if re.search(r'eye.*color', field_name) or re.search(r'eye.*color', tooltip):
            return 'eye_color'
        if re.search(r'hair.*color', field_name) or re.search(r'hair.*color', tooltip):
            return 'hair_color'
            
        # Employment
        if re.search(r'employer', field_name) or re.search(r'employer', tooltip):
            return 'employer_name'
        if re.search(r'occupation', field_name) or re.search(r'occupation', tooltip):
            return 'occupation'
            
        # Immigration-specific
        if re.search(r'alien.*number', field_name) or re.search(r'alien.*number', tooltip):
            return 'alien_number'
        if re.search(r'(ssn|social.*security)', field_name) or re.search(r'(ssn|social.*security)', tooltip):
            return 'social_security_number'
            
        # Gender/Sex
        if re.search(r'(sex|gender|male|female)', field_name) or re.search(r'(sex|gender|male|female)', tooltip):
            return 'gender'
            
        # Marital status
        if re.search(r'marital', field_name) or re.search(r'marital', tooltip):
            return 'marital_status'
            
        return None
    
    def generate_persona_collection_fields(self, form_data: List[Dict]) -> Dict[str, PersonaCollectionField]:
        """Generate persona-aware collection fields based on the actual data"""
        logger.info("Generating persona-aware collection fields...")
        
        collection_fields = {}
        field_persona_combinations = set()
        
        # Analyze all fields to find which persona + field type combinations exist
        for field in form_data:
            persona = field.get('persona', '')
            field_type = self._predict_field_type_rule_based(field)
            
            if field_type and persona and persona in self.personas:
                field_persona_combinations.add((persona, field_type))
        
        # Create collection fields for each valid combination
        for persona, field_type in field_persona_combinations:
            collection_name = f"{persona}_{field_type}"
            data_type = self.field_types.get(field_type, 'text')
            
            collection_fields[collection_name] = PersonaCollectionField(
                name=collection_name,
                persona=persona,
                field_type=field_type,
                data_type=data_type,
                description=f"{persona.title()}'s {field_type.replace('_', ' ')}"
            )
        
        logger.info(f"Generated {len(collection_fields)} persona-aware collection fields")
        return collection_fields
    
    def extract_features(self, field_data: Dict) -> Dict:
        """Extract features for ML prediction"""
        features = {}
        
        field_name = field_data.get('name', '')
        tooltip = field_data.get('tooltip', '')
        persona = field_data.get('persona', '')
        domain = field_data.get('domain', '')
        
        # Basic features
        features['field_name_length'] = len(field_name)
        features['has_underscore'] = '_' in field_name
        features['has_number'] = bool(re.search(r'\d', field_name))
        features['has_part_prefix'] = bool(re.search(r'^Pt\d+', field_name))
        
        # Pattern matching features for field types
        type_patterns = {
            'name_pattern': r'(name|given|family|middle|first|last)',
            'address_pattern': r'(address|street|city|state|zip|country)',
            'date_pattern': r'(date|birth|dob|marriage)',
            'employment_pattern': r'(employ|job|work|occupation)',
            'physical_pattern': r'(height|weight|eye|hair|color)',
            'id_pattern': r'(alien|number|id|ssn|receipt)',
            'contact_pattern': r'(phone|telephone|email)',
            'gender_pattern': r'(sex|gender|male|female)',
        }
        
        for pattern_name, pattern in type_patterns.items():
            features[f'field_{pattern_name}'] = bool(re.search(pattern, field_name, re.IGNORECASE))
            if tooltip:
                features[f'tooltip_{pattern_name}'] = bool(re.search(pattern, tooltip, re.IGNORECASE))
        
        # Persona and domain
        features['persona'] = persona or 'unknown'
        features['domain'] = domain or 'unknown'
        
        # Tooltip analysis
        if tooltip:
            features['tooltip_length'] = len(tooltip)
            features['tooltip_words'] = len(tooltip.split())
        else:
            features['tooltip_length'] = 0
            features['tooltip_words'] = 0
        
        return features
    
    def create_training_data(self, form_data: List[Dict]) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """Create training data for both persona and field type prediction"""
        logger.info("Creating training data...")
        
        training_data = []
        persona_labels = []
        field_type_labels = []
        text_features = []
        
        for field in form_data:
            persona = field.get('persona', '')
            field_type = self._predict_field_type_rule_based(field)
            
            # Only include fields where we can determine both persona and field type
            if persona and field_type and persona in self.personas and field_type in self.field_types:
                features = self.extract_features(field)
                training_data.append(features)
                persona_labels.append(persona)
                field_type_labels.append(field_type)
                
                # Text features
                tooltip = field.get('tooltip', '')
                field_name = field.get('name', '')
                combined_text = f"{field_name} {tooltip}"
                text_features.append(combined_text)
        
        logger.info(f"Created training data with {len(training_data)} samples")
        
        if len(training_data) == 0:
            return pd.DataFrame(), pd.Series([]), pd.Series([])
        
        # Convert to DataFrame
        df = pd.DataFrame(training_data)
        
        # Add text features
        if text_features:
            text_vectors = self.text_vectorizer.fit_transform(text_features)
            text_df = pd.DataFrame(text_vectors.toarray(), 
                                 columns=[f'text_feature_{i}' for i in range(text_vectors.shape[1])])
            df = pd.concat([df, text_df], axis=1)
        
        # Encode categorical features
        categorical_cols = ['persona', 'domain']
        for col in categorical_cols:
            if col in df.columns:
                df[col] = df[col].fillna('unknown')
                unique_values = df[col].unique()
                value_map = {val: idx for idx, val in enumerate(unique_values)}
                df[col] = df[col].map(value_map)
        
        return df, pd.Series(persona_labels), pd.Series(field_type_labels)
    
    def predict_persona_collections(self, form_data: List[Dict]) -> List[PersonaFieldMapping]:
        """Predict persona-aware collection field mappings"""
        logger.info("Predicting persona-aware collection mappings...")
        
        mappings = []
        collection_fields = self.generate_persona_collection_fields(form_data)
        
        for field in form_data:
            # Use rule-based approach for prediction
            detected_persona = field.get('persona', '')
            detected_field_type = self._predict_field_type_rule_based(field)
            
            confidence = 1.0 if detected_persona and detected_field_type else 0.0
            
            # Create persona collection field name
            if detected_persona and detected_field_type:
                persona_collection_field = f"{detected_persona}_{detected_field_type}"
            else:
                # Default fallback
                persona_collection_field = f"unknown_unknown"
                confidence = 0.1
            
            mapping = PersonaFieldMapping(
                form_field_id=field.get('name', ''),
                form_name=field.get('form', ''),
                persona_collection_field=persona_collection_field,
                confidence=confidence,
                detected_persona=detected_persona,
                detected_field_type=detected_field_type or 'unknown',
                context=field.get('tooltip', '')
            )
            
            mappings.append(mapping)
        
        return mappings, collection_fields
    
    def generate_persona_mapping_report(self, mappings: List[PersonaFieldMapping], 
                                      collection_fields: Dict[str, PersonaCollectionField], 
                                      output_file: str):
        """Generate detailed persona-aware mapping report"""
        logger.info(f"Generating persona-aware mapping report to {output_file}")
        
        # Group by persona collection field
        by_persona_collection = {}
        for mapping in mappings:
            pcf = mapping.persona_collection_field
            if pcf not in by_persona_collection:
                by_persona_collection[pcf] = []
            by_persona_collection[pcf].append(mapping)
        
        # Generate report
        report = {
            'summary': {
                'total_mappings': len(mappings),
                'unique_persona_collection_fields': len(by_persona_collection),
                'high_confidence_mappings': len([m for m in mappings if m.confidence > 0.8]),
                'medium_confidence_mappings': len([m for m in mappings if 0.5 < m.confidence <= 0.8]),
                'low_confidence_mappings': len([m for m in mappings if m.confidence <= 0.5])
            },
            'persona_collection_fields': {
                name: {
                    'persona': field.persona,
                    'field_type': field.field_type,
                    'data_type': field.data_type,
                    'description': field.description
                }
                for name, field in collection_fields.items()
            },
            'mappings_by_persona_collection': {}
        }
        
        for pcf, field_mappings in by_persona_collection.items():
            description = collection_fields.get(pcf, PersonaCollectionField('', '', '', '', 'Unknown')).description
            
            report['mappings_by_persona_collection'][pcf] = {
                'count': len(field_mappings),
                'description': description,
                'mappings': [
                    {
                        'form_field': m.form_field_id,
                        'form_name': m.form_name,
                        'confidence': round(m.confidence, 3),
                        'context': m.context[:100] + '...' if len(m.context) > 100 else m.context
                    }
                    for m in sorted(field_mappings, key=lambda x: x.confidence, reverse=True)
                ]
            }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Persona-aware mapping report saved to {output_file}")

def main():
    # Load the complete analysis data
    analysis_file = Path("model_analysis/results/run_20250604_085938/complete_analysis_20250604_085938.json")
    
    if not analysis_file.exists():
        logger.error(f"Analysis file not found: {analysis_file}")
        return
    
    with open(analysis_file, 'r') as f:
        data = json.load(f)
    
    all_fields = data
    logger.info(f"Loaded {len(all_fields)} fields")
    
    # Initialize mapper
    mapper = PersonaAwareMapper()
    
    # Generate persona-aware mappings
    mappings, collection_fields = mapper.predict_persona_collections(all_fields)
    
    # Generate report
    output_file = f"model_analysis/persona_aware_mappings_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
    mapper.generate_persona_mapping_report(mappings, collection_fields, output_file)
    
    # Save as CSV for easy review
    csv_file = output_file.replace('.json', '.csv')
    mappings_df = pd.DataFrame([
        {
            'form_field': m.form_field_id,
            'form_name': m.form_name,
            'persona_collection_field': m.persona_collection_field,
            'confidence': m.confidence,
            'detected_persona': m.detected_persona,
            'detected_field_type': m.detected_field_type,
            'context': m.context
        }
        for m in mappings
    ])
    mappings_df.to_csv(csv_file, index=False)
    
    logger.info(f"Persona-aware mappings saved to {csv_file}")
    
    # Print summary by persona
    persona_summary = mappings_df.groupby('detected_persona').size().sort_values(ascending=False)
    print(f"\nPersona-Aware Field Mapping Complete!")
    print(f"Total persona collection fields: {len(collection_fields)}")
    print(f"Total mappings: {len(mappings)}")
    print("\nMappings by persona:")
    for persona, count in persona_summary.items():
        print(f"  {persona}: {count} fields")

if __name__ == "__main__":
    main() 