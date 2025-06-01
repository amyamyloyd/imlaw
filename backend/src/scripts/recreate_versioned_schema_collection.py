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

async def recreate_collection(db: Database) -> None:
    """Recreate the versioned form schema collection with validation rules"""
    collection_name = VersionedFormSchemaCollection.name
    
    print(f"\nRecreating collection '{collection_name}'...")
    
    # 1. Backup existing data if any
    existing_data = []
    collections = await db.db.list_collections()
    collection_names = [col["name"] async for col in collections]
    
    if collection_name in collection_names:
        print("Backing up existing data...")
        collection = db.get_collection(collection_name)
        cursor = collection.find({})
        async for doc in cursor:
            existing_data.append(doc)
        print(f"Backed up {len(existing_data)} documents")
        
        # Drop the existing collection
        print("Dropping existing collection...")
        await db.db.drop_collection(collection_name)
    
    # 2. Create new collection with validation
    print("Creating new collection with validation rules...")
    try:
        await db.db.create_collection(
            collection_name,
            validator=VersionedFormSchemaCollection.validation,
            validationAction="error"
        )
        print("Collection created successfully")
    except Exception as e:
        print(f"Error creating collection: {str(e)}")
        return
    
    # 3. Create indexes
    print("Creating indexes...")
    collection = db.get_collection(collection_name)
    for index in VersionedFormSchemaCollection.indexes:
        name = index.pop('name')
        keys = index.pop('keys')
        try:
            await collection.create_index(keys, name=name, **index)
            print(f"Created index '{name}'")
        except Exception as e:
            print(f"Error creating index '{name}': {str(e)}")
    
    # 4. Restore data if any
    if existing_data:
        print("\nRestoring existing data...")
        try:
            if len(existing_data) == 1:
                await collection.insert_one(existing_data[0])
            elif len(existing_data) > 1:
                await collection.insert_many(existing_data)
            print(f"Restored {len(existing_data)} documents")
        except Exception as e:
            print(f"Error restoring data: {str(e)}")

async def main():
    # Initialize database connection
    print("Initializing database connection...")
    db = Database()
    try:
        print(f"Successfully connected to database: {db.db.name}")
        
        await recreate_collection(db)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        await db.close()
        print("\nClosed database connection")

if __name__ == "__main__":
    asyncio.run(main()) 