import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from typing import Dict, Any

from db.database import Database
from services.schema_migration_service import SchemaMigrationService, MigrationType
from services.versioned_schema_service import VersionedSchemaService
from models.versioned_form_schema import FieldChange

async def test_migration_service():
    """Test the schema migration service functionality"""
    print("\nTesting Schema Migration Service...")
    
    # Initialize services
    db = Database()
    schema_service = VersionedSchemaService(db)
    migration_service = SchemaMigrationService(db)
    
    # Test data
    form_type = "test_form"
    initial_fields = [
        {
            "field_id": "name",
            "field_type": "string",
            "properties": {
                "maxLength": 50,
                "required": True
            }
        },
        {
            "field_id": "age",
            "field_type": "string",
            "properties": {
                "pattern": r"^\d+$",
                "required": True
            }
        }
    ]
    
    # Create initial schema (v1.0.0)
    print("\nCreating initial schema version...")
    schema_v1 = await schema_service.create_schema(
        form_type=form_type,
        fields=initial_fields,
        draft=False  # Create as released version
    )
    version_1 = f"{schema_v1['schema_version']['major']}.{schema_v1['schema_version']['minor']}.{schema_v1['schema_version']['patch']}"
    print(f"Created schema version {version_1}")
    
    # Create updated schema with changes (v2.0.0)
    updated_fields = [
        {
            "field_id": "name",
            "field_type": "string",
            "properties": {
                "maxLength": 100,  # Changed max length
                "required": True
            }
        },
        {
            "field_id": "age",
            "field_type": "number",  # Changed type
            "properties": {
                "minimum": 0,
                "required": True
            }
        },
        {
            "field_id": "email",  # New field
            "field_type": "string",
            "properties": {
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "required": True,
                "default": "user@example.com"
            }
        }
    ]
    
    print("\nCreating updated schema version...")
    schema_v2 = await schema_service.create_schema(
        form_type=form_type,
        fields=updated_fields,
        draft=False  # Create as released version
    )
    version_2 = f"{schema_v2['schema_version']['major']}.{schema_v2['schema_version']['minor']}.{schema_v2['schema_version']['patch']}"
    print(f"Created schema version {version_2}")
    
    # Generate field changes
    field_changes = []
    
    # Check name field changes
    old_name = next(f for f in initial_fields if f["field_id"] == "name")
    new_name = next(f for f in updated_fields if f["field_id"] == "name")
    if old_name != new_name:
        field_changes.append(FieldChange(
            field_id="name",
            change_type="modified",
            previous_value=old_name,
            new_value=new_name
        ))
    
    # Check age field changes
    old_age = next(f for f in initial_fields if f["field_id"] == "age")
    new_age = next(f for f in updated_fields if f["field_id"] == "age")
    if old_age != new_age:
        field_changes.append(FieldChange(
            field_id="age",
            change_type="modified",
            previous_value=old_age,
            new_value=new_age
        ))
    
    # Check new email field
    new_email = next(f for f in updated_fields if f["field_id"] == "email")
    field_changes.append(FieldChange(
        field_id="email",
        change_type="added",
        previous_value=None,
        new_value=new_email
    ))
    
    print("\nCreating migration strategy...")
    strategy = await migration_service.create_migration_strategy(
        form_type=form_type,
        from_version=version_1,
        to_version=version_2,
        field_changes=field_changes
    )
    print(f"Created strategy with type: {strategy.migration_type}")
    
    # Store the migration strategy
    print("\nStoring migration strategy...")
    strategy_id = await migration_service.store_migration_strategy(
        form_type=form_type,
        strategy=strategy
    )
    print(f"Stored migration strategy with ID: {strategy_id}")
    
    # Test Cases for Migration
    print("\nRunning migration test cases...")
    
    test_cases = [
        {
            "name": "Valid data with type conversion",
            "data": {
                "name": "John Smith",
                "age": "30"
            },
            "expected_valid": True,
            "expected_result": {
                "name": "John Smith",
                "age": 30,
                "email": "user@example.com"  # Default value
            }
        },
        {
            "name": "Valid data with long name (will be truncated)",
            "data": {
                "name": "X" * 150,  # Longer than maxLength
                "age": "25"
            },
            "expected_valid": True,
            "expected_result": {
                "name": "X" * 100,  # Truncated to maxLength
                "age": 25,
                "email": "user@example.com"
            }
        },
        {
            "name": "Invalid age format",
            "data": {
                "name": "Jane Doe",
                "age": "not a number"
            },
            "expected_valid": False,
            "expected_errors": ["Field age requires type conversion"]
        },
        {
            "name": "Missing required field",
            "data": {
                "name": "Bob Wilson"
                # Missing age field
            },
            "expected_valid": False,
            "expected_errors": ["Required field age missing with no default"]
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTesting: {test_case['name']}")
        
        # Validate migration
        is_valid, errors = await migration_service.validate_migration(
            form_type=form_type,
            from_version=version_1,
            to_version=version_2,
            data=test_case["data"]
        )
        
        if test_case["expected_valid"]:
            if not is_valid:
                print(f"❌ Validation failed unexpectedly: {errors}")
                continue
                
            try:
                migrated_data = await migration_service.migrate_data(
                    form_type=form_type,
                    from_version=version_1,
                    to_version=version_2,
                    data=test_case["data"]
                )
                
                # Verify migrated data matches expected result
                success = True
                for key, expected_value in test_case["expected_result"].items():
                    if key not in migrated_data:
                        print(f"❌ Missing field {key} in migrated data")
                        success = False
                    elif migrated_data[key] != expected_value:
                        print(f"❌ Field {key} has value {migrated_data[key]}, expected {expected_value}")
                        success = False
                
                if success:
                    print("✅ Migration successful and matches expected result")
                    print("Original:", test_case["data"])
                    print("Migrated:", migrated_data)
            except ValueError as e:
                print(f"❌ Migration failed: {str(e)}")
        else:
            if is_valid:
                print("❌ Validation succeeded unexpectedly")
            else:
                # Check if we got the expected errors
                expected_errors = set(test_case["expected_errors"])
                actual_errors = set(errors)
                if expected_errors == actual_errors:
                    print("✅ Validation failed as expected with correct errors")
                else:
                    print("❌ Unexpected validation errors")
                    print("Expected:", expected_errors)
                    print("Got:", actual_errors)
    
    print("\nTests completed!")

if __name__ == "__main__":
    asyncio.run(test_migration_service()) 