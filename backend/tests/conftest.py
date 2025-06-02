"""Test configuration and fixtures"""
import pytest
import os
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from src.db.database import Database

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_database() -> AsyncGenerator[Database, None]:
    """Create a test database connection"""
    # Set test environment variables if not set
    if not os.getenv('MONGODB_URI'):
        os.environ['MONGODB_URI'] = "mongodb+srv://amyamylloyd:imlaw2020@cluster0.6jkf0yo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
    if not os.getenv('MONGODB_DB_NAME'):
        os.environ['MONGODB_DB_NAME'] = "imlaw_test"
    
    # Initialize database connection
    client = AsyncIOMotorClient(os.getenv('MONGODB_URI'))
    db = client[os.getenv('MONGODB_DB_NAME')]
    Database.db = db
    
    yield db
    
    # Cleanup after tests
    await client.drop_database(os.getenv('MONGODB_DB_NAME'))
    client.close()

@pytest.fixture(scope="function")
async def clean_db(test_database):
    """Clean the database before each test"""
    collections = await test_database.list_collection_names()
    for collection in collections:
        await test_database[collection].delete_many({})
    yield test_database 

@pytest.fixture
async def test_db():
    """Create a test database connection."""
    # ... existing code ...

@pytest.fixture
async def gridfs_bucket(test_db):
    """Create a GridFS bucket for file storage testing."""
    bucket = AsyncIOMotorGridFSBucket(test_db)
    yield bucket
    # Cleanup: Delete all test files
    async for grid_file in bucket.find({}):
        await bucket.delete(grid_file._id) 