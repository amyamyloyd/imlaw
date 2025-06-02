"""
Script to analyze patterns in form fields and suggest mappings.
Uses ML features to detect field relationships, contexts, and temporal relationships.
"""

import os
import json
import re
import logging
from collections import defaultdict
from typing import Dict, List, Any, Tuple

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class FormPatternAnalyzer:
    def __init__(self):
        self.forms_dir = "/Users/claudiapitts/imlaw/Imlaw/generalscripts/field_analysis"
        
        # Enhanced context keywords
        self.context_markers = {
            'subject': {
                'client': ['your', 'you', 'applicant', 'I am', 'I have', 'my'],
                'spouse': ['spouse', 'husband', 'wife', 'marriage partner'],
                'child': ['child', 'son', 'daughter'],
                'parent': ['father', 'mother', 'parent'],
                'sibling': ['brother', 'sister', 'sibling'],
                'employer': ['employer', 'company', 'organization'],
                'representative': ['attorney', 'lawyer', 'representative', 'preparer', 'interpreter']
            },
            'temporal': {
                'current': ['current', 'present', 'now', 'existing', 'this time'],
                'past': ['previous', 'former', 'past', 'prior', 'last', 'history'],
                'future': ['intended', 'planned', 'will', 'future']
            },
            'info_type': {
                'personal': ['name', 'birth', 'gender', 'marital', 'race', 'ethnicity'],
                'contact': ['address', 'phone', 'email', 'residence'],
                'identity': ['ssn', 'alien', 'passport', 'id number'],
                'employment': ['job', 'work', 'employer', 'occupation', 'income'],
                'education': ['school', 'degree', 'education'],
                'travel': ['travel', 'trip', 'journey', 'visited'],
                'medical': ['health', 'medical', 'doctor', 'condition']
            }
        }

    def extract_field_context(self, field: Dict) -> Dict[str, str]:
        """
        Extract comprehensive context from a field including:
        - Who the information is about (subject)
        - When the information applies (temporal)
        - What type of information it is (info_type)
        - Whether it's likely part of repeated information
        """
        # Combine all text sources for analysis
        field_text = ' '.join(filter(None, [
            field.get('name', ''),
            field.get('tooltip', ''),
            field.get('label', ''),  # We'll need to extract this from the PDF
            field.get('partial_name', ''),
            str(field.get('page_label', ''))  # We'll need to extract this from the PDF
        ])).lower()

        context = {
            'subject': 'unknown',
            'temporal': 'unknown',
            'info_type': 'unknown',
            'is_repeated': False
        }

        # Determine subject
        for subject, keywords in self.context_markers['subject'].items():
            if any(keyword in field_text for keyword in keywords):
                context['subject'] = subject
                break

        # Determine temporal context
        for temporal, keywords in self.context_markers['temporal'].items():
            if any(keyword in field_text for keyword in keywords):
                context['temporal'] = temporal
                break

        # Determine information type
        for info_type, keywords in self.context_markers['info_type'].items():
            if any(keyword in field_text for keyword in keywords):
                context['info_type'] = info_type
                break

        # Check for repeated information patterns
        repeated_patterns = [
            r'previous.*address',
            r'other.*names',
            r'former.*employer',
            r'additional.*family',
            r'other.*residence',
            r'previous.*employment'
        ]
        context['is_repeated'] = any(re.search(pattern, field_text) for pattern in repeated_patterns)

        return context

    def analyze_field_patterns(self, fields: List[Dict], form_data: Dict) -> Dict[str, List]:
        """Analyze fields for common patterns with enhanced context."""
        patterns = defaultdict(list)
        
        # First pass: Group fields by their structural relationships
        field_groups = self._group_related_fields(fields)
        
        # Second pass: Analyze each group with context
        for group_type, field_group in field_groups.items():
            for group in field_group:
                group_fields = []
                group_context = defaultdict(set)
                
                for field in group['fields']:
                    # Extract rich context
                    context = self.extract_field_context(field)
                    
                    # Add to group analysis with tooltip
                    field_data = {
                        'name': field['name'],
                        'context': context,
                        'page': field.get('page'),
                        'type': field.get('type'),
                        'tooltip': field.get('tooltip', '')  # Include tooltip in output
                    }
                    group_fields.append(field_data)
                    
                    # Aggregate group context
                    group_context['subjects'].add(context['subject'])
                    group_context['temporal'].add(context['temporal'])
                    group_context['info_types'].add(context['info_type'])
                
                # Convert sets to lists for JSON serialization
                serializable_context = {
                    'subjects': list(group_context['subjects']),
                    'temporal': list(group_context['temporal']),
                    'info_types': list(group_context['info_types'])
                }
                
                # Add analyzed group to patterns
                patterns[group_type].append({
                    'fields': group_fields,
                    'group_context': serializable_context,
                    'suggestion': self._generate_suggestion(group_type, serializable_context),
                    'action_needed': self._determine_action_needed(group_type, serializable_context)
                })
        
        return patterns

    def _group_related_fields(self, fields: List[Dict]) -> Dict[str, List]:
        """Group fields based on structural relationships."""
        groups = defaultdict(list)
        
        # Group by parent-child relationships
        parent_groups = defaultdict(list)
        for field in fields:
            parent = field.get('hierarchy', {}).get('parent_name')
            if parent:
                parent_groups[parent].append(field)

        # Analyze each parent group
        for parent, group in parent_groups.items():
            self._categorize_field_group(group, groups)

        return groups

    def _categorize_field_group(self, fields: List[Dict], groups: Dict):
        """Categorize a group of related fields."""
        # Check for name components
        name_fields = [f for f in fields if any(x in f['name'] for x in ['GivenName', 'FamilyName', 'MiddleName'])]
        if name_fields:
            groups['name_groups'].append({
                'type': 'name',
                'fields': name_fields
            })

        # Check for address components
        addr_fields = [f for f in fields if any(x in f['name'] for x in ['Street', 'City', 'State', 'ZIP', 'Country'])]
        if addr_fields:
            groups['address_groups'].append({
                'type': 'address',
                'fields': addr_fields
            })

        # Check for date series
        date_fields = [f for f in fields if 'Date' in f['name']]
        if len(date_fields) > 1:
            groups['date_series'].append({
                'type': 'date_series',
                'fields': date_fields
            })

        # Check for enumeration groups (radio/checkbox)
        enum_fields = [f for f in fields if f.get('type') == '/Btn']
        if len(enum_fields) > 1:
            groups['enum_groups'].append({
                'type': 'enumeration',
                'fields': enum_fields
            })

    def _generate_suggestion(self, group_type: str, context: Dict) -> str:
        """Generate mapping suggestions based on group type and context."""
        subjects = context['subjects']
        temporal = context['temporal']
        info_types = context['info_types']
        
        suggestion = f"Map as {group_type} for "
        
        if len(subjects) == 1:
            subject = next(iter(subjects))
            suggestion += f"{subject}'s "
        else:
            suggestion += "multiple subjects' "
            
        if len(info_types) == 1:
            info_type = next(iter(info_types))
            suggestion += f"{info_type} information"
        else:
            suggestion += "mixed information"
            
        if len(temporal) == 1:
            temp = next(iter(temporal))
            if temp != 'unknown':
                suggestion += f" ({temp})"
                
        return suggestion

    def _determine_action_needed(self, group_type: str, context: Dict) -> List[str]:
        """Determine required actions based on group analysis."""
        actions = []
        
        if 'unknown' in context['subjects']:
            actions.append("Verify subject relationship")
            
        if len(context['subjects']) > 1:
            actions.append("Resolve multiple subject references")
            
        if 'unknown' in context['temporal']:
            actions.append("Clarify temporal context")
            
        if group_type == 'enum_groups':
            actions.append("Define allowed values")
            
        return actions

    def analyze_forms(self):
        """Analyze all forms and generate pattern report."""
        logger.info("Starting enhanced pattern analysis...")
        
        # Load the complete analysis
        analysis_file = os.path.join(self.forms_dir, "complete_analysis.json")
        with open(analysis_file) as f:
            all_forms_data = json.load(f)
        
        results = {}
        
        for form_name, form_data in all_forms_data.items():
            logger.info(f"Analyzing patterns in {form_name}")
            
            # Analyze patterns with enhanced context
            patterns = self.analyze_field_patterns(form_data['fields'], form_data)
            
            results[form_name] = {
                'patterns': patterns,
                'form_metadata': {
                    'total_fields': len(form_data['fields']),
                    'pages': len(form_data.get('pages', [])),
                    'has_outlines': bool(form_data.get('outline'))
                }
            }
        
        # Save results
        output_file = os.path.join(self.forms_dir, "pattern_analysis.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info(f"Enhanced pattern analysis saved to: {output_file}")

if __name__ == '__main__':
    analyzer = FormPatternAnalyzer()
    analyzer.analyze_forms() 