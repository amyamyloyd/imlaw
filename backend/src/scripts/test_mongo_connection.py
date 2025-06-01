from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus
import re

load_dotenv()

def test_connection():
    uri = os.getenv('MONGODB_URL')
    if not uri:
        print("Error: MONGODB_URL not found in environment variables")
        return

    print("Attempting to connect to MongoDB...")
    
    try:
        # Find the position of the last @ symbol (which separates credentials from host)
        last_at = uri.rindex('@')
        prefix = uri[:uri.index('://') + 3]
        credentials = uri[len(prefix):last_at]
        host_part = uri[last_at + 1:]
        
        # Split credentials into username and password
        colon_pos = credentials.rindex(':')
        username = credentials[:colon_pos]
        password = credentials[colon_pos + 1:]
        
        # Clean and encode
        username = re.sub(r'[<>]', '', username).strip()
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)
        
        # Reconstruct the URL
        uri = f"{prefix}{encoded_username}:{encoded_password}@{host_part}"
        print("Encoded URI format (with password hidden):", 
              uri.replace(encoded_password, '****'))
    
        print("Connecting with encoded URI...")
        
        # Create a new client and connect to the server
        client = MongoClient(uri, server_api=ServerApi('1'))
        
        # Send a ping to confirm a successful connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB!")
        
        # Get database name
        db_name = os.getenv('MONGODB_DB', 'imlaw')
        db = client[db_name]
        
        # List collections
        print(f"\nCollections in {db_name} database:")
        collections = db.list_collection_names()
        for collection in collections:
            print(f"- {collection}")
            
    except Exception as e:
        print(f"Error connecting to MongoDB: {str(e)}")
        print("\nPlease ensure your .env file contains the MongoDB URL in this format:")
        print("MONGODB_URL=mongodb+srv://username:password@cluster0.6jkf0yo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
        print("\nIf using an email as username, it should be properly URL encoded.")
    finally:
        if 'client' in locals():
            client.close()
            print("\nClosed MongoDB connection")

if __name__ == "__main__":
    test_connection() 