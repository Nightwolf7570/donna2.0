"""Call management for active call state and conversation flow."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class CallStatus(Enum):
    """Status of a call session."""
    
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CallState:
    """Represents the state of an active call session.
    
    Attributes:
        call_sid: Unique identifier for the call (from Twilio)
        caller_number: Phone number of the caller
        transcript_history: List of transcribed text from the conversation
        context: Accumulated context from searches and reasoning
        status: Current status of the call
        started_at: Timestamp when the call started
    """
    
    call_sid: str
    caller_number: str
    transcript_history: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    status: CallStatus = CallStatus.INITIATED
    started_at: datetime = field(default_factory=datetime.now)


class CallManager:
    """Manages active call state and orchestrates conversation flow.
    
    Maintains context across multiple exchanges within a call session,
    ensuring transcript history and accumulated context persist throughout
    the conversation.
    """
    
    def __init__(self) -> None:
        """Initialize the call manager with empty active calls."""
        self.active_calls: dict[str, CallState] = {}

    async def start_call(self, call_sid: str, caller_number: str) -> CallState:
        """Initialize a new call session.
        
        Creates a new CallState for the incoming call and stores it
        in the active calls dictionary.
        
        Args:
            call_sid: Unique identifier for the call (from Twilio)
            caller_number: Phone number of the caller
            
        Returns:
            The newly created CallState for this call session
        """
        call_state = CallState(
            call_sid=call_sid,
            caller_number=caller_number,
            transcript_history=[],
            context={},
            status=CallStatus.IN_PROGRESS,
            started_at=datetime.now(),
        )
        self.active_calls[call_sid] = call_state
        return call_state

    async def update_transcript(self, call_sid: str, text: str) -> None:
        """Add transcribed text to call history.
        
        Appends the new transcript to the call's transcript_history,
        maintaining context across multiple exchanges.
        
        Args:
            call_sid: Unique identifier for the call
            text: Transcribed text to add to history
            
        Raises:
            KeyError: If the call_sid is not found in active calls
        """
        if call_sid not in self.active_calls:
            raise KeyError(f"Call {call_sid} not found in active calls")
        
        self.active_calls[call_sid].transcript_history.append(text)

    async def update_context(self, call_sid: str, context_update: dict[str, Any]) -> None:
        """Update the accumulated context for a call.
        
        Merges new context information into the existing context,
        allowing context to accumulate rather than reset.
        
        Args:
            call_sid: Unique identifier for the call
            context_update: Dictionary of context to merge
            
        Raises:
            KeyError: If the call_sid is not found in active calls
        """
        if call_sid not in self.active_calls:
            raise KeyError(f"Call {call_sid} not found in active calls")
        
        self.active_calls[call_sid].context.update(context_update)

    async def get_call_state(self, call_sid: str) -> CallState | None:
        """Get the current state of a call.
        
        Args:
            call_sid: Unique identifier for the call
            
        Returns:
            The CallState if found, None otherwise
        """
        return self.active_calls.get(call_sid)

    async def end_call(self, call_sid: str) -> None:
        """Clean up call session.
        
        Marks the call as completed and removes it from active calls.
        
        Args:
            call_sid: Unique identifier for the call
            
        Raises:
            KeyError: If the call_sid is not found in active calls
        """
        if call_sid not in self.active_calls:
            raise KeyError(f"Call {call_sid} not found in active calls")
        
        call_state = self.active_calls[call_sid]
        call_state.status = CallStatus.COMPLETED
        del self.active_calls[call_sid]
