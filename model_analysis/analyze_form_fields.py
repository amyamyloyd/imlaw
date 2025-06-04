#!/usr/bin/env python3

"""
Script to extract field data and additional metadata from immigration PDF forms.
"""

import os
import json
import logging
from datetime import datetime
from PyPDF2 import PdfReader
import re
from typing import Dict, List, Set, Tuple
import csv

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Define personas and their codes
PERSONAS = {
    'APP': 'applicant',           # Person filing the form
    'BEN': 'beneficiary',         # Person benefiting from the application
    'FAM': 'family_member',       # Family member of applicant
    'PRE': 'preparer',           # Person helping fill out the form
    'ATT': 'attorney',           # Attorney or accredited representative
    'INT': 'interpreter',        # Person who translated for applicant
    'EMP': 'employer',           # Current or prospective employer
    'PHY': 'physician',          # Medical professional (for I-693)
    'SPO': 'sponsor'             # Financial sponsor (for I-864)
}

# Form-specific part mappings
FORM_PART_MAPPINGS = {
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
    },
    'i130.pdf': {
        'Pt1': 'applicant',      # Relationship
        'Pt2': 'applicant',      # Information About You
        'Pt3': 'beneficiary',    # Information About Beneficiary
        'Pt4': 'beneficiary',    # Other Information
        'Pt5': 'applicant',      # Petitioner's Statement, Contact Information
        'Pt6': 'interpreter',    # Interpreter's Contact Information
        'Pt7': 'preparer',       # Contact Information, Declaration, and Signature of the Person Preparing this Petition
    },
    'i765.pdf': {
        'Pt1': 'applicant',      # Reason for Applying
        'Pt2': 'applicant',      # Information About You
        'Pt3': 'applicant',      # Biographic Information
        'Pt4': 'applicant',      # Your Contact Information
        'Pt5': 'applicant',      # Applicant's Statement and Signature
        'Pt6': 'interpreter',    # Interpreter's Contact Information
        'Pt7': 'preparer',       # Contact Information, Declaration, and Signature of the Person Preparing this Application
    },
    'i693.pdf': {
        'Pt1': 'applicant',      # Information About You
        'Pt2': 'physician',      # Civil Surgeon's Contact Information
        'Pt3': 'applicant',      # Applicant's Identification Information
        'Pt4': 'applicant',      # Medical Examination (Changed from physician to applicant - it's the applicant's medical info)
        'Pt5': 'physician',      # Civil Surgeon's Declaration
        'Pt6': 'interpreter',    # Interpreter's Contact Information
        'Pt7': 'preparer',       # Contact Information, Declaration, and Signature of the Person Preparing this Form
    }
}

# Form structure fields that don't need personas
FORM_STRUCTURE_PATTERNS = [
    r'^#subform\[\d+\]$',
    r'^#pageSet\[\d+\]$', 
    r'^#area\[\d+\]$',
    r'^form1\[\d+\]$',
    r'^Page\d+\[\d+\]$',
    r'^PDF417BarCode2\[\d+\]$',
    r'^sfTable\[\d+\]$'
]

# Personal information field patterns that indicate applicant
PERSONAL_INFO_PATTERNS = [
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
MEDICAL_PATTERNS = [
    r'^Pt\d+Line\d+_(Medical|Health|Exam|Vaccine|Test|Treatment|Diagnosis|Doctor|Physician)',
    r'CompleteSeries',
    r'Immunization',
    r'MedicalExam',
    r'HealthScreening'
]

# Domain/category patterns for field classification
DOMAIN_PATTERNS = {
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

class FormFieldAnalyzer:
    def __init__(self):
        # Use uscis_forms at the project root for PDF forms
        self.forms_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uscis_forms'))
        self.target_forms = ['i485.pdf', 'i130.pdf', 'i765.pdf', 'i693.pdf']
        self.output_dir = None
        
        # Add office/administrative patterns to preparer persona
        self.persona_patterns = {
            'preparer': [
                r'preparer[\'s]?\s',  # Must have space after to avoid matching other fields
                r'person\swho\sprepared',
                r'prepared\sthis\s(?:form|application)',
                r'contact\sinformation.*person\spreparing',
                r'^office\s(?:use|only)',  # Must start with 'office'
                r'^uscis\soffice',  # Must start with 'uscis office'
                r'^administrative',  # Must start with 'administrative'
                r'^receipt',  # Must start with 'receipt'
                r'^filing',  # Must start with 'filing'
                r'^processing',  # Must start with 'processing'
                r'^action\sblock',  # Must start with 'action block'
                r'^for\sofficial\suse',  # Must start with 'for official use'
                r'^agency\suse'  # Must start with 'agency use'
            ],
            'applicant': [
                r'applicant[\'s]?', 
                r'your\s', 
                r'you[r]?\s(?:are|have|were)',
                r'information\sabout\syou',
                r'your\sbiographic\sinformation',
                r'your\scontact\sinformation'
            ],
            'beneficiary': [
                r'(?:information|details)\s+about\s+(?:the\s+)?beneficiary',
                r'beneficiary[\'s]?\s+(?:name|information|details)',
                r'person\s+for\s+whom\s+you\s+are\s+filing',
                r'alien\s+beneficiary',
                r'sponsored\s+beneficiary'
            ],
            'family_member': [
                r'spouse',
                r'husband',
                r'wife',
                r'child(?:ren)?',
                r'son',
                r'daughter',
                r'parent',
                r'father',
                r'mother',
                r'sibling',
                r'brother',
                r'sister',
                r'family\s+member',
                r'relative',
                r'dependent',
                r'household\s+member'
            ],
            'attorney': [
                r'attorney[\'s]?',
                r'lawyer[\'s]?',
                r'legal\srepresentative',
                r'accredited\srepresentative',
                r'g-28'
            ],
            'interpreter': [
                r'interpreter[\'s]?',
                r'person\swho\sinterpreted',
                r'translated\sfor\syou',
                r'interpreter\'s\scontact\sinformation'
            ],
            'employer': [
                r'employer[\'s]?',
                r'company[\'s]?',
                r'business[\'s]?',
                r'organization[\'s]?',
                r'employment\sauthorization'
            ],
            'physician': [
                r'physician[\'s]?',
                r'doctor[\'s]?',
                r'medical\s(?:examiner|professional)',
                r'civil\ssurgeon',
                r'medical\sexamination\sresults',
                r'physician\'s\s(?:signature|declaration|certification)',
                r'doctor\'s\s(?:signature|declaration|certification)'
            ],
            'sponsor': [
                r'sponsor[\'s]?',
                r'person\sproviding\sfinancial\ssupport',
                r'financial\ssponsor',
                r'affidavit\sof\ssupport'
            ]
        }

    def _is_form_structure_field(self, field_id: str) -> bool:
        """Check if field is a form structure field that doesn't need a persona"""
        return any(re.match(pattern, field_id) for pattern in FORM_STRUCTURE_PATTERNS)

    def _is_personal_info_field(self, field_id: str) -> bool:
        """Check if field contains personal information about the applicant"""
        logger.debug(f"Checking if field {field_id} is a personal info field")
        for pattern in PERSONAL_INFO_PATTERNS:
            if re.search(pattern, field_id, re.IGNORECASE):
                logger.debug(f"Field {field_id} matches pattern {pattern}")
                return True
            logger.debug(f"Field {field_id} does not match pattern {pattern}")
        return False

    def _is_medical_field(self, field_id: str) -> bool:
        """Check if field contains medical information about the applicant"""
        return any(re.match(pattern, field_id) for pattern in MEDICAL_PATTERNS)

    def _get_form_part_persona(self, form_name: str, field_id: str) -> str:
        """Determine persona based on form part number from field ID."""
        if form_name not in FORM_PART_MAPPINGS:
            return None
            
        # Extract part number (e.g., "Pt1" from "Pt1Line1b_GivenName")
        part_match = re.match(r'Pt(\d+)', field_id)
        if not part_match:
            return None
            
        part_num = f"Pt{part_match.group(1)}"
        return FORM_PART_MAPPINGS[form_name].get(part_num)

    def _extract_persona(self, field_id: str, tooltip: str = None, parent_field: Dict = None) -> str:
        """Extract persona from field context"""
        # Volag override
        if (field_id and 'volag' in field_id.lower()) or (tooltip and 'volag' in tooltip.lower()):
            return 'preparer'
        if not tooltip:
            return None
        ttip = tooltip.lower()
        # 1. Beneficiary
        if 'beneficiary' in ttip:
            return 'beneficiary'
        # 2. Family Member (child)
        if 'your child' in ttip or 'your children' in ttip:
            return 'family_member'
        # 3. Spouse
        if 'spouse' in ttip:
            return 'spouse'
        # 4. Parent
        if 'father' in ttip or 'mother' in ttip or 'parent' in ttip:
            return 'parent'
        # 5. Preparer
        if 'preparer' in ttip:
            return 'preparer'
        # 6. Employer
        if 'employer' in ttip:
            return 'employer'
        # 7. Applicant
        if (('applicant' in ttip or 'you' in ttip or 'your' in ttip) and
            not any(x in ttip for x in ['your child', 'your children', 'spouse', 'parent', 'father', 'mother', 'beneficiary', 'employer', 'preparer'])):
            return 'applicant'
        # 8. Family (general)
        if 'family' in ttip and not any(x in ttip for x in ['beneficiary', 'spouse', 'parent', 'father', 'mother']):
            return 'family'
        return None

    def _extract_domain(self, field_id: str, tooltip: str = None, persona: str = None) -> str:
        """Extract domain/category from field context"""
        # Volag override
        if (field_id and 'volag' in field_id.lower()) or (tooltip and 'volag' in tooltip.lower()):
            return 'office'
        # Attorney/Preparer override
        if persona in ['attorney', 'preparer']:
            return 'office'
        # Lawful override
        if (field_id and 'lawful' in field_id.lower()) or (tooltip and 'lawful' in tooltip.lower()):
            if persona == 'applicant':
                return 'personal'
            if persona in ['attorney', 'preparer']:
                return 'office'
        # Inadmissibility override
        if (field_id and 'inadmissibility' in field_id.lower()) or (tooltip and 'inadmissibility' in tooltip.lower()):
            return 'criminal'
        # Lawful Permanent Resident override
        if (field_id and (('lawful permanent resident' in field_id.lower()) or ('lpr' in field_id.lower()))) or \
           (tooltip and (('lawful permanent resident' in tooltip.lower()) or ('lpr' in tooltip.lower()))):
            return 'personal'
        # Address/Street override (never medical)
        if (field_id and (('address' in field_id.lower()) or ('street' in field_id.lower()))) or \
           (tooltip and (('address' in tooltip.lower()) or ('street' in tooltip.lower()))):
            return 'personal'
        
        # Skip domain assignment for form structure fields
        if self._is_form_structure_field(field_id):
            return None
            
        # If persona is preparer or field is a form structure field, default to office
        if persona == 'preparer' or self._is_form_structure_field(field_id):
            return 'office'
            
        # Check field ID and tooltip against domain patterns
        for domain, patterns in DOMAIN_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, field_id, re.IGNORECASE):
                    # Don't assign office domain unless it's explicitly an office field and persona is preparer
                    if domain == 'office' and persona != 'preparer':
                        continue
                    return domain
                if tooltip and re.search(pattern, tooltip, re.IGNORECASE):
                    if domain == 'office' and persona != 'preparer':
                        continue
                    return domain
        
        # For non-preparer personas, default to personal domain instead of office
        if persona != 'preparer':
            return 'personal'
        
        return 'office'

    def _extract_screen_label(self, tooltip: str, domain: str = None) -> str:
        """Extract screen label from tooltip's last sentence, or last two for criminal domain."""
        if not tooltip:
            return None
        sentences = re.split('[.!?]\s+', tooltip.strip())
        sentences = [s for s in sentences if s.strip()]
        if not sentences:
            return None
        if domain == 'criminal' and len(sentences) >= 2:
            return '. '.join(sentences[-2:]).strip()
        # Remove common instruction prefixes from the last sentence
        last_sentence = sentences[-1]
        prefixes = [
            'Enter', 'Select', 'Type', 'Choose', 'Provide', 'Indicate',
            'Check', 'Fill in', 'Write', 'Specify'
        ]
        for prefix in prefixes:
            pattern = f'^{prefix}\s+'
            last_sentence = re.sub(pattern, '', last_sentence, flags=re.IGNORECASE)
        return last_sentence.strip() or None

    def _extract_text_value(self, field_id: str) -> str:
        match = re.search(r'_([^_\[]+)\[\d+\]$', field_id)
        if match:
            return match.group(1)
        return None

    def _extract_btn_value(self, field_id: str, tooltip: str = None) -> dict:
        value_info = {
            'type': 'selection',
            'value': None
        }
        # Try to extract last two sentences from tooltip
        if tooltip:
            sentences = re.split(r'[.!?]\s+', tooltip.strip())
            sentences = [s for s in sentences if s.strip()]
            if len(sentences) >= 2:
                value_info['value'] = '. '.join(sentences[-2:]).strip()
            elif sentences:
                value_info['value'] = sentences[-1].strip()
        # Fallback to value from field name
        if not value_info['value']:
            match = re.search(r'_([^_\[]+)\[\d+\]$', field_id)
            if match:
                value_info['value'] = match.group(1)
        return value_info

    def extract_field_data(self, field, page_num=None) -> dict:
        """Extract all relevant data from a field"""
        data = {
            'name': field['/T'],
            'page': page_num,
            'type': field.get('/FT', 'Unknown'),
            'persona': None,
            'domain': None,
            'value_info': None,
            'screen_label': None,
            'tooltip': None,  # Store the raw tooltip
            'hierarchy': {
                'parent_name': None,
                'parent_type': None,
                'children': []
            }
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
        
        # Extract screen label from tooltip's last sentence
        if tooltip:
            data['screen_label'] = self._extract_screen_label(tooltip, data['domain'])
        
        # Extract persona
        data['persona'] = self._extract_persona(data['name'], tooltip)
        
        # Extract domain (now passing persona)
        data['domain'] = self._extract_domain(data['name'], tooltip, data['persona'])
        
        # Extract value info for buttons/checkboxes
        if data['type'] == '/Btn':
            data['value_info'] = self._extract_btn_value(data['name'], tooltip)
            
            # If no screen label but we have a value, use it as screen label
            if not data['screen_label'] and data['value_info']['value']:
                if isinstance(data['value_info']['value'], bool):
                    data['screen_label'] = 'Yes' if data['value_info']['value'] else 'No'
                else:
                    data['screen_label'] = str(data['value_info']['value'])
        elif data['type'] == '/Tx':
            parsed_value = self._extract_text_value(data['name'])
            if parsed_value:
                data['value_info'] = {"type": "text", "value": parsed_value}
            
        return data

    def extract_document_metadata(self, pdf_reader) -> dict:
        """Extract document-level metadata."""
        metadata = {}
        
        # Basic document info
        info = pdf_reader.metadata
        if info:
            metadata['document_info'] = dict(info)
        
        # Get PDF version
        metadata['pdf_version'] = pdf_reader.pdf_header
        
        # Get encryption info
        metadata['is_encrypted'] = pdf_reader.is_encrypted
        
        return metadata

    def extract_outline_data(self, pdf_reader) -> list:
        """Extract outline/bookmark structure."""
        outlines = []
        try:
            outline_list = pdf_reader.outline
            if outline_list:
                for item in outline_list:
                    if isinstance(item, list):
                        # Handle nested outlines
                        outlines.extend(self._process_outline_item(item))
                    else:
                        outlines.append(self._process_outline_item(item))
        except Exception as e:
            logger.warning(f"Could not extract outline data: {e}")
        return outlines

    def _process_outline_item(self, item) -> dict:
        """Process a single outline/bookmark item with detailed properties."""
        if isinstance(item, list):
            return [self._process_outline_item(i) for i in item]
        
        outline_data = {}
        try:
            # Basic properties
            if hasattr(item, '/Title'):
                outline_data['title'] = str(item['/Title'])
            if hasattr(item, '/Dest'):
                outline_data['destination'] = str(item['/Dest'])
            
            # Action and destination details
            if '/A' in item:
                action = item['/A']
                if '/D' in action:
                    dest = action['/D']
                    if isinstance(dest, list):
                        outline_data['zoom'] = dest[1] if len(dest) > 1 else None
                        outline_data['page_number'] = dest[0] if len(dest) > 0 else None
            
            # Color and style properties
            if '/C' in item:  # Color array [R G B]
                outline_data['color'] = [float(x) for x in item['/C']]
            if '/F' in item:  # Style flags
                flags = int(item['/F'])
                outline_data['style'] = {
                    'italic': bool(flags & 1),
                    'bold': bool(flags & 2)
                }
            
            # Structure information
            if '/First' in item:
                outline_data['has_children'] = True
            if '/Parent' in item:
                outline_data['has_parent'] = True
            if '/Next' in item:
                outline_data['has_next'] = True
            if '/Prev' in item:
                outline_data['has_prev'] = True
            
        except Exception as e:
            logger.warning(f"Error processing outline item: {e}")
        return outline_data

    def extract_page_data(self, page, page_num) -> dict:
        """Extract detailed page-level metadata."""
        page_data = {
            'page_number': page_num,
            'rotation': page.get('/Rotate', 0),
            'dimensions': {
                'media_box': [float(x) for x in page.mediabox] if hasattr(page, 'mediabox') else None,
                'crop_box': [float(x) for x in page.cropbox] if hasattr(page, 'cropbox') else None,
                'bleed_box': [float(x) for x in page.get('/BleedBox', [])] if '/BleedBox' in page else None,
                'trim_box': [float(x) for x in page.get('/TrimBox', [])] if '/TrimBox' in page else None,
                'art_box': [float(x) for x in page.get('/ArtBox', [])] if '/ArtBox' in page else None
            }
        }

        # Extract resources
        if '/Resources' in page:
            resources = page['/Resources']
            page_data['resources'] = {}
            
            # Font information
            if '/Font' in resources:
                fonts = resources['/Font']
                page_data['resources']['fonts'] = []
                for font_key, font in fonts.items():
                    try:
                        font_info = {
                            'name': str(font_key),
                            'type': str(font.get('/Subtype', '')),
                            'base_font': str(font.get('/BaseFont', ''))
                        }
                        page_data['resources']['fonts'].append(font_info)
                    except:
                        continue

            # Image and XObject information
            if '/XObject' in resources:
                xobjects = resources['/XObject']
                page_data['resources']['xobjects'] = []
                for xobj_key, xobj in xobjects.items():
                    try:
                        if xobj.get('/Subtype') == '/Image':
                            image_info = {
                                'name': str(xobj_key),
                                'width': int(xobj.get('/Width', 0)),
                                'height': int(xobj.get('/Height', 0)),
                                'bits_per_component': int(xobj.get('/BitsPerComponent', 0)),
                                'color_space': str(xobj.get('/ColorSpace', ''))
                            }
                            page_data['resources']['xobjects'].append(image_info)
                    except:
                        continue

        # Extract annotations (excluding form fields which we handle separately)
        if '/Annots' in page:
            try:
                annotations = page['/Annots']
                page_data['annotations'] = []
                for annot in annotations:
                    if hasattr(annot, "get_object"):
                        annot = annot.get_object()
                    if annot.get('/Subtype') != '/Widget':  # Skip form fields
                        try:
                            annot_data = {
                                'type': str(annot.get('/Subtype', '')),
                                'rect': [float(x) for x in annot['/Rect']] if '/Rect' in annot else None,
                                'contents': str(annot.get('/Contents', '')),
                                'color': [float(x) for x in annot['/C']] if '/C' in annot else None
                            }
                            page_data['annotations'].append(annot_data)
                        except:
                            continue
            except Exception as e:
                logger.warning(f"Error processing annotations: {e}")

        return page_data

    def analyze_form(self, form_path: str, form_name: str = None) -> Dict:
        """Analyze all fields in a form"""
        logger.info(f"Starting analysis of form: {form_path}")
        try:
            reader = PdfReader(form_path)
            form_fields = {}
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
                                    # Add form name to each field record
                                    field_data['form'] = form_name if form_name else os.path.basename(form_path)
                                    form_fields[field_name] = field_data
            return form_fields
        except Exception as e:
            logger.error(f"Error analyzing form {form_path}: {str(e)}")
            return {}

    def analyze_all_forms(self, forms_dir: str) -> Dict:
        """Analyze all PDF forms in the specified directory"""
        logger.info("Starting analysis of all forms...")
        all_forms_data = {}
        for form_file in os.listdir(forms_dir):
            if form_file.endswith('.pdf'):
                logger.info(f"Analyzing form: {form_file}")
                form_path = os.path.join(forms_dir, form_file)
                form_data = self.analyze_form(form_path, form_name=form_file)
                all_forms_data[form_file] = form_data
        return all_forms_data

    def generate_field_listing(self, all_forms_data):
        """Generate a consolidated listing of all fields with relationship and persona information."""
        output_file = os.path.join(self.output_dir, "all_fields_listing.csv")
        relationships_file = os.path.join(self.output_dir, "field_relationships.json")
        persona_review_file = os.path.join(self.output_dir, "fields_needing_persona_review.txt")
        
        # Track fields needing persona review
        needs_review = []
        
        # Save detailed relationships to JSON
        relationships_data = {}
        for form_name, form_data in all_forms_data.items():
            if 'field_relationships' in form_data:
                relationships = [r for r in form_data['field_relationships'] 
                               if r.get('parent') or r.get('children')]
                if relationships:
                    relationships_data[form_name] = relationships
        
        with open(relationships_file, 'w') as f:
            json.dump(relationships_data, f, indent=2)
        logger.info(f"Field relationships saved to: {relationships_file}")
        
        # Generate basic field listing with persona information
        with open(output_file, 'w') as f:
            f.write("field_name,form,type,readonly,required,page,personas,has_parent,has_children,needs_persona_review\n")
            
            for form_name, form_data in all_forms_data.items():
                for field in form_data['fields']:
                    has_parent = 'parent_name' in field.get('hierarchy', {})
                    has_children = bool(field.get('hierarchy', {}).get('children', []))
                    personas = ';'.join(field.get('personas', []))
                    needs_persona_review = field.get('needs_persona_review', False)
                    
                    if needs_persona_review:
                        needs_review.append({
                            'form': form_name,
                            'field': field['name'],
                            'tooltip': field.get('tooltip', ''),
                            'parent': field.get('hierarchy', {}).get('parent_name', '')
                        })
                    
                    f.write(f"{field['name']},{form_name},{field['type']},{field['readonly']},{field['required']},{field['page']},{personas},{has_parent},{has_children},{needs_persona_review}\n")
        
        # Generate list of fields needing persona review
        with open(persona_review_file, 'w') as f:
            f.write("Fields Needing Persona Review\n")
            f.write("=" * 50 + "\n\n")
            for field in needs_review:
                f.write(f"Form: {field['form']}\n")
                f.write(f"Field: {field['field']}\n")
                f.write(f"Tooltip: {field['tooltip']}\n")
                f.write(f"Parent Field: {field['parent']}\n")
                f.write("-" * 50 + "\n\n")
        
        logger.info(f"Field listing saved to: {output_file}")
        logger.info(f"Fields needing persona review saved to: {persona_review_file}")

def main():
    analyzer = FormFieldAnalyzer()
    forms_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uscis_forms'))
    value_mapping_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "value_mapping")
    os.makedirs(value_mapping_root, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(value_mapping_root, f"value_mapping_{timestamp}.json")
    all_forms_data = analyzer.analyze_all_forms(forms_dir)
    all_fields_flat = []
    for form_data in all_forms_data.values():
        all_fields_flat.extend(list(form_data.values()))
    # Post-process:
    for field in all_fields_flat:
        # 1. If domain == 'medical' and value == 'name', set value = screen_label
        if field.get('domain') == 'medical' and field.get('value_info', {}).get('value', '').lower() == 'name':
            if field.get('screen_label'):
                field['value_info']['value'] = field['screen_label']
        # 2. If domain == 'personal' and persona is None, set persona = 'applicant'
        if field.get('domain') == 'personal' and not field.get('persona'):
            field['persona'] = 'applicant'
        # 3. Existing rules: domain == 'medical' or value == 'AlienNumber' => persona = 'applicant'
        if field.get('domain') == 'medical':
            field['persona'] = 'applicant'
        if field.get('value_info') and field['value_info'].get('value') == 'AlienNumber':
            field['persona'] = 'applicant'
    with open(output_file, "w") as f:
        json.dump(all_fields_flat, f, indent=2)
    print(f"Value-mapped analysis saved to: {output_file}")

if __name__ == "__main__":
    main() 