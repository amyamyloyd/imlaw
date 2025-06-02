"""
Script to extract field data and additional metadata from immigration PDF forms.
"""

import os
import json
import logging
from datetime import datetime
from PyPDF2 import PdfReader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class FormFieldAnalyzer:
    def __init__(self):
        self.forms_dir = "/Users/claudiapitts/imlaw/Imlaw/generalscripts"
        self.target_forms = ['i485.pdf', 'i130.pdf', 'i765.pdf', 'i693.pdf']
        self.output_dir = os.path.join(self.forms_dir, "field_analysis")
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_field_data(self, field, page_num=None) -> dict:
        """Extract field data with detailed parent-child relationships."""
        data = {
            'name': field.name,
            'type': str(field['/FT']) if '/FT' in field else None,
            'page': page_num,
            'flags': int(field['/Ff']) if '/Ff' in field else 0,
            'hierarchy': {}
        }
        
        # Extract field flags
        flags = data['flags']
        data['readonly'] = bool(flags & 1) if flags is not None else False
        data['required'] = bool(flags & 2) if flags is not None else False
        
        # Extract parent information
        if '/Parent' in field:
            parent = field['/Parent']
            if '/T' in parent:
                data['hierarchy']['parent_name'] = str(parent['/T'])
            if '/FT' in parent:
                data['hierarchy']['parent_type'] = str(parent['/FT'])
        
        # Extract child information
        if '/Kids' in field:
            kids = field['/Kids']
            data['hierarchy']['children'] = []
            for kid in kids:
                try:
                    if hasattr(kid, "get_object"):
                        kid = kid.get_object()
                    child_data = {
                        'name': str(kid['/T']) if '/T' in kid else None,
                        'type': str(kid['/FT']) if '/FT' in kid else None
                    }
                    data['hierarchy']['children'].append(child_data)
                except Exception as e:
                    logger.warning(f"Error processing child field: {e}")
        
        # Extract additional metadata if available
        if '/TU' in field:  # Tooltip/user name
            data['tooltip'] = str(field['/TU'])
        if '/T' in field:   # Partial field name
            data['partial_name'] = str(field['/T'])
        if '/V' in field:   # Field value
            try:
                data['value'] = str(field['/V'])
            except:
                data['value'] = "<<complex value>>"
        if '/DV' in field:  # Default value
            try:
                data['default_value'] = str(field['/DV'])
            except:
                data['default_value'] = "<<complex value>>"
        if '/MaxLen' in field:  # Maximum length
            data['max_length'] = int(field['/MaxLen'])
        
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

    def analyze_form(self, pdf_path: str) -> dict:
        """Analyze a single PDF form and extract all data."""
        logger.info(f"Starting analysis of form: {pdf_path}")
        
        form_data = {
            'filename': os.path.basename(pdf_path),
            'fields': [],
            'metadata': {},
            'field_relationships': [],
            'pages': []
        }

        try:
            with open(pdf_path, 'rb') as file:
                pdf = PdfReader(file)
                
                # Extract document metadata
                form_data['metadata'] = self.extract_document_metadata(pdf)
                
                # Extract fields and their relationships
                if pdf.get_fields():
                    fields = pdf.get_fields()
                    
                    # First pass: collect all fields
                    for field_name, field in fields.items():
                        field_data = self.extract_field_data(field)
                        form_data['fields'].append(field_data)
                        
                        # Analyze relationships
                        if field_data.get('hierarchy', {}).get('parent_name') or \
                           field_data.get('hierarchy', {}).get('children'):
                            relationship = {
                                'field_name': field_name,
                                'parent': field_data.get('hierarchy', {}).get('parent_name'),
                                'children': field_data.get('hierarchy', {}).get('children', []),
                                'type': field_data.get('type'),
                                'tooltip': field_data.get('tooltip')
                            }
                            form_data['field_relationships'].append(relationship)
                
                # Extract page data
                for page_num in range(len(pdf.pages)):
                    page = pdf.pages[page_num]
                    form_data['pages'].append(
                        self.extract_page_data(page, page_num)
                    )

        except Exception as e:
            logger.error(f"Error analyzing form {pdf_path}: {e}")
            return None

        return form_data

    def analyze_all_forms(self):
        """Analyze all target forms and save results."""
        logger.info("Starting analysis of all forms...")
        
        all_forms_data = {}
        
        for form_name in self.target_forms:
            form_path = os.path.join(self.forms_dir, form_name)
            logger.info(f"Analyzing form: {form_name}")
            
            form_data = self.analyze_form(form_path)
            if form_data:
                all_forms_data[form_name] = form_data

        # Save complete analysis
        output_file = os.path.join(self.output_dir, "complete_analysis.json")
        with open(output_file, 'w') as f:
            json.dump(all_forms_data, f, indent=2)
        logger.info(f"Complete analysis saved to: {output_file}")

        # Generate field listing CSV
        self.generate_field_listing(all_forms_data)

    def generate_field_listing(self, all_forms_data):
        """Generate a consolidated listing of all fields with relationship information."""
        output_file = os.path.join(self.output_dir, "all_fields_listing.csv")
        relationships_file = os.path.join(self.output_dir, "field_relationships.json")
        
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
        
        # Generate basic field listing
        with open(output_file, 'w') as f:
            f.write("field_name,form,type,readonly,required,page,has_parent,has_children\n")
            
            for form_name, form_data in all_forms_data.items():
                for field in form_data['fields']:
                    has_parent = 'parent_name' in field.get('hierarchy', {})
                    has_children = bool(field.get('hierarchy', {}).get('children', []))
                    f.write(f"{field['name']},{form_name},{field['type']},{field['readonly']},{field['required']},{field['page']},{has_parent},{has_children}\n")
        
        logger.info(f"Field listing saved to: {output_file}")

if __name__ == '__main__':
    analyzer = FormFieldAnalyzer()
    analyzer.analyze_all_forms() 