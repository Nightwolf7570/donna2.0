# Changelog

## [Unreleased]

### Added
- Business config model (`BusinessConfig`) with CEO name, company info
- `business_config` MongoDB collection for storing configuration
- REST API endpoints: `GET/PUT /config/business`
- Dynamic system prompt injection in reasoning engine
- Dashboard stats endpoint (`GET /stats`) with calls today, contacts, emails count
- Admin UI: Business config editing in Settings view
- Admin UI: API client methods for business config
- Google Calendar OAuth2 integration (`google_auth.py`)
- Calendar Service for event management (`calendar_service.py`)
- API endpoints for calendar sync, listing, and creation
- MongoDB `calendar_events` collection
- Unit tests for Google Auth and Calendar Service
- Admin UI: Connected `CalendarAlerts` and `DecisionTimeline` to real API
- Admin UI: Added calendar methods to `ApiClient`


### Changed
- Database name changed to `donna_dev`
- CLAUDE.md streamlined with concise structure

### Fixed
- ElevenLabs TTS integration

### Infrastructure
- FastAPI backend with Twilio webhooks
- Deepgram STT/TTS integration
- Fireworks AI reasoning with tool calling
- MongoDB Atlas vector search (Voyage AI embeddings)
- Electron Admin UI (React + Vite)

