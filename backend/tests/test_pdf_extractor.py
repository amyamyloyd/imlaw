import pytest
from src.services.pdf_extractor import PDFFormExtractor
import os
from PyPDF2 import PdfReader

@pytest.fixture
def pdf_extractor():
    return PDFFormExtractor()

@pytest.fixture
def sample_pdf_path(tmp_path):
    """This is a placeholder - in real tests, you would use a real PDF form file"""
    return str(tmp_path / "test_form.pdf")

def test_extract_form_metadata_validates_pdf_exists(pdf_extractor):
    """Test that the extractor properly handles non-existent files"""
    with pytest.raises(FileNotFoundError):
        pdf_extractor.extract_form_metadata("nonexistent.pdf")

def test_extract_field_info_structure(pdf_extractor, sample_pdf_path):
    """
    Test that field info extraction returns the expected structure.
    This test needs a real PDF form file to work properly.
    """
    # Skip if we don't have a real PDF to test with
    if not os.path.exists(sample_pdf_path):
        pytest.skip("No sample PDF form available for testing")
    
    metadata = pdf_extractor.extract_form_metadata(sample_pdf_path)
    
    assert isinstance(metadata, dict)
    assert "form_type" in metadata
    assert "extracted_at" in metadata
    assert "total_fields" in metadata
    assert "fields" in metadata
    assert isinstance(metadata["fields"], dict)

def test_determine_form_type_from_filename(pdf_extractor, tmp_path):
    """Test that form type is correctly determined from filename"""
    # Create a minimal PDF file
    test_pdf_path = str(tmp_path / "I-485.pdf")
    with open(test_pdf_path, "wb") as f:
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.write(f)
    
    reader = PdfReader(test_pdf_path)
    form_type = pdf_extractor._determine_form_type(reader, test_pdf_path)
    assert form_type == "I-485"

def test_write_form_data_validates_input(pdf_extractor, tmp_path):
    """Test that write_form_data validates its inputs properly"""
    output_path = str(tmp_path / "output.pdf")
    
    with pytest.raises(FileNotFoundError):
        pdf_extractor.write_form_data(
            "nonexistent.pdf",
            output_path,
            {"field1": "value1"}
        ) 