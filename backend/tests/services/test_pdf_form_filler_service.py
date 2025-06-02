"""Tests for PDF Form Filler Service"""
import pytest
from unittest.mock import Mock, patch
import PyPDF2
import io
import json
import os
import shutil
from src.services.pdf_form_filler_service import PDFFormFillerService
from src.models.form_schema import FormSchema
from src.utils.form_mapping_converter import convert_mapping_to_schema

@pytest.fixture
def pdf_form_filler_service():
    """Create a PDF form filler service instance for testing."""
    return PDFFormFillerService()

@pytest.fixture
def i485_pdf_template():
    """Load the real I-485 form for testing."""
    # Go up from backend/tests/services to the root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    form_path = os.path.join(root_dir, 'generalscripts', 'i485.pdf')
    with open(form_path, 'rb') as f:
        return f.read()

@pytest.fixture
def i485_field_mappings():
    """Load the real I-485 field mappings."""
    # Go up from backend/tests/services to the root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    mappings_path = os.path.join(root_dir, 'generalscripts', 'i485_fill_map.json')
    with open(mappings_path, 'r') as f:
        return json.load(f)

@pytest.fixture
def i485_form_schema(i485_field_mappings):
    """Create a form schema using real I-485 mappings."""
    return convert_mapping_to_schema(i485_field_mappings)

@pytest.fixture
def output_dir(tmp_path):
    """Create a temporary output directory."""
    output_path = tmp_path / "output"
    output_path.mkdir()
    return output_path

@pytest.mark.asyncio
async def test_fill_i485_form_basic(
    pdf_form_filler_service,
    i485_form_schema,
    output_dir
):
    """Test basic PDF form filling functionality with I-485."""
    # Test data based on real I-485 fields - focusing on simple string fields
    client_data = {
        "Family Name (Last Name)": "Smith",
        "Given Name (First Name)": "John",
        "Middle Name": "Robert",
        "Street Number and Name": "123 Main Street",
        "City or Town": "Boston",
        "State": "Massachusetts",
        "ZIP Code": "02108"
    }
    
    # Fill the form
    output_path = output_dir / "john_smith_i485.pdf"
    filled_pdf = await pdf_form_filler_service.fill_pdf_form(
        client_data=client_data,
        form_schema=i485_form_schema,
        client_name="John Smith",
        output_path=str(output_path)
    )
    
    # Verify the filled PDF
    reader = PyPDF2.PdfReader(io.BytesIO(filled_pdf))
    form_fields = reader.get_form_text_fields()
    
    # Check only simple string fields
    assert form_fields.get("Pt1Line1a_FamilyName[0]") == "Smith"
    assert form_fields.get("Pt1Line1b_GivenName[0]") == "John"
    assert form_fields.get("Pt1Line1c_MiddleName[0]") == "Robert"
    assert form_fields.get("Pt1Line7a_StreetNumberName[0]") == "123 Main Street"
    assert form_fields.get("Pt1Line7b_CityOrTown[0]") == "Boston"
    assert form_fields.get("Pt1Line7c_State[0]") == "Massachusetts"
    assert form_fields.get("Pt1Line7d_ZipCode[0]") == "02108"
    
    # Verify file was saved
    assert output_path.exists()
    with open(output_path, 'rb') as f:
        saved_reader = PyPDF2.PdfReader(f)
        saved_fields = saved_reader.get_form_text_fields()
        assert saved_fields.get("Pt1Line1a_FamilyName[0]") == "Smith"

@pytest.mark.asyncio
async def test_fill_i485_form_missing_data(
    pdf_form_filler_service,
    i485_form_schema,
    output_dir
):
    """Test handling of missing client data with I-485."""
    # Empty client data
    client_data = {}
    
    # Fill the form
    output_path = output_dir / "empty_i485.pdf"
    filled_pdf = await pdf_form_filler_service.fill_pdf_form(
        client_data=client_data,
        form_schema=i485_form_schema,
        client_name="Empty Test",
        output_path=str(output_path)
    )
    
    # Verify the filled PDF
    reader = PyPDF2.PdfReader(io.BytesIO(filled_pdf))
    form_fields = reader.get_form_text_fields()
    
    # Fields should be empty
    assert form_fields.get("Pt1Line1a_FamilyName[0]") == ""
    assert form_fields.get("Pt1Line1b_GivenName[0]") == ""
    assert form_fields.get("Pt1Line1c_MiddleName[0]") == ""

@pytest.mark.asyncio
async def test_fill_i485_form_invalid_template():
    """Test handling of invalid PDF template."""
    service = PDFFormFillerService()
    
    with pytest.raises(ValueError):
        await service.fill_pdf_form(
            template_pdf=b"invalid pdf content",
            client_data={},
            form_schema=Mock(spec=FormSchema),
            client_name="Test Client"
        )

@pytest.mark.asyncio
async def test_fill_i485_form_auto_output_path(
    pdf_form_filler_service,
    i485_form_schema,
    tmp_path
):
    """Test automatic output path generation based on client name."""
    # Test data - only simple string fields
    client_data = {
        "Family Name (Last Name)": "Smith",
        "Given Name (First Name)": "John",
        "Street Number and Name": "123 Main Street"
    }
    
    # Mock the output directory to use tmp_path
    with patch.object(pdf_form_filler_service, '_get_output_path') as mock_get_path:
        output_path = tmp_path / "John_Smith_i485.pdf"
        mock_get_path.return_value = str(output_path)
        
        # Fill the form without specifying output_path
        filled_pdf = await pdf_form_filler_service.fill_pdf_form(
            client_data=client_data,
            form_schema=i485_form_schema,
            client_name="John Smith"
        )
        
        # Verify the file was saved with the generated name
        assert output_path.exists()
        with open(output_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            form_fields = reader.get_form_text_fields()
            assert form_fields.get("Pt1Line1a_FamilyName[0]") == "Smith"
            assert form_fields.get("Pt1Line1b_GivenName[0]") == "John"
            assert form_fields.get("Pt1Line7a_StreetNumberName[0]") == "123 Main Street"

@pytest.mark.asyncio
async def test_fill_i485_form_special_chars_in_name(
    pdf_form_filler_service,
    i485_form_schema,
    tmp_path
):
    """Test handling of special characters in client name for filename."""
    client_data = {
        "Family Name (Last Name)": "O'Brien",
        "Given Name (First Name)": "Mary-Jane"
    }
    
    # Mock the output directory to use tmp_path
    with patch.object(pdf_form_filler_service, '_get_output_path') as mock_get_path:
        output_path = tmp_path / "Mary-Jane_OBrien_i485.pdf"
        mock_get_path.return_value = str(output_path)
        
        # Fill the form
        filled_pdf = await pdf_form_filler_service.fill_pdf_form(
            client_data=client_data,
            form_schema=i485_form_schema,
            client_name="Mary-Jane O'Brien"
        )
        
        # Verify the file exists and fields are filled
        assert output_path.exists()
        with open(output_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            form_fields = reader.get_form_text_fields()
            assert form_fields.get("Pt1Line1a_FamilyName[0]") == "O'Brien"
            assert form_fields.get("Pt1Line1b_GivenName[0]") == "Mary-Jane" 