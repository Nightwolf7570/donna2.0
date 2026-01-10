"""Tests for Calendar Service."""

from unittest.mock import Mock, patch
from datetime import datetime
from src.receptionist.calendar_service import CalendarService

@patch('src.receptionist.calendar_service.get_calendar_service')
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
            {'id': '1', 'summary': 'Test Event'}
        ]
    }
    
    service = CalendarService()
    events = service.list_events()
    
    assert len(events) == 1
    assert events[0]['summary'] == 'Test Event'

@patch('src.receptionist.calendar_service.get_calendar_service')
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
        'htmlLink': 'http://calendar.google.com/event'
    }
    
    service = CalendarService()
    start = datetime(2024, 1, 1, 10, 0)
    end = datetime(2024, 1, 1, 11, 0)
    
    result = service.create_event(
        summary="Meeting",
        start_time=start,
        end_time=end,
        attendees=["test@example.com"]
    )
    
    assert result['id'] == 'new_id'
    
    # Verify call arguments
    call_args = mock_events.insert.call_args[1]
    assert call_args['calendarId'] == 'primary'
    assert call_args['body']['summary'] == 'Meeting'
    assert call_args['body']['attendees'][0]['email'] == 'test@example.com'
