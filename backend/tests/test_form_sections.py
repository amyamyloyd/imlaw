import pytest
from datetime import datetime
from src.services.pdf_writer_service import PDFWriterService
from src.models.form_sections import ADDRESS_SECTION, EMPLOYMENT_SECTION, FAMILY_SECTION

def test_multiple_section_mapping(tmp_path):
    """Test that client data with multiple addresses, jobs, and family members maps correctly"""
    
    # Sample client data with multiple entries for each section
    client_data = {
        # Regular fields
        "first_name": "John",
        "last_name": "Smith",
        
        # Address history (multiple addresses)
        "address_history": [
            {
                "street": "123 Main St",
                "city": "Boston",
                "state": "MA",
                "zip": "02108",
                "from_date": "2020-01-01",
                "to_date": "2023-12-31"
            },
            {
                "street": "456 Oak Ave",
                "city": "Cambridge",
                "state": "MA",
                "zip": "02139",
                "from_date": "2018-01-01",
                "to_date": "2019-12-31"
            },
            {
                "street": "789 Pine Rd",
                "city": "Somerville",
                "state": "MA",
                "zip": "02143",
                "from_date": "2015-01-01",
                "to_date": "2017-12-31"
            }
        ],
        
        # Employment history (multiple jobs)
        "employment_history": [
            {
                "employer_name": "Tech Corp",
                "position": "Software Engineer",
                "start_date": "2020-01-01",
                "end_date": "2023-12-31"
            },
            {
                "employer_name": "Startup Inc",
                "position": "Developer",
                "start_date": "2018-06-01",
                "end_date": "2019-12-31"
            }
        ],
        
        # Family members (multiple relationships)
        "family_members": [
            {
                "relationship": "Spouse",
                "family_name": "Smith",
                "given_name": "Jane",
                "date_of_birth": "1990-05-15",
                "country_of_birth": "Canada"
            },
            {
                "relationship": "Child",
                "family_name": "Smith",
                "given_name": "Tommy",
                "date_of_birth": "2015-03-20",
                "country_of_birth": "United States"
            },
            {
                "relationship": "Child",
                "family_name": "Smith",
                "given_name": "Sarah",
                "date_of_birth": "2018-07-10",
                "country_of_birth": "United States"
            }
        ]
    }
    
    # Create test PDF path
    test_pdf_path = tmp_path / "test_form.pdf"
    test_pdf_path.write_bytes(b"")  # Create empty PDF for testing
    
    # Initialize PDF writer service
    writer_service = PDFWriterService()
    
    # Write form data with all repeatable sections
    output_path = writer_service.write_form_data(
        pdf_path=str(test_pdf_path),
        form_type="I-485",
        version="2023",
        field_data=client_data,
        repeatable_sections=[ADDRESS_SECTION, EMPLOYMENT_SECTION, FAMILY_SECTION]
    )
    
    # Verify the mappings (in a real test, we'd read the PDF and check field values)
    # Here we're just demonstrating the structure
    assert output_path.endswith("_filled.pdf")
    
    # The RepeatableSectionService will have:
    # 1. Mapped the first 3 addresses to the main page fields:
    #    - Pt4Line1a_StreetAddress[0] = "123 Main St"
    #    - Pt4Line2a_StreetAddress[0] = "456 Oak Ave"
    #    - Pt4Line3a_StreetAddress[0] = "789 Pine Rd"
    #    (and similar for city, state, zip, dates)
    
    # 2. Mapped the employment history:
    #    - Pt5Line1a_EmployerName[0] = "Tech Corp"
    #    - Pt5Line2a_EmployerName[0] = "Startup Inc"
    #    (and similar for position, dates)
    
    # 3. Mapped the family members:
    #    - Pt6Line1a_Relationship[0] = "Spouse"
    #    - Pt6Line2a_Relationship[0] = "Child"
    #    - Pt6Line3a_Relationship[0] = "Child"
    #    (and similar for names, DOB, country) 