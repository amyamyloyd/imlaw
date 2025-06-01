import asyncio
from datetime import datetime, UTC, timedelta
import sys
from pathlib import Path
from copy import deepcopy

# Add the src directory to Python path
src_dir = str(Path(__file__).parent.parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from db.database import Database

def is_released(release_date: datetime) -> bool:
    """Check if a schema version is released by comparing with current time"""
    if not release_date.tzinfo:
        release_date = release_date.replace(tzinfo=UTC)
    return release_date <= datetime.now(UTC)

async def test_schema_operations():
    # Initialize database connection
    db = Database()
    collection = db.get_collection('versioned_form_schemas')
    
    # Current timestamp for release date
    now = datetime.now(UTC)
    future = now + timedelta(days=30)  # Draft versions use a future release date
    
    # Test form schema
    test_schema = {
        "form_type": "i485",
        "schema_version": {
            "major": 1,
            "minor": 0,
            "patch": 0,
            "released": now  # Set to current date for released version
        },
        "version": "1.0",
        "created_at": now,
        "fields": [
            {
                "name": "first_name",
                "type": "string",
                "required": True,
                "label": "First Name",
                "validation": {"min_length": 1, "max_length": 50}
            },
            {
                "name": "last_name",
                "type": "string",
                "required": True,
                "label": "Last Name",
                "validation": {"min_length": 1, "max_length": 50}
            },
            {
                "name": "date_of_birth",
                "type": "date",
                "required": True,
                "label": "Date of Birth"
            }
        ],
        "total_fields": 3,
        "metadata": {
            "description": "Application to Register Permanent Residence",
            "category": "Immigration Forms",
            "estimated_completion_time": "60 minutes"
        }
    }
    
    try:
        # 1. Insert the test schema
        print("\nInserting test schema...")
        result = await collection.insert_one(test_schema)
        print(f"Inserted schema with ID: {result.inserted_id}")
        
        # 2. Retrieve and display the schema
        print("\nRetrieving inserted schema...")
        found_schema = await collection.find_one({"form_type": "i485", "version": "1.0"})
        if found_schema:
            print("Found schema:")
            print(f"- Form Type: {found_schema['form_type']}")
            sv = found_schema['schema_version']
            release_date = sv['released']
            status = 'Released' if is_released(release_date) else 'Draft'
            print(f"- Schema Version: {sv['major']}.{sv['minor']}.{sv['patch']} ({status})")
            if status == 'Released':
                print(f"  Released on: {release_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            else:
                print(f"  Planned release: {release_date.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"- Version: {found_schema['version']}")
            print(f"- Total Fields: {found_schema['total_fields']}")
            print("- Field names:", [f["name"] for f in found_schema["fields"]])
        
        # 3. Create a new version with an additional field
        # Create a clean copy without _id field
        new_version = {
            "form_type": test_schema["form_type"],
            "schema_version": {
                "major": 1,
                "minor": 1,
                "patch": 0,
                "released": future  # Future date indicates draft status
            },
            "version": "1.1",
            "created_at": now,
            "fields": deepcopy(test_schema["fields"]),  # Deep copy to avoid reference issues
            "metadata": deepcopy(test_schema["metadata"])
        }
        
        # Add the new field
        new_version["fields"].append({
            "name": "email",
            "type": "string",
            "required": False,
            "label": "Email Address",
            "validation": {"pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"}
        })
        new_version["total_fields"] = len(new_version["fields"])
        
        print("\nInserting new version...")
        result = await collection.insert_one(new_version)
        print(f"Inserted new version with ID: {result.inserted_id}")
        
        # 4. List all versions of the form
        print("\nListing all versions of i485 form:")
        cursor = collection.find({"form_type": "i485"}).sort("version", 1)
        async for version in cursor:
            sv = version['schema_version']
            release_date = sv['released']
            status = 'Released' if is_released(release_date) else f"Draft (Release: {release_date.strftime('%Y-%m-%d')})"
            print(f"- Version {version['version']}: {version['total_fields']} fields (Schema v{sv['major']}.{sv['minor']}.{sv['patch']} - {status})")
            
    except Exception as e:
        print(f"Error during operations: {str(e)}")
    finally:
        # Close the database connection
        await db.close()

if __name__ == "__main__":
    # Run the async function
    asyncio.run(test_schema_operations()) 