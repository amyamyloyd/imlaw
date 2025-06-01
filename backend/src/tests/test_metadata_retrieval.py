import pytest
from datetime import datetime, timedelta
import os
import json
from ..services.pdf_metadata_service import PDFMetadataService
from ..services.cache_service import CacheService
from ..db.database import Database
import asyncio
from bson import ObjectId
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

class TestPDFMetadataService:
    """Test helper class for PDFMetadataService tests"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database dependency"""
        with patch('src.services.pdf_metadata_service.Database') as mock:
            mock_db = MagicMock()
            mock.get_db.return_value = mock_db
            yield mock
            
    @pytest.fixture
    def mock_cache(self):
        """Mock cache dependency"""
        with patch('src.services.pdf_metadata_service.CacheService') as mock:
            mock_cache = MagicMock()
            mock.return_value = mock_cache
            yield mock
            
    @pytest.fixture
    def service(self, mock_db, mock_cache):
        """Create a PDFMetadataService instance with mocked dependencies"""
        return PDFMetadataService()
    
    def test_extract_field_metadata(self, service):
        """Test basic field metadata extraction"""
        # Test with simple field data
        field_name = "test_field"
        field_data = {
            '/FT': b'Tx',  # Text field
            '/T': b'Test Field',  # Field name
            '/TU': b'Field Tooltip',  # Tooltip
            '/Rect': [10, 20, 110, 40]  # Position
        }
        
        result = service._extract_field_metadata(field_name, field_data)
        
        assert result is not None
        assert result['field_id'] == "test_field"
        assert result['field_type'] == "Tx"
        assert result['field_name'] == "Test Field"
        assert result['tooltip'] == "Field Tooltip"
        assert result['position']['x'] == 10
        assert result['position']['y'] == 20
        assert result['position']['width'] == 100
        assert result['position']['height'] == 20
    
    def test_extract_field_metadata_handles_invalid_data(self, service):
        """Test field metadata extraction with invalid data"""
        # Test with invalid field data
        result = service._extract_field_metadata("bad_field", None)
        assert result is None
        
        result = service._extract_field_metadata("empty_field", {})
        assert result is not None
        assert result['field_id'] == "empty_field"
    
    def test_extract_field_position(self, service):
        """Test field position extraction"""
        # Test with valid rectangle data
        field = {'/Rect': [10, 20, 110, 40]}
        position = service._extract_field_position(field)
        assert position['x'] == 10
        assert position['y'] == 20
        assert position['width'] == 100
        assert position['height'] == 20
        
        # Test with invalid data
        field = {'/Rect': None}
        position = service._extract_field_position(field)
        assert position == {'x': 0, 'y': 0, 'width': 0, 'height': 0}
    
    def test_extract_field_properties(self, service):
        """Test field properties extraction"""
        # Test with various property types
        field = {
            '/FT': b'Tx',
            '/T': 'Field Name',
            '/F': 4,
            '/Ff': 0
        }
        
        properties = service._extract_field_properties(field)
        assert 'FT' in properties
        assert 'T' in properties
        assert 'F' in properties
        assert 'Ff' in properties
        
    def test_extract_metadata_basic(self, service):
        """Test basic PDF metadata extraction"""
        # Mock PdfReader directly in the service
        with patch('src.services.pdf_metadata_service.PdfReader') as mock_pdf_reader:
            # Setup mock reader
            mock_reader = Mock()
            mock_reader.pages = [Mock(), Mock()]  # 2 pages
            mock_reader.get_form_text_fields.return_value = {"field1": "value1"}
            mock_reader.get_fields.return_value = {
                "field1": {
                    '/FT': b'Tx',
                    '/T': b'Field 1',
                    '/TU': b'First Field'
                }
            }
            mock_pdf_reader.return_value = mock_reader
            
            metadata = service.extract_metadata("test.pdf", "test_form")
            
            assert metadata is not None
            assert metadata['title'] == "TEST_FORM"
            assert metadata['form_type'] == "test_form"
            assert metadata['pages'] == 2
            assert len(metadata['fields']) == 1
            assert metadata['fields'][0]['field_name'] == "Field 1" 