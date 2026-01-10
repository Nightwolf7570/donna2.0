import asyncio
import logging
from src.receptionist.database import get_database
from src.receptionist.vector_search import VectorSearch
from src.receptionist.data_ingestion import DataIngestion
from src.receptionist.models import Email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def backfill():
    # Initialize components
    logger.info("Initializing components...")
    db_manager = get_database()
    
    # Verify we are connected to the right DB
    logger.info(f"Connected to database: {db_manager.db.name}")
    
    vector_search = VectorSearch(db_manager=db_manager)
    ingestion = DataIngestion(vector_search)
    
    # 1. Fetch emails needing embeddings
    logger.info("Fetching emails without embeddings...")
    # Query for docs where embedding is missing or null
    query = {
        "$or": [
            {"embedding": {"$exists": False}},
            {"embedding": None}
        ]
    }
    cursor = db_manager.emails.find(query)
    
    emails_to_process = []
    
    for doc in cursor:
        try:
            # Patch missing fields to satisfy validation
            if not doc.get("sender"): doc["sender"] = "Unknown Sender"
            if not doc.get("subject"): doc["subject"] = "No Subject"
            if not doc.get("body") or not doc.get("body").strip(): doc["body"] = "No body content"
            
            # Ensure ID is string
            doc["_id"] = str(doc["_id"])
            
            email = Email.from_dict(doc)
            emails_to_process.append(email)
        except Exception as e:
            logger.warning(f"Skipping document {doc.get('_id')}: {e}")
    
    total = len(emails_to_process)
    logger.info(f"Found {total} emails needing embeddings.")
    
    if total == 0:
        logger.info("No emails to process.")
        return

    # 2. Process in batches
    batch_size = 20
    for i in range(0, total, batch_size):
        batch = emails_to_process[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1}/{(total + batch_size - 1)//batch_size} (Items {i+1}-{min(i+batch_size, total)})")
        
        try:
            # DataIngestion.bulk_ingest_emails generates embeddings and updates DB
            processed_count = await ingestion.bulk_ingest_emails(batch)
            logger.info(f"Successfully processed {processed_count} emails in this batch.")
        except Exception as e:
            logger.error(f"Error processing batch: {e}")
            
    logger.info("Backfill complete!")
    db_manager.close()

if __name__ == "__main__":
    asyncio.run(backfill())
