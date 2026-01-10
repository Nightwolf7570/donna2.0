"""Vector search functionality using Voyage AI embeddings and MongoDB Atlas."""

from dataclasses import dataclass
from typing import Any

import voyageai
from pymongo.collection import Collection

from .config import get_settings
from .database import DatabaseManager


@dataclass
class SearchResult:
    """Result from a vector search query.
    
    Attributes:
        content: The matched content (email body or contact info)
        metadata: Additional metadata about the match
        score: Relevance score (higher is more relevant)
    """

    content: str
    metadata: dict[str, Any]
    score: float


class VectorSearch:
    """Handles embedding generation and MongoDB Atlas vector search.
    
    Uses Voyage AI for generating 1024-dimension embeddings and MongoDB Atlas
    vector search for semantic similarity queries.
    """

    EMBEDDING_MODEL = "voyage-2"
    EMBEDDING_DIMENSIONS = 1024
    DEFAULT_LIMIT = 3

    def __init__(
        self,
        voyage_api_key: str | None = None,
        db_manager: DatabaseManager | None = None,
    ):
        """Initialize VectorSearch with Voyage AI client and MongoDB connection.
        
        Args:
            voyage_api_key: Voyage AI API key (defaults to settings)
            db_manager: Database manager instance (defaults to global instance)
        """
        self._api_key = voyage_api_key or get_settings().voyage_api_key
        self._voyage_client = voyageai.Client(api_key=self._api_key)
        
        if db_manager is not None:
            self._db_manager = db_manager
        else:
            from .database import get_database
            self._db_manager = get_database()

    @property
    def emails_collection(self) -> Collection:
        """Get the emails collection."""
        return self._db_manager.emails

    @property
    def contacts_collection(self) -> Collection:
        """Get the contacts collection."""
        return self._db_manager.contacts

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector using Voyage AI.
        
        Args:
            text: Text to embed
            
        Returns:
            List of 1024 floats representing the embedding vector
        """
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")
        
        result = self._voyage_client.embed(
            texts=[text],
            model=self.EMBEDDING_MODEL,
        )
        return result.embeddings[0]

    async def search_emails(
        self, query: str, limit: int = DEFAULT_LIMIT
    ) -> list[SearchResult]:
        """Search emails using vector similarity.
        
        Args:
            query: Search query text
            limit: Maximum number of results (default 3, max 3)
            
        Returns:
            List of SearchResult objects sorted by relevance (highest first)
        """
        # Enforce maximum limit of 3 per requirements
        limit = min(limit, self.DEFAULT_LIMIT)
        
        # Generate query embedding
        query_embedding = await self.embed_text(query)
        
        # MongoDB Atlas vector search aggregation pipeline
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "email_vector_index",
                    "path": "embedding",
                    "queryVector": query_embedding,
                    "numCandidates": limit * 10,  # Search more candidates for better results
                    "limit": limit,
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "sender": 1,
                    "subject": 1,
                    "body": 1,
                    "timestamp": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        
        results = []
        cursor = self.emails_collection.aggregate(pipeline)
        
        for doc in cursor:
            results.append(
                SearchResult(
                    content=doc.get("body", ""),
                    metadata={
                        "id": str(doc.get("_id", "")),
                        "sender": doc.get("sender", ""),
                        "subject": doc.get("subject", ""),
                        "timestamp": doc.get("timestamp"),
                    },
                    score=doc.get("score", 0.0),
                )
            )
        
        # Ensure results are sorted by score descending (highest first)
        results.sort(key=lambda r: r.score, reverse=True)
        
        return results

    async def search_contacts(self, name: str) -> list[SearchResult]:
        """Search contacts by name.
        
        Args:
            name: Name to search for (case-insensitive partial match)
            
        Returns:
            List of SearchResult objects for matching contacts
        """
        if not name or not name.strip():
            return []
        
        # Use regex for case-insensitive partial name matching
        query = {"name": {"$regex": name.strip(), "$options": "i"}}
        
        results = []
        cursor = self.contacts_collection.find(query).limit(self.DEFAULT_LIMIT)
        
        for doc in cursor:
            contact_info = f"{doc.get('name', '')} - {doc.get('email', '')}"
            if doc.get("company"):
                contact_info += f" ({doc.get('company')})"
            
            results.append(
                SearchResult(
                    content=contact_info,
                    metadata={
                        "id": str(doc.get("_id", "")),
                        "name": doc.get("name", ""),
                        "email": doc.get("email", ""),
                        "phone": doc.get("phone"),
                        "company": doc.get("company"),
                    },
                    score=1.0,  # Exact/partial match gets full score
                )
            )
        
        return results
