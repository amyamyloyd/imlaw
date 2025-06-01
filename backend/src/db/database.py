from typing import Optional, Dict, Any
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
        if Database._instance is None:
            # Use the known working connection string
            mongodb_url = "mongodb+srv://amyamylloyd:imlaw2020@cluster0.6jkf0yo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
            database_name = 'imlaw'
            
            print(f"Initializing database connection...")
            
            try:
                # Create client with server API version 1
                Database._client = AsyncIOMotorClient(
                    mongodb_url,
                    server_api=ServerApi('1')  # Fixed parameter name and using ServerApi class
                )
                Database._instance = Database._client[database_name]
                print(f"Successfully connected to database: {database_name}")
            except Exception as e:
                print(f"Error connecting to MongoDB: {str(e)}")
                raise
    
    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Get the database instance"""
        if Database._instance is None:
            raise RuntimeError("Database not initialized")
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