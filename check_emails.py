"""Quick script to check what emails are in MongoDB."""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGODB_URI")
if not uri:
    print("ERROR: MONGODB_URI not set in .env")
    exit(1)

print(f"Connecting to MongoDB...")
client = MongoClient(uri)

# Check donna_dev db
db_name = "donna_dev"
print(f"Checking database: {db_name}")
db = client[db_name]

# Check if collection exists
if "emails" not in db.list_collection_names():
    print("Warning: 'emails' collection not found in database.")
    print(f"Available collections: {db.list_collection_names()}")
    
emails_collection = db["emails"]

# Count emails
count = emails_collection.count_documents({})
print(f"\nTotal emails in database: {count}")

# Show first 3 emails
print("\n--- Sample Emails ---")
for i, email in enumerate(emails_collection.find().limit(3)):
    print(f"\nEmail {i+1}:")
    print(f"  ID: {email.get('_id')}")
    print(f"  Sender: {email.get('sender')}")
    print(f"  Subject: {email.get('subject')}")
    print(f"  Body: {email.get('body', '')[:200]}...")
    print(f"  Has embedding: {'embedding' in email and email['embedding'] is not None}")
    if 'embedding' in email and email['embedding']:
        print(f"  Embedding dimensions: {len(email['embedding'])}")

client.close()
