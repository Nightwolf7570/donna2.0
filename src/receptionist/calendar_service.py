"""Google Calendar service operations."""

import logging
from datetime import datetime, timedelta
from typing import Any

from googleapiclient.errors import HttpError

from .database import get_database
from .google_auth import get_calendar_service, retry_with_backoff

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for interacting with Google Calendar."""

    def __init__(self):
        """Initialize the calendar service."""
        # We don't initialize the service here to avoid doing it on import
        # It will be lazy-loaded via get_calendar_service()
        pass

    def list_events(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        max_results: int = 10
    ) -> list[dict[str, Any]]:
        """List upcoming calendar events.
        
        Args:
            start_time: Start of time range (defaults to now)
            end_time: End of time range (defaults to 7 days from now)
            max_results: Maximum number of events to return
            
        Returns:
            List of event objects
        """
        service = get_calendar_service()
        if not service:
            logger.warning("Calendar service unavailable - not authenticated")
            return []

        if not start_time:
            start_time = datetime.utcnow()
        if not end_time:
            end_time = start_time + timedelta(days=7)

        try:
            # Call the Calendar API
            events_result = retry_with_backoff(lambda: service.events().list(
                calendarId='primary',
                timeMin=start_time.isoformat() + 'Z',
                timeMax=end_time.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute())
            
            return events_result.get('items', [])
            
        except HttpError as e:
            logger.error(f"Failed to list events: {e}")
            return []

    def create_event(
        self,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        attendees: list[str] | None = None,
        description: str | None = None
    ) -> dict[str, Any] | None:
        """Create a new calendar event.
        
        Args:
            summary: Event title
            start_time: Event start (datetime)
            end_time: Event end (datetime)
            attendees: List of email addresses to invite
            description: Event description
            
        Returns:
            Created event object or None if failed
        """
        service = get_calendar_service()
        if not service:
            logger.warning("Calendar service unavailable")
            return None

        event = {
            'summary': summary,
            'description': description or '',
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',  # Assuming UTC for simplicity, should config
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
        }
        
        if attendees:
            event['attendees'] = [{'email': email} for email in attendees]

        try:
            created_event = retry_with_backoff(lambda: service.events().insert(
                calendarId='primary',
                body=event
            ).execute())
            
            logger.info(f"Created event: {created_event.get('htmlLink')}")
            return created_event
            
        except HttpError as e:
            logger.error(f"Failed to create event: {e}")
            return None

    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event."""
        service = get_calendar_service()
        if not service:
            return False

        try:
            retry_with_backoff(lambda: service.events().delete(
                calendarId='primary',
                eventId=event_id
            ).execute())
            return True
        except HttpError as e:
            logger.error(f"Failed to delete event {event_id}: {e}")
            return False

    def sync_events_to_db(self, days: int = 30) -> int:
        """Sync upcoming events to MongoDB for context availability.
        
        Args:
            days: Number of days forward to sync
            
        Returns:
            Number of new events imported
        """
        db_manager = get_database()
        if not db_manager:
            logger.error("Database unavailable")
            return 0
            
        events = self.list_events(max_results=100)  # Add day range logic here properly if needed
        if not events:
            return 0
            
        new_count = 0
        for event in events:
            event_id = event.get('id')
            if not event_id:
                continue
                
            # Check for existing
            existing = db_manager.calendar_events.find_one({"google_event_id": event_id})
            if existing:
                continue
                
            # Parse times
            start = event.get('start', {})
            end = event.get('end', {})
            
            # Handle full-day events (date only, no dateTime)
            start_dt = start.get('dateTime') or start.get('date')
            end_dt = end.get('dateTime') or end.get('date')
            
            event_doc = {
                'google_event_id': event_id,
                'calendar_id': 'primary',
                'summary': event.get('summary', 'Busy'),
                'description': event.get('description', ''),
                'start': start_dt,
                'end': end_dt,
                'attendees': [a.get('email') for a in event.get('attendees', []) if a.get('email')],
                'status': event.get('status', 'confirmed'),
                'source': 'calendar_import',
                'imported_at': datetime.utcnow()
            }
            
            db_manager.calendar_events.insert_one(event_doc)
            new_count += 1
            
        return new_count
