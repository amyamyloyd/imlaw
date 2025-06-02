"""Test PDF metadata API"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from copy import deepcopy
from src.main import app
from src.services.field_mapping_service import FieldMapping
from src.services.version_control_service import FormVersion
from src.db.database import Database

# Remove global client instance and use fixture instead

# Test data
SAMPLE_FIELD_MAPPING = {
    "form_type": "i485",
    "form_version": "2024",
    "field_id": "Pt1Line1a_FamilyName",
    "canonical_name": "applicant.lastName",
    "description": "Applicant's family name (last name)",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "updated_at": datetime.now(timezone.utc).isoformat(),
    "metadata": {
        "section": "Part 1. Information About You",
        "subsection": "Your Full Name"
    }
}

SAMPLE_FORM_VERSION = {
    "form_type": "i485",
    "version": "2024",
    "effective_date": datetime.now(timezone.utc).isoformat(),
    "expiration_date": None,
    "changes": [
        {
            "field_id": "Pt1Line1a_FamilyName",
            "type": "modified",
            "description": "Updated field label"
        }
    ],
    "metadata": {
        "revision": "1.0",
        "release_notes": "Initial 2024 version"
    },
    "is_active": True
}

@pytest.fixture
def sample_mapping():
    """Create a sample field mapping"""
    return deepcopy(SAMPLE_FIELD_MAPPING)

@pytest.fixture
def sample_version():
    """Create a sample form version"""
    return deepcopy(SAMPLE_FORM_VERSION)

@pytest.fixture
def test_client(test_database):
    """Create a test client"""
    return TestClient(app)

@pytest.fixture
def test_form_data():
    """Create test form data"""
    return {
        "form_type": "i485",
        "version": "2024",
        "fields": [
            {
                "id": "Pt1Line1a_FamilyName",
                "label": "Family Name (Last Name)",
                "type": "string",
                "position": {
                    "page": 1,
                    "x": 100,
                    "y": 100
                },
                "validation_rules": []
            }
        ]
    }

# Field Mapping Tests
def test_create_field_mapping(test_client, sample_mapping):
    """Test creating a new field mapping"""
    response = test_client.post("/api/pdf-metadata/mappings", json=sample_mapping)
    assert response.status_code == 201
    assert isinstance(response.json(), str)  # Should return mapping ID

def test_create_invalid_field_mapping():
    """Test creating a mapping with invalid data"""
    invalid_mapping = {
        "form_type": "i485",
        # Missing required fields
    }
    response = test_client.post("/api/pdf-metadata/mappings", json=invalid_mapping)
    assert response.status_code == 400

def test_get_form_mappings(sample_mapping):
    """Test retrieving mappings for a form version"""
    # First create a mapping
    test_client.post("/api/pdf-metadata/mappings", json=sample_mapping)
    
    response = test_client.get(
        f"/api/pdf-metadata/mappings/{sample_mapping['form_type']}/{sample_mapping['form_version']}"
    )
    assert response.status_code == 200
    mappings = response.json()
    assert isinstance(mappings, list)
    assert len(mappings) > 0
    assert mappings[0]["field_id"] == sample_mapping["field_id"]

def test_bulk_create_mappings(sample_mapping):
    """Test creating multiple mappings at once"""
    mappings = [
        sample_mapping,
        {**sample_mapping, "field_id": "Pt1Line1b_GivenName", "canonical_name": "applicant.firstName"}
    ]
    response = test_client.post("/api/pdf-metadata/mappings/bulk", json=mappings)
    assert response.status_code == 201
    mapping_ids = response.json()
    assert isinstance(mapping_ids, list)
    assert len(mapping_ids) == 2

def test_get_unmapped_fields(sample_mapping):
    """Test finding unmapped fields"""
    # First create a mapping
    test_client.post("/api/pdf-metadata/mappings", json=sample_mapping)
    
    field_ids = [
        sample_mapping["field_id"],  # This one is mapped
        "Pt1Line1b_GivenName",      # This one isn't
        "Pt1Line1c_MiddleName"      # This one isn't
    ]
    
    response = test_client.get(
        f"/api/pdf-metadata/mappings/unmapped/{sample_mapping['form_type']}/{sample_mapping['form_version']}",
        params={"field_ids": field_ids}
    )
    assert response.status_code == 200
    unmapped = response.json()
    assert isinstance(unmapped, list)
    assert len(unmapped) == 2
    assert "Pt1Line1b_GivenName" in unmapped
    assert "Pt1Line1c_MiddleName" in unmapped
    assert sample_mapping["field_id"] not in unmapped

# Version Control Tests
def test_create_form_version(sample_version):
    """Test creating a new form version"""
    response = test_client.post("/api/pdf-metadata/versions", json=sample_version)
    assert response.status_code == 201
    assert isinstance(response.json(), str)  # Should return version ID

def test_create_invalid_form_version():
    """Test creating a version with invalid data"""
    invalid_version = {
        "form_type": "i485",
        # Missing required fields
    }
    response = test_client.post("/api/pdf-metadata/versions", json=invalid_version)
    assert response.status_code == 400

def test_list_form_versions(sample_version):
    """Test listing versions for a form type"""
    # First create a version
    test_client.post("/api/pdf-metadata/versions", json=sample_version)
    
    response = test_client.get(f"/api/pdf-metadata/versions/{sample_version['form_type']}")
    assert response.status_code == 200
    versions = response.json()
    assert isinstance(versions, list)
    assert len(versions) > 0
    assert versions[0]["version"] == sample_version["version"]

def test_get_active_version(sample_version):
    """Test getting the active version for a form type"""
    # First create an active version
    test_client.post("/api/pdf-metadata/versions", json=sample_version)
    
    response = test_client.get(f"/api/pdf-metadata/versions/{sample_version['form_type']}/active")
    assert response.status_code == 200
    version = response.json()
    assert version["version"] == sample_version["version"]
    assert version["is_active"] is True

def test_activate_form_version(sample_version):
    """Test activating a specific version"""
    # First create a version
    test_client.post("/api/pdf-metadata/versions", json=sample_version)
    
    response = test_client.post(
        f"/api/pdf-metadata/versions/{sample_version['form_type']}/{sample_version['version']}/activate"
    )
    assert response.status_code == 200
    result = response.json()
    assert result["message"] == "Version activated successfully"

def test_activate_nonexistent_version():
    """Test activating a version that doesn't exist"""
    response = test_client.post("/api/pdf-metadata/versions/i485/nonexistent/activate")
    assert response.status_code == 404

def test_compare_form_versions(sample_version):
    """Test comparing two versions"""
    # Create first version
    test_client.post("/api/pdf-metadata/versions", json=sample_version)
    
    # Create second version with some changes
    version2 = deepcopy(sample_version)
    version2["version"] = "2024.1"
    version2["metadata"]["revision"] = "1.1"
    test_client.post("/api/pdf-metadata/versions", json=version2)
    
    response = test_client.get(
        f"/api/pdf-metadata/versions/{sample_version['form_type']}/compare",
        params={
            "version1": sample_version["version"],
            "version2": version2["version"]
        }
    )
    assert response.status_code == 200
    differences = response.json()
    assert "metadata_changes" in differences
    assert "field_changes" in differences
    assert differences["metadata_changes"]["revision"]["type"] == "modified"

def test_compare_nonexistent_versions():
    """Test comparing versions that don't exist"""
    response = test_client.get(
        "/api/pdf-metadata/versions/i485/compare",
        params={"version1": "nonexistent1", "version2": "nonexistent2"}
    )
    assert response.status_code == 404

# Integration Tests
def test_full_form_lifecycle(sample_version, sample_mapping):
    """Test the complete lifecycle of form version and field mapping management"""
    # 1. Create initial version
    version_response = test_client.post("/api/pdf-metadata/versions", json=sample_version)
    assert version_response.status_code == 201
    
    # 2. Create field mappings
    mapping_response = test_client.post("/api/pdf-metadata/mappings", json=sample_mapping)
    assert mapping_response.status_code == 201
    
    # 3. Create updated version
    version2 = deepcopy(sample_version)
    version2["version"] = "2024.1"
    version2["metadata"]["revision"] = "1.1"
    version2_response = test_client.post("/api/pdf-metadata/versions", json=version2)
    assert version2_response.status_code == 201
    
    # 4. Compare versions
    compare_response = test_client.get(
        f"/api/pdf-metadata/versions/{sample_version['form_type']}/compare",
        params={
            "version1": sample_version["version"],
            "version2": version2["version"]
        }
    )
    assert compare_response.status_code == 200
    differences = compare_response.json()
    assert differences["metadata_changes"]["revision"]["type"] == "modified"
    
    # 5. Activate new version
    activate_response = test_client.post(
        f"/api/pdf-metadata/versions/{version2['form_type']}/{version2['version']}/activate"
    )
    assert activate_response.status_code == 200
    
    # 6. Verify active version
    active_response = test_client.get(f"/api/pdf-metadata/versions/{version2['form_type']}/active")
    assert active_response.status_code == 200
    active_version = active_response.json()
    assert active_version["version"] == version2["version"]
    
    # 7. Check field mappings are preserved
    mappings_response = test_client.get(
        f"/api/pdf-metadata/mappings/{sample_mapping['form_type']}/{sample_mapping['form_version']}"
    )
    assert mappings_response.status_code == 200
    mappings = mappings_response.json()
    assert len(mappings) > 0
    assert mappings[0]["field_id"] == sample_mapping["field_id"]

@pytest.mark.asyncio
async def test_create_form_metadata(test_client, test_database, test_form_data):
    """Test creating form metadata"""
    response = test_client.post("/api/pdf-metadata", json=test_form_data)
    assert response.status_code == 201
    data = response.json()
    assert data["form_type"] == test_form_data["form_type"]
    assert data["version"] == test_form_data["version"]
    assert len(data["fields"]) == len(test_form_data["fields"])

@pytest.mark.asyncio
async def test_get_form_metadata(test_client, test_database, test_form_data):
    """Test getting form metadata"""
    # First create the metadata
    create_response = test_client.post("/api/pdf-metadata", json=test_form_data)
    assert create_response.status_code == 201
    
    # Then get it
    response = test_client.get(
        f"/api/pdf-metadata/{test_form_data['form_type']}/{test_form_data['version']}"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["form_type"] == test_form_data["form_type"]
    assert data["version"] == test_form_data["version"]

@pytest.mark.asyncio
async def test_list_form_metadata(test_client, test_database, test_form_data):
    """Test listing form metadata"""
    # Create form metadata
    create_response = test_client.post("/api/pdf-metadata", json=test_form_data)
    assert create_response.status_code == 201
    
    # List all metadata
    response = test_client.get("/api/pdf-metadata")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(
        m["form_type"] == test_form_data["form_type"] and 
        m["version"] == test_form_data["version"] 
        for m in data
    ) 