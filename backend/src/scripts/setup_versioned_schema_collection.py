#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any
from pymongo.errors import CollectionInvalid

# Add the src directory to the Python path
src_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(src_dir))

from db.database import Database
from models.versioned_form_schema import VersionedFormSchemaCollection

async def setup_collection(db: Database) -> None:
    """Set up the versioned form schema collection with validation rules"""
    try:
        # Create collection with validation
        await db.create_collection(
            VersionedFormSchemaCollection.name,
            validator=VersionedFormSchemaCollection.validation,
            validationAction="error"
        )
        print(f"Created collection '{VersionedFormSchemaCollection.name}' with validation rules")
    except CollectionInvalid as e:
        if "already exists" in str(e):
            # Update validation on existing collection
            await db.command({
                "collMod": VersionedFormSchemaCollection.name,
                "validator": VersionedFormSchemaCollection.validation,
                "validationAction": "error"
            })
            print(f"Updated validation rules for existing collection '{VersionedFormSchemaCollection.name}'")
        else:
            raise

    # Create indexes
    collection = db.get_collection(VersionedFormSchemaCollection.name)
    for index in VersionedFormSchemaCollection.indexes:
        name = index.pop('name')
        keys = index.pop('keys')
        await collection.create_index(keys, name=name, **index)
        print(f"Created index '{name}' on collection '{VersionedFormSchemaCollection.name}'")

async def main():
    """Main entry point"""
    db = None
    try:
        db = Database()
        await setup_collection(db)
        print("Successfully set up versioned form schema collection")
    except Exception as e:
        print(f"Error setting up collection: {str(e)}")
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_exception(type(e), e, e.__traceback__)
    finally:
        if db:
            await db.close()

if __name__ == "__main__":
    asyncio.run(main()) 