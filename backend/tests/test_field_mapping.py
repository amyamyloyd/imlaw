"""Test script to verify field mappings and writing to PDF.

This script focuses on the fields we know worked (name fields)
and compares them with fields that didn't work (address fields).
"""
import asyncio
import os
import sys

# Add the backend directory to the Python path
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(backend_dir)

from src.services.pdf_form_filler_service import PDFFormFillerService
from src.models.form_schema import FormSchema, FormFieldDefinition, Position, FieldType
from src.models.repeatable_section import RepeatableSection
from src.models.repeatable_field import RepeatableFieldMapping

async def test_field_writing():
    # Initialize service
    service = PDFFormFillerService()
    
    # Create minimal form schema with just the fields we want to test
    basic_fields = [
        # These fields worked before
        FormFieldDefinition(
            field_name="Family Name (Last Name)",
            field_id="Pt1Line1a_FamilyName[0]",
            page_number=1,
            field_type=FieldType.TEXT,
            label="Family Name (Last Name)",
            position=Position(x=100, y=100, width=200, height=20),
            required=True
        ),
        FormFieldDefinition(
            field_name="Given Name (First Name)", 
            field_id="Pt1Line1b_GivenName[0]",
            page_number=1,
            field_type=FieldType.TEXT,
            label="Given Name (First Name)",
            position=Position(x=100, y=130, width=200, height=20),
            required=True
        ),
        FormFieldDefinition(
            field_name="Middle Name",
            field_id="Pt1Line1c_MiddleName[0]",
            page_number=1,
            field_type=FieldType.TEXT,
            label="Middle Name",
            position=Position(x=100, y=160, width=200, height=20),
            required=False
        )
    ]
    
    # Address section that didn't work
    address_section = RepeatableSection(
        section_id="address_history",
        section_name="Address History",
        description="List of previous addresses",
        base_page_number=3,
        max_entries_per_page=4,
        field_mappings={
            "street": RepeatableFieldMapping(
                field_name="street",
                pdf_field_pattern="Pt3Line{index}_StreetNumberName[0]",
                field_type=FieldType.TEXT,
                max_entries=4,
                field_indices=[5, 7, 9, 11]
            ),
            "city": RepeatableFieldMapping(
                field_name="city",
                pdf_field_pattern="Pt3Line{index}_CityOrTown[0]",
                field_type=FieldType.TEXT,
                max_entries=4,
                field_indices=[5, 7, 9, 11]
            ),
            "state": RepeatableFieldMapping(
                field_name="state",
                pdf_field_pattern="Pt3Line{index}_State[0]",
                field_type=FieldType.TEXT,
                max_entries=4,
                field_indices=[5, 7, 9, 11]
            ),
            "zip_code": RepeatableFieldMapping(
                field_name="zip_code",
                pdf_field_pattern="Pt3Line{index}_ZipCode[0]",
                field_type=FieldType.TEXT,
                max_entries=4,
                field_indices=[5, 7, 9, 11]
            )
        }
    )
    
    form_schema = FormSchema(
        form_type="I-485",
        version="2023",
        title="Test Form",
        fields=basic_fields,
        repeatable_sections={"address_history": address_section},
        total_fields=len(basic_fields)
    )
    
    # Test data
    client_data = {
        # Basic fields that worked
        "Family Name (Last Name)": "GARCIA",
        "Given Name (First Name)": "MARIA",
        "Middle Name": "ELENA",
        
        # Address data that didn't work
        "address_history": [
            {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip_code": "02108"
            },
            {
                "street": "456 Oak Ave",
                "city": "Cambridge",
                "state": "MA", 
                "zip_code": "02139"
            }
        ]
    }
    
    # Fill form and save to output directory
    output_path = os.path.join(os.path.dirname(__file__), "test_output.pdf")
    try:
        filled_pdf = await service.fill_pdf_form(
            client_data=client_data,
            form_schema=form_schema,
            client_name="Test Client",
            output_path=output_path
        )
        print("Form filled successfully!")
        
        # Read back and verify fields
        from PyPDF2 import PdfReader
        reader = PdfReader(output_path)
        fields = reader.get_form_text_fields()
        
        print("\nBasic Fields:")
        print(f"Family Name: {fields.get('Pt1Line1a_FamilyName[0]')}")
        print(f"Given Name: {fields.get('Pt1Line1b_GivenName[0]')}")
        print(f"Middle Name: {fields.get('Pt1Line1c_MiddleName[0]')}")
        
        print("\nAddress Fields (First Address):")
        print(f"Street: {fields.get('Pt3Line5_StreetNumberName[0]')}")
        print(f"City: {fields.get('Pt3Line5_CityOrTown[0]')}")
        print(f"State: {fields.get('Pt3Line5_State[0]')}")
        print(f"ZIP: {fields.get('Pt3Line5_ZipCode[0]')}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_field_writing()) 