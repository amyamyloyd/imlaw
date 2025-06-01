import pytest
import os
from src.config.database import Database

def test_database_connection():
    """Test that we can connect to MongoDB"""
    # Ensure we have the required environment variables
    assert 'MONGODB_URI' in os.environ, "MONGODB_URI environment variable is required"
    
    # Initialize database
    Database.initialize()
    
    # Get database instance
    db = Database.get_db()
    assert db is not None
    
    # Test we can perform a basic operation
    result = db.command('ping')
    assert result.get('ok') == 1
    
    # Clean up
    Database.close() 