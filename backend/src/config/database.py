from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

class Database:
    client = None
    db = None

    @classmethod
    def initialize(cls):
        """Initialize database connection"""
        if cls.client is None:
            uri = os.getenv('MONGODB_URI')
            if not uri:
                raise ValueError("MongoDB URI not found in environment variables")
            
            cls.client = MongoClient(uri, server_api=ServerApi('1'))
            
            # Test connection
            try:
                cls.client.admin.command('ping')
                print("Successfully connected to MongoDB!")
                
                # Initialize database
                db_name = os.getenv('MONGODB_DB_NAME', 'imlaw')
                cls.db = cls.client[db_name]
            except Exception as e:
                print(f"Failed to connect to MongoDB: {e}")
                raise

    @classmethod
    def get_db(cls):
        """Get database instance"""
        if cls.db is None:
            cls.initialize()
        return cls.db

    @classmethod
    def close(cls):
        """Close database connection"""
        if cls.client is not None:
            cls.client.close()
            cls.client = None
            cls.db = None 