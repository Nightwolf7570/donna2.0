# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI Receptionist system that handles incoming phone calls using context-aware adaptive retrieval. The system integrates Twilio (telephony), Deepgram (STT/TTS), Fireworks AI (reasoning/tool calling), Voyage AI (embeddings), and MongoDB Atlas (vector storage). It includes a FastAPI backend and an Electron-based Admin UI for system management.

## Development Commands

### Backend (Python)

```bash
# Start the development server with hot reload
python run_server.py

# Install dependencies
pip install -e .

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with hypothesis statistics
pytest -v --hypothesis-show-statistics

# Run specific test file
pytest tests/test_filename.py

# Run linter
ruff check .

# Format code
ruff format .
```

### Admin UI (Electron + React)

```bash
# Navigate to admin-ui directory first
cd admin-ui

# Install dependencies
npm install

# Run development mode (Vite dev server only)
npm run dev

# Run Electron in development with hot reload
npm run electron:dev

# Build for production
npm run build

# Build Electron app
npm run electron:build
```

### Exposing Local Server

During development, Twilio webhooks need to reach your local server:

```bash
# In a separate terminal
ngrok http 8000

# Copy the ngrok URL and set it as BASE_URL in .env
```

## Architecture

### Component Interaction Flow

1. **Incoming Call**: Twilio → Webhook Handler → Call Manager
2. **Audio Processing**: Call Manager → Voice Pipeline → Deepgram (STT/TTS)
3. **Reasoning**: Voice Pipeline → Reasoning Engine → Fireworks AI (tool calling)
4. **Context Retrieval**: Reasoning Engine → Vector Search → Voyage AI (embeddings) → MongoDB Atlas
5. **Response**: Reasoning Engine → Voice Pipeline → Twilio

### Core Components

#### Backend (src/receptionist/)

- **main.py**: FastAPI application with Twilio webhook endpoints (`/incoming-call`, `/process-speech`, `/call-status`, `/audio-stream`) and Admin UI REST API (`/contacts`, `/emails`, `/calls`, `/config`)
- **call_manager.py**: Manages active call state (CallState) and conversation flow
- **voice_pipeline.py**: Handles Deepgram STT/TTS, audio streaming
- **reasoning_engine.py**: Uses Fireworks AI firefunction-v2 for tool calling decisions and response generation
- **vector_search.py**: Vector similarity search via Voyage AI embeddings and MongoDB Atlas
- **webhook_handler.py**: Processes Twilio webhooks and coordinates pipeline
- **database.py**: MongoDB connection and collection management (emails, contacts, calls)
- **models.py**: Data models (Email, Contact) with validation
- **config.py**: Pydantic settings from environment variables

#### Admin UI (admin-ui/)

- **electron/main.ts**: Electron main process
- **electron/preload.ts**: Preload script for IPC
- **src/App.tsx**: Main React application
- **src/api/**: API client for backend communication
- **src/components/**: Reusable React components
- **src/views/**: Dashboard, CallHistory, ContactManager, EmailManager, Settings

### MongoDB Collections

- **emails**: Stores email data with 1024-dimensional embeddings for vector search
- **contacts**: Stores contact information (name, email, phone, company)
- **calls**: Stores call history with transcripts, outcomes, and identified callers

Vector search index must be configured on `emails.embedding` field with:
- Type: vectorSearch
- Dimensions: 1024
- Similarity: cosine

### Environment Configuration

Copy `.env.example` to `.env` and configure:
- MONGODB_URI: MongoDB Atlas connection string
- VOYAGE_API_KEY: Voyage AI for embeddings
- DEEPGRAM_API_KEY: Deepgram for STT/TTS
- ELEVENLABS_API_KEY: ElevenLabs for high-quality TTS (optional)
- FIREWORKS_API_KEY: Fireworks AI for reasoning
- TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER: Twilio telephony
- BASE_URL: Your ngrok URL for TTS audio serving

## Key Implementation Details

### Adaptive Retrieval

The system performs context-aware retrieval by:
1. Extracting caller name and purpose from transcript (Reasoning Engine)
2. Searching contacts by name when name is identified
3. Searching emails by semantic similarity when purpose is identified
4. Synthesizing context from both sources
5. Generating contextual responses referencing found information

### Tool Calling

The Reasoning Engine uses Fireworks AI firefunction-v2 for tool selection:
- `search_emails`: Vector search across email embeddings
- `search_contacts`: Contact lookup by name
- `generate_response`: Generate contextual response

Tools are invoked only when needed; if sufficient context exists, the system responds without additional searches.

### Audio Caching

TTS audio is cached by text hash to reduce latency on repeated phrases. Cache is limited to 100 entries (LRU-style). Audio is served via `/tts/{audio_id}` endpoint for Twilio playback.

### Error Handling Philosophy

- Gracefully degrade when services fail (e.g., TTS falls back to Twilio Say verb)
- Log errors but continue processing
- Return empty results rather than crashing
- Retry critical operations (e.g., Deepgram API timeout) once

## Testing

### Test Organization

- Tests use pytest with asyncio support
- Property-based tests use Hypothesis (minimum 100 iterations per property)
- Tests are organized around the properties defined in `.kiro/specs/ai-receptionist/design.md`

### Important Test Patterns

When writing tests for this codebase:
- Use `pytest.mark.asyncio` for async tests
- Mock external services (Twilio, Deepgram, Fireworks, Voyage, MongoDB) to avoid API calls
- Property tests should verify universal invariants (e.g., embedding dimension always 1024, search results always sorted by score)
- Integration tests should use test MongoDB instance, not production

## Admin UI Integration

The Admin UI communicates with the backend via REST API:
- GET /contacts, POST /contacts, PUT /contacts/{id}, DELETE /contacts/{id}
- GET /emails, POST /emails, POST /emails/import, DELETE /emails/{id}
- GET /calls, GET /calls/{call_sid}
- GET /config, PUT /config
- GET /health

When modifying backend endpoints, ensure Admin UI API client is updated accordingly.

## Common Gotchas

1. **BASE_URL must be set**: Twilio needs a public URL to fetch TTS audio. Without BASE_URL in .env, audio playback will fail.
2. **MongoDB vector index required**: The `emails` collection needs a vector search index configured in MongoDB Atlas. Without it, email searches return empty results.
3. **ElevenLabs vs Deepgram TTS**: System uses ElevenLabs if ELEVENLABS_API_KEY is set, otherwise falls back to Deepgram TTS.
4. **CORS enabled for Admin UI**: Backend allows all origins in development. Restrict in production.
5. **Embedding dimension**: Voyage AI produces 1024-dimensional vectors. Any code handling embeddings must expect this size.
6. **Call state cleanup**: CallManager maintains in-memory state. If a call ends unexpectedly, state may linger until explicit cleanup.
