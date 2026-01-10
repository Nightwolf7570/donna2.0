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

