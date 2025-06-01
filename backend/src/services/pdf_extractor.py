from typing import Dict, Any, Optional
from PyPDF2 import PdfReader
import logging
from datetime import datetime

class PDFFormExtractor:
    """Service for extracting form field metadata from any PDF form."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def extract_form_metadata(self, pdf_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a PDF form including form type and field definitions.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing form metadata and field definitions
        """
        try:
            reader = PdfReader(pdf_path)
            
            # Get form fields
            if not reader.get_form_text_fields() and not reader.get_fields():
                raise ValueError("No form fields found in PDF")
            
            # Extract form type from filename
            form_type = self._extract_form_type(pdf_path)
            
            # Get all fields with full metadata
            fields = {}
            for name, field in reader.get_fields().items():
                field_info = self._extract_field_metadata(name, field)
                if field_info:  # Only add if we got valid metadata
                    fields[name] = field_info
            
            return {
                "form_type": form_type,
                "total_fields": len(fields),
                "extraction_date": datetime.now().isoformat(),
                "fields": fields
            }
            
        except Exception as e:
            self.logger.error(f"Error extracting form metadata: {str(e)}")
            raise
    
    def _extract_form_type(self, pdf_path: str) -> str:
        """Extract form type from filename."""
        filename = pdf_path.lower().split('/')[-1]
        if 'i485' in filename:
            return 'uscis_I485'
        elif 'i130' in filename:
            return 'uscis_I130'
        elif 'i765' in filename:
            return 'uscis_I765'
        elif 'i693' in filename:
            return 'uscis_I693'
        else:
            return 'unknown'
    
    def _extract_field_metadata(self, name: str, field: Dict) -> Optional[Dict]:
        """
        Extract all metadata for a single form field.
        
        Args:
            name: Field name
            field: PyPDF2 field object
            
        Returns:
            Dictionary containing field metadata
        """
        try:
            # Get field type
            field_type = "Unknown"
            if "/FT" in field:
                field_type_raw = field["/FT"]
                if hasattr(field_type_raw, 'get_object'):
                    field_type_raw = field_type_raw.get_object()
                if field_type_raw == "/Tx":
                    field_type = "Tx"  # Text field
                elif field_type_raw == "/Btn":
                    field_type = "Btn"  # Button (checkbox/radio)
                elif field_type_raw == "/Ch":
                    field_type = "Ch"  # Choice field
            
            # Build metadata dictionary
            metadata = {
                "internal_name": name,
                "field_type": field_type,
            }
            
            # Add all direct field properties
            for key in field:
                if key.startswith('/'):
                    value = field[key]
                    if hasattr(value, 'get_object'):
                        value = value.get_object()
                    clean_key = key[1:]  # Remove leading slash
                    metadata[clean_key] = str(value)
            
            # Extract tooltip/label from TU (tooltip) field
            if "/TU" in field:
                tooltip = field["/TU"]
                if hasattr(tooltip, 'get_object'):
                    tooltip = tooltip.get_object()
                metadata["tooltip"] = str(tooltip)
                # Use tooltip as alternate name since it often contains the full field label
                metadata["alternate_name"] = str(tooltip)
            
            # Get label from T field
            if "/T" in field:
                label = field["/T"]
                if hasattr(label, 'get_object'):
                    label = label.get_object()
                metadata["label"] = str(label)
            
            # Create mapping key (normalized name for database)
            mapping_key = name.split('[')[0] if '[' in name else name
            metadata["mapping_key"] = mapping_key
            
            # Get default value
            if "/DV" in field:
                default = field["/DV"]
                if hasattr(default, 'get_object'):
                    default = default.get_object()
                metadata["default_value"] = str(default)
            elif "/V" in field:
                value = field["/V"]
                if hasattr(value, 'get_object'):
                    value = value.get_object()
                metadata["default_value"] = str(value)
            
            # Extract field properties from Ff (field flags)
            if "/Ff" in field:
                flags = field["/Ff"]
                if hasattr(flags, 'get_object'):
                    flags = flags.get_object()
                flags = int(flags)
                metadata["properties"] = {
                    "readonly": bool(flags & 1),
                    "required": bool(flags & 2),
                    "multiline": bool(flags & 0x1000),
                    "password": bool(flags & 0x2000),
                    "no_export": bool(flags & 0x4000),
                    "radio": bool(flags & 0x8000),
                    "pushbutton": bool(flags & 0x10000),
                    "combo": bool(flags & 0x20000),
                    "edit_combo": bool(flags & 0x40000),
                    "sort_combo": bool(flags & 0x80000),
                    "multiselect": bool(flags & 0x200000),
                    "commit_on_change": bool(flags & 0x4000000),
                }
            
            # Handle parent/child relationships
            if "/Parent" in field:
                parent = field["/Parent"]
                if hasattr(parent, 'get_object'):
                    parent = parent.get_object()
                metadata["parent"] = str(parent)
            
            if "/Kids" in field:
                kids = field["/Kids"]
                if hasattr(kids, 'get_object'):
                    kids = kids.get_object()
                
                kid_data = []
                for kid in kids:
                    if hasattr(kid, 'get_object'):
                        kid = kid.get_object()
                    
                    # Extract kid metadata
                    kid_info = {}
                    if hasattr(kid, 'items'):
                        for k, v in kid.items():
                            if k.startswith('/'):
                                if hasattr(v, 'get_object'):
                                    v = v.get_object()
                                kid_info[k[1:]] = str(v)
                    else:
                        kid_info["reference"] = str(kid)
                    
                    if kid_info:
                        kid_data.append(kid_info)
                
                if kid_data:
                    metadata["kids"] = kid_data
            
            return metadata
            
        except Exception as e:
            self.logger.warning(f"Error extracting metadata for field {name}: {str(e)}")
            return None
    
    def _normalize_field_name(self, field_name: str) -> str:
        """
        Normalize a field name to create a consistent mapping key.
        Example: "topmostSubform[0].Page1[0].Line1[0]" -> "Page1_Line1"
        """
        # Remove array indices and brackets
        clean_name = field_name.replace('[0]', '')
        
        # Split on periods and remove common prefixes
        parts = clean_name.split('.')
        if len(parts) > 1 and parts[0].lower() in ['topmostsubform', 'form1']:
            parts = parts[1:]
            
        # Join remaining parts with underscores
        return '_'.join(parts)
    
    def _determine_form_type(self, pdf_path: str, fields: Dict[str, Any]) -> str:
        """
        Determine the form type from the PDF filename or fields.
        """
        # Try to get form type from filename first
        import os
        filename = os.path.basename(pdf_path).lower()
        
        # Check for common USCIS form patterns
        if 'i-' in filename or 'i' in filename:
            form_num = filename.split('.')[0].replace('-', '')
            return f"uscis_{form_num.upper()}"
            
        # If not found in filename, try to determine from fields
        field_names = list(fields.keys())
        if any('i485' in name.lower() for name in field_names):
            return 'uscis_I485'
        elif any('i130' in name.lower() for name in field_names):
            return 'uscis_I130'
        elif any('i765' in name.lower() for name in field_names):
            return 'uscis_I765'
        elif any('i693' in name.lower() for name in field_names):
            return 'uscis_I693'
            
        # If no specific form type found, use generic identifier
        return 'unknown_form'
    
    def write_form_data(self, pdf_path: str, output_path: str, field_data: Dict[str, Any]) -> None:
        """
        Write data to form fields in a PDF.
        
        Args:
            pdf_path: Path to the source PDF
            output_path: Path where to save the filled PDF
            field_data: Dictionary mapping field internal IDs to values
        """
        try:
            reader = PdfReader(pdf_path)
            if not reader.is_form:
                raise ValueError("PDF does not contain fillable form fields")
            
            # Get the form fields
            form_fields = reader.get_fields()
            
            # Update fields with provided data
            for field_id, value in field_data.items():
                if field_id in form_fields:
                    form_fields[field_id].update({
                        "/V": value,
                        "/AS": value  # For checkboxes/radio buttons
                    })
            
            # Save the filled form
            with open(output_path, "wb") as output_file:
                writer = PdfWriter()
                writer.write(output_file)
                
            self.logger.info(f"Successfully wrote data to form and saved at: {output_path}")
            
        except Exception as e:
            self.logger.error(f"Error writing to PDF form: {str(e)}")
            raise 