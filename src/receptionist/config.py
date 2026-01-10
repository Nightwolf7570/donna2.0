"""Configuration management using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # MongoDB Atlas
    mongodb_uri: str

    # Voyage AI (embeddings)
    voyage_api_key: str

    # Deepgram (STT)
    deepgram_api_key: str

    # ElevenLabs (TTS)
    elevenlabs_api_key: str = ""

    # Fireworks AI (reasoning)
    fireworks_api_key: str

    # Twilio (telephony)
    twilio_account_sid: str
    twilio_auth_token: str
    twilio_phone_number: str

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    
    # Base URL for TTS audio (ngrok URL in development)
    base_url: str = ""


def get_settings() -> Settings:
    """Get application settings (cached)."""
    return Settings()
