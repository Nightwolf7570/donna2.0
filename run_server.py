"""Start the AI Receptionist server."""

import sys
sys.path.insert(0, '.')

import uvicorn
from src.receptionist.config import get_settings

if __name__ == "__main__":
    settings = get_settings()
    print(f"Starting AI Receptionist on {settings.server_host}:{settings.server_port}")
    print(f"Webhook URL: http://localhost:{settings.server_port}/incoming-call")
    print("\nTo expose via ngrok: ngrok http {settings.server_port}")
    uvicorn.run(
        "src.receptionist.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=True,
    )
