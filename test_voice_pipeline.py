"""Quick test script for VoicePipeline TTS functionality."""

import asyncio
import sys
sys.path.insert(0, '.')

from src.receptionist.voice_pipeline import VoicePipeline
from src.receptionist.config import Settings


async def test_tts():
    print("Loading settings...")
    try:
        settings = Settings()
        print(f"✓ Settings loaded (Deepgram API key: {settings.deepgram_api_key[:8]}...)")
    except Exception as e:
        print(f"✗ Failed to load settings: {e}")
        return
    
    print("\nInitializing VoicePipeline...")
    pipeline = VoicePipeline(settings)
    print("✓ VoicePipeline initialized")
    
    # Test greeting
    greeting = pipeline.get_greeting()
    print(f"\nGreeting message: \"{greeting}\"")
    
    # Test TTS
    print("\nTesting TTS (synthesize_speech)...")
    try:
        audio = await pipeline.synthesize_speech("Hello, this is a test of the AI receptionist.")
        print(f"✓ Generated {len(audio)} bytes of audio")
        
        # Save to file
        with open("test_audio.raw", "wb") as f:
            f.write(audio)
        print("✓ Saved to test_audio.raw (linear16, 16kHz mono)")
        print("\n  To play: ffplay -f s16le -ar 16000 -ac 1 test_audio.raw")
        print("  Or convert: ffmpeg -f s16le -ar 16000 -ac 1 -i test_audio.raw test_audio.wav")
        
    except Exception as e:
        print(f"✗ TTS failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_tts())
