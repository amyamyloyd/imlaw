import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path
src_dir = str(Path(__file__).parent.parent)
if src_dir not in sys.path:
    sys.path.append(src_dir)

from db.database import Database

async def clear_collection():
    # Initialize database connection
    db = Database()
    collection = db.get_collection('versioned_form_schemas')
    
    try:
        # Delete all documents
        result = await collection.delete_many({})
        print(f"Deleted {result.deleted_count} documents from versioned_form_schemas collection")
    except Exception as e:
        print(f"Error clearing collection: {str(e)}")
    finally:
        await db.close()

if __name__ == "__main__":
    asyncio.run(clear_collection()) 