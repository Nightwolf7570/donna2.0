import asyncio
from datetime import datetime, timedelta
from src.receptionist.database import get_database

async def cleanup_stale_calls():
    print("Connecting to database...")
    db = get_database()
    
    # define stale threshold (e.g., 1 hour ago)
    threshold = datetime.now() - timedelta(minutes=10)
    
    query = {
        "outcome": "in-progress",
        "timestamp": {"$lt": threshold}
    }
    
    count = db.calls.count_documents(query)
    print(f"Found {count} stale calls.")
    
    if count > 0:
        result = db.calls.update_many(
            query,
            {"$set": {"outcome": "failed", "summary": "Call ended unexpectedly (server restart)"}}
        )
        print(f"Updated {result.modified_count} calls to 'failed'.")
    else:
        print("No cleanup needed.")

if __name__ == "__main__":
    asyncio.run(cleanup_stale_calls())
