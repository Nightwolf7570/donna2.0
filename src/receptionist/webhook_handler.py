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
from .reasoning_engine import ReasoningEngine, Tool
from .vector_search import VectorSearch
from .voice_pipeline import VoicePipeline
from .connection_manager import manager as connection_manager
from .calendar_service import CalendarService

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
        audio_cache: dict[str, bytes] | None = None,
    ) -> None:
        """Initialize the webhook handler.
        
        Args:
            call_manager: Manager for call state.
            voice_pipeline: Pipeline for voice processing.
            reasoning_engine: Engine for AI reasoning (optional).
            vector_search: Vector search for context retrieval (optional).
            calendar_service: Calendar service for scheduling (optional).
            base_url: Base URL for TTS audio endpoints (e.g., ngrok URL).
            audio_cache: Shared dictionary for caching TTS audio bytes.
        """
        self._call_manager = call_manager
        self._voice_pipeline = voice_pipeline
        self._reasoning_engine = reasoning_engine
        self._vector_search = vector_search
        self._calendar_service = calendar_service
        self._base_url = base_url
        self._use_elevenlabs = voice_pipeline.is_elevenlabs_enabled() if voice_pipeline else False
        
        # Audio cache for TTS (shared with main app)
        self._audio_cache = audio_cache if audio_cache is not None else {}
    
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
            # Fallback to Polly if TTS fails (using Salli-Neural as preferred)
            response.say(text, voice="Polly.Salli-Neural")
        return response
    
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
        
        # Get greeting from voice pipeline
        greeting = self._voice_pipeline.get_greeting()
        
        # Build TwiML response with proper conversation flow
        response = TwiMLResponse()
        await self._add_speech(response, greeting)
        
        # Gather speech input from caller - this is the conversation loop
        response.gather(
            action="/process-speech",
            speech_timeout="auto",
        )
        
        # Fallback if caller doesn't respond
        response.say("I didn't hear anything. Please call back if you need assistance. Goodbye.")
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
        
        # Get call state for context
        call_state = await self._call_manager.get_call_state(call_sid)
        if not call_state:
            logger.warning(f"Call {call_sid} not active")
            response.hangup()
            return response
            
        context = call_state.context
        
        # Initialize history if needed - include the initial greeting so AI knows not to repeat it
        if "history" not in context:
            context["history"] = []
            # Mark that greeting was already given
            context["greeted"] = True
            
        # Generate response using reasoning engine (returns tuple with end_call flag)
        response_text, should_end_call = await self._generate_ai_response(
            speech_result, context, call_sid
        )
        
        # Broadcast assistant response to frontend
        await connection_manager.broadcast({
            "call_sid": call_sid,
            "speaker": "assistant",
            "transcript": response_text,
            "timestamp": int(datetime.now().timestamp() * 1000)
        })
        
        # Build TwiML response
        await self._add_speech(response, response_text)
        
        # End call or continue listening
        if should_end_call:
            logger.info(f"Ending call {call_sid} - AI requested hangup")
            response.hangup()
        else:
            response.gather(action="/process-speech")
        
        return response

    async def _generate_ai_response(
        self,
        speech_result: str,
        context: dict[str, Any],
        call_sid: str,
    ) -> tuple[str, bool]:
        """Generate an AI response using the reasoning engine.
        
        Args:
            speech_result: The transcribed speech.
            context: Current conversation context.
            call_sid: The call identifier.
            
        Returns:
            Tuple of (response_text, should_end_call).
        """
        if not self._reasoning_engine:
            return ("Thank you for calling. How can I assist you today?", False)
        
        # Track if we should end the call
        should_end_call = False
        
        # Extract caller info from transcript
        caller_info = self._reasoning_engine.extract_caller_info(speech_result)
        
        # Update context with caller info
        if caller_info.get("name") or caller_info.get("purpose"):
            await self._call_manager.update_context(call_sid, {
                "caller_name": caller_info.get("name"),
                "call_purpose": caller_info.get("purpose"),
            })
        
        # Check if caller is saying goodbye before even asking AI
        goodbye_phrases = ["thank you", "thanks", "bye", "goodbye", "that's all", "that is all", 
                          "that's it", "that is it", "no thanks", "i'm done", "i am done",
                          "no that's it", "nope", "no thank you", "have a good", "take care"]
        speech_lower = speech_result.lower().strip()
        
        # If caller is clearly saying goodbye, skip AI and end call
        if any(phrase in speech_lower for phrase in goodbye_phrases) and len(speech_lower) < 50:
            logger.info(f"Caller said goodbye phrase: '{speech_result}' - ending call {call_sid}")
            return ("You're welcome! Have a great day. Goodbye!", True)
        
        # Decide what tools to use
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
            
            elif tc.tool == Tool.CHECK_CALENDAR:
                # Check calendar availability using google_auth service
                date_str = tc.arguments.get("date", "")
                time_pref = tc.arguments.get("time_preference", "")
                if date_str:
                    try:
                        from datetime import datetime, timedelta
                        from zoneinfo import ZoneInfo
                        from .google_auth import get_calendar_service
                        
                        google_service = get_calendar_service()
                        if not google_service:
                            logger.error("Google Calendar service not available")
                            continue
                        
                        # Parse date in Pacific timezone
                        pacific_tz = ZoneInfo("America/Los_Angeles")
                        check_date = datetime.strptime(date_str, "%Y-%m-%d")
                        check_date = check_date.replace(hour=0, minute=0, second=0, tzinfo=pacific_tz)
                        end_date = check_date + timedelta(days=1)
                        
                        # Query Google Calendar directly
                        events_result = google_service.events().list(
                            calendarId='primary',
                            timeMin=check_date.isoformat(),
                            timeMax=end_date.isoformat(),
                            maxResults=10,
                            singleEvents=True,
                            orderBy='startTime'
                        ).execute()
                        
                        events = events_result.get('items', [])
                        
                        # Format availability info in human-readable format
                        if events:
                            busy_times = []
                            for event in events:
                                start = event.get("start", {})
                                time_raw = start.get("dateTime", start.get("date", ""))
                                summary = event.get("summary", "Busy")
                                
                                # Parse and format time nicely
                                try:
                                    if "T" in time_raw:
                                        event_time = datetime.fromisoformat(time_raw.replace("Z", "+00:00"))
                                        event_time_pacific = event_time.astimezone(pacific_tz)
                                        formatted_time = event_time_pacific.strftime("%I:%M %p").lstrip("0")
                                    else:
                                        formatted_time = "All day"
                                except:
                                    formatted_time = time_raw
                                
                                busy_times.append(f"{formatted_time}: {summary}")
                            context["calendar_busy"] = busy_times
                            context["calendar_check_date"] = check_date.strftime("%A, %B %d")
                        else:
                            context["calendar_busy"] = []
                            context["calendar_check_date"] = check_date.strftime("%A, %B %d")
                            context["calendar_available"] = True
                        
                        await self._call_manager.update_context(
                            call_sid, {
                                "calendar_busy": context.get("calendar_busy", []),
                                "calendar_check_date": context.get("calendar_check_date", date_str)
                            }
                        )
                        logger.info(f"Calendar check for {date_str}: {len(events)} events found")
                    except Exception as e:
                        logger.error(f"Calendar check failed: {e}")
                        context["calendar_error"] = str(e)
            
            elif tc.tool == Tool.END_CALL:
                # AI wants to end the call
                farewell = tc.arguments.get("farewell_message", "Goodbye!")
                should_end_call = True
                context["end_call_message"] = farewell
                logger.info(f"AI requested end_call with message: {farewell}")
            
            elif tc.tool == Tool.SCHEDULE_MEETING and self._calendar_service:
                # Schedule a meeting
                title = tc.arguments.get("title", "Meeting")
                date_str = tc.arguments.get("date", "")
                time_str = tc.arguments.get("time", "")
                duration = tc.arguments.get("duration_minutes", 30)
                attendee_name = tc.arguments.get("attendee_name", "")
                attendee_email = tc.arguments.get("attendee_email", "")
                
                if date_str and time_str:
                    try:
                        from datetime import datetime, timedelta
                        from zoneinfo import ZoneInfo
                        from dateutil import parser as date_parser
                        
                        logger.info(f"Attempting to schedule: {title} on {date_str} at {time_str}")
                        
                        # Parse date and time robustly
                        pacific_tz = ZoneInfo("America/Los_Angeles")
                        
                        try:
                            # Try combining them
                            datetime_str = f"{date_str} {time_str}"
                            start_time = date_parser.parse(datetime_str)
                        except:
                            # Try parsing separately
                            d = date_parser.parse(date_str)
                            t = date_parser.parse(time_str)
                            start_time = datetime.combine(d.date(), t.time())
                        
                        # Ensure timezone awareness (assuming Pacific as instructed)
                        if start_time.tzinfo is None:
                            start_time = start_time.replace(tzinfo=pacific_tz)
                        else:
                            start_time = start_time.astimezone(pacific_tz)
                            
                        end_time = start_time + timedelta(minutes=duration)
                        
                        # Build description
                        description = f"Call with {attendee_name}" if attendee_name else "Phone call meeting"
                        if context.get("caller_number"):
                            description += f"\nCaller: {context['caller_number']}"
                        
                        # Create the event using google_auth service (uses file-based auth)
                        from .google_auth import get_calendar_service
                        google_service = get_calendar_service()
                        
                        if google_service:
                            event_body = {
                                'summary': title,
                                'description': description,
                                'start': {
                                    'dateTime': start_time.isoformat(),
                                    'timeZone': 'America/Los_Angeles',
                                },
                                'end': {
                                    'dateTime': end_time.isoformat(),
                                    'timeZone': 'America/Los_Angeles',
                                },
                            }
                            
                            if attendee_email:
                                event_body['attendees'] = [{'email': attendee_email}]
                            
                            result = google_service.events().insert(
                                calendarId='primary',
                                body=event_body
                            ).execute()
                            
                            # Format time for display (12-hour format)
                            display_time = start_time.strftime("%I:%M %p").lstrip("0")
                            display_date = start_time.strftime("%A, %B %d")
                            
                            context["meeting_scheduled"] = True
                            context["meeting_details"] = {
                                "title": title,
                                "date": display_date,
                                "time": display_time,
                                "duration": duration,
                                "link": result.get("htmlLink", "")
                            }
                            await self._call_manager.update_context(
                                call_sid, {"meeting_scheduled": context["meeting_details"]}
                            )
                            logger.info(f"Meeting scheduled: {title} at {display_time} on {display_date}")
                        else:
                            context["meeting_error"] = "Calendar service not authenticated"
                            logger.error("Google Calendar service not available")
                    except Exception as e:
                        context["meeting_error"] = str(e)
                        logger.error(f"Meeting scheduling failed: {e}")
        
        # If ending call, use the farewell message directly
        if should_end_call and context.get("end_call_message"):
            response_text = context["end_call_message"]
        else:
            # Generate response with updated context
            response_text = await self._reasoning_engine.generate_response(
                speech_result, context
            )
        
        # Detect if AI is stuck in a loop or generating greetings
        current_lower = response_text.lower().strip()
        
        # Check if AI is generating a greeting when it shouldn't
        greeting_phrases = ["how can i help", "how may i help", "what can i do for you", "how can i assist"]
        is_greeting = any(phrase in current_lower for phrase in greeting_phrases)
        
        if is_greeting and context.get("greeted"):
            # AI is trying to greet again - check if we scheduled something
            logger.warning(f"AI generated greeting when already greeted - fixing for {call_sid}")
            
            if context.get("meeting_scheduled") and context.get("meeting_details"):
                # We scheduled a meeting but AI didn't acknowledge it properly
                details = context["meeting_details"]
                response_text = f"Done! I've scheduled '{details.get('title', 'your appointment')}' for {details.get('time', '')} on {details.get('date', '')}. Anything else?"
            elif speech_result and speech_result.strip():
                # Check if caller is saying goodbye/thanks
                goodbye_phrases = ["thank", "thanks", "bye", "goodbye", "that's all", "that's it", "no", "nothing"]
                if any(phrase in speech_result.lower() for phrase in goodbye_phrases):
                    response_text = "You're welcome! Have a great day. Goodbye!"
                    should_end_call = True
                else:
                    # Something went wrong - end the call gracefully
                    logger.error(f"AI keeps generating greetings, ending call for {call_sid}")
                    response_text = "I'm having some technical difficulties. Please try calling back in a moment. Goodbye!"
                    should_end_call = True
            else:
                response_text = "I'm sorry, I didn't catch that. Could you please repeat?"
        
        # Also check for exact repetition in history (but not for short responses)
        history = context.get("history", [])
        if len(history) >= 2 and len(current_lower) > 30:
            recent_responses = [h.get("assistant", "").lower().strip() for h in history[-2:]]
            
            # Check for exact repetition
            if current_lower in recent_responses:
                logger.warning(f"Detected AI loop (exact repeat) - forcing end call for {call_sid}")
                response_text = "I'm sorry, I'm having trouble understanding. Please call back and I'll be happy to help. Goodbye!"
                should_end_call = True
        
        # Store conversation exchange in history
        history = context.get("history", [])
        history.append({"user": speech_result, "assistant": response_text})
        await self._call_manager.update_context(call_sid, {"history": history})
        
        return (response_text, should_end_call)
    
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
