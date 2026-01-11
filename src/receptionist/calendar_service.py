"""Google Calendar integration service for creating and managing events."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pymongo.collection import Collection

from .models import GoogleCalendarToken

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for Google Calendar OAuth and event management.

    Uses desktop/installed app OAuth flow for authentication.
    """

    SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        tokens_collection: Collection,
    ):
        """Initialize the calendar service.

        Args:
            client_id: Google OAuth client ID
            client_secret: Google OAuth client secret
            redirect_uri: OAuth callback URL (http://localhost:8000/google/callback)
            tokens_collection: MongoDB collection for storing tokens
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._tokens_collection = tokens_collection
        self._credentials: Credentials | None = None

    def _get_client_config(self) -> dict[str, Any]:
        """Get OAuth client configuration for installed/desktop app."""
        return {
            "installed": {
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "redirect_uris": ["http://localhost", self._redirect_uri],
            }
        }

    def get_auth_url(self) -> str:
        """Generate Google OAuth authorization URL.

        Returns:
            Authorization URL for user to visit
        """
        flow = InstalledAppFlow.from_client_config(
            self._get_client_config(),
            scopes=self.SCOPES,
            redirect_uri=self._redirect_uri,
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
        return auth_url

    def exchange_code(self, code: str, user_id: str = "default") -> GoogleCalendarToken:
        """Exchange authorization code for tokens and store them.

        Args:
            code: Authorization code from OAuth callback
            user_id: User identifier for token storage

        Returns:
            Stored token object
        """
        flow = InstalledAppFlow.from_client_config(
            self._get_client_config(),
            scopes=self.SCOPES,
            redirect_uri=self._redirect_uri,
        )
        flow.fetch_token(code=code)
        credentials = flow.credentials

        token = GoogleCalendarToken(
            user_id=user_id,
            access_token=credentials.token,
            refresh_token=credentials.refresh_token or "",
            expires_at=credentials.expiry.replace(tzinfo=timezone.utc)
            if credentials.expiry
            else datetime.now(timezone.utc) + timedelta(hours=1),
            calendar_id="primary",
        )

        # Store in MongoDB (upsert)
        self._tokens_collection.update_one(
            {"_id": user_id},
            {"$set": token.to_dict()},
            upsert=True,
        )

        self._credentials = credentials
        return token

    def _load_credentials(self, user_id: str = "default") -> Credentials | None:
        """Load and refresh credentials from MongoDB.

        Args:
            user_id: User identifier

        Returns:
            Valid credentials or None if not found
        """
        token_doc = self._tokens_collection.find_one({"_id": user_id})
        if not token_doc:
            return None

        token = GoogleCalendarToken.from_dict(token_doc)

        credentials = Credentials(
            token=token.access_token,
            refresh_token=token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self._client_id,
            client_secret=self._client_secret,
            scopes=self.SCOPES,
        )

        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            try:
                from google.auth.transport.requests import Request

                credentials.refresh(Request())

                # Update stored token
                self._tokens_collection.update_one(
                    {"_id": user_id},
                    {
                        "$set": {
                            "access_token": credentials.token,
                            "expires_at": credentials.expiry.replace(tzinfo=timezone.utc)
                            if credentials.expiry
                            else datetime.now(timezone.utc) + timedelta(hours=1),
                        }
                    },
                )
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                return None

        return credentials

    def _get_service(self, user_id: str = "default"):
        """Get Google Calendar API service.

        Args:
            user_id: User identifier

        Returns:
            Calendar API service instance

        Raises:
            ValueError: If not authenticated
        """
        credentials = self._load_credentials(user_id)
        if not credentials:
            raise ValueError("Google Calendar not connected. Please authenticate first.")

        return build("calendar", "v3", credentials=credentials)

    def is_connected(self, user_id: str = "default") -> bool:
        """Check if Google Calendar is connected for user.

        Args:
            user_id: User identifier

        Returns:
            True if valid tokens exist
        """
        token_doc = self._tokens_collection.find_one({"_id": user_id})
        return token_doc is not None

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: str | None = None,
        attendees: list[str] | None = None,
        user_id: str = "default",
    ) -> dict[str, Any]:
        """Create a new calendar event.

        Args:
            summary: Event title
            start_time: Event start time
            end_time: Event end time
            description: Optional event description
            attendees: Optional list of attendee emails
            user_id: User identifier

        Returns:
            Created event data with id, htmlLink, etc.

        Raises:
            ValueError: If not authenticated
            HttpError: If API call fails
        """
        service = self._get_service(user_id)

        event_body: dict[str, Any] = {
            "summary": summary,
            "start": {
                "dateTime": start_time.isoformat(),
                "timeZone": "UTC",
            },
            "end": {
                "dateTime": end_time.isoformat(),
                "timeZone": "UTC",
            },
        }

        if description:
            event_body["description"] = description

        if attendees:
            event_body["attendees"] = [{"email": email} for email in attendees]

        try:
            event = service.events().insert(calendarId="primary", body=event_body).execute()
            logger.info(f"Created calendar event: {event.get('id')}")
            return {
                "id": event.get("id"),
                "summary": event.get("summary"),
                "start": event.get("start"),
                "end": event.get("end"),
                "htmlLink": event.get("htmlLink"),
            }
        except HttpError as e:
            logger.error(f"Failed to create event: {e}")
            raise

    def delete_event(self, event_id: str, user_id: str = "default") -> bool:
        """Delete a calendar event.

        Args:
            event_id: Google Calendar event ID
            user_id: User identifier

        Returns:
            True if deleted successfully

        Raises:
            ValueError: If not authenticated
            HttpError: If API call fails
        """
        service = self._get_service(user_id)

        try:
            service.events().delete(calendarId="primary", eventId=event_id).execute()
            logger.info(f"Deleted calendar event: {event_id}")
            return True
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Event not found: {event_id}")
                return False
            logger.error(f"Failed to delete event: {e}")
            raise

    def list_events(
        self,
        time_min: datetime | None = None,
        time_max: datetime | None = None,
        max_results: int = 10,
        user_id: str = "default",
    ) -> list[dict[str, Any]]:
        """List upcoming calendar events.

        Args:
            time_min: Start of time range (defaults to now)
            time_max: End of time range (defaults to 7 days from now)
            max_results: Maximum events to return
            user_id: User identifier

        Returns:
            List of event dictionaries

        Raises:
            ValueError: If not authenticated
            HttpError: If API call fails
        """
        service = self._get_service(user_id)

        if time_min is None:
            time_min = datetime.now(timezone.utc)
        if time_max is None:
            time_max = time_min + timedelta(days=7)

        try:
            events_result = (
                service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min.isoformat(),
                    timeMax=time_max.isoformat(),
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            return [
                {
                    "id": event.get("id"),
                    "summary": event.get("summary"),
                    "start": event.get("start"),
                    "end": event.get("end"),
                    "description": event.get("description"),
                    "htmlLink": event.get("htmlLink"),
                }
                for event in events
            ]
        except HttpError as e:
            logger.error(f"Failed to list events: {e}")
            raise

    def disconnect(self, user_id: str = "default") -> bool:
        """Remove stored tokens for user.

        Args:
            user_id: User identifier

        Returns:
            True if tokens were removed
        """
        result = self._tokens_collection.delete_one({"_id": user_id})
        self._credentials = None
        return result.deleted_count > 0
