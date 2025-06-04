#!/usr/bin/env python3
"""
ML-based Field Mapper for USCIS Form Fields
Builds on existing rule-based approach but uses ML for better context understanding
"""

import json
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
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
class CollectionField:
    """Represents a canonical collection field that form fields map to"""
    name: str
    category: str  # personal, address, employment, family, etc.
    data_type: str  # text, date, selection, etc.
    personas: List[str]  # which personas this field applies to
    description: str

@dataclass
class FieldMapping:
    """Represents a mapping between a form field and collection field"""
    form_field_id: str
    form_name: str
    collection_field: str
    confidence: float
    persona: str
    context: str

class MLFieldMapper:
    """Machine Learning-based field mapper for USCIS forms"""
    
    def __init__(self):
        self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.persona_encoder = LabelEncoder()
        self.domain_encoder = LabelEncoder()
        self.collection_field_encoder = LabelEncoder()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        
        # Define canonical collection fields
        self.collection_fields = self._define_collection_fields()
        
    def _define_collection_fields(self) -> Dict[str, CollectionField]:
        """Define canonical collection fields based on common USCIS patterns"""
        fields = {
            # Personal Information
            'given_name': CollectionField('given_name', 'personal', 'text', 
                                        ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                        'First/Given name'),
            'family_name': CollectionField('family_name', 'personal', 'text', 
                                         ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                         'Last/Family name'),
            'middle_name': CollectionField('middle_name', 'personal', 'text', 
                                         ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                         'Middle name'),
            'full_name': CollectionField('full_name', 'personal', 'text', 
                                       ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                       'Full name'),
            'date_of_birth': CollectionField('date_of_birth', 'personal', 'date', 
                                           ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                           'Date of birth'),
            'country_of_birth': CollectionField('country_of_birth', 'personal', 'text', 
                                              ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                              'Country of birth'),
            'alien_number': CollectionField('alien_number', 'personal', 'text', 
                                          ['applicant', 'beneficiary'], 
                                          'Alien Registration Number'),
            'social_security_number': CollectionField('social_security_number', 'personal', 'text', 
                                                    ['applicant', 'beneficiary', 'spouse'], 
                                                    'Social Security Number'),
            'gender': CollectionField('gender', 'personal', 'selection', 
                                    ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                    'Gender/Sex'),
            
            # Address Information
            'current_address_street': CollectionField('current_address_street', 'address', 'text', 
                                                    ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                                    'Current street address'),
            'current_address_city': CollectionField('current_address_city', 'address', 'text', 
                                                  ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                                  'Current city'),
            'current_address_state': CollectionField('current_address_state', 'address', 'text', 
                                                   ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                                   'Current state'),
            'current_address_zipcode': CollectionField('current_address_zipcode', 'address', 'text', 
                                                     ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                                     'Current ZIP code'),
            'current_address_country': CollectionField('current_address_country', 'address', 'text', 
                                                     ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                                     'Current country'),
            
            # Contact Information
            'phone_number': CollectionField('phone_number', 'contact', 'text', 
                                          ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                          'Phone number'),
            'email_address': CollectionField('email_address', 'contact', 'text', 
                                           ['applicant', 'beneficiary', 'spouse', 'family_member'], 
                                           'Email address'),
            
            # Employment Information
            'employer_name': CollectionField('employer_name', 'employment', 'text', 
                                           ['applicant', 'beneficiary', 'spouse'], 
                                           'Current employer name'),
            'job_title': CollectionField('job_title', 'employment', 'text', 
                                       ['applicant', 'beneficiary', 'spouse'], 
                                       'Current job title'),
            'occupation': CollectionField('occupation', 'employment', 'text', 
                                        ['applicant', 'beneficiary', 'spouse'], 
                                        'Occupation'),
            'employment_start_date': CollectionField('employment_start_date', 'employment', 'date', 
                                                   ['applicant', 'beneficiary', 'spouse'], 
                                                   'Employment start date'),
            
            # Marriage/Family Information
            'marriage_date': CollectionField('marriage_date', 'family', 'date', 
                                           ['applicant', 'spouse'], 
                                           'Marriage date'),
            'marital_status': CollectionField('marital_status', 'family', 'selection', 
                                            ['applicant', 'beneficiary', 'spouse'], 
                                            'Marital status'),
            
            # Physical Characteristics
            'height': CollectionField('height', 'physical', 'text', 
                                    ['applicant', 'beneficiary'], 
                                    'Height'),
            'weight': CollectionField('weight', 'physical', 'text', 
                                    ['applicant', 'beneficiary'], 
                                    'Weight'),
            'eye_color': CollectionField('eye_color', 'physical', 'selection', 
                                       ['applicant', 'beneficiary'], 
                                       'Eye color'),
            'hair_color': CollectionField('hair_color', 'physical', 'selection', 
                                        ['applicant', 'beneficiary'], 
                                        'Hair color'),
            
            # Background Checks
            'criminal_history': CollectionField('criminal_history', 'background', 'selection', 
                                              ['applicant', 'beneficiary'], 
                                              'Criminal history questions'),
            'medical_history': CollectionField('medical_history', 'medical', 'selection', 
                                             ['applicant', 'beneficiary'], 
                                             'Medical history questions'),
        }
        return fields
    
    def extract_features(self, field_data: Dict) -> Dict:
        """Extract features from field data for ML model"""
        features = {}
        
        # Basic field information
        field_name = field_data.get('name', '')
        tooltip = field_data.get('tooltip', '')
        persona = field_data.get('persona', '')
        domain = field_data.get('domain', '')
        
        # Text-based features from field name
        features['field_name_length'] = len(field_name)
        features['has_underscore'] = '_' in field_name
        features['has_number'] = bool(re.search(r'\d', field_name))
        features['has_part_prefix'] = bool(re.search(r'^Pt\d+', field_name))
        
        # Pattern matching features
        name_patterns = {
            'name_pattern': r'(name|given|family|middle|first|last)',
            'address_pattern': r'(address|street|city|state|zip|country)',
            'date_pattern': r'(date|birth|dob)',
            'employment_pattern': r'(employ|job|work|occupation)',
            'physical_pattern': r'(height|weight|eye|hair|color)',
            'id_pattern': r'(alien|number|id|ssn|receipt)',
        }
        
        for pattern_name, pattern in name_patterns.items():
            features[f'field_{pattern_name}'] = bool(re.search(pattern, field_name, re.IGNORECASE))
            if tooltip:
                features[f'tooltip_{pattern_name}'] = bool(re.search(pattern, tooltip, re.IGNORECASE))
        
        # Persona and domain features
        features['persona'] = persona or 'unknown'
        features['domain'] = domain or 'unknown'
        
        # Tooltip analysis
        if tooltip:
            features['tooltip_length'] = len(tooltip)
            features['tooltip_words'] = len(tooltip.split())
            features['tooltip_sentences'] = len(re.split(r'[.!?]', tooltip))
        else:
            features['tooltip_length'] = 0
            features['tooltip_words'] = 0
            features['tooltip_sentences'] = 0
        
        # Form context
        features['form_name'] = field_data.get('form', '')
        features['page_number'] = field_data.get('page', 0)
        
        return features
    
    def prepare_training_data(self, form_data: List[Dict]) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare training data from form field data"""
        logger.info("Preparing training data...")
        
        training_data = []
        labels = []
        text_features = []
        
        for field in form_data:
            # Try to map to collection field based on existing rules
            collection_field = self._predict_collection_field_rule_based(field)
            
            if collection_field:  # Only include fields that have rule-based mappings
                features = self.extract_features(field)
                training_data.append(features)
                labels.append(collection_field)
                
                # Add text features for this field
                tooltip = field.get('tooltip', '')
                field_name = field.get('name', '')
                combined_text = f"{field_name} {tooltip}"
                text_features.append(combined_text)
        
        logger.info(f"Found {len(training_data)} fields with rule-based mappings out of {len(form_data)} total fields")
        
        if len(training_data) == 0:
            logger.error("No training data available - no fields match rule-based patterns")
            return pd.DataFrame(), pd.Series([])
        
        # Convert to DataFrame
        df = pd.DataFrame(training_data)
        
        # Vectorize text features
        if text_features:
            text_vectors = self.text_vectorizer.fit_transform(text_features)
            text_df = pd.DataFrame(text_vectors.toarray(), 
                                 columns=[f'text_feature_{i}' for i in range(text_vectors.shape[1])])
            df = pd.concat([df, text_df], axis=1)
        
        # Encode categorical features properly
        categorical_cols = ['persona', 'domain', 'form_name']
        for col in categorical_cols:
            if col in df.columns:
                # Fill any NaN values
                df[col] = df[col].fillna('unknown')
                
                # Get the encoder for this column
                encoder_name = f'{col}_encoder'
                if hasattr(self, encoder_name):
                    encoder = getattr(self, encoder_name)
                    # Fit and transform the data
                    unique_values = df[col].unique()
                    encoder.fit(unique_values)
                    df[col] = encoder.transform(df[col])
                else:
                    # Create a simple mapping for unknown encoders
                    unique_values = df[col].unique()
                    value_map = {val: idx for idx, val in enumerate(unique_values)}
                    df[col] = df[col].map(value_map)
        
        return df, pd.Series(labels)
    
    def _predict_collection_field_rule_based(self, field_data: Dict) -> Optional[str]:
        """Use rule-based approach to predict collection field for training"""
        field_name = field_data.get('name', '').lower()
        tooltip = field_data.get('tooltip', '').lower()
        persona = field_data.get('persona', '')
        
        # Name patterns
        if re.search(r'(given|first).*name', field_name) or re.search(r'(given|first).*name', tooltip):
            return 'given_name'
        if re.search(r'(family|last|surname).*name', field_name) or re.search(r'(family|last|surname).*name', tooltip):
            return 'family_name'
        if re.search(r'middle.*name', field_name) or re.search(r'middle.*name', tooltip):
            return 'middle_name'
        
        # Full name pattern (for forms that ask for complete name)
        if re.search(r'full.*name', field_name) or re.search(r'full.*name', tooltip):
            return 'full_name'
        
        # Date patterns
        if re.search(r'(date.*birth|birth.*date|dob)', field_name) or re.search(r'(date.*birth|birth.*date|dob)', tooltip):
            return 'date_of_birth'
        
        # Address patterns
        if re.search(r'street.*address', field_name) or re.search(r'street.*address', tooltip):
            return 'current_address_street'
        if re.search(r'(^city|[^a-z]city)', field_name) or re.search(r'(^city|[^a-z]city)', tooltip):
            return 'current_address_city'
        if re.search(r'(^state|[^a-z]state)', field_name) or re.search(r'(^state|[^a-z]state)', tooltip):
            return 'current_address_state'
        if re.search(r'(zip|postal)', field_name) or re.search(r'(zip|postal)', tooltip):
            return 'current_address_zipcode'
        if re.search(r'country', field_name) or re.search(r'country', tooltip):
            return 'current_address_country'
        
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
        
        # Marriage information
        if re.search(r'(marriage|married)', field_name) or re.search(r'(marriage|married)', tooltip):
            return 'marriage_date'
        
        # Sex/Gender
        if re.search(r'(sex|gender|male|female)', field_name) or re.search(r'(sex|gender|male|female)', tooltip):
            return 'gender'
        
        # Yes/No questions (generic mapping based on persona and context)
        if re.search(r'(yes|no)', field_name) or re.search(r'(yes|no)', tooltip):
            if 'criminal' in tooltip or 'arrest' in tooltip or 'convicted' in tooltip:
                return 'criminal_history'
            elif 'medical' in tooltip or 'disease' in tooltip or 'health' in tooltip:
                return 'medical_history'
            elif 'marriage' in tooltip or 'married' in tooltip:
                return 'marital_status'
            
        return None
    
    def train(self, form_data: List[Dict], test_size: float = 0.2):
        """Train the ML model on form data"""
        logger.info("Training ML field mapper...")
        
        # Prepare training data
        X, y = self.prepare_training_data(form_data)
        
        if len(X) == 0:
            logger.error("No training data available")
            return
        
        # Encode labels
        self.collection_field_encoder.fit(y)
        y_encoded = self.collection_field_encoder.transform(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=test_size, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        
        # Convert back to original labels for reporting
        y_test_labels = self.collection_field_encoder.inverse_transform(y_test)
        y_pred_labels = self.collection_field_encoder.inverse_transform(y_pred)
        
        logger.info("Training complete!")
        logger.info(f"Training accuracy: {self.model.score(X_train, y_train):.3f}")
        logger.info(f"Test accuracy: {self.model.score(X_test, y_test):.3f}")
        
        print("\nClassification Report:")
        print(classification_report(y_test_labels, y_pred_labels))
        
        # Feature importance
        feature_names = X.columns.tolist()
        importance_scores = self.model.feature_importances_
        feature_importance = list(zip(feature_names, importance_scores))
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        print("\nTop 10 Most Important Features:")
        for feature, importance in feature_importance[:10]:
            print(f"{feature}: {importance:.3f}")
    
    def predict_collection_fields(self, form_data: List[Dict]) -> List[FieldMapping]:
        """Predict collection field mappings for form data"""
        if not self.is_trained:
            logger.error("Model not trained yet. Call train() first.")
            return []
        
        logger.info("Predicting collection field mappings...")
        
        mappings = []
        
        for field in form_data:
            features = self.extract_features(field)
            
            # Convert to DataFrame for prediction
            df = pd.DataFrame([features])
            
            # Add text features
            tooltip = field.get('tooltip', '')
            field_name = field.get('name', '')
            combined_text = f"{field_name} {tooltip}"
            
            try:
                text_vector = self.text_vectorizer.transform([combined_text])
                text_df = pd.DataFrame(text_vector.toarray(), 
                                     columns=[f'text_feature_{i}' for i in range(text_vector.shape[1])])
                df = pd.concat([df, text_df], axis=1)
            except:
                # Handle case where text vectorizer wasn't fitted
                pass
            
            # Encode categorical features
            categorical_cols = ['persona', 'domain', 'form_name']
            for col in categorical_cols:
                if col in df.columns:
                    try:
                        encoder = getattr(self, f'{col}_encoder')
                        df[col] = encoder.transform(df[col])
                    except:
                        # Handle unknown categories
                        df[col] = 0
            
            # Make prediction
            try:
                prediction = self.model.predict(df)[0]
                probabilities = self.model.predict_proba(df)[0]
                confidence = max(probabilities)
                
                collection_field = self.collection_field_encoder.inverse_transform([prediction])[0]
                
                mapping = FieldMapping(
                    form_field_id=field.get('name', ''),
                    form_name=field.get('form', ''),
                    collection_field=collection_field,
                    confidence=confidence,
                    persona=field.get('persona', ''),
                    context=field.get('tooltip', '')
                )
                
                mappings.append(mapping)
                
            except Exception as e:
                logger.warning(f"Could not predict for field {field.get('name', '')}: {e}")
        
        return mappings
    
    def generate_mapping_report(self, mappings: List[FieldMapping], output_file: str):
        """Generate a detailed mapping report"""
        logger.info(f"Generating mapping report to {output_file}")
        
        # Group by collection field
        by_collection = {}
        for mapping in mappings:
            if mapping.collection_field not in by_collection:
                by_collection[mapping.collection_field] = []
            by_collection[mapping.collection_field].append(mapping)
        
        # Generate report
        report = {
            'summary': {
                'total_mappings': len(mappings),
                'unique_collection_fields': len(by_collection),
                'high_confidence_mappings': len([m for m in mappings if m.confidence > 0.8]),
                'medium_confidence_mappings': len([m for m in mappings if 0.5 < m.confidence <= 0.8]),
                'low_confidence_mappings': len([m for m in mappings if m.confidence <= 0.5])
            },
            'mappings_by_collection_field': {}
        }
        
        for collection_field, field_mappings in by_collection.items():
            report['mappings_by_collection_field'][collection_field] = {
                'count': len(field_mappings),
                'description': self.collection_fields.get(collection_field, CollectionField('', '', '', [], '')).description,
                'mappings': [
                    {
                        'form_field': m.form_field_id,
                        'form_name': m.form_name,
                        'confidence': round(m.confidence, 3),
                        'persona': m.persona,
                        'context': m.context[:100] + '...' if len(m.context) > 100 else m.context
                    }
                    for m in sorted(field_mappings, key=lambda x: x.confidence, reverse=True)
                ]
            }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Mapping report saved to {output_file}")

def main():
    # Load the complete analysis data
    analysis_file = Path("model_analysis/results/run_20250604_085938/complete_analysis_20250604_085938.json")
    
    if not analysis_file.exists():
        logger.error(f"Analysis file not found: {analysis_file}")
        return
    
    with open(analysis_file, 'r') as f:
        data = json.load(f)
    
    # Data is already a list of field objects
    all_fields = data
    
    logger.info(f"Loaded {len(all_fields)} fields")
    
    # Initialize and train the mapper
    mapper = MLFieldMapper()
    mapper.train(all_fields)
    
    # Generate predictions
    mappings = mapper.predict_collection_fields(all_fields)
    
    # Generate report
    output_file = f"model_analysis/ml_field_mappings_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
    mapper.generate_mapping_report(mappings, output_file)
    
    # Save mappings as CSV for easy review
    csv_file = output_file.replace('.json', '.csv')
    mappings_df = pd.DataFrame([
        {
            'form_field': m.form_field_id,
            'form_name': m.form_name,
            'collection_field': m.collection_field,
            'confidence': m.confidence,
            'persona': m.persona,
            'context': m.context
        }
        for m in mappings
    ])
    mappings_df.to_csv(csv_file, index=False)
    
    logger.info(f"Mappings saved to {csv_file}")
    
    # Print summary
    print(f"\nML Field Mapping Complete!")
    print(f"Total mappings: {len(mappings)}")
    print(f"High confidence (>80%): {len([m for m in mappings if m.confidence > 0.8])}")
    print(f"Medium confidence (50-80%): {len([m for m in mappings if 0.5 < m.confidence <= 0.8])}")
    print(f"Low confidence (<50%): {len([m for m in mappings if m.confidence <= 0.5])}")

if __name__ == "__main__":
    main() 