from typing import Optional, Dict, Any, AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    _instance: Optional[AsyncIOMotorDatabase] = None
    _client: Optional[AsyncIOMotorClient] = None
    
    def __init__(self):
        """Initialize database connection"""
        pass
    
    def _ensure_connection(self):
        """Ensure database connection is established"""
        if Database._instance is None:
            # Get connection string from environment
            mongodb_url = os.getenv('MONGODB_URI')
            if not mongodb_url:
                raise ValueError("MONGODB_URI environment variable is required")
            
            database_name = os.getenv('MONGODB_DB_NAME', 'imlaw')
            
            try:
                # Create client with server API version 1
                Database._client = AsyncIOMotorClient(
                    mongodb_url,
                    server_api=ServerApi('1')
                )
                Database._instance = Database._client[database_name]
            except Exception as e:
                print(f"Error connecting to MongoDB: {str(e)}")
                raise
    
    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get the database instance"""
        self._ensure_connection()
        return Database._instance
    
    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """Get a collection by name"""
        return self.db[name]
    
    async def create_collection(self, name: str, **kwargs) -> AsyncIOMotorCollection:
        """Create a new collection with optional configuration"""
        await self.db.create_collection(name, **kwargs)
        return self.get_collection(name)
    
    async def command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """Run a database command"""
        return await self.db.command(command)
    
    async def close(self):
        """Close database connection"""
        if Database._client is not None:
            Database._client.close()
            Database._client = None
            Database._instance = None

# Create a global database instance that initializes lazily
db = Database()

async def get_db() -> AsyncGenerator[Database, None]:
    """FastAPI dependency for getting the database instance"""
    db = Database()
    try:
        yield db
    finally:
        await db.close() 