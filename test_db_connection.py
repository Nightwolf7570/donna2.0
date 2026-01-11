
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

mongodb_uri = os.getenv("MONGODB_URI")
print(f"Testing connection to: {mongodb_uri.split('@')[-1] if '@' in mongodb_uri else 'hidden'}")

try:
    client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
    # Force a connection verification
    client.admin.command('ping')
    print("MongoDB connection successful!")
    
    db = client.get_database("donna_dev")
    print("\nCollections:")
    for collection in db.list_collection_names():
        count = db[collection].count_documents({})
        print(f"- {collection}: {count} documents")
        
    print("\nChecking 'calls' collection specifically:")
    calls_count = db.calls.count_documents({})
    print(f"Total calls: {calls_count}")
    
    if calls_count > 0:
        latest_call = db.calls.find_one(sort=[("timestamp", -1)])
        print("Latest call sample:", latest_call)
    else:
        print("No calls found.")

except Exception as e:
    print(f"Connection failed: {e}")
