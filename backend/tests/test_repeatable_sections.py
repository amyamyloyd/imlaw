import os
import pytest
from PyPDF2 import PdfReader
from datetime import datetime

from src.models.repeatable_section import RepeatableSection, RepeatableFieldMapping
from src.services.pdf_writer_service import PDFWriterService
from src.services.repeatable_section_service import RepeatableSectionService

@pytest.fixture
def employment_section():
    """Fixture for an employment history repeatable section"""
    return RepeatableSection(
        section_id="employment_history",
        section_name="Employment History",
        description="List of previous employers",
        base_page_number=3,
        field_mappings={
            "employer_name": RepeatableFieldMapping(
                field_name="employer_name",
                pdf_field_pattern="Pt3Line{index}a_EmployerName[0]",
                field_type="text",
                max_entries=3
            ),
            "start_date": RepeatableFieldMapping(
                field_name="start_date",
                pdf_field_pattern="Pt3Line{index}b_StartDate[0]",
                field_type="date",
                max_entries=3
            ),
            "end_date": RepeatableFieldMapping(
                field_name="end_date",
                pdf_field_pattern="Pt3Line{index}c_EndDate[0]",
                field_type="date",
                max_entries=3
            )
        },
        max_entries_per_page=3,
        supplemental_page_template="i485_supplement_employment",
        entry_prefix="Pt3Line"
    )

@pytest.fixture
def sample_employment_data():
    """Fixture for sample employment history data"""
    return {
        "employment_history": [
            {
                "employer_name": "Tech Corp",
                "start_date": "2020-01-01",
                "end_date": "2022-12-31"
            },
            {
                "employer_name": "Innovation Labs",
                "start_date": "2018-06-15",
                "end_date": "2019-12-31"
            },
            {
                "employer_name": "Startup Inc",
                "start_date": "2016-03-01",
                "end_date": "2018-05-31"
            },
            {
                "employer_name": "Global Solutions",
                "start_date": "2014-07-01",
                "end_date": "2016-02-28"
            }
        ],
        "first_name": "John",
        "last_name": "Smith"
    }

def test_repeatable_section_processing(employment_section, sample_employment_data, tmp_path):
    """Test processing of repeatable sections"""
    # Create a test PDF path
    test_pdf_path = os.path.join(tmp_path, "test.pdf")
    
    # Initialize services
    writer_service = PDFWriterService()
    
    # Write form data with repeatable section
    output_path = writer_service.write_form_data(
        pdf_path=test_pdf_path,
        form_type="I-485",
        version="10/15/2023",
        field_data=sample_employment_data,
        repeatable_sections=[employment_section]
    )
    
    # Verify the output PDF exists
    assert os.path.exists(output_path)
    
    # Read the output PDF and verify fields
    reader = PdfReader(output_path)
    fields = reader.get_fields()
    
    # Check first employment entry fields
    assert fields["Pt3Line1a_EmployerName[0]"].value == "Tech Corp"
    assert fields["Pt3Line1b_StartDate[0]"].value == "2020-01-01"
    assert fields["Pt3Line1c_EndDate[0]"].value == "2022-12-31"
    
    # Check second employment entry fields
    assert fields["Pt3Line2a_EmployerName[0]"].value == "Innovation Labs"
    assert fields["Pt3Line2b_StartDate[0]"].value == "2018-06-15"
    assert fields["Pt3Line2c_EndDate[0]"].value == "2019-12-31"
    
    # Check that regular fields were also written
    assert fields["first_name"].value == "John"
    assert fields["last_name"].value == "Smith"
    
    # Check that supplemental page was added (4th entry)
    assert fields["Pt3Line1a_EmployerName_Supp[0]"].value == "Global Solutions"
    assert fields["Pt3Line1b_StartDate_Supp[0]"].value == "2014-07-01"
    assert fields["Pt3Line1c_EndDate_Supp[0]"].value == "2016-02-28"

def test_repeatable_section_validation(employment_section):
    """Test validation of repeatable section data"""
    # Test invalid field name
    with pytest.raises(ValueError) as exc_info:
        RepeatableFieldMapping(
            field_name="",
            pdf_field_pattern="Pt3Line{index}a_EmployerName[0]",
            field_type="text"
        )
    assert "field_name" in str(exc_info.value)
    
    # Test invalid pattern
    with pytest.raises(ValueError) as exc_info:
        RepeatableFieldMapping(
            field_name="employer_name",
            pdf_field_pattern="",
            field_type="text"
        )
    assert "pdf_field_pattern" in str(exc_info.value)
    
    # Test invalid max_entries_per_page
    with pytest.raises(ValueError) as exc_info:
        RepeatableSection(
            section_id="test",
            section_name="Test Section",
            base_page_number=1,
            field_mappings={},
            max_entries_per_page=0
        )
    assert "max_entries_per_page" in str(exc_info.value)

def test_supplemental_page_handling(employment_section, sample_employment_data, tmp_path):
    """Test handling of supplemental pages for overflow data"""
    # Create test PDF and supplemental template
    test_pdf_path = os.path.join(tmp_path, "test.pdf")
    supplemental_path = os.path.join(tmp_path, "i485_supplement_employment.pdf")
    
    # Add more entries to exceed max_entries_per_page
    for i in range(5):  # Add 5 more entries
        sample_employment_data["employment_history"].append({
            "employer_name": f"Company {i+5}",
            "start_date": "2010-01-01",
            "end_date": "2013-12-31"
        })
    
    writer_service = PDFWriterService()
    
    # Write form data with repeatable section
    output_path = writer_service.write_form_data(
        pdf_path=test_pdf_path,
        form_type="I-485",
        version="10/15/2023",
        field_data=sample_employment_data,
        repeatable_sections=[employment_section]
    )
    
    # Verify output PDF exists
    assert os.path.exists(output_path)
    
    # Read the output PDF
    reader = PdfReader(output_path)
    
    # Verify number of pages (should have added supplemental pages)
    expected_supplemental_pages = (len(sample_employment_data["employment_history"]) - 3 + 2) // 3
    assert len(reader.pages) == 1 + expected_supplemental_pages  # Base page + supplemental pages 