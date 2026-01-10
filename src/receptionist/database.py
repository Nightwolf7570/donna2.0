"""MongoDB database connection and collection management."""

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database

from .config import get_settings


class DatabaseManager:
    """Manages MongoDB connection and provides access to collections."""

    def __init__(self, uri: str | None = None):
        """Initialize database connection."""
        self._uri = uri or get_settings().mongodb_uri
        self._client: MongoClient | None = None
        self._db: Database | None = None

    @property
    def client(self) -> MongoClient:
        """Get MongoDB client (lazy initialization)."""
        if self._client is None:
            self._client = MongoClient(self._uri)
        return self._client

    @property
    def db(self) -> Database:
        """Get the receptionist database."""
        if self._db is None:
            self._db = self.client["donna_dev"]
        return self._db

    @property
    def emails(self) -> Collection:
        """Get the emails collection."""
        return self.db["emails"]

    @property
    def contacts(self) -> Collection:
        """Get the contacts collection."""
        return self.db["contacts"]

    @property
    def calls(self) -> Collection:
        """Get the calls collection for call history."""
        return self.db["calls"]

    @property
    def business_config(self) -> Collection:
        """Get the business_config collection for CEO/company settings."""
        return self.db["business_config"]

    def close(self) -> None:
        """Close the database connection."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None


# Global database instance
_db_manager: DatabaseManager | None = None


def get_database() -> DatabaseManager:
    """Get the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
