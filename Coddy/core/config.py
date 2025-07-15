# c:/Users/gilbe/Documents/GitHub/Coddy V2/Coddy/core/config.py
"""
Central configuration for Coddy services.
"""
import os

# The base URL for the FastAPI backend which handles memory, file operations, etc.
API_BASE_URL = os.getenv("CODDY_API_URL", "http://127.0.0.1:8000")

# WebSocket server configuration
WEBSOCKET_HOST = os.getenv("CODDY_WEBSOCKET_HOST", "localhost")
WEBSOCKET_PORT = int(os.getenv("CODDY_WEBSOCKET_PORT", 8080))

# The URL for the WebSocket server for real-time UI updates.
WEBSOCKET_URL = f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}"