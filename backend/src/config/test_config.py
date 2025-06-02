"""Test configuration module"""
import os
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.server_api import ServerApi

async def get_test_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """Get a test database connection"""
    # Get MongoDB connection details from environment
    mongodb_url = os.getenv('MONGODB_TEST_URI')
    if not mongodb_url:
        raise ValueError("MONGODB_TEST_URI environment variable is not set")
        
    test_db_name = os.getenv('MONGODB_TEST_DB_NAME', 'imlaw_test')
    
    # Set test environment variables
    os.environ['MONGODB_URI'] = mongodb_url
    os.environ['MONGODB_DB_NAME'] = test_db_name
    os.environ['JWT_SECRET'] = os.getenv('JWT_TEST_SECRET', 'test-secret-key')
    os.environ['JWT_ALGORITHM'] = 'HS256'
    os.environ['JWT_ACCESS_TOKEN_EXPIRE_MINUTES'] = '30'
    
    # Create test client
    client = AsyncIOMotorClient(mongodb_url, server_api=ServerApi('1'))
    db = client[test_db_name]
    
    try:
        # Test connection
        await db.command('ping')
        yield db
    finally:
        # Clean up test database
        await db.command({'dropDatabase': 1})
        client.close() 