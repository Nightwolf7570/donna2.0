from pymongo import MongoClient
from bson import ObjectId
import os
from src.receptionist.config import get_settings

settings = get_settings()
client = MongoClient(settings.mongodb_uri)
db = client[settings.database_name]
collection = db["emails"]

print(f"Connected to database: {settings.database_name}")

# Delete documents with String type _ids
# These are the duplicates created in the previous run
delete_result = collection.delete_many({"_id": {"$type": "string"}})
print(f"Deleted {delete_result.deleted_count} duplicate documents (string _id).")

client.close()
