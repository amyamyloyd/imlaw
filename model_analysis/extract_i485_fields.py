#!/usr/bin/env python3

"""
Script to extract field data specifically from i485.pdf for rule testing.
"""

import os
import json
import logging
from datetime import datetime
from PyPDF2 import PdfReader
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class I485FieldExtractor:
    def __init__(self):
        self.forms_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uscis_forms'))
        self.i485_path = os.path.join(self.forms_dir, 'i485.pdf')
        
    def _extract_screen_label(self, tooltip: str, field_type: str = None) -> str:
        """Extract screen label from tooltip - last two sentences for buttons, last sentence for text."""
        if not tooltip:
            return None
        sentences = re.split(r'[.!?]\s+', tooltip.strip())
        sentences = [s for s in sentences if s.strip()]
        if not sentences:
            return None
        
        # For buttons (/Btn), use last two sentences if available
        if field_type == '/Btn' and len(sentences) >= 2:
            screen_label = '. '.join(sentences[-2:]).strip()
        else:
            # For text fields or single sentence, use last sentence
            screen_label = sentences[-1].strip()
        
        # Remove common instruction prefixes
        prefixes = [
            'Enter', 'Select', 'Type', 'Choose', 'Provide', 'Indicate',
            'Check', 'Fill in', 'Write', 'Specify'
        ]
        for prefix in prefixes:
            pattern = f'^{prefix}\\s+'
            screen_label = re.sub(pattern, '', screen_label, flags=re.IGNORECASE)
        
        return screen_label.strip() or None

    def _extract_text_value(self, field_id: str) -> str:
        """Extract value from field name like 'Pt2Line10_State[0]' -> 'State'"""
        # Match pattern like _ValueName[0] at the end
        match = re.search(r'_([^_\[]+)\[\d+\]$', field_id)
        if match:
            return match.group(1)
        
        # Fallback: try to extract after last underscore before bracket
        match = re.search(r'_([^_]+)$', field_id.split('[')[0])
        if match:
            return match.group(1)
            
        return None

    def _extract_btn_value(self, field_id: str, tooltip: str = None) -> dict:
        value_info = {
            'type': 'selection',
            'value': None
        }
        
        # First try to extract value from field name (like _Yes[0] or _Male[0])
        match = re.search(r'_([^_\[]+)\[\d+\]$', field_id)
        if match:
            value_info['value'] = match.group(1)
        
        # If we have tooltip and no value yet, try to extract from tooltip
        if not value_info['value'] and tooltip:
            sentences = re.split(r'[.!?]\s+', tooltip.strip())
            sentences = [s for s in sentences if s.strip()]
            if len(sentences) >= 2:
                value_info['value'] = '. '.join(sentences[-2:]).strip()
            elif sentences:
                value_info['value'] = sentences[-1].strip()
        
        # If still no value, try fallback patterns from field name
        if not value_info['value']:
            # Try to extract after last underscore
            parts = field_id.split('_')
            if len(parts) > 1:
                last_part = parts[-1].split('[')[0]  # Remove [0] suffix
                if last_part:
                    value_info['value'] = last_part
                    
        return value_info

    def extract_field_data(self, field, page_num=None) -> dict:
        """Extract all relevant data from a field"""
        data = {
            'name': field['/T'],
            'page': page_num,
            'type': field.get('/FT', 'Unknown'),
            'persona': None,  # To be determined by rules
            'domain': None,   # To be determined by rules
            'value_info': None,
            'screen_label': None,
            'tooltip': None,
            'hierarchy': {
                'parent_name': None,
                'parent_type': None,
                'children': []
            },
            'form': 'i485.pdf'
        }
        
        # Extract parent field information
        if '/Parent' in field:
            parent = field['/Parent']
            if '/T' in parent:
                parent_name = parent['/T']
                data['hierarchy']['parent_name'] = parent_name
                data['hierarchy']['parent_type'] = parent.get('/FT', 'Unknown')
                
        # Extract tooltip if available
        tooltip = field.get('/TU', None)
        data['tooltip'] = tooltip
        
        # Extract screen label from tooltip using field type
        if tooltip:
            data['screen_label'] = self._extract_screen_label(tooltip, data['type'])
        
        # Extract value info based on field type
        if data['type'] == '/Btn':
            # For buttons, extract value from tooltip or field name
            data['value_info'] = self._extract_btn_value(data['name'], tooltip)
            
            # If no screen label but we have a value, use it as screen label
            if not data['screen_label'] and data['value_info'].get('value'):
                if isinstance(data['value_info']['value'], bool):
                    data['screen_label'] = 'Yes' if data['value_info']['value'] else 'No'
                else:
                    data['screen_label'] = str(data['value_info']['value'])
                    
        elif data['type'] == '/Tx':
            # For text fields, extract value from field name
            parsed_value = self._extract_text_value(data['name'])
            if parsed_value:
                data['value_info'] = {"type": "text", "value": parsed_value}
            
        return data

    def extract_i485_fields(self) -> dict:
        """Extract all fields from i485.pdf"""
        logger.info(f"Starting extraction from: {self.i485_path}")
        
        if not os.path.exists(self.i485_path):
            logger.error(f"File not found: {self.i485_path}")
            return {}
            
        try:
            reader = PdfReader(self.i485_path)
            fields = {}
            
            for page_num, page in enumerate(reader.pages):
                if '/Annots' in page:
                    annotations = page['/Annots']
                    if annotations is not None:
                        for annotation in annotations:
                            if annotation.get_object()['/Subtype'] == '/Widget':
                                field = annotation.get_object()
                                if '/T' in field:
                                    field_name = field['/T']
                                    field_data = self.extract_field_data(field, page_num)
                                    fields[field_name] = field_data
            
            logger.info(f"Extracted {len(fields)} fields from i485.pdf")
            return fields
            
        except Exception as e:
            logger.error(f"Error extracting fields from {self.i485_path}: {str(e)}")
            return {}

def main():
    extractor = I485FieldExtractor()
    fields = extractor.extract_i485_fields()
    
    # Save to timestamped file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i485_extraction")
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"i485_fields_{timestamp}.json")
    
    with open(output_file, "w") as f:
        json.dump(fields, f, indent=2)
    
    print(f"I-485 fields extracted to: {output_file}")
    print(f"Total fields: {len(fields)}")

if __name__ == "__main__":
    main() 