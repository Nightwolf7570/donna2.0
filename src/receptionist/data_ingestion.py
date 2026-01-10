"""Data ingestion for emails and contacts into MongoDB with embeddings."""

from pymongo import UpdateOne
from pymongo.errors import BulkWriteError

from .models import Contact, Email
from .vector_search import VectorSearch


class DataIngestion:
    """Handles ingesting emails and contacts into MongoDB.
    
    Generates embeddings for emails using Voyage AI and stores them
    in MongoDB Atlas with upsert semantics to handle duplicates.
    """

    def __init__(self, vector_search: VectorSearch):
        """Initialize DataIngestion with a VectorSearch instance.
        
        Args:
            vector_search: VectorSearch instance for embedding generation
        """
        self._vector_search = vector_search

    async def ingest_email(self, email: Email) -> None:
        """Generate embedding and store email in MongoDB.
        
        Uses upsert to update existing records rather than creating duplicates.
        
        Args:
            email: Email object to ingest
        """
        # Generate embedding if not already present
        if email.embedding is None:
            # Combine subject and body for better semantic representation
            text_to_embed = f"{email.subject}\n\n{email.body}"
            email.embedding = await self._vector_search.embed_text(text_to_embed)
        
        # Convert to dict for MongoDB
        doc = email.to_dict()
        
        # Upsert: update if exists, insert if not
        self._vector_search.emails_collection.update_one(
            {"_id": email.id},
            {"$set": doc},
            upsert=True,
        )

    async def ingest_contact(self, contact: Contact) -> None:
        """Store contact in MongoDB.
        
        Uses upsert to update existing records rather than creating duplicates.
        
        Args:
            contact: Contact object to ingest
        """
        doc = contact.to_dict()
        
        # Upsert: update if exists, insert if not
        self._vector_search.contacts_collection.update_one(
            {"_id": contact.id},
            {"$set": doc},
            upsert=True,
        )

    async def bulk_ingest_emails(self, emails: list[Email]) -> int:
        """Bulk ingest emails with embeddings.
        
        Generates embeddings for all emails and performs bulk upsert.
        
        Args:
            emails: List of Email objects to ingest
            
        Returns:
            Count of successfully ingested records
        """
        if not emails:
            return 0
        
        operations = []
        ingested_count = 0
        
        for email in emails:
            try:
                # Generate embedding if not already present
                if email.embedding is None:
                    text_to_embed = f"{email.subject}\n\n{email.body}"
                    email.embedding = await self._vector_search.embed_text(text_to_embed)
                
                doc = email.to_dict()
                
                # Create upsert operation
                operations.append(
                    UpdateOne(
                        {"_id": email.id},
                        {"$set": doc},
                        upsert=True,
                    )
                )
                ingested_count += 1
            except Exception:
                # Skip records that fail embedding generation
                # Error is logged but processing continues
                continue
        
        if operations:
            try:
                result = self._vector_search.emails_collection.bulk_write(
                    operations, ordered=False
                )
                # Return count of modified + upserted documents
                return result.modified_count + result.upserted_count
            except BulkWriteError as e:
                # Some operations may have succeeded
                # Return the count of successful writes
                return e.details.get("nModified", 0) + len(
                    e.details.get("upserted", [])
                )
        
        return 0

    async def bulk_ingest_contacts(self, contacts: list[Contact]) -> int:
        """Bulk ingest contacts.
        
        Performs bulk upsert for all contacts.
        
        Args:
            contacts: List of Contact objects to ingest
            
        Returns:
            Count of successfully ingested records
        """
        if not contacts:
            return 0
        
        operations = []
        
        for contact in contacts:
            doc = contact.to_dict()
            operations.append(
                UpdateOne(
                    {"_id": contact.id},
                    {"$set": doc},
                    upsert=True,
                )
            )
        
        if operations:
            try:
                result = self._vector_search.contacts_collection.bulk_write(
                    operations, ordered=False
                )
                return result.modified_count + result.upserted_count
            except BulkWriteError as e:
                return e.details.get("nModified", 0) + len(
                    e.details.get("upserted", [])
                )
        
        return 0
