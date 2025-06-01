#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from datetime import datetime, UTC

# Add the src directory to the Python path
src_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(src_dir))

from db.database import Database

async def test_validation():
    """Test MongoDB validation rules by attempting to insert valid and invalid documents"""
    db = Database()
    collection = db.get_collection('versioned_form_schemas')
    
    # Test 1: Try to insert an invalid document (missing required fields)
    print("\nTest 1: Inserting invalid document (missing required fields)")
    invalid_doc = {
        "form_type": "test-form",
        # Missing schema_version, fields, and total_fields
    }
    
    try:
        await collection.insert_one(invalid_doc)
        print("❌ Validation failed: Inserted invalid document")
    except Exception as e:
        print("✅ Validation worked: Rejected invalid document")
        print(f"Error message: {str(e)}")
    
    # Test 2: Try to insert a valid document
    print("\nTest 2: Inserting valid document")
    valid_doc = {
        "form_type": "test-form",
        "schema_version": {
            "major": 1,
            "minor": 0,
            "patch": 0,
            "released": datetime.now(UTC)
        },
        "fields": [
            {
                "field_id": "test_field",
                "field_type": "text",
                "field_name": "Test Field",
                "required": True
            }
        ],
        "total_fields": 1
    }
    
    try:
        result = await collection.insert_one(valid_doc)
        print("✅ Validation worked: Inserted valid document")
        print(f"Inserted ID: {result.inserted_id}")
        
        # Clean up the test document
        await collection.delete_one({"_id": result.inserted_id})
        print("Cleaned up test document")
    except Exception as e:
        print("❌ Validation failed: Could not insert valid document")
        print(f"Error message: {str(e)}")

async def main():
    try:
        await test_validation()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 