"""FastAPI application with Twilio webhook handlers and Admin UI REST API.

This module provides:
- Twilio webhook endpoints for call handling
- WebSocket endpoint for audio streaming
- REST API endpoints for Admin UI (contacts, emails, calls, config)
- Audio TTS endpoint for ElevenLabs voice synthesis
"""

import base64
import hashlib
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Form, HTTPException, Query, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .call_manager import CallManager
from .config import Settings, get_settings

from .database import DatabaseManager, get_database
from .google_auth import authenticate_google, SCOPES
from .calendar_service import CalendarService
from .models import BusinessConfig, Contact, Email, ValidationError
from .reasoning_engine import ReasoningEngine
from .vector_search import VectorSearch
from .voice_pipeline import VoicePipeline
from .webhook_handler import (
    CallStatusRequest,
    TwilioRequest,
    TwiMLResponse,
    WebhookHandler,
)
from .connection_manager import manager as connection_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for API requests/responses
class ContactInput(BaseModel):
    """Input model for creating/updating contacts."""
    
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    phone: str | None = None
    company: str | None = None


class ContactResponse(BaseModel):
    """Response model for contact data."""
    
    id: str
    name: str
    email: str
    phone: str | None = None
    company: str | None = None


class EmailInput(BaseModel):
    """Input model for creating emails."""
    
    sender: str = Field(..., min_length=1)
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    timestamp: datetime | None = None


class EmailResponse(BaseModel):
    """Response model for email data."""
    
    id: str
    sender: str
    subject: str
    body: str
    timestamp: datetime


class CallRecord(BaseModel):
    """Response model for call history."""
    
    call_sid: str
    caller_number: str
    identified_name: str | None = None
    company: str | None = None
    call_purpose: str | None = None
    outcome: str
    timestamp: datetime
    duration: int = 0
    transcript: list[str] = []
    

    
    # Analysis fields
    summary: str | None = None
    decision: str | None = None
    decision_label: str | None = None
    reasoning: str | None = None
    action_taken: str | None = None


class SystemConfig(BaseModel):
    """Response model for system configuration."""
    
    server_host: str
    server_port: int
    # Note: API keys are not exposed for security


class BulkEmailImport(BaseModel):
    """Input model for bulk email import."""
    
    emails: list[EmailInput]


class BusinessConfigInput(BaseModel):
    """Input model for updating business configuration."""
    
    ceo_name: str = Field(..., min_length=1)
    company_name: str | None = None
    company_description: str | None = None


class BusinessConfigResponse(BaseModel):
    """Response model for business configuration."""
    
    ceo_name: str
    company_name: str | None = None
    company_description: str | None = None


class EventInput(BaseModel):
    """Input model for creating calendar events."""
    
    summary: str = Field(..., min_length=1)
    description: str | None = None
    start_time: datetime
    end_time: datetime
    attendees: list[str] = []


# Global instances
call_manager: CallManager | None = None
voice_pipeline: VoicePipeline | None = None
reasoning_engine: ReasoningEngine | None = None
vector_search: VectorSearch | None = None
webhook_handler: WebhookHandler | None = None
db_manager: DatabaseManager | None = None
calendar_service: CalendarService | None = None

# Audio cache for TTS (text hash -> audio bytes)
audio_cache: dict[str, bytes] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global call_manager, voice_pipeline, reasoning_engine, vector_search
    global webhook_handler, db_manager, calendar_service
    
    settings = get_settings()
    
    # Initialize database first (needed to load config)
    try:
        db_manager = get_database()
        logger.info("Database connection initialized")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        db_manager = None
    
    # Load business config from MongoDB (no hardcoded defaults)
    business_config = None
    if db_manager:
        config_doc = db_manager.business_config.find_one({"_id": "business_config"})
        if config_doc:
            business_config = BusinessConfig.from_dict(config_doc)
            logger.info(f"Loaded business config: CEO is {business_config.ceo_name}")
        else:
            logger.info("No business config found - configure via PUT /config/business")
    
    # Initialize core components
    call_manager = CallManager()
    voice_pipeline = VoicePipeline(settings)
    reasoning_engine = ReasoningEngine(settings, business_config=business_config)
    
    # Initialize vector search
    try:
        vector_search = VectorSearch(voyage_api_key=settings.voyage_api_key)
        logger.info("VectorSearch initialized")
    except Exception as e:
        logger.warning(f"VectorSearch initialization failed: {e}")
        vector_search = None
    
    # Initialize calendar service (before webhook handler)
    calendar_service = CalendarService()
    
    # Initialize webhook handler with all services
    webhook_handler = WebhookHandler(
        call_manager=call_manager,
        voice_pipeline=voice_pipeline,
        reasoning_engine=reasoning_engine,
        vector_search=vector_search,
        calendar_service=calendar_service,
        base_url=settings.base_url,
        audio_cache=audio_cache,
    )
    
    logger.info("AI Receptionist started")
    yield
    
    # Cleanup
    if reasoning_engine:
        await reasoning_engine.close()
    if db_manager:
        db_manager.close()
    
    logger.info("AI Receptionist stopped")


app = FastAPI(
    title="AI Receptionist",
    description="Context-aware voice assistant with adaptive retrieval",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware for Admin UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to Admin UI origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def twiml_response(twiml: TwiMLResponse | str) -> Response:
    """Create a TwiML XML response."""
    content = twiml.to_xml() if isinstance(twiml, TwiMLResponse) else twiml
    return Response(content=content, media_type="application/xml")


# =============================================================================
# Twilio Webhook Endpoints
# =============================================================================

@app.post("/incoming-call")
async def handle_incoming_call(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(default="ringing"),
):
    """Handle incoming call webhook from Twilio.
    
    Returns TwiML to greet caller and start gathering speech.
    """
    if not webhook_handler:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    request = TwilioRequest(
        call_sid=CallSid,
        from_number=From,
        to_number=To,
        call_status=CallStatus,
    )
    
    response = await webhook_handler.handle_incoming_call(request)
    return twiml_response(response)


@app.post("/process-speech")
async def process_speech(
    CallSid: str = Form(...),
    SpeechResult: str = Form(default=""),
    Confidence: float = Form(default=0.0),
):
    """Process speech input from caller.
    
    Uses reasoning engine to decide actions and generate response.
    """
    if not webhook_handler:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    response = await webhook_handler.handle_process_speech(
        call_sid=CallSid,
        speech_result=SpeechResult,
        confidence=Confidence,
    )
    return twiml_response(response)


@app.post("/call-status")
async def handle_call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: int = Form(default=0),
):
    """Handle call status updates from Twilio."""
    if not webhook_handler:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    request = CallStatusRequest(
        call_sid=CallSid,
        call_status=CallStatus,
        call_duration=CallDuration,
    )
    
    return await webhook_handler.handle_call_status(request)


@app.websocket("/audio-stream")
async def audio_stream(websocket: WebSocket):
    """WebSocket endpoint for bidirectional audio streaming with Twilio."""
    if not webhook_handler:
        await websocket.close(code=1011, reason="Service not initialized")
        return
    
    await webhook_handler.handle_audio_stream(websocket)


@app.websocket("/ws/transcription")
async def transcription_stream(websocket: WebSocket):
    """WebSocket endpoint for live transcription updates to frontend."""
    await connection_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        connection_manager.disconnect(websocket)


# =============================================================================
# Admin UI REST API - Contacts
# =============================================================================

@app.get("/contacts", response_model=list[ContactResponse])
def get_contacts(
    limit: int = Query(default=100, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
):
    """Get all contacts with pagination."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    contacts = list(
        db_manager.contacts.find().skip(skip).limit(limit)
    )
    
    return [
        ContactResponse(
            id=str(c.get("_id", "")),
            name=c.get("name", ""),
            email=c.get("email", ""),
            phone=c.get("phone"),
            company=c.get("company"),
        )
        for c in contacts
    ]


@app.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: str):
    """Get a specific contact by ID."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    contact = db_manager.contacts.find_one({"_id": contact_id})
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return ContactResponse(
        id=str(contact.get("_id", "")),
        name=contact.get("name", ""),
        email=contact.get("email", ""),
        phone=contact.get("phone"),
        company=contact.get("company"),
    )


@app.post("/contacts", response_model=ContactResponse, status_code=201)
def create_contact(contact_input: ContactInput):
    """Create a new contact."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    contact_id = str(uuid.uuid4())
    
    try:
        contact = Contact(
            id=contact_id,
            name=contact_input.name,
            email=contact_input.email,
            phone=contact_input.phone,
            company=contact_input.company,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    db_manager.contacts.insert_one(contact.to_dict())
    
    return ContactResponse(
        id=contact_id,
        name=contact.name,
        email=contact.email,
        phone=contact.phone,
        company=contact.company,
    )


@app.put("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(contact_id: str, contact_input: ContactInput):
    """Update an existing contact."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    existing = db_manager.contacts.find_one({"_id": contact_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    try:
        contact = Contact(
            id=contact_id,
            name=contact_input.name,
            email=contact_input.email,
            phone=contact_input.phone,
            company=contact_input.company,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    db_manager.contacts.update_one(
        {"_id": contact_id},
        {"$set": contact.to_dict()},
    )
    
    return ContactResponse(
        id=contact_id,
        name=contact.name,
        email=contact.email,
        phone=contact.phone,
        company=contact.company,
    )


@app.delete("/contacts/{contact_id}", status_code=204)
def delete_contact(contact_id: str):
    """Delete a contact."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    result = db_manager.contacts.delete_one({"_id": contact_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    return None


# =============================================================================
# Admin UI REST API - Emails
# =============================================================================

@app.get("/emails", response_model=list[EmailResponse])
def get_emails(
    limit: int = Query(default=100, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
):
    """Get all emails with pagination."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    emails = list(
        db_manager.emails.find().sort("timestamp", -1).skip(skip).limit(limit)
    )
    
    return [
        EmailResponse(
            id=str(e.get("_id", "")),
            sender=e.get("sender", ""),
            subject=e.get("subject", ""),
            body=e.get("body", ""),
            timestamp=e.get("timestamp", datetime.now()),
        )
        for e in emails
    ]


@app.get("/emails/{email_id}", response_model=EmailResponse)
def get_email(email_id: str):
    """Get a specific email by ID."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    email = db_manager.emails.find_one({"_id": email_id})
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return EmailResponse(
        id=str(email.get("_id", "")),
        sender=email.get("sender", ""),
        subject=email.get("subject", ""),
        body=email.get("body", ""),
        timestamp=email.get("timestamp", datetime.now()),
    )


@app.post("/emails", response_model=EmailResponse, status_code=201)
async def create_email(email_input: EmailInput):
    """Create a new email record."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    email_id = str(uuid.uuid4())
    timestamp = email_input.timestamp or datetime.now()
    
    try:
        email = Email(
            id=email_id,
            sender=email_input.sender,
            subject=email_input.subject,
            body=email_input.body,
            timestamp=timestamp,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Generate embedding if vector search is available
    if vector_search:
        try:
            text_to_embed = f"{email.subject}\n\n{email.body}"
            email.embedding = await vector_search.embed_text(text_to_embed)
        except Exception as e:
            logger.warning(f"Failed to generate embedding: {e}")
    
    db_manager.emails.insert_one(email.to_dict())
    
    return EmailResponse(
        id=email_id,
        sender=email.sender,
        subject=email.subject,
        body=email.body,
        timestamp=email.timestamp,
    )


@app.post("/emails/import", response_model=dict)
async def import_emails(bulk_import: BulkEmailImport):
    """Bulk import emails."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    imported_count = 0
    errors = []
    
    for email_input in bulk_import.emails:
        try:
            email_id = str(uuid.uuid4())
            timestamp = email_input.timestamp or datetime.now()
            
            email = Email(
                id=email_id,
                sender=email_input.sender,
                subject=email_input.subject,
                body=email_input.body,
                timestamp=timestamp,
            )
            
            # Generate embedding if vector search is available
            if vector_search:
                try:
                    text_to_embed = f"{email.subject}\n\n{email.body}"
                    email.embedding = await vector_search.embed_text(text_to_embed)
                except Exception:
                    pass  # Continue without embedding
            
            db_manager.emails.insert_one(email.to_dict())
            imported_count += 1
            
        except Exception as e:
            errors.append(str(e))
    
    return {
        "imported": imported_count,
        "total": len(bulk_import.emails),
        "errors": errors[:10] if errors else [],  # Limit error messages
    }


@app.delete("/emails/{email_id}", status_code=204)
def delete_email(email_id: str):
    """Delete an email."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    result = db_manager.emails.delete_one({"_id": email_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return None


# =============================================================================
# Admin UI REST API - Calls
# =============================================================================

@app.get("/calls", response_model=list[CallRecord])
def get_calls(
    limit: int = Query(default=100, ge=1, le=1000),
    skip: int = Query(default=0, ge=0),
):
    """Get call history with pagination."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    calls = list(
        db_manager.calls.find().sort("timestamp", -1).skip(skip).limit(limit)
    )
    
    return [
        CallRecord(
            call_sid=c.get("call_sid", ""),
            caller_number=c.get("caller_number", ""),
            identified_name=c.get("identified_name"),
            company=c.get("company"),
            call_purpose=c.get("call_purpose"),
            outcome=c.get("outcome", "unknown"),
            timestamp=c.get("timestamp", datetime.now()),
            duration=c.get("duration", 0),
            transcript=c.get("transcript", []),
            summary=c.get("summary"),
            decision=c.get("decision"),
            decision_label=c.get("decision_label"),
            reasoning=c.get("reasoning"),
            action_taken=c.get("action_taken"),
        )
        for c in calls
    ]


@app.get("/calls/{call_sid}", response_model=CallRecord)
def get_call(call_sid: str):
    """Get details of a specific call."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    call = db_manager.calls.find_one({"call_sid": call_sid})
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    return CallRecord(
        call_sid=call.get("call_sid", ""),
        caller_number=call.get("caller_number", ""),
        identified_name=call.get("identified_name"),
        company=call.get("company"),
        call_purpose=call.get("call_purpose"),
        outcome=call.get("outcome", "unknown"),
        timestamp=call.get("timestamp", datetime.now()),
        duration=call.get("duration", 0),
        transcript=call.get("transcript", []),
        summary=call.get("summary"),
        decision=call.get("decision"),
        decision_label=call.get("decision_label"),
        reasoning=call.get("reasoning"),
        action_taken=call.get("action_taken"),
    )


# =============================================================================
# Admin UI REST API - Config
# =============================================================================

@app.get("/config", response_model=SystemConfig)
def get_config():
    """Get system configuration (non-sensitive values only)."""
    settings = get_settings()
    
    return SystemConfig(
        server_host=settings.server_host,
        server_port=settings.server_port,
    )


@app.put("/config", response_model=SystemConfig)
def update_config(config: SystemConfig):
    """Update system configuration.
    
    Note: This endpoint only updates runtime configuration.
    Sensitive values like API keys must be updated via environment variables.
    """
    # In a production system, this would persist configuration changes
    # For now, we just acknowledge the request
    logger.info(f"Config update requested: {config}")
    
    return config


# =============================================================================
# Admin UI REST API - Business Config
# =============================================================================

@app.get("/config/business", response_model=BusinessConfigResponse)
def get_business_config():
    """Get business configuration (CEO, company info)."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    config_doc = db_manager.business_config.find_one({"_id": "business_config"})
    if not config_doc:
        raise HTTPException(status_code=404, detail="Business config not found")
    
    return BusinessConfigResponse(
        ceo_name=config_doc.get("ceo_name", ""),
        company_name=config_doc.get("company_name"),
        company_description=config_doc.get("company_description"),
    )


@app.put("/config/business", response_model=BusinessConfigResponse)
def update_business_config(config_input: BusinessConfigInput):
    """Update business configuration."""
    if not db_manager:
        raise HTTPException(status_code=503, detail="Database not available")
    
    try:
        config = BusinessConfig(
            ceo_name=config_input.ceo_name,
            company_name=config_input.company_name,
            company_description=config_input.company_description,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Upsert the config
    db_manager.business_config.update_one(
        {"_id": "business_config"},
        {"$set": config.to_dict()},
        upsert=True,
    )
    
    # Update the reasoning engine with new config
    if reasoning_engine:
        reasoning_engine.set_business_config(config)
        logger.info(f"Updated business config: CEO is {config.ceo_name}")
    
    return BusinessConfigResponse(
        ceo_name=config.ceo_name,
        company_name=config.company_name,
        company_description=config.company_description,
    )


# =============================================================================
# Health Check
# =============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = {
        "status": "healthy",
        "service": "ai-receptionist",
        "components": {
            "call_manager": call_manager is not None,
            "voice_pipeline": voice_pipeline is not None,
            "reasoning_engine": reasoning_engine is not None,
            "vector_search": vector_search is not None,
            "database": db_manager is not None,
        },
    }
    return status


@app.get("/stats")
def get_dashboard_stats():
    """Get dashboard statistics."""
    from datetime import timedelta
    
    stats = {
        "callsToday": 0,
        "totalContacts": 0,
        "emailsIndexed": 0,
        "avgResponseTime": 1.2,  # Default placeholder
    }
    
    if db_manager:
        # Count calls from today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        stats["callsToday"] = db_manager.calls.count_documents({
            "timestamp": {"$gte": today_start}
        })
        
        # Count total contacts
        stats["totalContacts"] = db_manager.contacts.count_documents({})
        
        # Count indexed emails
        stats["emailsIndexed"] = db_manager.emails.count_documents({})
    
    return stats


# =============================================================================
# Google Calendar & Auth Endpoints
# =============================================================================

@app.post("/google/auth")
async def initiate_google_auth():
    """Initiate Google OAuth flow.
    
    This will trigger the local browser flow if running locally.
    In a headless server environment, this would need to return an auth URL.
    """
    try:
        creds = authenticate_google()
        return {"status": "authenticated", "valid": creds is not None and creds.valid}
    except Exception as e:
        logger.error(f"Auth failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/google/status")
async def get_google_status():
    """Check authentication status."""
    import os
    token_exists = os.path.exists("token.json")
    return {"authenticated": token_exists}


@app.post("/calendar/sync")
def sync_calendar():
    """Sync calendar events to MongoDB."""
    if not calendar_service:
        raise HTTPException(status_code=503, detail="Calendar service not available")
    
    try:
        count = calendar_service.sync_events_to_db()
        return {"synced_events": count}
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/calendar/events")
def list_calendar_events(
    start: datetime | None = None,
    days: int = 7
):
    """List upcoming calendar events."""
    if not calendar_service:
        raise HTTPException(status_code=503, detail="Calendar service not available")
    
    from datetime import timedelta
    if not start:
        start = datetime.utcnow()
    end = start + timedelta(days=days)
    
    return calendar_service.list_events(start_time=start, end_time=end)


@app.post("/calendar/events")
def create_calendar_event(event: EventInput):
    """Create a new calendar event."""
    if not calendar_service:
        raise HTTPException(status_code=503, detail="Calendar service not available")
    
    result = calendar_service.create_event(
        summary=event.summary,
        start_time=event.start_time,
        end_time=event.end_time,
        attendees=event.attendees,
        description=event.description
    )
    
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create event")
        
    return result


# =============================================================================
# TTS Audio Endpoint for ElevenLabs
# =============================================================================

@app.get("/tts/{audio_id}")
async def get_tts_audio(audio_id: str):
    """Serve cached TTS audio for Twilio to play.
    
    Args:
        audio_id: Hash ID of the cached audio.
        
    Returns:
        Audio file in MP3 format.
    """
    if audio_id not in audio_cache:
        raise HTTPException(status_code=404, detail="Audio not found")
    
    audio_bytes = audio_cache[audio_id]
    
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": f"inline; filename={audio_id}.mp3",
            "Cache-Control": "public, max-age=3600",
        }
    )


@app.post("/tts/generate")
async def generate_tts(text: str = Form(...)):
    """Generate TTS audio and return the URL to play it.
    
    Args:
        text: Text to convert to speech.
        
    Returns:
        URL to the generated audio.
    """
    if not voice_pipeline:
        raise HTTPException(status_code=503, detail="Voice pipeline not initialized")
    
    # Generate hash for caching
    text_hash = hashlib.md5(text.encode()).hexdigest()[:12]
    
    # Check cache first
    if text_hash not in audio_cache:
        try:
            audio_bytes = await voice_pipeline.synthesize_speech(text)
            audio_cache[text_hash] = audio_bytes
            
            # Limit cache size (keep last 100 entries)
            if len(audio_cache) > 100:
                oldest_key = next(iter(audio_cache))
                del audio_cache[oldest_key]
                
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            raise HTTPException(status_code=500, detail="TTS generation failed")
    
    return {"audio_id": text_hash, "url": f"/tts/{text_hash}"}


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(app, host=settings.server_host, port=settings.server_port)
