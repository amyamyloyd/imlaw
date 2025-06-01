#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from pprint import pprint

# Add the src directory to the Python path
src_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(src_dir))

from db.database import Database
from services.versioned_schema_service import VersionedSchemaService

async def test_schema_service():
    """Test the versioned schema service functionality"""
    db = Database()
    service = VersionedSchemaService(db)
    
    # Test data
    form_type = "i485"
    initial_fields = [
        {
            "field_id": "first_name",
            "field_type": "text",
            "field_name": "First Name",
            "required": True
        },
        {
            "field_id": "last_name",
            "field_type": "text",
            "field_name": "Last Name",
            "required": True
        }
    ]
    
    updated_fields = [
        *initial_fields,
        {
            "field_id": "email",
            "field_type": "email",
            "field_name": "Email Address",
            "required": False
        }
    ]
    
    try:
        # 1. Create initial draft schema
        print("\n1. Creating initial draft schema...")
        schema = await service.create_schema(form_type, initial_fields)
        print("✅ Created draft schema:")
        pprint(schema)
        
        # 2. List schemas (should show draft)
        print("\n2. Listing all schemas (including drafts)...")
        schemas = await service.list_schemas(form_type, include_drafts=True)
        print(f"✅ Found {len(schemas)} schemas")
        
        # 3. Update draft schema
        print("\n3. Updating draft schema fields...")
        updated = await service.update_schema_fields(str(schema["_id"]), updated_fields)
        print("✅ Updated schema:")
        pprint(updated)
        
        # 4. Release the schema
        print("\n4. Releasing schema...")
        released = await service.release_schema(str(schema["_id"]))
        print("✅ Released schema:")
        pprint(released)
        
        # 5. Create new draft version
        print("\n5. Creating new draft version...")
        new_draft = await service.create_schema(form_type, updated_fields)
        print("✅ Created new draft:")
        pprint(new_draft)
        
        # 6. List only released schemas
        print("\n6. Listing only released schemas...")
        released_schemas = await service.list_schemas(form_type, include_drafts=False)
        print(f"✅ Found {len(released_schemas)} released schemas")
        
        # 7. Get latest released version
        print("\n7. Getting latest released version...")
        latest = await service.get_schema(form_type)
        print("✅ Latest released version:")
        pprint(latest)
        
        # 8. Get specific version
        print("\n8. Getting specific version...")
        specific = await service.get_schema(form_type, {
            "major": released["schema_version"]["major"],
            "minor": released["schema_version"]["minor"],
            "patch": released["schema_version"]["patch"]
        })
        print("✅ Specific version:")
        pprint(specific)
        
        # 9. Delete draft
        print("\n9. Deleting draft schema...")
        deleted = await service.delete_draft_schema(str(new_draft["_id"]))
        print(f"✅ Draft deleted: {deleted}")
        
        # 10. Verify final state
        print("\n10. Final state check...")
        final_schemas = await service.list_schemas(form_type, include_drafts=True)
        print(f"✅ Total schemas remaining: {len(final_schemas)}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(test_schema_service()) 