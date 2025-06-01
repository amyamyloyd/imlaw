from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://amyamylloyd:imlaw2020@cluster0.6jkf0yo.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    
    # Try to list collections in the imlaw database
    db = client['imlaw']
    print("\nCollections in imlaw database:")
    collections = db.list_collection_names()
    for collection in collections:
        print(f"- {collection}")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
    print("\nClosed MongoDB connection") 