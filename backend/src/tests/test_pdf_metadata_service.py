import pytest
from datetime import datetime
import os
import json
from services.pdf_metadata_service import PDFMetadataService
from services.cache_service import CacheService
from database import Database
import asyncio
from bson import ObjectId

@pytest.fixture
async def metadata_service():
    """Create a PDFMetadataService instance for testing"""
    service = PDFMetadataService()
    # Clear test data after each test
    yield service
    await service.forms_collection.delete_many({})
    await service.cache_service.redis.flushdb()

@pytest.fixture
def sample_pdf_path():
    """Get path to test PDF file"""
    return os.path.join(
        os.path.dirname(__file__),
        'test_data',
        'sample_form.pdf'
    )

@pytest.fixture
def sample_metadata():
    """Create sample form metadata"""
    return {
        'id': str(ObjectId()),
        'title': 'TEST_FORM',
        'description': 'Test form field definitions',
        'pages': 2,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow(),
        'form_type': 'test_form',
        'fields': [
            {
                'field_id': 'field1',
                'field_type': 'Tx',
                'field_name': 'First Name',
                'field_value': None,
                'position': {'x': 0, 'y': 0, 'width': 100, 'height': 20},
                'properties': {'required': True}
            },
            {
                'field_id': 'field2',
                'field_type': 'Btn',
                'field_name': 'Agree',
                'field_value': 'Off',
                'position': {'x': 0, 'y': 30, 'width': 20, 'height': 20},
                'properties': {'required': True}
            }
        ]
    }

@pytest.mark.asyncio
async def test_extract_metadata(metadata_service, sample_pdf_path):
    """Test metadata extraction from PDF"""
    metadata = await metadata_service.extract_metadata(
        sample_pdf_path,
        'test_form'
    )
    
    assert metadata is not None
    assert metadata['form_type'] == 'test_form'
    assert len(metadata['fields']) > 0
    assert all(
        required_field in metadata
        for required_field in ['id', 'title', 'created_at', 'fields']
    )

@pytest.mark.asyncio
async def test_list_forms_with_cache(metadata_service, sample_metadata):
    """Test form listing with caching"""
    # Insert test data
    await metadata_service.forms_collection.insert_one(sample_metadata)
    
    # First call should hit database
    forms = await metadata_service.list_forms()
    assert len(forms) == 1
    assert forms[0]['id'] == sample_metadata['id']
    
    # Second call should hit cache
    cached_forms = await metadata_service.list_forms()
    assert len(cached_forms) == 1
    assert cached_forms[0]['id'] == sample_metadata['id']
    
    # Verify cache was used
    cache_key = metadata_service.cache_service.generate_key(
        "form:list",
        "all",
        "1",
        "10"
    )
    assert await metadata_service.cache_service.get(cache_key) is not None

@pytest.mark.asyncio
async def test_get_form_metadata_with_cache(metadata_service, sample_metadata):
    """Test getting form metadata with caching"""
    # Insert test data
    await metadata_service.forms_collection.insert_one(sample_metadata)
    
    # First call should hit database
    form = await metadata_service.get_form_metadata(sample_metadata['id'])
    assert form['id'] == sample_metadata['id']
    
    # Second call should hit cache
    cached_form = await metadata_service.get_form_metadata(sample_metadata['id'])
    assert cached_form['id'] == sample_metadata['id']
    
    # Verify cache was used
    cache_key = metadata_service.cache_service.generate_key(
        "form:metadata",
        sample_metadata['id']
    )
    assert await metadata_service.cache_service.get(cache_key) is not None

@pytest.mark.asyncio
async def test_get_form_fields_with_cache(metadata_service, sample_metadata):
    """Test getting form fields with caching"""
    # Insert test data
    await metadata_service.forms_collection.insert_one(sample_metadata)
    
    # First call should hit database
    fields = await metadata_service.get_form_fields(sample_metadata['id'])
    assert len(fields) == 2
    
    # Second call should hit cache
    cached_fields = await metadata_service.get_form_fields(sample_metadata['id'])
    assert len(cached_fields) == 2
    
    # Verify cache was used
    cache_key = metadata_service.cache_service.generate_key(
        "form:fields",
        sample_metadata['id'],
        "all"
    )
    assert await metadata_service.cache_service.get(cache_key) is not None

@pytest.mark.asyncio
async def test_update_field_definitions_clears_cache(
    metadata_service,
    sample_metadata
):
    """Test that updating fields clears the cache"""
    # Insert test data
    await metadata_service.forms_collection.insert_one(sample_metadata)
    
    # Get fields to populate cache
    await metadata_service.get_form_fields(sample_metadata['id'])
    
    # Update fields
    new_fields = [
        {
            'field_id': 'field3',
            'field_type': 'Tx',
            'field_name': 'Last Name',
            'field_value': None,
            'position': {'x': 0, 'y': 60, 'width': 100, 'height': 20},
            'properties': {'required': True}
        }
    ]
    
    await metadata_service.update_field_definitions(
        sample_metadata['id'],
        new_fields
    )
    
    # Verify cache was cleared
    cache_key = metadata_service.cache_service.generate_key(
        "form:fields",
        sample_metadata['id'],
        "all"
    )
    assert await metadata_service.cache_service.get(cache_key) is None
    
    # Get updated fields
    updated_fields = await metadata_service.get_form_fields(sample_metadata['id'])
    assert len(updated_fields) == 1
    assert updated_fields[0]['field_name'] == 'Last Name'

@pytest.mark.asyncio
async def test_delete_form_metadata_clears_cache(
    metadata_service,
    sample_metadata
):
    """Test that deleting form metadata clears the cache"""
    # Insert test data
    await metadata_service.forms_collection.insert_one(sample_metadata)
    
    # Get metadata and fields to populate cache
    await metadata_service.get_form_metadata(sample_metadata['id'])
    await metadata_service.get_form_fields(sample_metadata['id'])
    
    # Delete form
    result = await metadata_service.delete_form_metadata(sample_metadata['id'])
    assert result is True
    
    # Verify caches were cleared
    metadata_key = metadata_service.cache_service.generate_key(
        "form:metadata",
        sample_metadata['id']
    )
    fields_key = metadata_service.cache_service.generate_key(
        "form:fields",
        sample_metadata['id'],
        "all"
    )
    
    assert await metadata_service.cache_service.get(metadata_key) is None
    assert await metadata_service.cache_service.get(fields_key) is None 