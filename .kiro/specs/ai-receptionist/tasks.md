# Implementation Plan: AI Receptionist

## Overview

This plan implements the AI Receptionist system in phases: core infrastructure first, then the voice pipeline, adaptive retrieval, and finally the Admin UI. Each phase builds on the previous, with property tests validating correctness at each step.

## Tasks

- [x] 1. Project setup and core infrastructure
  - [x] 1.1 Initialize Python project with FastAPI, dependencies (pydantic, pymongo, httpx)
    - Create pyproject.toml with dependencies: fastapi, uvicorn, pymongo, voyageai, deepgram-sdk, twilio, httpx
    - Set up project structure: src/receptionist/, tests/
    - _Requirements: 7.3_

  - [x] 1.2 Create configuration and environment management
    - Create config.py with Pydantic settings for all API keys and connection strings
    - Support .env file loading
    - _Requirements: 7.4_

  - [x] 1.3 Set up MongoDB connection and collections
    - Create database.py with MongoClient initialization
    - Define emails and contacts collections
    - _Requirements: 5.4_

- [x] 2. Data models and ingestion
  - [x] 2.1 Implement Email and Contact data models
    - Create models.py with Email and Contact dataclasses
    - Add validation for required fields
    - _Requirements: 5.2, 5.3_

  - [ ]* 2.2 Write property test for data ingestion round-trip
    - **Property 11: Data Ingestion Round-Trip**
    - **Validates: Requirements 5.2, 5.3**

  - [x] 2.3 Implement VectorSearch class with Voyage AI embeddings
    - Create vector_search.py with embed_text(), search_emails(), search_contacts()
    - Configure Voyage AI client for 1024-dimension embeddings
    - _Requirements: 3.1, 3.2, 3.4_

  - [ ]* 2.4 Write property test for embedding generation consistency
    - **Property 5: Embedding Generation Consistency**
    - **Validates: Requirements 3.1, 5.1**

  - [x] 2.5 Implement DataIngestion class
    - Create data_ingestion.py with ingest_email(), ingest_contact(), bulk_ingest_emails()
    - Implement upsert logic for duplicate handling
    - _Requirements: 5.1, 5.5_

  - [ ]* 2.6 Write property test for idempotent ingestion
    - **Property 12: Idempotent Ingestion**
    - **Validates: Requirements 5.5**

- [x] 3. Checkpoint - Data layer complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Vector search and retrieval
  - [x] 4.1 Implement MongoDB Atlas vector search queries
    - Add vector search aggregation pipeline to search_emails()
    - Implement result limiting (max 3 results)
    - _Requirements: 3.2, 3.5_

  - [ ]* 4.2 Write property test for search result limiting
    - **Property 7: Search Result Limiting**
    - **Validates: Requirements 3.5**

  - [ ]* 4.3 Write property test for search results ordering
    - **Property 6: Search Results Ordering**
    - **Validates: Requirements 3.3**

- [x] 5. Voice pipeline
  - [x] 5.1 Implement VoicePipeline class with Deepgram integration
    - Create voice_pipeline.py with transcribe_stream(), synthesize_speech(), get_greeting()
    - Configure Deepgram client for STT and TTS
    - _Requirements: 1.2, 1.3, 4.2, 4.3_

  - [ ]* 5.2 Write property test for TTS audio production
    - **Property 9: TTS Audio Production**
    - **Validates: Requirements 4.2**

- [ ] 6. Reasoning engine
  - [x] 6.1 Implement ReasoningEngine class with Fireworks AI
    - Create reasoning_engine.py with decide_action(), generate_response(), extract_caller_info()
    - Configure firefunction-v2 model for tool calling
    - Define tool schemas for search_emails, search_contacts
    - _Requirements: 2.1, 6.1, 6.2, 6.4_

  - [ ]* 6.2 Write property test for caller information extraction
    - **Property 2: Caller Information Extraction**
    - **Validates: Requirements 2.1**

  - [ ]* 6.3 Write property test for tool selection correctness
    - **Property 13: Tool Selection Correctness**
    - **Validates: Requirements 6.1, 6.2**

  - [x] 6.4 Implement context synthesis from search results
    - Add synthesize_context() method combining contact and email results
    - _Requirements: 2.4_

  - [ ]* 6.5 Write property test for context synthesis completeness
    - **Property 4: Context Synthesis Completeness**
    - **Validates: Requirements 2.4**

- [x] 7. Checkpoint - Core AI components complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Call management
  - [x] 8.1 Implement CallManager class
    - Create call_manager.py with CallState dataclass
    - Implement start_call(), update_transcript(), end_call()
    - _Requirements: 4.5_

  - [ ]* 8.2 Write property test for context persistence across exchanges
    - **Property 10: Context Persistence Across Exchanges**
    - **Validates: Requirements 4.5**

- [x] 9. Webhook handler and API server
  - [x] 9.1 Implement WebhookHandler for Twilio
    - Create webhook_handler.py with handle_incoming_call(), handle_audio_stream(), handle_call_status()
    - Generate TwiML responses for call flow
    - _Requirements: 1.1, 7.2, 7.3_

  - [ ]* 9.2 Write property test for webhook routing correctness
    - **Property 1: Webhook Routing Correctness**
    - **Validates: Requirements 1.1**

  - [x] 9.3 Create FastAPI application with endpoints
    - Create main.py with POST /incoming-call, WebSocket /audio-stream, POST /call-status
    - Add REST endpoints for Admin UI: GET/POST/PUT/DELETE /contacts, /emails, /calls, /config
    - _Requirements: 7.1, 7.3, 8.6_

  - [ ]* 9.4 Write property test for error response codes
    - **Property 16: Error Response Codes**
    - **Validates: Requirements 7.5**

- [x] 10. Checkpoint - Backend complete
  - Ensure all tests pass, ask the user if questions arise.


- [x] 11. Admin UI - Electron setup
  - [x] 11.1 Initialize Electron project with React and TypeScript
    - Create admin-ui/ directory with electron-forge or electron-vite
    - Set up React with TypeScript, Tailwind CSS for styling
    - _Requirements: 8.1_

  - [x] 11.2 Implement API client for backend communication
    - Create src/api/client.ts with methods for all REST endpoints
    - Add error handling and retry logic
    - _Requirements: 8.6, 8.7_

  - [ ]* 11.3 Write property test for server connection resilience
    - **Property 19: Admin UI Server Connection Resilience**
    - **Validates: Requirements 8.7**

- [ ] 12. Admin UI - Views
  - [ ] 12.1 Implement Dashboard view
    - Create Dashboard.tsx showing recent calls, system status
    - Display quick stats (calls today, contacts count)
    - _Requirements: 8.1_

  - [ ] 12.2 Implement Call History view
    - Create CallHistory.tsx with table of calls
    - Display caller number, identified name, purpose, outcome, timestamp
    - _Requirements: 8.2_

  - [ ]* 12.3 Write property test for call history completeness
    - **Property 18: Admin UI Call History Completeness**
    - **Validates: Requirements 8.2**

  - [ ] 12.4 Implement Contact Manager view
    - Create ContactManager.tsx with CRUD form
    - Add validation for contact fields
    - _Requirements: 8.3_

  - [ ]* 12.5 Write property test for contact CRUD round-trip
    - **Property 17: Admin UI Contact CRUD Round-Trip**
    - **Validates: Requirements 8.3**

  - [ ] 12.6 Implement Email Manager view
    - Create EmailManager.tsx with list view and import functionality
    - Support bulk email import from file
    - _Requirements: 8.4_

  - [ ] 12.7 Implement Settings view
    - Create Settings.tsx with API key configuration form
    - Store settings securely (electron-store or similar)
    - _Requirements: 8.5_

- [ ] 13. Integration and wiring
  - [ ] 13.1 Wire all backend components together
    - Create orchestrator that connects CallManager → VoicePipeline → ReasoningEngine → VectorSearch
    - Implement full call flow from webhook to response
    - _Requirements: 1.1, 2.2, 2.3, 4.1_

  - [ ]* 13.2 Write property test for adaptive retrieval triggers
    - **Property 3: Adaptive Retrieval Triggers**
    - **Validates: Requirements 2.2, 2.3**

  - [ ] 13.3 Add ngrok tunnel setup script
    - Create scripts/start-dev.sh to launch server with ngrok
    - Document Twilio webhook configuration
    - _Requirements: 7.4_

- [ ] 14. Final checkpoint - Full system complete
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Python backend uses Hypothesis for property-based testing
- Admin UI uses Jest + React Testing Library for tests
- Each property test references specific design document properties
