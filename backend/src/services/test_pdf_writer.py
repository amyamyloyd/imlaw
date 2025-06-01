import sys
import os
import pytest
from datetime import datetime, UTC
from PyPDF2 import PdfReader

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.pdf_writer_service import PDFWriterService
from src.services.pdf_storage_service import PDFStorageService

# Path to test PDFs
TEST_PDF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tests", "data", "pdfs"))
I485_PDF_PATH = os.path.join(TEST_PDF_DIR, "i485.pdf")
I485_FILLED_PATH = os.path.join(TEST_PDF_DIR, "i485_filled.pdf")

print(f"\nTest PDF directory: {TEST_PDF_DIR}")
print(f"I-485 PDF path: {I485_PDF_PATH}")
print(f"I-485 filled PDF will be saved to: {I485_FILLED_PATH}")

def setup_test_schema():
    """Set up test form schema in MongoDB using real I-485 field IDs"""
    storage_service = PDFStorageService()
    
    # Real I-485 field definitions (subset for testing)
    test_fields = [
        {
            "id": "Pt1Line1_FamilyName[0]",
            "type": "text",
            "label": "Family Name (Last Name)",
            "required": True,
            "tooltip": "Enter your legal last name",
            "page": 1,
            "properties": {
                "maxLength": 50,
                "pattern": "^[a-zA-Z\\s'-]+$"
            }
        },
        {
            "id": "Pt1Line1_GivenName[0]",
            "type": "text",
            "label": "Given Name (First Name)",
            "required": True,
            "tooltip": "Enter your legal first name",
            "page": 1,
            "properties": {
                "maxLength": 50,
                "pattern": "^[a-zA-Z\\s'-]+$"
            }
        },
        {
            "id": "Pt1Line1_MiddleName[0]",
            "type": "text",
            "label": "Middle Name",
            "required": False,
            "tooltip": "Enter your middle name if any",
            "page": 1,
            "properties": {
                "maxLength": 50,
                "pattern": "^[a-zA-Z\\s'-]+$"
            }
        },
        {
            "id": "alien_number",
            "type": "text",
            "label": "Alien Registration Number (A-Number)",
            "required": True,
            "tooltip": "Enter your A-Number",
            "page": 1,
            "properties": {
                "maxLength": 9,
                "pattern": "^[0-9]{9}$",
                "pdf_fields": [
                    {"type": "box", "base_name": "AlienNumber", "num_boxes": 24},
                    {"type": "full", "name": "Pt1Line4_AlienNumber[0]"},
                    {"type": "full", "name": "Pt2Line2_AlienNumber[0]"},
                    {"type": "full", "name": "Pt6Line5_AlienNumber[0]"},
                    {"type": "full", "name": "Pt7Line2_AlienNumber[0]"},
                    {"type": "full", "name": "Pt7Line3_AlienNumber[0]"}
                ]
            }
        }
    ]
    
    # Store test schema
    storage_service.store_form_fields("i485", "2024", test_fields)

def test_pdf_writer():
    """Test PDF writer functionality with real I-485 form"""
    # Set up test schema
    setup_test_schema()
    
    writer_service = PDFWriterService()
    
    # Test data (focusing on basic text fields)
    test_data = {
        "Pt1Line1_FamilyName[0]": "Lloyd",
        "Pt1Line1_GivenName[0]": "Margaret",
        "Pt1Line1_MiddleName[0]": "Amelia"
    }
    
    # Write data to PDF
    print("\nWriting test data to PDF...")
    filled_pdf_path = writer_service.write_form_data(
        I485_PDF_PATH,
        "i485",
        "2024",
        test_data,
        I485_FILLED_PATH
    )
    
    print(f"\nFilled PDF saved to: {filled_pdf_path}")
    
    # Verify the filled PDF exists
    assert os.path.exists(filled_pdf_path), f"Filled PDF not found at {filled_pdf_path}"
    
    # Verify the text fields were written correctly
    print("\nVerifying text field values:")
    filled_reader = PdfReader(filled_pdf_path)
    filled_fields = filled_reader.get_fields()
    
    # Check each text field
    for field_id, expected_value in test_data.items():
        if field_id in filled_fields:
            value = filled_fields[field_id].get('/V', '')
            print(f"{field_id}: {value} (Expected: {expected_value})")
            assert value == expected_value, f"Field {field_id} has incorrect value"
            
if __name__ == "__main__":
    test_pdf_writer() 