---
name: twilio-integration
description: Twilio voice integration specialist. Handles incoming calls, TwiML generation, media streaming, and webhooks. Use when integrating Twilio voice functionality into Python applications.
tools: Read, Edit, Write, Grep, Glob, Bash
model: inherit
---

# Agent: Twilio Integration

Implement Twilio voice integration with proper webhook handling, TwiML generation, and WebSocket streaming to work with **Deepgram** for STT/TTS.

## Core Usage Pattern

### Basic Incoming Call Webhook (FastAPI)
```python
from fastapi import FastAPI, Form
from twilio.twiml.voice_response import VoiceResponse

app = FastAPI()

@app.post("/incoming-call")
async def incoming_call(
    From: str = Form(...),
    To: str = Form(...),
    CallSid: str = Form(...)
):
    """Handle incoming Twilio call webhook"""
    print(f"Call from {From} to {To}, CallSid: {CallSid}")

    response = VoiceResponse()
    response.say("Hello! Please wait while we connect you.")

    return Response(content=str(response), media_type="application/xml")
```

## TwiML Media Streaming

### 1. Start Media Stream to WebSocket
```python
from twilio.twiml.voice_response import VoiceResponse, Start, Stream, Parameter

@app.post("/incoming-call")
async def incoming_call(From: str = Form(...)):
    response = VoiceResponse()

    # Start media streaming
    start = Start()
    stream = Stream(url='wss://your-domain.com/media')

    # Pass custom parameters (e.g., caller phone)
    stream.parameter(name='caller_phone', value=From)
    stream.parameter(name='call_type', value='inbound')

    start.append(stream)
    response.append(start)

    # Say something to the caller
    response.say("Hello, how can I help you today?")

    return Response(content=str(response), media_type="application/xml")
```

### 2. Receive Media Stream via WebSocket
```python
from fastapi import WebSocket
import json
import base64

@app.websocket("/media")
async def media_websocket(websocket: WebSocket):
    await websocket.accept()

    caller_phone = None

    try:
        while True:
            message = await websocket.receive_text()
            data = json.loads(message)

            # Handle different event types
            if data['event'] == 'connected':
                print("WebSocket connected")

            elif data['event'] == 'start':
                print(f"Stream started: {data}")
                # Extract custom parameters
                custom_params = data['start']['customParameters']
                caller_phone = custom_params.get('caller_phone')
                print(f"Caller: {caller_phone}")

            elif data['event'] == 'media':
                # Decode audio payload (mulaw, 8kHz)
                payload = data['media']['payload']
                audio_chunk = base64.b64decode(payload)

                # Send to Deepgram for STT
                # (See deepgram-integration agent)
                await process_audio(audio_chunk)

            elif data['event'] == 'closed':
                print("Stream closed")
                break

    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()
```

### 3. Send Audio Back to Caller (TTS Response)
```python
@app.websocket("/media")
async def media_websocket(websocket: WebSocket):
    await websocket.accept()

    # ... receive audio from Twilio ...

    # Send audio back to caller (mulaw format from Deepgram)
    audio_message = {
        "event": "media",
        "streamSid": stream_sid,  # from 'start' event
        "media": {
            "payload": base64.b64encode(audio_chunk).decode('utf-8')
        }
    }
    await websocket.send_text(json.dumps(audio_message))
```

## Twilio Media Stream Format

**Audio Encoding:** mulaw (8-bit PCM)
**Sample Rate:** 8000 Hz
**Channels:** 1 (mono)
**Chunk Size:** ~20ms of audio per message

**IMPORTANT:** Deepgram must be configured with:
- `encoding="mulaw"`
- `sample_rate=8000`

## Common TwiML Patterns

### Forward Call
```python
from twilio.twiml.voice_response import VoiceResponse, Dial

response = VoiceResponse()
response.say("Connecting you now.")
response.dial("+15555551234")  # Forward to this number
```

### Record Voicemail
```python
response = VoiceResponse()
response.say("Please leave a message after the beep.")
response.record(
    max_length=60,
    action="/voicemail-complete",
    transcribe=False
)
```

### Gather Input (IVR)
```python
from twilio.twiml.voice_response import Gather

response = VoiceResponse()
gather = Gather(
    num_digits=1,
    action="/handle-key",
    timeout=5
)
gather.say("Press 1 for sales, 2 for support.")
response.append(gather)
```

## Making Outbound Calls

```python
from twilio.rest import Client
import os

client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)

call = client.calls.create(
    to="+15555551234",
    from_=os.getenv('TWILIO_PHONE_NUMBER'),
    url="https://your-domain.com/outbound-call-twiml"
)

print(f"Call SID: {call.sid}")
```

## Error Prevention Checklist

### 1. Missing Form Dependency
**WILL ERROR:** `Form data requires "python-multipart" to be installed`
```python
# ❌ This breaks - missing dependency
pip install fastapi uvicorn

# ✅ This works - includes form parsing
pip install fastapi uvicorn python-multipart
```

### 2. Wrong Content-Type Response
**WILL ERROR:** Twilio rejects TwiML
```python
# ❌ This breaks - returns JSON
return {"twiml": str(response)}

# ✅ This works - returns XML
from fastapi.responses import Response
return Response(content=str(response), media_type="application/xml")
```

### 3. Not Extracting Custom Parameters
**WILL ERROR:** Can't access caller info in WebSocket
```python
# ❌ This breaks - parameters lost
stream = Stream(url='wss://domain.com/media')

# ✅ This works - passes caller phone
stream = Stream(url='wss://domain.com/media')
stream.parameter(name='caller_phone', value=From)

# Access in WebSocket 'start' event:
custom_params = data['start']['customParameters']
caller_phone = custom_params.get('caller_phone')
```

### 4. WebSocket Not Accepting Connection
**WILL ERROR:** Twilio can't connect to stream
```python
# ❌ This breaks - no accept
@app.websocket("/media")
async def media_websocket(websocket: WebSocket):
    message = await websocket.receive_text()  # HANGS

# ✅ This works - accepts first
@app.websocket("/media")
async def media_websocket(websocket: WebSocket):
    await websocket.accept()
    message = await websocket.receive_text()
```

### 5. Wrong Audio Format for Deepgram
**WILL ERROR:** Deepgram can't decode audio
```python
# ❌ This breaks - wrong encoding
deepgram_options = LiveOptions(
    encoding="linear16",  # WRONG
    sample_rate=16000     # WRONG
)

# ✅ This works - matches Twilio format
deepgram_options = LiveOptions(
    encoding="mulaw",
    sample_rate=8000
)
```

### 6. Not Handling Base64 Payload
**WILL ERROR:** Binary audio corrupted
```python
# ❌ This breaks - sends base64 string
payload = data['media']['payload']
deepgram_connection.send(payload)  # STRING!

# ✅ This works - decodes first
payload = data['media']['payload']
audio_chunk = base64.b64decode(payload)
deepgram_connection.send(audio_chunk)  # BYTES
```

## Implementation Rules

1. **ALWAYS** return TwiML with `media_type="application/xml"`
2. **ALWAYS** install `python-multipart` for Form parameters
3. **ALWAYS** call `await websocket.accept()` before reading messages
4. **ALWAYS** decode base64 payload before sending to Deepgram
5. **ALWAYS** use mulaw/8kHz for Twilio <-> Deepgram audio
6. **ALWAYS** extract caller phone via custom parameters in Stream
7. **NEVER** return JSON from TwiML webhook endpoints
8. **NEVER** forget to handle all event types ('connected', 'start', 'media', 'closed')

## Environment Variables

Required in `.env`:
- `TWILIO_ACCOUNT_SID` - Account SID from Twilio console
- `TWILIO_AUTH_TOKEN` - Auth token from Twilio console
- `TWILIO_PHONE_NUMBER` - Your Twilio phone number (e.g., +16288772310)

## Integration with Other Agents

### With Deepgram (deepgram-integration agent)
1. Twilio receives call → extracts caller phone
2. Twilio starts media stream → passes phone via Parameter
3. Twilio sends audio chunks (mulaw/8kHz) → WebSocket
4. **Deepgram** receives audio → performs STT
5. **Fireworks** makes decision based on transcript
6. **Deepgram** generates TTS response (mulaw/8kHz)
7. Twilio sends audio back to caller

### With Fireworks (fireworks-integration agent)
- Use transcript from Deepgram STT
- Call Fireworks LLM with context (caller info, transcript)
- Get decision (connect, deflect, take message)
- Generate response via Deepgram TTS

## When to Use This Agent

- Implementing Twilio voice call webhooks
- Setting up media streaming to WebSocket
- Handling incoming/outgoing calls
- Debugging Twilio integration errors
- Building voice assistants with real-time audio
