from pymongo import MongoClient
from bson import ObjectId
import os
from src.receptionist.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri)
db = client[settings.database_name]
collection = db["emails"]

print(f"Total documents: {collection.count_documents({})}")

# Check for ObjectId type _ids
oid_count = collection.count_documents({"_id": {"$type": "objectId"}})
print(f"Documents with ObjectId _id: {oid_count}")

# Check for String type _ids
str_count = collection.count_documents({"_id": {"$type": "string"}})
print(f"Documents with String _id: {str_count}")

# Check embeddings in both
oid_with_emb = collection.count_documents({"_id": {"$type": "objectId"}, "embedding": {"$ne": None}})
str_with_emb = collection.count_documents({"_id": {"$type": "string"}, "embedding": {"$ne": None}})

print(f"ObjectId docs with embedding: {oid_with_emb}")
print(f"String docs with embedding: {str_with_emb}")
