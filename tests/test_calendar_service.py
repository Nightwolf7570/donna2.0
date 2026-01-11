"""Tests for Calendar Service."""

from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from src.receptionist.calendar_service import CalendarService


def create_calendar_service():
    """Create a CalendarService instance with mock dependencies."""
    mock_collection = MagicMock()
    return CalendarService(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8000/google/callback",
        tokens_collection=mock_collection,
    )


@patch.object(CalendarService, '_get_service')
def test_list_events(mock_get_service):
    """Test listing events from calendar."""
    mock_service = Mock()
    mock_get_service.return_value = mock_service
    
    # Mock event list response
    mock_events = Mock()
    mock_service.events.return_value = mock_events
    mock_list = Mock()
    mock_events.list.return_value = mock_list
    mock_list.execute.return_value = {
        'items': [
            {
                'id': '1', 
                'summary': 'Test Event',
                'start': {'dateTime': '2024-01-01T10:00:00Z'},
                'end': {'dateTime': '2024-01-01T11:00:00Z'},
                'description': 'Test description',
                'htmlLink': 'http://calendar.google.com/event/1'
            }
        ]
    }
    
    service = create_calendar_service()
    events = service.list_events()
    
    assert len(events) == 1
    assert events[0]['summary'] == 'Test Event'
    assert events[0]['id'] == '1'


@patch.object(CalendarService, '_get_service')
def test_create_event(mock_get_service):
    """Test creating a new event."""
    mock_service = Mock()
    mock_get_service.return_value = mock_service
    
    # Mock create response
    mock_events = Mock()
    mock_service.events.return_value = mock_events
    mock_insert = Mock()
    mock_events.insert.return_value = mock_insert
    mock_insert.execute.return_value = {
        'id': 'new_id',
        'summary': 'Meeting',
        'start': {'dateTime': '2024-01-01T10:00:00Z'},
        'end': {'dateTime': '2024-01-01T11:00:00Z'},
        'htmlLink': 'http://calendar.google.com/event'
    }
    
    service = create_calendar_service()
    start = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 1, 11, 0, tzinfo=timezone.utc)
    
    result = service.create_event(
        summary="Meeting",
        start_time=start,
        end_time=end,
        attendees=["test@example.com"]
    )
    
    assert result['id'] == 'new_id'
    assert result['summary'] == 'Meeting'
    
    # Verify call arguments
    call_args = mock_events.insert.call_args[1]
    assert call_args['calendarId'] == 'primary'
    assert call_args['body']['summary'] == 'Meeting'
    assert call_args['body']['attendees'][0]['email'] == 'test@example.com'


@patch.object(CalendarService, '_get_service')
def test_delete_event(mock_get_service):
    """Test deleting an event."""
    mock_service = Mock()
    mock_get_service.return_value = mock_service
    
    # Mock delete response
    mock_events = Mock()
    mock_service.events.return_value = mock_events
    mock_delete = Mock()
    mock_events.delete.return_value = mock_delete
    mock_delete.execute.return_value = {}
    
    service = create_calendar_service()
    result = service.delete_event("event_123")
    
    assert result is True
    mock_events.delete.assert_called_once_with(calendarId='primary', eventId='event_123')


def test_is_connected_with_token():
    """Test is_connected returns True when token exists."""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = {
        '_id': 'default',
        'access_token': 'test_token',
        'refresh_token': 'test_refresh',
    }
    
    service = CalendarService(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8000/google/callback",
        tokens_collection=mock_collection,
    )
    
    assert service.is_connected() is True


def test_is_connected_without_token():
    """Test is_connected returns False when no token exists."""
    mock_collection = MagicMock()
    mock_collection.find_one.return_value = None
    
    service = CalendarService(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8000/google/callback",
        tokens_collection=mock_collection,
    )
    
    assert service.is_connected() is False


def test_get_auth_url():
    """Test generating OAuth authorization URL."""
    service = create_calendar_service()
    auth_url = service.get_auth_url()
    
    assert "accounts.google.com" in auth_url
    assert "client_id=test_client_id" in auth_url
    assert "redirect_uri" in auth_url


def test_disconnect():
    """Test disconnecting/removing tokens."""
    mock_collection = MagicMock()
    mock_collection.delete_one.return_value = Mock(deleted_count=1)
    
    service = CalendarService(
        client_id="test_client_id",
        client_secret="test_client_secret",
        redirect_uri="http://localhost:8000/google/callback",
        tokens_collection=mock_collection,
    )
    
    result = service.disconnect()
    
    assert result is True
    mock_collection.delete_one.assert_called_once_with({"_id": "default"})
