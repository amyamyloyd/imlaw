"""Test schema version routes"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from copy import deepcopy
from src.main import app
from src.models.schema_version import SchemaVersion
from src.db.database import Database
from src.config.test_config import get_test_db
from src.models.form_schema import FormSchema, FormFieldDefinition, FieldType, Position, FieldFlags

@pytest.fixture
def test_client(test_database):
    """Create a test client"""
    return TestClient(app)

@pytest.fixture
def schema_version_data() -> Dict[str, Any]:
    """Create test schema version data"""
    return {
        "form_type": "i485",
        "version": "2024",
        "schema": FormSchema(
            form_type="i485",
            version="2024",
            fields={
                "Pt1Line1a_FamilyName": FormFieldDefinition(
                    id="Pt1Line1a_FamilyName",
                    label="Family Name (Last Name)",
                    type=FieldType.STRING,
                    position=Position(page=1, x=100, y=100),
                    flags=FieldFlags(),
                    validation_rules=[],
                    help_text="Enter your family name as it appears on your birth certificate."
                )
            }
        ),
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
        "notes": "Initial version"
    }

@pytest.mark.asyncio
async def test_create_schema_version(test_client: TestClient, test_database: Database, schema_version_data: Dict[str, Any]):
    """Test creating a schema version"""
    response = test_client.post("/api/schema-versions", json=schema_version_data)
    assert response.status_code == 201
    data = response.json()
    assert data["form_type"] == schema_version_data["form_type"]
    assert data["version"] == schema_version_data["version"]
    assert data["is_active"] == schema_version_data["is_active"]

@pytest.mark.asyncio
async def test_get_schema_version(test_client: TestClient, test_database: Database, schema_version_data: Dict[str, Any]):
    """Test getting a schema version"""
    # First create a schema version
    create_response = test_client.post("/api/schema-versions", json=schema_version_data)
    assert create_response.status_code == 201
    created_data = create_response.json()
    
    # Then get it
    response = test_client.get(f"/api/schema-versions/{created_data['_id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["form_type"] == schema_version_data["form_type"]
    assert data["version"] == schema_version_data["version"]

@pytest.mark.asyncio
async def test_list_schema_versions(test_client: TestClient, test_database: Database, schema_version_data: Dict[str, Any]):
    """Test listing schema versions"""
    # Create a schema version
    create_response = test_client.post("/api/schema-versions", json=schema_version_data)
    assert create_response.status_code == 201
    
    # List all versions
    response = test_client.get("/api/schema-versions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(v["form_type"] == schema_version_data["form_type"] for v in data)

@pytest.mark.asyncio
async def test_update_schema_version(test_client: TestClient, test_database: Database, schema_version_data: Dict[str, Any]):
    """Test updating a schema version"""
    # First create a schema version
    create_response = test_client.post("/api/schema-versions", json=schema_version_data)
    assert create_response.status_code == 201
    created_data = create_response.json()
    
    # Update it
    update_data = schema_version_data.copy()
    update_data["notes"] = "Updated version"
    response = test_client.put(f"/api/schema-versions/{created_data['_id']}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["notes"] == "Updated version"

@pytest.mark.asyncio
async def test_delete_schema_version(test_client: TestClient, test_database: Database, schema_version_data: Dict[str, Any]):
    """Test deleting a schema version"""
    # First create a schema version
    create_response = test_client.post("/api/schema-versions", json=schema_version_data)
    assert create_response.status_code == 201
    created_data = create_response.json()
    
    # Delete it
    response = test_client.delete(f"/api/schema-versions/{created_data['_id']}")
    assert response.status_code == 204
    
    # Verify it's gone
    get_response = test_client.get(f"/api/schema-versions/{created_data['_id']}")
    assert get_response.status_code == 404 