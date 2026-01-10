# Donna 2.0 - AI Receptionist

## Overview

AI Receptionist handling incoming phone calls using context-aware adaptive retrieval. Integrates Twilio (telephony), Deepgram (STT), ElevenLabs/Deepgram (TTS), Fireworks AI (reasoning/tool calling), Voyage AI (embeddings), MongoDB Atlas (vector storage). Includes FastAPI backend + Electron Admin UI.

## Quick Start

```bash
# Backend
pip install -e ".[dev]"
python run_server.py  # Hot reload enabled

# Admin UI
cd admin-ui && npm install && npm run dev
```

Expose local server for Twilio: `ngrok http 8000` → set BASE_URL in `.env`

## Architecture

```
Incoming Call → Twilio → Webhook → Call Manager
                                      ↓
                              Voice Pipeline ↔ Deepgram STT
                                      ↓
                              Reasoning Engine → Fireworks AI (tool calls)
                                      ↓
                              Vector Search → Voyage AI → MongoDB Atlas
                                      ↓
                              Response → ElevenLabs/Deepgram TTS → Twilio
```

## File Structure

```
src/receptionist/
├── main.py           # FastAPI app, webhooks, REST API
├── call_manager.py   # Active call state
├── voice_pipeline.py # Deepgram STT, ElevenLabs/Deepgram TTS
├── reasoning_engine.py # Fireworks AI tool calling
├── vector_search.py  # Voyage embeddings + MongoDB vector search
├── webhook_handler.py # Twilio webhook processing
├── database.py       # MongoDB collections
├── models.py         # Pydantic models
└── config.py         # Environment settings

admin-ui/             # Electron + React + Vite + Tailwind
├── src/views/        # Dashboard, CallHistory, ContactManager, EmailManager, Settings
└── src/api/          # Backend API client
```

## MongoDB Collections

- **emails**: 1024-dim Voyage embeddings, requires vector search index (cosine)
- **contacts**: name, email, phone, company
- **calls**: transcripts, outcomes, caller info
- **business_identity**: CEO name, company info (NEW)

## Key API Endpoints

Twilio webhooks: `/incoming-call`, `/process-speech`, `/call-status`, `/audio-stream`

Admin API:
- `GET/POST/PUT/DELETE /contacts`, `/emails`
- `POST /emails/import`
- `GET /calls`, `GET /calls/{call_sid}`
- `GET/PUT /config`, `GET/PUT /config/identity` (NEW)
- `GET /health`

## Tools (Reasoning Engine)

- `search_emails`: Vector search across email embeddings
- `search_contacts`: Contact lookup by name
- `generate_response`: Contextual response generation

## Environment (.env)

Required:
- `MONGODB_URI`, `VOYAGE_API_KEY`, `DEEPGRAM_API_KEY`, `FIREWORKS_API_KEY`
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`
- `BASE_URL` (ngrok URL)

Optional: `ELEVENLABS_API_KEY` (higher quality TTS)

## Testing

```bash
pytest                          # All tests
pytest -v --hypothesis-show-statistics  # With hypothesis stats
ruff check . && ruff format .   # Lint + format
```

## Gotchas

1. **BASE_URL required** - Twilio needs public URL for TTS audio
2. **Vector index required** - Must configure in MongoDB Atlas on `emails.embedding`
3. **TTS fallback** - ElevenLabs if key set, else Deepgram
4. **Embedding dimension** - Always 1024 (Voyage AI)
5. **CORS** - All origins in dev, restrict in prod

## Recent Updates (2026-01-10)

- Business identity config: CEO name, company info stored in MongoDB
- REST API for identity management (`/config/identity`)
- Dynamic system prompt injection in reasoning engine

- ElevenLabs TTS integration fixed
- Google Calendar integration (OAuth2, Sync, Scheduling)

## Rules

- **Python:** 3.11+, type hints, ruff lint/format
- **Async:** Use `pytest.mark.asyncio`, mock external services
- **Property tests:** Hypothesis, min 100 iterations
- **Imports:** Absolute imports from `src.receptionist`

## Crucial Notes

- **MANDATORY:** Commit after every change
- Update `/CHANGELOG.md` after commits
- Mock all external APIs in tests (Twilio, Deepgram, Fireworks, Voyage, MongoDB)
- Sacrifice grammar for conciseness
- Keep CLAUDE.md short
