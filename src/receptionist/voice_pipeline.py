"""Voice pipeline for speech-to-text (Deepgram) and text-to-speech."""

import asyncio
import logging
from collections.abc import AsyncIterator

import httpx
from deepgram import DeepgramClient, LiveOptions

from .config import Settings

logger = logging.getLogger(__name__)


class VoicePipeline:
    """Handles speech-to-text via Deepgram."""

    DEFAULT_GREETING = "Hello, this is Donna, your AI assistant. How may I help you today?"

    def __init__(self, settings: Settings | None = None):
        if settings is None:
            from .config import get_settings
            settings = get_settings()
        
        self._settings = settings
        self._deepgram_api_key = settings.deepgram_api_key
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        """Stream audio to Deepgram and yield transcribed text."""
        transcript_queue: asyncio.Queue[str | None] = asyncio.Queue()
        connection_ready = asyncio.Event()
        
        try:
            deepgram = DeepgramClient(self._deepgram_api_key)
            dg_connection = deepgram.listen.asyncwebsocket.v("1")
            
            async def on_open(self_conn, open_response, **kwargs):
                logger.info("Deepgram connection opened")
                connection_ready.set()
            
            async def on_message(self_conn, result, **kwargs):
                try:
                    sentence = result.channel.alternatives[0].transcript
                    if sentence and result.is_final:
                        logger.info(f"Deepgram transcript: {sentence}")
                        await transcript_queue.put(sentence)
                except Exception as e:
                    logger.error(f"Error in on_message: {e}")
            
            async def on_error(self_conn, error, **kwargs):
                logger.error(f"Deepgram error: {error}")
            
            async def on_close(self_conn, close, **kwargs):
                logger.info("Deepgram connection closed")
                await transcript_queue.put(None)
            
            dg_connection.on("Open", on_open)
            dg_connection.on("Results", on_message)
            dg_connection.on("Error", on_error)
            dg_connection.on("Close", on_close)
            
            options = LiveOptions(
                model="nova-2",
                language="en-US",
                encoding="mulaw",
                sample_rate=8000,
                smart_format=True,
                interim_results=False,
                utterance_end_ms="1000",
                vad_events=True,
            )
            
            # Start connection - this is the key fix
            if await dg_connection.start(options) is False:
                logger.error("Failed to start Deepgram")
                return
            
            # Wait for connection to be ready
            await asyncio.wait_for(connection_ready.wait(), timeout=5.0)
            logger.info("Deepgram ready, starting audio stream")
            
            # Send audio in background
            async def send_audio():
                try:
                    async for chunk in audio_stream:
                        if chunk:
                            await dg_connection.send(chunk)
                except Exception as e:
                    logger.error(f"Send audio error: {e}")
                finally:
                    try:
                        await dg_connection.finish()
                    except:
                        pass
            
            send_task = asyncio.create_task(send_audio())
            
            # Yield transcripts
            while True:
                try:
                    transcript = await asyncio.wait_for(transcript_queue.get(), timeout=1.0)
                    if transcript is None:
                        break
                    yield transcript
                except asyncio.TimeoutError:
                    if send_task.done():
                        break
                    continue
            
            send_task.cancel()
            try:
                await send_task
            except asyncio.CancelledError:
                pass
                
        except Exception as e:
            logger.error(f"Transcription stream error: {e}")

    def get_greeting(self) -> str:
        return self.DEFAULT_GREETING

    def is_elevenlabs_enabled(self) -> bool:
        return False

    async def synthesize_speech(self, text: str) -> bytes:
        """Convert text to speech using Deepgram TTS.
        
        Args:
            text: The text to convert to speech.
            
        Returns:
            Audio bytes in MP3 format.
            
        Raises:
            Exception: If TTS synthesis fails.
        """
        try:
            # Use Deepgram TTS API
            url = "https://api.deepgram.com/v1/speak"
            
            headers = {
                "Authorization": f"Token {self._deepgram_api_key}",
                "Content-Type": "application/json",
            }
            
            # Use aura-asteria-en for a natural female voice
            params = {
                "model": "aura-asteria-en",
                "encoding": "mp3",
            }
            
            payload = {
                "text": text
            }
            
            response = await self._http_client.post(
                url,
                headers=headers,
                params=params,
                json=payload,
            )
            
            if response.status_code != 200:
                logger.error(f"Deepgram TTS error: {response.status_code} - {response.text}")
                raise Exception(f"TTS failed with status {response.status_code}")
            
            return response.content
            
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            raise

    async def close(self) -> None:
        await self._http_client.aclose()
