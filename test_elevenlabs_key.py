
import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ELEVENLABS_API_KEY")
print(f"Loaded API Key: {api_key[:5]}...{api_key[-5:] if api_key else ''} (Length: {len(api_key) if api_key else 0})")

async def test_tts():
    voice_id = "21m00Tcm4TlvDq8ikWAM"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": "Hello world",
        "model_id": "eleven_turbo_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        }
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            print(f"Status Code: {response.status_code}")
            if response.status_code != 200:
                print(f"Response: {response.text}")
            else:
                print("TTS Successful (Audio data received)")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not found in environment.")
    else:
        asyncio.run(test_tts())
