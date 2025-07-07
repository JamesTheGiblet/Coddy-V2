# c:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\dashboard_api.py

import httpx
from typing import List

# --- Configuration ---
# The base URL for the Coddy FastAPI backend.
# Make sure the backend is running at this address.
API_BASE_URL = "http://127.0.0.1:8000"

# --- API Client ---
# Use a single AsyncClient instance for connection pooling and efficiency.
client = httpx.AsyncClient(base_url=API_BASE_URL)

# --- API Functions ---

async def get_roadmap() -> str:
    """Fetches the project roadmap from the API."""
    response = await client.get("/api/roadmap")
    response.raise_for_status()  # Will raise an exception for 4xx/5xx responses
    return response.json()["content"]

async def list_files(path: str = ".") -> List[str]:
    """Lists files and directories at a given path via the API."""
    params = {"path": path}
    response = await client.get("/api/files/list", params=params)
    response.raise_for_status()
    return response.json()["items"]

async def read_file(path: str) -> str:
    """Reads the content of a file at a given path via the API."""
    params = {"path": path}
    response = await client.get("/api/files/read", params=params)
    response.raise_for_status()
    return response.json()["content"]

async def write_file(path: str, content: str) -> str:
    """Writes content to a file at a given path via the API."""
    json_payload = {"path": path, "content": content}
    response = await client.post("/api/files/write", json=json_payload)
    response.raise_for_status()
    return response.json()["message"]

async def decompose_task(instruction: str) -> List[str]:
    """Sends an instruction to the API for decomposition into subtasks."""
    json_payload = {"instruction": instruction}
    response = await client.post("/api/tasks/decompose", json=json_payload)
    response.raise_for_status()
    return response.json()

async def check_api_status() -> bool:
    """Checks if the API is running and reachable."""
    try:
        response = await client.get("/")
        return response.status_code == 200
    except httpx.RequestError:
        return False