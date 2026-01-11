"""Webhook handler for Twilio call events and audio streaming.

This module provides the WebhookHandler class that processes incoming
Twilio webhooks for call initiation, audio streaming, and call status updates.
"""

import asyncio
import base64
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from .call_manager import CallManager, CallState
from .calendar_service import CalendarService
from .reasoning_engine import ReasoningEngine, Tool
from .vector_search import VectorSearch
from .voice_pipeline import VoicePipeline
from .connection_manager import manager as connection_manager

logger = logging.getLogger(__name__)


@dataclass
class TwilioRequest:
    """Represents an incoming Twilio webhook request."""
    
    call_sid: str
    from_number: str
    to_number: str
    call_status: str


@dataclass
class CallStatusRequest:
    """Represents a call status update from Twilio."""
    
    call_sid: str
    call_status: str
    call_duration: int | None = None


class TwiMLResponse:
    """Builder for TwiML XML responses.
    
    Provides a fluent interface for constructing TwiML responses
    for Twilio call flow control.
    """
    
    def __init__(self) -> None:
        """Initialize an empty TwiML response."""
        self._elements: list[str] = []
    
    def say(self, text: str, voice: str = "Polly.Joanna") -> "TwiMLResponse":
        """Add a Say verb to speak text to the caller.
        
        Args:
            text: The text to speak.
            voice: The voice to use (default: Polly.Joanna).
            
        Returns:
            Self for method chaining.
        """
        # Escape XML special characters
        escaped_text = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )
        self._elements.append(f'<Say voice="{voice}">{escaped_text}</Say>')
        return self
    
    def play(self, url: str) -> "TwiMLResponse":
        """Add a Play verb to play audio from a URL.
        
        Args:
            url: URL of the audio file to play.
            
        Returns:
            Self for method chaining.
        """
        self._elements.append(f'<Play>{url}</Play>')
        return self
    
    def gather(
        self,
        action: str,
        method: str = "POST",
        input_type: str = "speech",
        speech_timeout: str = "auto",
        speech_model: str = "phone_call",
        enhanced: bool = True,
        inner_say: str | None = None,
        voice: str = "Polly.Joanna",
    ) -> "TwiMLResponse":
        """Add a Gather verb to collect caller input.
        
        Args:
            action: URL to send gathered input to.
            method: HTTP method for the action URL.
            input_type: Type of input to gather (speech, dtmf, or both).
            speech_timeout: Timeout for speech input.
            speech_model: Speech recognition model.
            enhanced: Whether to use enhanced speech recognition.
            inner_say: Optional text to say while gathering.
            voice: Voice for inner Say element.
            
        Returns:
            Self for method chaining.
        """
        enhanced_str = "true" if enhanced else "false"
        gather_attrs = (
            f'input="{input_type}" action="{action}" method="{method}" '
            f'speechTimeout="{speech_timeout}" speechModel="{speech_model}" '
            f'enhanced="{enhanced_str}"'
        )
        
        if inner_say:
            escaped_inner = (
                inner_say.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&apos;")
            )
            self._elements.append(
                f'<Gather {gather_attrs}>'
                f'<Say voice="{voice}">{escaped_inner}</Say>'
                f'</Gather>'
            )
        else:
            self._elements.append(f'<Gather {gather_attrs}></Gather>')
        
        return self

    def connect_stream(
        self,
        url: str,
        name: str = "audio_stream",
    ) -> "TwiMLResponse":
        """Add a Connect verb with Stream for bidirectional audio.
        
        Args:
            url: WebSocket URL for the audio stream.
            name: Name identifier for the stream.
            
        Returns:
            Self for method chaining.
        """
        self._elements.append(
            f'<Connect>'
            f'<Stream url="{url}" name="{name}" />'
            f'</Connect>'
        )
        return self
    
    def pause(self, length: int = 1) -> "TwiMLResponse":
        """Add a Pause verb.
        
        Args:
            length: Pause duration in seconds.
            
        Returns:
            Self for method chaining.
        """
        self._elements.append(f'<Pause length="{length}" />')
        return self
    
    def hangup(self) -> "TwiMLResponse":
        """Add a Hangup verb to end the call.
        
        Returns:
            Self for method chaining.
        """
        self._elements.append('<Hangup />')
        return self
    
    def redirect(self, url: str, method: str = "POST") -> "TwiMLResponse":
        """Add a Redirect verb.
        
        Args:
            url: URL to redirect to.
            method: HTTP method for the redirect.
            
        Returns:
            Self for method chaining.
        """
        self._elements.append(f'<Redirect method="{method}">{url}</Redirect>')
        return self
    
    def to_xml(self) -> str:
        """Convert the response to TwiML XML string.
        
        Returns:
            Complete TwiML XML document.
        """
        elements_str = "\n    ".join(self._elements)
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {elements_str}
</Response>"""


class WebhookHandler:
    """Handles incoming Twilio webhooks for call events.
    
    This class processes:
    - Incoming call webhooks to initiate call sessions
    - Audio stream WebSocket connections for real-time transcription
    - Call status updates for session cleanup
    """
    
    def __init__(
        self,
        call_manager: CallManager,
        voice_pipeline: VoicePipeline,
        reasoning_engine: ReasoningEngine | None = None,
        vector_search: VectorSearch | None = None,
        calendar_service: CalendarService | None = None,
        base_url: str = "",
    ) -> None:
        """Initialize the webhook handler.
        
        Args:
            call_manager: Manager for call state.
            voice_pipeline: Pipeline for voice processing.
            reasoning_engine: Engine for AI reasoning (optional).
            vector_search: Vector search for context retrieval (optional).
            calendar_service: Calendar service for scheduling (optional).
            base_url: Base URL for TTS audio endpoints (e.g., ngrok URL).
        """
        self._call_manager = call_manager
        self._voice_pipeline = voice_pipeline
        self._reasoning_engine = reasoning_engine
        self._vector_search = vector_search
        self._calendar_service = calendar_service
        self._base_url = base_url
        self._use_elevenlabs = voice_pipeline.is_elevenlabs_enabled() if voice_pipeline else False
        
        # Audio cache for TTS
        self._audio_cache: dict[str, bytes] = {}
    
    def _get_audio_url(self, audio_id: str) -> str:
        """Get the full URL for a cached audio file."""
        return f"{self._base_url}/tts/{audio_id}"
    
    async def _cache_tts(self, text: str) -> str:
        """Generate TTS audio and cache it, return the audio ID.
        
        Args:
            text: Text to convert to speech.
            
        Returns:
            Audio ID for the cached audio.
        """
        import hashlib
        text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
        
        if text_hash not in self._audio_cache:
            try:
                audio_bytes = await self._voice_pipeline.synthesize_speech(text)
                self._audio_cache[text_hash] = audio_bytes
                
                # Also add to global cache in main.py
                from . import main
                main.audio_cache[text_hash] = audio_bytes
                
            except Exception as e:
                logger.error(f"TTS caching failed: {e}")
                return ""
        
        return text_hash
    
    async def _add_speech(self, response: TwiMLResponse, text: str) -> TwiMLResponse:
        """Add speech using Deepgram TTS for consistent voice.
        
        Args:
            response: TwiML response builder.
            text: Text to speak.
            
        Returns:
            Updated TwiML response.
        """
        audio_id = await self._cache_tts(text)
        if audio_id and self._base_url:
            response.play(self._get_audio_url(audio_id))
        else:
            # Fallback to Polly if TTS fails
            response.say(text, voice="Polly.Joanna")
        return response
    
    def _parse_appointment_time(self, when: str) -> datetime | None:
        """Parse natural language time into a datetime.
        
        Args:
            when: Natural language time like "tomorrow at 2pm", "Monday 10am"
            
        Returns:
            Parsed datetime or None if parsing fails.
        """
        import re
        from datetime import timedelta
        
        now = datetime.now()
        when_lower = when.lower().strip()
        
        # Try to extract time (e.g., "2pm", "10:30am", "14:00")
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', when_lower)
        hour = 9  # default to 9am
        minute = 0
        
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            meridiem = time_match.group(3)
            
            if meridiem == 'pm' and hour != 12:
                hour += 12
            elif meridiem == 'am' and hour == 12:
                hour = 0
        
        # Parse the date part
        target_date = now.date()
        
        if 'today' in when_lower:
            target_date = now.date()
        elif 'tomorrow' in when_lower:
            target_date = (now + timedelta(days=1)).date()
        elif 'next week' in when_lower:
            target_date = (now + timedelta(days=7)).date()
        else:
            # Check for day names
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for i, day in enumerate(days):
                if day in when_lower:
                    current_day = now.weekday()
                    days_ahead = i - current_day
                    if days_ahead <= 0:  # Target day already happened this week
                        days_ahead += 7
                    target_date = (now + timedelta(days=days_ahead)).date()
                    break
            else:
                # Try parsing ISO format or common formats
                date_patterns = [
                    r'(\d{4})-(\d{2})-(\d{2})',  # 2026-01-15
                    r'(\d{1,2})/(\d{1,2})/(\d{4})',  # 1/15/2026
                    r'(\d{1,2})/(\d{1,2})',  # 1/15 (assume current year)
                ]
                for pattern in date_patterns:
                    match = re.search(pattern, when_lower)
                    if match:
                        groups = match.groups()
                        if len(groups) == 3:
                            if '-' in pattern:
                                year, month, day = int(groups[0]), int(groups[1]), int(groups[2])
                            else:
                                month, day, year = int(groups[0]), int(groups[1]), int(groups[2])
                        else:
                            month, day = int(groups[0]), int(groups[1])
                            year = now.year
                        try:
                            from datetime import date
                            target_date = date(year, month, day)
                        except ValueError:
                            pass
                        break
        
        try:
            return datetime.combine(target_date, datetime.min.time().replace(hour=hour, minute=minute))
        except (ValueError, TypeError):
            return None
    
    async def handle_incoming_call(self, request: TwilioRequest) -> TwiMLResponse:
        """Process incoming call webhook and return TwiML to start streaming.
        
        Creates a new call session and returns TwiML that greets the caller
        and begins gathering speech input.
        
        Args:
            request: The incoming Twilio webhook request.
            
        Returns:
            TwiML response to control call flow.
        """
        logger.info(
            f"Incoming call: {request.call_sid} from {request.from_number}"
        )
        
        # Initialize call session
        await self._call_manager.start_call(
            request.call_sid, request.from_number
        )
        
        # Get greeting message
        greeting = self._voice_pipeline.get_greeting()
        
        # Build TwiML response
        response = TwiMLResponse()
        await self._add_speech(response, greeting)
        response.gather(
            action="/process-speech",
            inner_say="Please go ahead.",
        )
        response.say("I didn't hear anything. Goodbye.")
        response.hangup()
        
        return response

    async def handle_audio_stream(self, websocket: WebSocket) -> None:
        """Handle bidirectional audio streaming via WebSocket.
        
        Receives audio from Twilio, transcribes it using the voice pipeline,
        processes it through the reasoning engine, and sends responses back.
        
        Args:
            websocket: The WebSocket connection from Twilio.
        """
        await websocket.accept()
        
        call_sid: str | None = None
        stream_sid: str | None = None
        
        try:
            async for message in websocket.iter_text():
                try:
                    data = json.loads(message)
                    event_type = data.get("event")
                    
                    if event_type == "connected":
                        logger.info("WebSocket connected to Twilio")
                    
                    elif event_type == "start":
                        # Extract call and stream identifiers
                        start_data = data.get("start", {})
                        call_sid = start_data.get("callSid")
                        stream_sid = start_data.get("streamSid")
                        logger.info(
                            f"Stream started: call={call_sid}, stream={stream_sid}"
                        )
                    
                    elif event_type == "media":
                        # Process incoming audio
                        media_data = data.get("media", {})
                        payload = media_data.get("payload", "")
                        
                        if payload and call_sid:
                            # Decode base64 audio
                            audio_bytes = base64.b64decode(payload)
                            
                            # Forward to voice pipeline for transcription
                            await self._process_audio_chunk(
                                call_sid, audio_bytes, websocket, stream_sid
                            )
                    
                    elif event_type == "stop":
                        logger.info(f"Stream stopped: {stream_sid}")
                        break
                    
                except json.JSONDecodeError:
                    logger.warning("Received invalid JSON on WebSocket")
                    continue
        
        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: {call_sid}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Clean up if needed
            if call_sid:
                logger.info(f"Cleaning up stream for call: {call_sid}")
    
    async def _process_audio_chunk(
        self,
        call_sid: str,
        audio_bytes: bytes,
        websocket: WebSocket,
        stream_sid: str | None,
    ) -> None:
        """Process an audio chunk from the stream.
        
        This is a simplified implementation that collects audio and
        processes it when silence is detected. A production implementation
        would use continuous streaming transcription.
        
        Args:
            call_sid: The call identifier.
            audio_bytes: Raw audio bytes.
            websocket: WebSocket for sending responses.
            stream_sid: The stream identifier.
        """
        # Get or create audio buffer for this call
        call_state = await self._call_manager.get_call_state(call_sid)
        if not call_state:
            return
        
        # In a production system, this would stream to Deepgram
        # For now, we accumulate and process in batches
        # The actual streaming transcription is handled by the
        # voice_pipeline.transcribe_stream() method
        
        # Forward audio bytes to voice pipeline (implementation depends on
        # how the streaming is set up with Deepgram)
        logger.debug(f"Received {len(audio_bytes)} bytes of audio for {call_sid}")
    
    async def handle_process_speech(
        self,
        call_sid: str,
        speech_result: str,
        confidence: float = 0.0,
    ) -> TwiMLResponse:
        """Process speech input from Twilio's Gather verb.
        
        Uses the reasoning engine to analyze the speech and generate
        an appropriate response.
        
        Args:
            call_sid: The call identifier.
            speech_result: Transcribed speech from Twilio.
            confidence: Confidence score of the transcription.
            
        Returns:
            TwiML response with AI-generated reply.
        """
        logger.info(
            f"Speech from {call_sid}: '{speech_result}' (confidence: {confidence})"
        )
        
        # Broadcast user speech to frontend
        await connection_manager.broadcast({
            "call_sid": call_sid,
            "speaker": "caller",
            "transcript": speech_result,
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
        
        response = TwiMLResponse()
        
        # Handle empty speech
        if not speech_result or not speech_result.strip():
            await self._add_speech(response, "I didn't catch that. Could you please repeat?")
            response.gather(action="/process-speech")
            return response
        
        # Update call transcript
        try:
            await self._call_manager.update_transcript(call_sid, speech_result)
        except KeyError:
            # Call not found, may have ended
            await self._add_speech(response, "I'm sorry, there was an error. Goodbye.")
            response.hangup()
            return response
        
        # Generate response using reasoning engine
        # (context will be retrieved fresh inside _generate_ai_response)
        response_text = await self._generate_ai_response(
            speech_result, call_sid
        )
        
        # Broadcast assistant response to frontend
        await connection_manager.broadcast({
            "call_sid": call_sid,
            "speaker": "assistant",
            "transcript": response_text,
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
        
        # Build TwiML response with ElevenLabs voice
        await self._add_speech(response, response_text)
        response.gather(action="/process-speech")
        await self._add_speech(response, "Is there anything else I can help you with?")
        response.gather(action="/process-speech")
        
        return response

    async def _generate_ai_response(
        self,
        speech_result: str,
        call_sid: str,
    ) -> str:
        """Generate an AI response using the reasoning engine.
        
        Args:
            speech_result: The transcribed speech.
            call_sid: The call identifier.
            
        Returns:
            Generated response text.
        """
        if not self._reasoning_engine:
            return "Thank you for calling. How can I assist you today?"
        
        # Get fresh context from call state (includes history from previous exchanges)
        call_state = await self._call_manager.get_call_state(call_sid)
        if not call_state:
            return "I'm sorry, there was an error. Goodbye."
        context = call_state.context.copy()  # Work with a copy to avoid mutation issues
        
        # Extract caller info from transcript
        caller_info = self._reasoning_engine.extract_caller_info(speech_result)
        
        # Update context with caller info
        if caller_info.get("name") or caller_info.get("purpose"):
            context["caller_name"] = caller_info.get("name")
            context["call_purpose"] = caller_info.get("purpose")
            await self._call_manager.update_context(call_sid, {
                "caller_name": caller_info.get("name"),
                "call_purpose": caller_info.get("purpose"),
            })
        
        # Decide what tools to use (with current context including history)
        tool_calls = await self._reasoning_engine.decide_action(
            speech_result, context
        )
        
        # Execute tool calls
        for tc in tool_calls:
            if tc.tool == Tool.SEARCH_CONTACTS and self._vector_search:
                name = tc.arguments.get("name", "")
                if name:
                    results = await self._vector_search.search_contacts(name)
                    contacts = [
                        {
                            "name": r.metadata.get("name"),
                            "email": r.metadata.get("email"),
                            "company": r.metadata.get("company"),
                        }
                        for r in results
                    ]
                    context["contacts"] = contacts
                    await self._call_manager.update_context(
                        call_sid, {"contacts": contacts}
                    )
            
            elif tc.tool == Tool.SEARCH_EMAILS and self._vector_search:
                query = tc.arguments.get("query", "")
                if query:
                    results = await self._vector_search.search_emails(query)
                    emails = [
                        {
                            "sender": r.metadata.get("sender"),
                            "subject": r.metadata.get("subject"),
                            "content": r.content[:200] if r.content else "",
                        }
                        for r in results
                    ]
                    context["emails"] = emails
                    await self._call_manager.update_context(
                        call_sid, {"emails": emails}
                    )
            
            elif tc.tool == Tool.SCHEDULE_APPOINTMENT and self._calendar_service:
                what = tc.arguments.get("what", "")
                who = tc.arguments.get("who", "")
                when = tc.arguments.get("when", "")

                if not self._calendar_service.is_connected():
                    context["appointment_scheduled"] = {
                        "success": False,
                        "error": "Google Calendar not connected. Please authenticate first."
                    }
                elif what and who and when:
                    # Parse the natural language date
                    appointment_time = self._parse_appointment_time(when)
                    if appointment_time:
                        # Default to 30 minute appointment
                        from datetime import timedelta
                        end_time = appointment_time + timedelta(minutes=30)

                        # Create the event with minimal info
                        summary = f"{what} with {who}"
                        try:
                            result = self._calendar_service.create_event(
                                summary=summary,
                                start_time=appointment_time,
                                end_time=end_time,
                                description=f"Scheduled via phone call with {who}"
                            )

                            if result:
                                context["appointment_scheduled"] = {
                                    "what": what,
                                    "who": who,
                                    "when": appointment_time.strftime("%A, %B %d at %I:%M %p"),
                                    "success": True
                                }
                                await self._call_manager.update_context(
                                    call_sid, {"appointment_scheduled": context["appointment_scheduled"]}
                                )
                                logger.info(f"Scheduled appointment: {summary} at {appointment_time}")
                            else:
                                context["appointment_scheduled"] = {"success": False, "error": "Failed to create event"}
                        except ValueError as e:
                            context["appointment_scheduled"] = {"success": False, "error": str(e)}
                    else:
                        context["appointment_scheduled"] = {"success": False, "error": f"Could not understand time: {when}"}
        
        # Refresh context from call state to get latest updates (including any history)
        call_state = await self._call_manager.get_call_state(call_sid)
        if call_state:
            context = call_state.context.copy()
        
        # Generate response with updated context (including history)
        response_text = await self._reasoning_engine.generate_response(
            speech_result, context
        )
        
        # Store conversation exchange in history
        history = context.get("history", [])
        history.append({"user": speech_result, "assistant": response_text})
        await self._call_manager.update_context(call_sid, {"history": history})
        
        return response_text
    
    async def handle_call_status(self, request: CallStatusRequest) -> dict[str, str]:
        """Process call status updates from Twilio.
        
        Handles call completion, failure, and other status changes.
        
        Args:
            request: The call status update request.
            
        Returns:
            Acknowledgment response.
        """
        logger.info(
            f"Call {request.call_sid} status: {request.call_status}, "
            f"duration: {request.call_duration}s"
        )
        
        # End call session for terminal statuses
        terminal_statuses = {"completed", "failed", "busy", "no-answer", "canceled"}
        
        if request.call_status in terminal_statuses:
            try:
                # Get call state before ending it
                call_state = await self._call_manager.get_call_state(request.call_sid)
                
                if call_state:
                    # Analyze call outcome if we have a reasoning engine and transcript
                    outcome_data = {}
                    if self._reasoning_engine and call_state.transcript_history:
                        try:
                            # Use modeling for analysis
                            outcome = await self._reasoning_engine.analyze_call_outcome(
                                call_state.transcript_history
                            )
                            outcome_data = outcome.to_dict()
                            logger.info(f"Analyzed call outcome: {outcome.decision_label}")
                        except Exception as e:
                            logger.error(f"Failed to analyze call outcome: {e}")
                    
                    # Persist to database
                    from .database import get_database
                    from datetime import datetime
                    
                    db = get_database()
                    if db:
                        call_doc = {
                            "call_sid": call_state.call_sid,
                            "caller_number": call_state.caller_number,
                            "identified_name": call_state.context.get("caller_name"),
                            "call_purpose": call_state.context.get("call_purpose"),
                            "outcome": request.call_status,
                            "timestamp": call_state.started_at,
                            "end_timestamp": datetime.now(),
                            "duration": request.call_duration or 0,
                            "transcript": call_state.transcript_history,
                            # Add analysis fields
                            "summary": outcome_data.get("summary", "No summary available"),
                            "decision": outcome_data.get("decision", "handled"),
                            "decision_label": outcome_data.get("decision_label", "Call Processed"),
                            "reasoning": outcome_data.get("reasoning", ""),
                            "action_taken": outcome_data.get("action_taken", ""),
                        }
                        
                        # Add company if found in context
                        if "contacts" in call_state.context:
                            for contact in call_state.context["contacts"]:
                                if contact.get("company"):
                                    call_doc["company"] = contact["company"]
                                    break
                        
                        try:
                            db.calls.insert_one(call_doc)
                            logger.info(f"Saved call record for {request.call_sid}")
                        except Exception as e:
                            logger.error(f"Failed to save call record: {e}")

                await self._call_manager.end_call(request.call_sid)
                
            except KeyError:
                # Call already ended or never started
                logger.debug(f"Call {request.call_sid} not found in active calls")
        
        return {"status": "ok"}
