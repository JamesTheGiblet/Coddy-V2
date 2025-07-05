# c:/Users/gilbe/Documents/GitHub/Coddy V2/Coddy/core/config.py
"""
Central configuration for Coddy services.
"""

# The base URL for the FastAPI backend which handles memory, file operations, etc.
API_BASE_URL = "http://127.0.0.1:8000"

# The URL for the WebSocket server for real-time UI updates.
WEBSOCKET_URL = "ws://localhost:8080"

# WebSocket server configuration
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8080