# C:\Users\gilbe\Documents\GitHub\Coddy V2\Coddy\dashboard_api.py
import httpx
import asyncio
from typing import List, Dict, Any, Union

# Define the base URL for your Coddy FastAPI backend
API_BASE_URL = "http://127.0.0.1:8000"

async def get_roadmap() -> str:
    """
    Fetches the project roadmap content from the Coddy API.

    Returns:
        The roadmap content as a string.
    Raises:
        httpx.RequestError: If there's a network error (e.g., API server is not running).
        httpx.HTTPStatusError: If the API returns a non-2xx status code.
        Exception: For any other unexpected errors.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/roadmap")
            response.raise_for_status()  # Raise an exception for 4xx/5xx responses
            data = response.json()
            return data.get("content", "No roadmap content found.")
    except httpx.RequestError as e:
        print(f"Network Error fetching roadmap: {e}")
        raise # Re-raise to be handled by the Streamlit app
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", e.response.text)
        print(f"API Error fetching roadmap ({e.response.status_code}): {detail}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred while fetching roadmap: {e}")
        raise

async def list_files(path: str = ".") -> List[str]:
    """
    Lists files and directories at a given path from the Coddy API.

    Args:
        path: The directory path to list. Defaults to current directory.

    Returns:
        A list of file and directory names.
    Raises:
        httpx.RequestError: If there's a network error.
        httpx.HTTPStatusError: If the API returns a non-2xx status code (e.g., 404 for not found).
        Exception: For any other unexpected errors.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/files/list", params={"path": path})
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
    except httpx.RequestError as e:
        print(f"Network Error listing files for '{path}': {e}")
        raise
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", e.response.text)
        print(f"API Error listing files for '{path}' ({e.response.status_code}): {detail}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred while listing files for '{path}': {e}")
        raise

async def read_file(path: str) -> str:
    """
    Reads the content of a file from the Coddy API.

    Args:
        path: The path to the file to read.

    Returns:
        The content of the file as a string.
    Raises:
        httpx.RequestError: If there's a network error.
        httpx.HTTPStatusError: If the API returns a non-2xx status code (e.g., 404 for file not found).
        Exception: For any other unexpected errors.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/files/read", params={"path": path})
            response.raise_for_status()
            data = response.json()
            return data.get("content", "")
    except httpx.RequestError as e:
        print(f"Network Error reading file '{path}': {e}")
        raise
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", e.response.text)
        print(f"API Error reading file '{path}' ({e.response.status_code}): {detail}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred while reading file '{path}': {e}")
        raise

async def write_file(path: str, content: str) -> str:
    """
    Writes content to a file via the Coddy API.

    Args:
        path: The path to the file to write.
        content: The content to write to the file.

    Returns:
        A success message from the API.
    Raises:
        httpx.RequestError: If there's a network error.
        httpx.HTTPStatusError: If the API returns a non-2xx status code (e.g., 400 for bad request).
        Exception: For any other unexpected errors.
    """
    try:
        async with httpx.AsyncClient() as client:
            json_data = {"path": path, "content": content}
            response = await client.post(f"{API_BASE_URL}/api/files/write", json=json_data)
            response.raise_for_status()
            data = response.json()
            return data.get("message", f"Successfully wrote to {path}")
    except httpx.RequestError as e:
        print(f"Network Error writing to file '{path}': {e}")
        raise
    except httpx.HTTPStatusError as e:
        detail = e.response.json().get("detail", e.response.text)
        print(f"API Error writing to file '{path}' ({e.response.status_code}): {detail}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred while writing to file '{path}': {e}")
        raise

# You can add more API functions here as you expose more endpoints
# e.g., for memory, patterns, etc.

# Example of how you might use these functions (for testing this module directly)
if __name__ == "__main__":
    async def main_test_api_client():
        print("--- Testing get_roadmap ---")
        try:
            roadmap_content = await get_roadmap()
            print(f"Roadmap fetched successfully (first 200 chars):\n{roadmap_content[:200]}...")
        except Exception as e:
            print(f"Failed to fetch roadmap: {e}")

        print("\n--- Testing list_files (current directory) ---")
        try:
            files = await list_files(".")
            print(f"Files in current directory: {files}")
        except Exception as e:
            print(f"Failed to list files: {e}")

        print("\n--- Testing read_file (this file) ---")
        try:
            # Assuming this file exists and is readable
            file_content = await read_file("dashboard_api.py")
            print(f"Content of dashboard_api.py (first 100 chars):\n{file_content[:100]}...")
        except Exception as e:
            print(f"Failed to read file: {e}")

        print("\n--- Testing write_file ---")
        test_file_name = "test_dashboard_write.txt"
        test_content = "This is a test content written from the dashboard API client."
        try:
            message = await write_file(test_file_name, test_content)
            print(f"Write successful: {message}")
            # Verify by reading it back
            read_back_content = await read_file(test_file_name)
            print(f"Content read back: {read_back_content}")
            if read_back_content == test_content:
                print("Write and read verification successful!")
            else:
                print("Content mismatch after write and read.")
        except Exception as e:
            print(f"Failed to write file: {e}")
        finally:
            # Clean up the test file
            import os
            if os.path.exists(test_file_name):
                os.remove(test_file_name)
                print(f"Cleaned up {test_file_name}")

    # Run the test functions
    asyncio.run(main_test_api_client())
