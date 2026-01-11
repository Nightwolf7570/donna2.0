"""Data models for Email and Contact entities."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class ValidationError(Exception):
    """Raised when model validation fails."""

    pass


@dataclass
class Email:
    """Email data model with vector embedding support.
    
    Attributes:
        id: Unique identifier for the email
        sender: Email sender address
        subject: Email subject line
        body: Email body content
        timestamp: When the email was sent/received
        embedding: Vector embedding for semantic search (optional)
    """

    id: str
    sender: str
    subject: str
    body: str
    timestamp: datetime
    embedding: list[float] | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate all required fields."""
        if not self.id or not self.id.strip():
            raise ValidationError("Email id is required and cannot be empty")
        if not self.sender or not self.sender.strip():
            raise ValidationError("Email sender is required and cannot be empty")
        if not self.subject or not self.subject.strip():
            raise ValidationError("Email subject is required and cannot be empty")
        if not self.body or not self.body.strip():
            raise ValidationError("Email body is required and cannot be empty")
        if self.timestamp is None:
            raise ValidationError("Email timestamp is required")
        if self.embedding is not None and len(self.embedding) != 1024:
            raise ValidationError("Email embedding must have exactly 1024 dimensions")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        result = {
            "_id": self.id,
            "sender": self.sender,
            "subject": self.subject,
            "body": self.body,
            "timestamp": self.timestamp,
        }
        if self.embedding is not None:
            result["embedding"] = self.embedding
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Email":
        """Create Email from MongoDB document."""
        return cls(
            id=str(data.get("_id", data.get("id", ""))),
            sender=data.get("sender", ""),
            subject=data.get("subject", ""),
            body=data.get("body", ""),
            timestamp=data.get("timestamp", datetime.now()),
            embedding=data.get("embedding"),
        )


@dataclass
class Contact:
    """Contact data model for caller identification.
    
    Attributes:
        id: Unique identifier for the contact
        name: Contact's full name
        email: Contact's email address
        phone: Contact's phone number (optional)
        company: Contact's company/organization (optional)
    """

    id: str
    name: str
    email: str
    phone: str | None = None
    company: str | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate all required fields."""
        if not self.id or not self.id.strip():
            raise ValidationError("Contact id is required and cannot be empty")
        if not self.name or not self.name.strip():
            raise ValidationError("Contact name is required and cannot be empty")
        if not self.email or not self.email.strip():
            raise ValidationError("Contact email is required and cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        result = {
            "_id": self.id,
            "name": self.name,
            "email": self.email,
        }
        if self.phone is not None:
            result["phone"] = self.phone
        if self.company is not None:
            result["company"] = self.company
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Contact":
        """Create Contact from MongoDB document."""
        return cls(
            id=str(data.get("_id", data.get("id", ""))),
            name=data.get("name", ""),
            email=data.get("email", ""),
            phone=data.get("phone"),
            company=data.get("company"),
        )


@dataclass
class GoogleCalendarToken:
    """OAuth tokens for Google Calendar integration.

    Attributes:
        user_id: User identifier (default for single-user setup)
        access_token: OAuth access token
        refresh_token: OAuth refresh token for renewal
        expires_at: Token expiration timestamp
        calendar_id: Google Calendar ID to use
    """

    user_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime
    calendar_id: str = "primary"

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate all required fields."""
        if not self.user_id or not self.user_id.strip():
            raise ValidationError("user_id is required and cannot be empty")
        if not self.access_token or not self.access_token.strip():
            raise ValidationError("access_token is required and cannot be empty")
        if not self.refresh_token or not self.refresh_token.strip():
            raise ValidationError("refresh_token is required and cannot be empty")
        if self.expires_at is None:
            raise ValidationError("expires_at is required")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        return {
            "_id": self.user_id,
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at,
            "calendar_id": self.calendar_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GoogleCalendarToken":
        """Create GoogleCalendarToken from MongoDB document."""
        return cls(
            user_id=str(data.get("_id", data.get("user_id", ""))),
            access_token=data.get("access_token", ""),
            refresh_token=data.get("refresh_token", ""),
            expires_at=data.get("expires_at", datetime.now()),
            calendar_id=data.get("calendar_id", "primary"),
        )


@dataclass
class BusinessConfig:
    """Business configuration for the AI receptionist.
    
    Attributes:
        ceo_name: Name of the CEO/boss
        company_name: Name of the company (optional)
        company_description: Brief company description (optional)
    """

    ceo_name: str
    company_name: str | None = None
    company_description: str | None = None

    def __post_init__(self) -> None:
        """Validate required fields after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate all required fields."""
        if not self.ceo_name or not self.ceo_name.strip():
            raise ValidationError("CEO name is required and cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for MongoDB storage."""
        result: dict[str, Any] = {
            "_id": "business_config",  # Singleton document
            "ceo_name": self.ceo_name,
        }
        if self.company_name is not None:
            result["company_name"] = self.company_name
        if self.company_description is not None:
            result["company_description"] = self.company_description
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BusinessConfig":
        """Create BusinessConfig from MongoDB document."""
        return cls(
            ceo_name=data.get("ceo_name", ""),
            company_name=data.get("company_name"),
            company_description=data.get("company_description"),
        )

