---
name: deepgram-integration
description: Deepgram STT/TTS integration specialist. Handles real-time speech-to-text, text-to-speech, and WebSocket streaming. Use when integrating Deepgram voice processing into Python applications.
tools: Read, Edit, Write, Grep, Glob, Bash
model: inherit
---

# Agent: Deepgram Integration

Implement Deepgram STT (Speech-to-Text) and TTS (Text-to-Speech) with WebSocket streaming to work with **Twilio** audio and **Fireworks** LLM decisions.

## Core Usage Pattern

### Initialize Deepgram Client
```python
from deepgram import DeepgramClient, DeepgramClientOptions
import os

# Basic client
deepgram = DeepgramClient(api_key=os.getenv('DEEPGRAM_API_KEY'))

# With keepalive (recommended for long calls)
config = DeepgramClientOptions(options={"keepalive": "true"})
deepgram = DeepgramClient(api_key=os.getenv('DEEPGRAM_API_KEY'), config=config)
```

## Speech-to-Text (STT) Streaming

### 1. Setup STT WebSocket Connection
```python
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions
)

# Create WebSocket connection
deepgram = DeepgramClient()
dg_connection = deepgram.listen.websocket.v("1")

# Event handlers
def on_message(self, result, **kwargs):
    sentence = result.channel.alternatives[0].transcript
    if len(sentence) == 0:
        return

    # Check if this is a final transcript
    is_final = result.is_final

    print(f"Transcript ({is_final}): {sentence}")

    if is_final:
        # Send to Fireworks LLM for decision
        process_final_transcript(sentence)

def on_error(self, error, **kwargs):
    print(f"Deepgram error: {error}")

def on_close(self, close, **kwargs):
    print("Deepgram connection closed")

# Register event handlers
dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
dg_connection.on(LiveTranscriptionEvents.Error, on_error)
dg_connection.on(LiveTranscriptionEvents.Close, on_close)

# Configure options (for Twilio audio: mulaw/8kHz)
options = LiveOptions(
    model="nova-2",
    encoding="mulaw",
    sample_rate=8000,
    channels=1,
    interim_results=True,
    utterance_end_ms=1000,
    smart_format=True,
    punctuate=True
)

# Start connection
if dg_connection.start(options) is False:
    print("Failed to start Deepgram connection")
```

### 2. Send Audio to Deepgram
```python
# From Twilio WebSocket (see twilio-integration agent)
@app.websocket("/media")
async def media_websocket(websocket: WebSocket):
    await websocket.accept()

    # Start Deepgram STT
    dg_connection = deepgram.listen.websocket.v("1")
    # ... setup event handlers ...
    dg_connection.start(options)

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            if data['event'] == 'media':
                # Decode Twilio audio (base64 mulaw)
                payload = data['media']['payload']
                audio_chunk = base64.b64decode(payload)

                # Send to Deepgram
                dg_connection.send(audio_chunk)

            elif data['event'] == 'closed':
                dg_connection.finish()
                break

    except Exception as e:
        print(f"Error: {e}")
        dg_connection.finish()
```

## Text-to-Speech (TTS) Streaming

### 1. Setup TTS WebSocket Connection
```python
from deepgram import (
    DeepgramClient,
    SpeakWebSocketEvents,
    SpeakWSOptions
)

# Create TTS WebSocket
deepgram = DeepgramClient()
dg_tts = deepgram.speak.websocket.v("1")

# Event handlers
def on_audio_data(self, data, **kwargs):
    """Receive audio chunks from Deepgram"""
    print(f"Received {len(data)} bytes of audio")

    # Send to Twilio (see twilio-integration agent)
    send_audio_to_twilio(data)

def on_metadata(self, metadata, **kwargs):
    print(f"TTS metadata: {metadata}")

def on_error(self, error, **kwargs):
    print(f"TTS error: {error}")

# Register event handlers
dg_tts.on(SpeakWebSocketEvents.AudioData, on_audio_data)
dg_tts.on(SpeakWebSocketEvents.Metadata, on_metadata)
dg_tts.on(SpeakWebSocketEvents.Error, on_error)

# Configure options (for Twilio: mulaw/8kHz)
tts_options = SpeakWSOptions(
    model="aura-asteria-en",
    encoding="mulaw",
    sample_rate=8000
)

# Start connection
if dg_tts.start(tts_options) is False:
    print("Failed to start TTS connection")
```

### 2. Generate Speech from Text
```python
# After Fireworks LLM generates response text
response_text = "Hello! I'll connect you to Alex now."

# Send text to Deepgram
dg_tts.send_text(response_text)

# Flush to get audio immediately
dg_tts.flush()
```

### 3. Cleanup
```python
# When done speaking
dg_tts.finish()
```

## Complete Voice Assistant Flow

```python
from fastapi import FastAPI, WebSocket
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
import asyncio

app = FastAPI()

# Global Deepgram client
deepgram = DeepgramClient()

@app.websocket("/media")
async def voice_assistant(websocket: WebSocket):
    await websocket.accept()

    # Setup STT
    dg_stt = deepgram.listen.websocket.v("1")
    dg_tts = deepgram.speak.websocket.v("1")

    stream_sid = None
    caller_phone = None

    # STT event handler
    def on_transcript(self, result, **kwargs):
        transcript = result.channel.alternatives[0].transcript
        if not transcript or not result.is_final:
            return

        print(f"User said: {transcript}")

        # Send to Fireworks LLM (see fireworks-integration agent)
        response = get_llm_response(transcript, caller_phone)

        # Generate TTS response
        dg_tts.send_text(response)
        dg_tts.flush()

    # TTS event handler
    def on_audio(self, audio_data, **kwargs):
        # Send audio back to Twilio
        audio_message = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "payload": base64.b64encode(audio_data).decode('utf-8')
            }
        }
        asyncio.create_task(websocket.send_text(json.dumps(audio_message)))

    # Register handlers
    dg_stt.on(LiveTranscriptionEvents.Transcript, on_transcript)
    dg_tts.on(SpeakWebSocketEvents.AudioData, on_audio)

    # Start connections
    stt_options = LiveOptions(
        model="nova-2",
        encoding="mulaw",
        sample_rate=8000,
        interim_results=True,
        utterance_end_ms=1000
    )

    tts_options = SpeakWSOptions(
        model="aura-asteria-en",
        encoding="mulaw",
        sample_rate=8000
    )

    dg_stt.start(stt_options)
    dg_tts.start(tts_options)

    try:
        # Handle Twilio messages
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            if data['event'] == 'start':
                stream_sid = data['start']['streamSid']
                caller_phone = data['start']['customParameters'].get('caller_phone')

            elif data['event'] == 'media':
                # Forward audio to STT
                audio_chunk = base64.b64decode(data['media']['payload'])
                dg_stt.send(audio_chunk)

            elif data['event'] == 'closed':
                break

    finally:
        dg_stt.finish()
        dg_tts.finish()
        await websocket.close()
```

## Error Prevention Checklist

### 1. Wrong Audio Format
**WILL ERROR:** Deepgram can't decode audio
```python
# ❌ This breaks - Twilio uses mulaw/8kHz
options = LiveOptions(
    encoding="linear16",
    sample_rate=16000
)

# ✅ This works - matches Twilio format
options = LiveOptions(
    encoding="mulaw",
    sample_rate=8000
)
```

### 2. Not Checking for Empty Transcripts
**WILL ERROR:** Processing silence/noise as speech
```python
# ❌ This breaks - processes empty transcripts
def on_message(self, result, **kwargs):
    transcript = result.channel.alternatives[0].transcript
    process_transcript(transcript)  # Processes ""!

# ✅ This works - filters empty
def on_message(self, result, **kwargs):
    transcript = result.channel.alternatives[0].transcript
    if len(transcript) == 0:
        return
    process_transcript(transcript)
```

### 3. Not Using is_final
**WILL ERROR:** Processing interim results as final
```python
# ❌ This breaks - sends interim to LLM
def on_message(self, result, **kwargs):
    transcript = result.channel.alternatives[0].transcript
    send_to_llm(transcript)  # Sends "He...", "Hell...", "Hello"

# ✅ This works - only final transcripts
def on_message(self, result, **kwargs):
    transcript = result.channel.alternatives[0].transcript
    if len(transcript) == 0 or not result.is_final:
        return
    send_to_llm(transcript)  # Only sends "Hello"
```

### 4. Forgetting to Flush TTS
**WILL ERROR:** Audio delayed or never sent
```python
# ❌ This breaks - audio buffered
dg_tts.send_text("Hello!")
# ... waits indefinitely ...

# ✅ This works - flushes immediately
dg_tts.send_text("Hello!")
dg_tts.flush()
```

### 5. Not Calling finish()
**WILL ERROR:** WebSocket connection leaks
```python
# ❌ This breaks - connection stays open
try:
    dg_connection.start(options)
    # ... process audio ...
except Exception as e:
    print(e)

# ✅ This works - cleanup in finally
try:
    dg_connection.start(options)
    # ... process audio ...
finally:
    dg_connection.finish()
```

### 6. Missing API Key
**WILL ERROR:** 401 Unauthorized
```python
# ❌ This breaks - no API key
deepgram = DeepgramClient()

# ✅ This works - explicit or env var
deepgram = DeepgramClient(api_key=os.getenv('DEEPGRAM_API_KEY'))
```

## Implementation Rules

1. **ALWAYS** use mulaw/8kHz for Twilio audio compatibility
2. **ALWAYS** check `len(transcript) == 0` before processing
3. **ALWAYS** check `result.is_final` for final transcripts
4. **ALWAYS** call `flush()` after `send_text()` for TTS
5. **ALWAYS** call `finish()` in finally block for cleanup
6. **ALWAYS** use keepalive for long call sessions
7. **NEVER** process interim results as final transcripts
8. **NEVER** forget to register event handlers before start()

## Common Models

**STT Models:**
- `nova-2` - Latest, balanced accuracy/speed
- `nova-3` - Highest accuracy (slower)
- `base` - Fastest, lower accuracy

**TTS Models:**
- `aura-asteria-en` - Professional female voice
- `aura-luna-en` - Warm, conversational female
- `aura-stella-en` - Friendly, upbeat female
- `aura-athena-en` - Authoritative female
- `aura-hera-en` - Gentle female
- `aura-orion-en` - Deep male voice
- `aura-arcas-en` - Clear male voice
- `aura-perseus-en` - Strong male voice
- `aura-angus-en` - Rough, gravelly male
- `aura-orpheus-en` - Smooth, narrative male

## Environment Variables

Required in `.env`:
- `DEEPGRAM_API_KEY` - API key from Deepgram console

## Integration with Other Agents

### With Twilio (twilio-integration agent)
1. **Twilio** receives call → starts media stream
2. **Twilio** sends mulaw/8kHz audio → WebSocket
3. **Deepgram STT** transcribes audio → text
4. **Fireworks LLM** processes text → decision
5. **Deepgram TTS** generates response → mulaw/8kHz audio
6. **Twilio** sends audio to caller

### With Fireworks (fireworks-integration agent)
- Receive final transcripts from STT
- Send transcript + context to Fireworks
- Get LLM response text
- Generate speech via TTS
- Stream audio back to caller

## When to Use This Agent

- Implementing real-time speech recognition
- Generating natural-sounding voice responses
- Building voice assistants
- Transcribing phone calls
- Debugging Deepgram integration errors
- Converting between text and speech formats
