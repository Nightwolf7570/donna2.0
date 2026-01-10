"""Google OAuth2 authentication and service creation."""

import logging
import os
import time
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from googleapiclient.errors import HttpError

from .config import get_settings

logger = logging.getLogger(__name__)

# Scopes required for the application
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
]

TOKEN_FILE = "token.json"


def authenticate_google() -> Credentials | None:
    """Authenticate with Google APIs and return credentials.
    
    Handles token refreshing and initial OAuth flow.
    Note: Initial flow requires local browser interaction.
    """
    creds = None
    settings = get_settings()
    
    # Check if credentials file is configured
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    
    # Load existing token
    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            logger.warning(f"Failed to load token file: {e}")
    
    # Refresh or create new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                logger.info("Refreshing expired Google access token")
                creds.refresh(Request())
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                # If refresh fails, we might need a new login, but we can't force it 
                # autonomously without user interaction if we are headless.
                # For now, let's assume we fall through to the re-auth flow 
                # IF we have the credentials.json to do so.
                creds = None

        if not creds:
            if not os.path.exists(creds_path):
                logger.warning(f"Google credentials file not found at {creds_path}")
                return None
                
            try:
                logger.info("Initiating Google OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
                # port=0 picks a random available port
                creds = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"OAuth flow failed: {e}")
                return None
        
        # Save credentials for next run
        try:
            with open(TOKEN_FILE, "w") as token:
                token.write(creds.to_json())
            logger.info("Saved new Google credentials to token.json")
        except Exception as e:
            logger.error(f"Failed to save token: {e}")

    return creds


def retry_with_backoff(func, max_retries=3, initial_delay=1.0):
    """Execute a function with exponential backoff for transient errors."""
    for attempt in range(max_retries):
        try:
            return func()
        except HttpError as e:
            # 429 = Too Many Requests
            # 5xx = Server Error
            if (e.resp.status == 429 or e.resp.status >= 500) and attempt < max_retries - 1:
                wait_time = initial_delay * (2 ** attempt)
                logger.warning(f"Google API error {e.resp.status}, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
        except Exception:
            # Don't retry other exceptions by default unless specified
            raise


def get_service(service_name: str, version: str) -> Resource | None:
    """Build a Google API service client."""
    creds = authenticate_google()
    if not creds:
        return None
    
    try:
        service = build(service_name, version, credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Failed to build {service_name} service: {e}")
        return None


def get_calendar_service() -> Resource | None:
    """Get authenticated Google Calendar service."""
    return get_service("calendar", "v3")


def get_gmail_service() -> Resource | None:
    """Get authenticated Gmail service."""
    return get_service("gmail", "v1")
