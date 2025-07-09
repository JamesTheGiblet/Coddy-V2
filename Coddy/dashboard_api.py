# C:\Users\gilbe\Documents\GitHub\Coddy V2\Coddy\dashboard_api.py

import httpx
import json
from typing import Dict, Any, Optional, List

# Base URL for your Coddy backend API
API_BASE_URL = "http://127.0.0.1:8000/api"

async def get_roadmap():
    """Fetches the project roadmap from the Coddy API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/roadmap")
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json().get("content", "No roadmap available.")

async def list_files(path: str = "."):
    """Lists files and directories at a given path via the Coddy API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/files/list", params={"path": path})
        response.raise_for_status()
        return response.json().get("items", [])

async def read_file(path: str):
    """Reads the content of a file via the Coddy API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/files/read", params={"path": path})
        response.raise_for_status()
        return response.json().get("content", "")

async def write_file(path: str, content: str):
    """Writes content to a file via the Coddy API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/files/write",
            json={"path": path, "content": content}
        )
        response.raise_for_status()
        return response.json().get("message", "File write operation completed.")

async def decompose_task(instruction: str, user_profile: Optional[Dict[str, Any]] = None):
    """
    Decomposes a high-level instruction into subtasks via the Coddy API,
    passing the user's profile for personalization.
    """
    async with httpx.AsyncClient() as client:
        payload = {"instruction": instruction}
        if user_profile:
            payload["user_profile"] = user_profile # Include user profile in the request
        
        response = await client.post(
            f"{API_BASE_URL}/tasks/decompose",
            json=payload
        )
        response.raise_for_status()
        return response.json() # This should be a list of strings

async def generate_code(prompt: str, context: Optional[Dict[str, Any]] = None, user_profile: Optional[Dict[str, Any]] = None):
    """
    Generates code based on a prompt via the Coddy API,
    passing the user's profile for personalization.
    """
    async with httpx.AsyncClient() as client:
        payload = {"prompt": prompt}
        if context:
            payload["context"] = context
        if user_profile:
            payload["user_profile"] = user_profile # Include user profile in the request
        
        response = await client.post(
            f"{API_BASE_URL}/code/generate",
            json=payload
        )
        response.raise_for_status()
        return response.json() # This should be a dictionary with a "code" key

async def refactor_code(file_path: str, original_code: str, instructions: str, user_profile: Optional[Dict[str, Any]] = None):
    """Refactors code via the Coddy API."""
    async with httpx.AsyncClient() as client:
        payload = {
            "file_path": file_path,
            "original_code": original_code,
            "instructions": instructions,
        }
        if user_profile:
            payload["user_profile"] = user_profile
        
        response = await client.post(
            f"{API_BASE_URL}/code/refactor",
            json=payload,
            timeout=120.0  # Allow longer timeout for potentially complex refactoring
        )
        response.raise_for_status()
        return response.json()

async def generate_changelog(output_file: str, user_profile: Optional[Dict[str, Any]] = None):
    """Generates a changelog via the Coddy API."""
    async with httpx.AsyncClient() as client:
        payload = {"output_file": output_file}
        if user_profile:
            payload["user_profile"] = user_profile
        
        response = await client.post(
            f"{API_BASE_URL}/automation/generate_changelog",
            json=payload,
            timeout=120.0 # Allow longer timeout for changelog generation
        )
        response.raise_for_status()
        return response.json()

async def generate_todo_stubs(scan_path: str, output_file: str, user_profile: Optional[Dict[str, Any]] = None):
    """Generates TODO stubs for incomplete functions via the Coddy API."""
    async with httpx.AsyncClient() as client:
        payload = {
            "scan_path": scan_path,
            "output_file": output_file,
        }
        if user_profile:
            payload["user_profile"] = user_profile
        
        response = await client.post(
            f"{API_BASE_URL}/automation/generate_todo_stubs",
            json=payload,
            timeout=180.0 # Allow even longer for scanning multiple files
        )
        response.raise_for_status()
        return response.json()

async def get_user_profile() -> Dict[str, Any]:
    """Fetches the current user profile from the Coddy API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/profile")
        response.raise_for_status()
        return response.json()

async def set_user_profile(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """Updates the user profile via the Coddy API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/profile/set",
            json={"profile_data": profile_data}
        )
        response.raise_for_status()
        return response.json()

async def clear_user_profile() -> Dict[str, Any]:
    """Resets the user profile to default via the Coddy API."""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{API_BASE_URL}/profile/clear")
        response.raise_for_status()
        return response.json()

async def add_feedback(rating: int, comment: Optional[str] = None, context_id: Optional[str] = None) -> Dict[str, Any]:
    """Submits user feedback via the Coddy API."""
    async with httpx.AsyncClient() as client:
        payload = {"rating": rating}
        if comment:
            payload["comment"] = comment
        if context_id:
            payload["context_id"] = context_id
        
        response = await client.post(
            f"{API_BASE_URL}/feedback/add",
            json=payload
        )
        response.raise_for_status()
        return response.json()
