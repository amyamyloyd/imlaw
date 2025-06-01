from typing import Dict, Any, Optional
import os
from datetime import datetime, UTC
from PyPDF2 import PdfReader, PdfWriter

from src.config.database import Database
from src.models.form_schema import FormSchema
from .pdf_storage_service import PDFStorageService

class PDFWriterService:
    """Service for writing data to PDF form fields"""
    
    def __init__(self):
        self.db = Database.get_db()
        self.storage_service = PDFStorageService()
        
    def write_form_data(
        self,
        pdf_path: str,
        form_type: str,
        version: str,
        field_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """Write data to PDF form fields"""
        try:
            # Create PDF reader and writer
            reader = PdfReader(pdf_path)
            writer = PdfWriter()
            writer.append(reader)
            
            # Get the form fields from the PDF
            pdf_fields = reader.get_fields()
            print("\nAvailable PDF fields:", list(pdf_fields.keys()))  # Debug logging
            
            # Create a mapping of field names to pages
            field_to_pages = {}
            for page_idx, page in enumerate(reader.pages):
                for annot in page.annotations:
                    annot_obj = annot.get_object()
                    if annot_obj.get("/Subtype") == "/Widget":
                        field_name = annot_obj.get("/T")
                        if field_name:
                            if field_name not in field_to_pages:
                                field_to_pages[field_name] = []
                            field_to_pages[field_name].append(page_idx)
            
            # Write data to fields
            for field_id, value in field_data.items():
                # Skip A-Number field for now
                if field_id == "alien_number":
                    continue
                    
                # Handle regular fields
                if field_id in pdf_fields:
                    print(f"Writing '{value}' to field: {field_id}")  # Debug logging
                    
                    # Write to all pages that contain this field
                    pages = field_to_pages.get(field_id, [0])  # Default to first page if not found
                    for page_idx in pages:
                        writer.update_page_form_field_values(
                            writer.pages[page_idx],
                            {field_id: str(value)}
                        )
            
            # Save the filled PDF
            output_path = output_path or pdf_path.replace(".pdf", "_filled.pdf")
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
                
            return output_path
            
        except Exception as e:
            print(f"Error writing form data: {str(e)}")
            raise 