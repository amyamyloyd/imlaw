"""Script for manual validation of PDF form filling.

This script fills an I-485 form with test data for visual inspection.
It includes multiple addresses, employment history, and family members
to verify repeatable section handling.
"""

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.services.pdf_writer_service import PDFWriterService
from src.services.repeatable_section_service import RepeatableSectionService
from src.models.form_sections import ADDRESS_SECTION, EMPLOYMENT_SECTION, FAMILY_SECTION
from src.config.database import Database
from src.services.pdf_storage_service import PDFStorageService

def main():
    # Mock all database and storage dependencies
    mock_db = MagicMock()
    mock_storage = MagicMock()
    
    with patch('src.config.database.Database.get_db', return_value=mock_db), \
         patch('src.services.pdf_storage_service.PDFStorageService', return_value=mock_storage), \
         patch('src.db.database.Database.db', mock_db):
        
        # Initialize services
        writer_service = PDFWriterService()
        
        # Define comprehensive test data
        test_data = {
            # Personal Information
            "Pt1Line1a_FamilyName[0]": "GARCIA",
            "Pt1Line1b_GivenName[0]": "MARIA",
            "Pt1Line1c_MiddleName[0]": "ELENA",
            "Pt1Line2a_FamilyName[0]": "RODRIGUEZ",  # Other names used
            "Pt1Line2b_GivenName[0]": "MARIA",
            "Pt1Line3_AlienNumber[0]": "123456789",
            "Pt1Line4_SSN[0]": "987654321",
            "Pt1Line5_DOB[0]": "1990-05-15",
            "Pt1Line6_Gender[0]": "F",
            "Pt1Line7_CityOfBirth[0]": "Mexico City",
            "Pt1Line8_CountryOfBirth[0]": "Mexico",
            
            # Address History (multiple addresses to test repeatable section)
            "address_history": [
                {
                    "street": "123 Main Street, Apt 4B",
                    "city": "Boston",
                    "state": "MA",
                    "zip": "02108",
                    "from_date": "2020-01-01",
                    "to_date": "2023-12-31"
                },
                {
                    "street": "456 Oak Avenue",
                    "city": "Cambridge",
                    "state": "MA",
                    "zip": "02139",
                    "from_date": "2018-01-01",
                    "to_date": "2019-12-31"
                },
                {
                    "street": "789 Pine Road",
                    "city": "Somerville",
                    "state": "MA",
                    "zip": "02143",
                    "from_date": "2015-01-01",
                    "to_date": "2017-12-31"
                },
                {
                    "street": "321 Maple Lane",
                    "city": "Medford",
                    "state": "MA",
                    "zip": "02155",
                    "from_date": "2012-01-01",
                    "to_date": "2014-12-31"
                }
            ],
            
            # Employment History (multiple jobs)
            "employment_history": [
                {
                    "employer_name": "Tech Solutions Inc.",
                    "position": "Software Developer",
                    "start_date": "2020-01-15",
                    "end_date": "2023-12-31"
                },
                {
                    "employer_name": "Global Innovations LLC",
                    "position": "Systems Analyst",
                    "start_date": "2018-06-01",
                    "end_date": "2019-12-31"
                },
                {
                    "employer_name": "Data Corp",
                    "position": "Database Administrator",
                    "start_date": "2016-03-15",
                    "end_date": "2018-05-31"
                },
                {
                    "employer_name": "StartUp Ventures",
                    "position": "Junior Developer",
                    "start_date": "2014-07-01",
                    "end_date": "2016-02-28"
                }
            ],
            
            # Family Members (spouse and children)
            "family_members": [
                {
                    "relationship": "Spouse",
                    "family_name": "GARCIA",
                    "given_name": "CARLOS",
                    "date_of_birth": "1988-08-20",
                    "country_of_birth": "Mexico"
                },
                {
                    "relationship": "Child",
                    "family_name": "GARCIA",
                    "given_name": "SOFIA",
                    "date_of_birth": "2015-03-10",
                    "country_of_birth": "United States"
                },
                {
                    "relationship": "Child",
                    "family_name": "GARCIA",
                    "given_name": "LUCAS",
                    "date_of_birth": "2018-11-25",
                    "country_of_birth": "United States"
                },
                {
                    "relationship": "Child",
                    "family_name": "GARCIA",
                    "given_name": "ISABELLA",
                    "date_of_birth": "2020-07-15",
                    "country_of_birth": "United States"
                }
            ],
            
            # Additional Information
            "Pt2Line1_EntryStatus[0]": "F-1 Student",
            "Pt2Line2_I94Number[0]": "987654321",
            "Pt2Line3_DateLastEntry[0]": "2010-08-15",
            "Pt2Line4_PlaceLastEntry[0]": "Boston, MA",
            "Pt2Line5_StatusLastEntry[0]": "F-1",
            "Pt2Line6_CurrentStatus[0]": "F-1"
        }
        
        # Get the template path
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "generalscripts",
            "i485.pdf"
        )
        
        # Generate output path
        output_path = os.path.join(
            os.path.dirname(__file__),
            "output",
            f"i485_test_filled_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        )
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Fill the form
        filled_pdf_path = writer_service.write_form_data(
            pdf_path=template_path,
            form_type="I-485",
            version="2023",
            field_data=test_data,
            repeatable_sections=[ADDRESS_SECTION, EMPLOYMENT_SECTION, FAMILY_SECTION],
            output_path=output_path
        )
        
        print(f"\nForm has been filled and saved to: {filled_pdf_path}")
        print("\nPlease review the following in the generated PDF:")
        print("1. Personal Information (Part 1)")
        print("2. Address History - should show 4 addresses with proper pagination")
        print("3. Employment History - should show 4 jobs with proper pagination")
        print("4. Family Members - should show spouse and 3 children with proper pagination")
        print("5. Check that dates are formatted correctly")
        print("6. Verify that supplemental pages are added and numbered correctly")
        print("7. Confirm that all text is properly aligned within fields")

if __name__ == "__main__":
    main() 