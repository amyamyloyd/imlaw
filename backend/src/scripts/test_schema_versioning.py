import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pytest
from datetime import datetime
from typing import List, Dict, Any

from db.database import Database
from models.versioned_form_schema import VersionedFormSchema, SchemaVersion, FieldChange
from services.versioned_schema_service import VersionedSchemaService
from services.schema_migration_service import SchemaMigrationService, MigrationStrategy, MigrationType

async def test_schema_versioning():
    """Test comprehensive schema versioning functionality"""
    print("\nTesting Schema Versioning System...")
    
    # Initialize services
    print("Initializing database connection...")
    db = Database()
    print("Successfully connected to database: imlaw")
    
    schema_service = VersionedSchemaService(db)
    migration_service = SchemaMigrationService(db)
    
    # Clean up any existing test data
    print("\nCleaning up existing test data...")
    await schema_service.collection.delete_many({"form_type": "test_form"})
    await migration_service.migrations_collection.delete_many({"form_type": "test_form"})
    print("✅ Test data cleanup complete")
    
    # Test Case 1: Schema Creation and Versioning
    print("\nTest Case 1: Schema Creation and Versioning")
    
    # Create initial schema (v1.0.0)
    form_type = "test_form"
    initial_fields = [
        {
            "field_id": "name",
            "field_type": "Tx",
            "field_name": "Full Name",
            "position": {
                "x": 50,
                "y": 50,
                "width": 200,
                "height": 30
            },
            "properties": {
                "maxLength": 50
            },
            "flags": {
                "required": True
            }
        },
        {
            "field_id": "age",
            "field_type": "Tx",
            "field_name": "Age",
            "position": {
                "x": 50,
                "y": 100,
                "width": 100,
                "height": 30
            },
            "properties": {
                "minimum": 0,
                "maximum": 150
            },
            "flags": {
                "required": True
            }
        }
    ]
    
    print("\nCreating initial schema version...")
    print("Input fields:", initial_fields)
    schema_v1 = await schema_service.create_schema(
        form_type=form_type,
        fields=initial_fields,
        draft=True
    )
    print("Stored schema:", schema_v1)
    
    # Test draft to released transition
    print("\nTesting draft to released transition...")
    await schema_service.release_schema(schema_v1["_id"])
    version_dict = {
        "major": schema_v1["schema_version"]["major"],
        "minor": schema_v1["schema_version"]["minor"],
        "patch": schema_v1["schema_version"]["patch"]
    }
    released_schema = await schema_service.get_schema(form_type, version_dict)
    assert not released_schema["metadata"]["draft"], "Schema should be released"
    print("✅ Successfully transitioned schema from draft to released")
    
    # Create minor version update (v1.1.0)
    minor_fields = [
        {
            "field_id": "name",
            "field_type": "Tx",
            "field_name": "Full Name",
            "position": {
                "x": 50,
                "y": 50,
                "width": 200,
                "height": 30
            },
            "properties": {
                "maxLength": 100  # Increased length
            },
            "flags": {
                "required": True
            }
        },
        {
            "field_id": "age",
            "field_type": "Tx",
            "field_name": "Age",
            "position": {
                "x": 50,
                "y": 100,
                "width": 100,
                "height": 30
            },
            "properties": {
                "minimum": 0,
                "maximum": 150
            },
            "flags": {
                "required": True
            }
        },
        {
            "field_id": "email",
            "field_type": "Tx",
            "field_name": "Email Address",
            "position": {
                "x": 50,
                "y": 150,
                "width": 200,
                "height": 30
            },
            "properties": {
                "maxLength": 100,
                "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
            },
            "flags": {
                "required": False
            }
        }
    ]
    
    print("\nCreating minor version update...")
    schema_v2 = await schema_service.create_schema(
        form_type=form_type,
        fields=minor_fields,
        draft=True
    )
    version_2 = f"{schema_v2['schema_version']['major']}.{schema_v2['schema_version']['minor']}.{schema_v2['schema_version']['patch']}"
    print(f"Created schema version {version_2}")
    
    # Create major version update (v2.0.0)
    major_fields = [
        {
            "field_id": "fullName",  # Changed field ID
            "field_type": "Tx",
            "field_name": "Full Name",
            "position": {
                "x": 50,
                "y": 50,
                "width": 200,
                "height": 30
            },
            "properties": {
                "maxLength": 100
            },
            "flags": {
                "required": True
            }
        },
        {
            "field_id": "age",
            "field_type": "Tx",
            "field_name": "Age",
            "position": {
                "x": 50,
                "y": 100,
                "width": 100,
                "height": 30
            },
            "properties": {
                "minimum": 18,  # Changed minimum age
                "maximum": 150
            },
            "flags": {
                "required": True
            }
        },
        {
            "field_id": "email",
            "field_type": "Tx",
            "field_name": "Email Address",
            "position": {
                "x": 50,
                "y": 150,
                "width": 200,
                "height": 30
            },
            "properties": {
                "maxLength": 100,
                "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
            },
            "flags": {
                "required": True  # Made email required
            }
        }
    ]
    
    print("\nCreating major version update...")
    schema_v3 = await schema_service.create_schema(
        form_type=form_type,
        fields=major_fields,
        draft=True
    )
    version_3 = f"{schema_v3['schema_version']['major']}.{schema_v3['schema_version']['minor']}.{schema_v3['schema_version']['patch']}"
    print(f"Created schema version {version_3}")
    
    # Test Case 2: Schema Retrieval
    print("\nTest Case 2: Schema Retrieval")
    
    # Test getting latest version
    print("\nRetrieving latest version...")
    latest = await schema_service.get_latest_version(form_type)
    print("Retrieved schema:", latest)
    assert latest["schema_version"]["major"] == 1  # Major version should be 1
    assert latest["schema_version"]["minor"] == 2  # Minor version should be 2 (after two updates)
    assert latest["schema_version"]["patch"] == 0  # Patch version should be 0
    print("✅ Successfully retrieved latest schema version")
    
    # Test getting specific version
    print("Testing get_schema...")
    v1_schema = await schema_service.get_schema(form_type, schema_v1["schema_version"])
    assert len(v1_schema["fields"]) == 2  # Should have original 2 fields
    print("✅ Successfully retrieved specific schema version")
    
    # Test getting all versions
    print("Testing get_all_versions...")
    versions = await schema_service.list_versions(form_type)
    assert len(versions) == 3  # Should have 3 versions
    print("✅ Successfully retrieved all schema versions")
    
    # Test Case 3: Migration Path Finding
    print("\nTest Case 3: Migration Path Finding")
    
    # Get version strings for migration testing
    version_1 = "1.0.0"  # Initial version
    version_2 = "1.1.0"  # Minor update
    version_3 = "1.2.0"  # Major update
    
    # Create migration strategies
    print("Creating migration strategies...")
    strategy_1_to_2 = await migration_service.create_migration_strategy(
        form_type=form_type,
        from_version=version_1,
        to_version=version_2,
        field_changes=[
            FieldChange(
                field_id="name",
                change_type="modified",
                previous_value={"field_type": "Tx", "properties": {"maxLength": 50}},
                new_value={"field_type": "Tx", "properties": {"maxLength": 100}}
            ),
            FieldChange(
                field_id="email",
                change_type="added",
                new_value={
                    "field_id": "email",
                    "field_type": "Tx",
                    "field_name": "Email Address",
                    "properties": {
                        "maxLength": 100,
                        "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$",
                        "default": "user@example.com"
                    }
                }
            )
        ]
    )
    await migration_service.store_migration_strategy(form_type, strategy_1_to_2)
    
    strategy_2_to_3 = await migration_service.create_migration_strategy(
        form_type=form_type,
        from_version=version_2,
        to_version=version_3,
        field_changes=[
            FieldChange(
                field_id="name",
                change_type="modified",
                previous_value={"field_id": "name", "field_type": "Tx"},
                new_value={"field_id": "fullName", "field_type": "Tx"}
            ),
            FieldChange(
                field_id="age",
                change_type="modified",
                previous_value={"field_type": "Tx", "properties": {"minimum": 0}},
                new_value={"field_type": "number", "properties": {"minimum": 18}}
            )
        ],
        breaking_changes=True
    )
    await migration_service.store_migration_strategy(form_type, strategy_2_to_3)
    print("✅ Successfully created migration strategies")
    
    print("Testing direct migration path...")
    path_1_to_2 = await migration_service.get_migration_path(form_type, version_1, version_2)
    assert len(path_1_to_2) == 1  # Should be a direct path
    print("✅ Successfully found direct migration path")
    
    print("Testing multi-step migration path...")
    path_1_to_3 = await migration_service.get_migration_path(form_type, version_1, version_3)
    assert len(path_1_to_3) == 2  # Should include both steps
    print("✅ Successfully found multi-step migration path")
    
    # Test Case 4: Data Migration
    print("\nTest Case 4: Data Migration")
    
    # Test simple migration
    test_data = {
        "name": "John Smith",
        "age": "30"
    }
    
    print("Testing simple data migration...")
    migrated_data = await migration_service.migrate_data(
        form_type=form_type,
        from_version=version_1,
        to_version=version_2,
        data=test_data
    )
    assert "email" in migrated_data  # Should have new email field
    print("✅ Successfully migrated data between minor versions")
    
    # Test complex migration
    print("Testing complex data migration...")
    migrated_data = await migration_service.migrate_data(
        form_type=form_type,
        from_version=version_1,
        to_version=version_3,
        data=test_data
    )
    assert isinstance(migrated_data["age"], (int, float))  # Age should be numeric
    assert migrated_data["email"] == "user@example.com"  # Should have default email
    print("✅ Successfully migrated data between major versions")
    
    # Test Case 5: Error Handling
    print("\nTest Case 5: Error Handling")
    
    # Test invalid version
    print("Testing invalid version handling...")
    invalid_version = {"major": 999, "minor": 999, "patch": 999}
    result = await schema_service.get_schema(form_type, invalid_version)
    assert result is None, "Should return None for non-existent version"
    print("✅ Successfully handled invalid version")
    
    # Test invalid migration
    print("Testing invalid migration handling...")
    invalid_data = {
        "name": "X" * 200,  # Too long
        "age": "not a number"
    }
    is_valid, errors = await migration_service.validate_migration(
        form_type=form_type,
        from_version=version_1,
        to_version=version_3,
        data=invalid_data
    )
    assert not is_valid
    assert len(errors) > 0
    print("✅ Successfully handled invalid migration data")
    
    print("\nAll schema versioning tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(test_schema_versioning())