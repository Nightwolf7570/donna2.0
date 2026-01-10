from src.receptionist.config import get_settings
import os

try:
    settings = get_settings()
    print(f"Voyage Key Present: {bool(settings.voyage_api_key)}")
    print(f"Key length: {len(settings.voyage_api_key) if settings.voyage_api_key else 0}")
except Exception as e:
    print(f"Error loading settings: {e}")
