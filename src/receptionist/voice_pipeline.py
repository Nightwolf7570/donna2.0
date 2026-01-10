"""Voice pipeline for speech-to-text and text-to-speech using Deepgram."""

import asyncio
import logging
from collections.abc import AsyncIterator

import httpx
from deepgram import AsyncDeepgramClient, listen

from .config import Settings

logger = logging.getLogger(__name__)


class VoicePipeline:
    """Handles speech-to-text and text-to-speech via Deepgram.
    
    This class provides methods to:
    - Transcribe streaming audio to text (STT)
    - Convert text to speech audio (TTS)
    - Generate greeting messages
    """

    DEFAULT_GREETING = "Hello, this is the AI assistant. How may I help you today?"

    def __init__(self, settings: Settings | None = None):
        """Initialize the VoicePipeline with Deepgram client.
        
        Args:
            settings: Application settings. If None, loads from environment.
        """
        if settings is None:
            from .config import get_settings
            settings = get_settings()
        
        self._settings = settings
        self._client = AsyncDeepgramClient(api_key=settings.deepgram_api_key)
        
        # Default STT options for live transcription
        self._stt_model = "nova-2"
        self._stt_language = "en-US"
        self._stt_encoding = "linear16"
        self._stt_sample_rate = "16000"
        
        # Default TTS options
        self._tts_model = "aura-asteria-en"
        self._tts_encoding = "linear16"
        self._tts_sample_rate = 16000

    def is_elevenlabs_enabled(self) -> bool:
        """Check if ElevenLabs TTS is enabled.
        
        Returns:
            True if ElevenLabs API key is configured.
        """
        return bool(self._settings.elevenlabs_api_key)

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        """Stream audio to Deepgram and yield transcribed text.
        
        Args:
            audio_stream: Async iterator yielding audio bytes (linear16, 16kHz).
            
        Yields:
            Transcribed text segments as they become available.
        """
        transcript_queue: asyncio.Queue[str | None] = asyncio.Queue()
        connection_closed = asyncio.Event()
        
        try:
            async with self._client.listen.v1.connect(
                model=self._stt_model,
                language=self._stt_language,
                encoding=self._stt_encoding,
                sample_rate=self._stt_sample_rate,
                smart_format="true",
                interim_results="true",
                utterance_end_ms="1000",
                vad_events="true",
            ) as socket_client:
                async def process_results() -> None:
                    try:
                        async for result in socket_client:
                            if isinstance(result, listen.ListenV1Results):
                                if (result.channel and 
                                    result.channel.alternatives and 
                                    len(result.channel.alternatives) > 0):
                                    transcript = result.channel.alternatives[0].transcript
                                    if transcript and result.is_final:
                                        await transcript_queue.put(transcript)
                    except Exception as e:
                        logger.error(f"Error processing transcription results: {e}")
                    finally:
                        connection_closed.set()
                        await transcript_queue.put(None)
                
                process_task = asyncio.create_task(process_results())
                
                try:
                    async for audio_chunk in audio_stream:
                        await socket_client.send(audio_chunk)
                except Exception as e:
                    logger.error(f"Error sending audio: {e}")
                finally:
                    await socket_client.close()
                
                while not connection_closed.is_set() or not transcript_queue.empty():
                    try:
                        transcript = await asyncio.wait_for(
                            transcript_queue.get(), 
                            timeout=0.5
                        )
                        if transcript is None:
                            break
                        yield transcript
                    except asyncio.TimeoutError:
                        if connection_closed.is_set():
                            break
                        continue
                
                await process_task
                

                
        except Exception as e:
            logger.error(f"Transcription stream error: {e}")
            raise

    async def _synthesize_elevenlabs(self, text: str) -> bytes:
        """Synthesize speech using ElevenLabs API.
        
        Args:
            text: Text to convert to speech.
            
        Returns:
            Audio bytes (MP3).
        """
        # Default voice: Rachel (American, Calm)
        voice_id = "21m00Tcm4TlvDq8ikWAM"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "xi-api-key": self._settings.elevenlabs_api_key,
            "Content-Type": "application/json",
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_turbo_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.content
            except httpx.HTTPError as e:
                logger.error(f"ElevenLabs API error: {e}")
                raise RuntimeError(f"ElevenLabs TTS failed: {e}")

    async def synthesize_speech(self, text: str) -> bytes:
        """Convert text to speech audio.
        
        Args:
            text: The text to convert to speech.
            
        Returns:
            Audio bytes in linear16 format at 16kHz sample rate.
            
        Raises:
            ValueError: If text is empty.
            RuntimeError: If TTS synthesis fails.
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        # Use ElevenLabs if enabled
        if self.is_elevenlabs_enabled():
            return await self._synthesize_elevenlabs(text)
        
        try:
            audio_bytes = b""
            async for chunk in self._client.speak.v1.audio.generate(
                text=text,
                model=self._tts_model,
                encoding=self._tts_encoding,
                sample_rate=self._tts_sample_rate,
            ):
                audio_bytes += chunk
            
            if not audio_bytes:
                raise RuntimeError("TTS produced no audio output")
            
            return audio_bytes
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"TTS synthesis failed: {e}")
            raise RuntimeError(f"Failed to synthesize speech: {e}") from e

    def get_greeting(self) -> str:
        """Return the initial greeting message.
        
        Returns:
            The default greeting message for incoming calls.
        """
        return self.DEFAULT_GREETING

    async def synthesize_greeting(self) -> bytes:
        """Synthesize the greeting message to audio.
        
        Returns:
            Audio bytes of the greeting message.
        """
        return await self.synthesize_speech(self.get_greeting())
