"""PDF Form Filler Service

This service handles filling PDF forms with client data based on form schemas.
It supports both standard fields and repeatable sections.
"""
from typing import Dict, Any, Optional, List
import PyPDF2
import io
import os
import logging
from collections import defaultdict
from ..models.form_schema import FormSchema
from ..models.client_profile import ClientProfile
from ..models.repeatable_section import RepeatableSection

logger = logging.getLogger(__name__)

class PDFFormFillerService:
    """Service for filling PDF forms with client data."""
    
    def __init__(self):
        """Initialize the PDF Form Filler Service."""
        self.logger = logging.getLogger(__name__)
        # Get the root directory (one level up from backend)
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.templates_dir = os.path.join(self.root_dir, '..', 'generalscripts')
    
    def _get_template_path(self, form_type: str) -> str:
        """Get the path to a form template."""
        # Remove any hyphens from form type and convert to lowercase
        template_name = f"{form_type.lower().replace('-', '')}.pdf"
        template_path = os.path.join(self.templates_dir, template_name)
        if not os.path.exists(template_path):
            raise ValueError(f"Template not found: {template_name}")
        return template_path
    
    def _get_output_path(self, form_type: str, client_name: str) -> str:
        """Generate output path for filled form."""
        # Clean client name for filename
        safe_name = "".join(c for c in client_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        # Remove any hyphens from form type for consistency with template names
        form_type = form_type.replace('-', '')
        filename = f"{safe_name}_{form_type.lower()}.pdf"
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(self.root_dir, '..', 'output')
        os.makedirs(output_dir, exist_ok=True)
        
        return os.path.join(output_dir, filename)
    
    async def fill_pdf_form(
        self,
        client_data: Dict[str, Any],
        form_schema: FormSchema,
        client_name: str,
        template_pdf: Optional[bytes] = None,
        output_path: Optional[str] = None
    ) -> bytes:
        """
        Fill a PDF form with client data according to the form schema.
        Uses direct field IDs from the PDF for writing values.
        
        Args:
            client_data: Dictionary containing client data to fill the form with
            form_schema: FormSchema instance defining the structure and mapping
            client_name: Name of the client (for output filename)
            template_pdf: Optional bytes of the PDF template (if not provided, will load from generalscripts)
            output_path: Optional specific output path (if not provided, will generate based on client name)
            
        Returns:
            bytes: The filled PDF as bytes
            
        Raises:
            ValueError: If template is invalid or required data is missing
            IOError: If there are issues reading/writing the PDF
        """
        try:
            # Get template PDF if not provided
            if template_pdf is None:
                template_path = self._get_template_path(form_schema.form_type)
                with open(template_path, 'rb') as f:
                    template_pdf = f.read()
            
            # Create PDF reader from template bytes
            pdf_bytes = io.BytesIO(template_pdf)
            reader = PyPDF2.PdfReader(pdf_bytes)
            writer = PyPDF2.PdfWriter()
            
            # Add all pages from the original PDF
            for page in reader.pages:
                writer.add_page(page)
            
            # Get all form fields
            pdf_fields = reader.get_fields()
            
            # Process regular fields first
            field_data = {}
            for field in form_schema.fields:
                if field.field_name in client_data:
                    value = client_data[field.field_name]
                    if value is not None:
                        field_data[field.field_id] = str(value)
            
            # Process repeatable sections
            for section_name, section_schema in form_schema.repeatable_sections.items():
                if section_name in client_data:
                    section_data = client_data[section_name]
                    if isinstance(section_data, list):
                        # Map each entry to its corresponding field IDs
                        for entry_idx, entry_data in enumerate(section_data):
                            if entry_idx >= section_schema.max_entries_per_page:
                                self.logger.warning(f"Skipping entry {entry_idx} - exceeds max entries")
                                break
                                
                            # Get the field index for this entry (e.g., 5, 7, 9 for addresses)
                            field_idx = section_schema.field_mappings[list(section_schema.field_mappings.keys())[0]].field_indices[entry_idx]
                            
                            # Map each field in the entry to its PDF field ID
                            for field_name, field_mapping in section_schema.field_mappings.items():
                                if field_name in entry_data:
                                    value = entry_data[field_name]
                                    if value is not None:
                                        # Use the exact field ID from the PDF
                                        pdf_field_id = field_mapping.pdf_field_pattern.format(index=field_idx)
                                        field_data[pdf_field_id] = str(value)
            
            # Write all field values at once
            for field_id, value in field_data.items():
                if field_id in pdf_fields:
                    field = pdf_fields[field_id]
                    field['/V'] = value
            
            # Generate output path if not provided
            if not output_path:
                output_path = self._get_output_path(form_schema.form_type, client_name)
            
            # Write the filled PDF to file
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            # Return the filled PDF as bytes
            with open(output_path, 'rb') as f:
                return f.read()
            
        except Exception as e:
            self.logger.error(f"Error filling PDF form: {str(e)}")
            raise 