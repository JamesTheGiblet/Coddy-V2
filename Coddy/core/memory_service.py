# Coddy/core/memory_service.py
import asyncio
import httpx # Changed from aiohttp to httpx for consistency
import json
import os
import datetime # Added datetime for timestamp generation
from typing import List, Dict, Optional, Any, Union

# Assuming these are available from the core module or passed in
from Coddy.core.logging_utility import log_info, log_warning, log_error, log_debug

# Configuration for the API base URL (consistent with backend/main.py)
API_BASE_URL = os.getenv("CODY_API_BASE_URL", "http://127.0.0.1:8000")

class MemoryService:
    """
    Manages long-term memory for Coddy, interacting with a backend API.
    """
    def __init__(self, session_id: str = None, user_id: str = None):
        self.session_id = session_id
        self.user_id = user_id
        # Use a single httpx.AsyncClient for the service for efficiency
        self.client = httpx.AsyncClient() 

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Helper method to make asynchronous HTTP requests to the backend.
        Handles common errors, JSON parsing, and adds retry logic for connection errors and read timeouts.
        """
        url = f"{API_BASE_URL}{endpoint}"
        max_retries = 8 # Increased max retries
        retry_delay_seconds = 2.0 # Increased initial delay further

        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    response = await self.client.get(url, params=params)
                elif method.upper() == 'POST':
                    response = await self.client.post(url, json=data, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status() # Raise an exception for 4xx/5xx responses
                return response.json()
            except httpx.RequestError as e:
                # Catch connection errors and read timeouts specifically for retries
                if isinstance(e, httpx.ConnectError) or \
                   isinstance(e, httpx.ConnectTimeout) or \
                   isinstance(e, httpx.ReadTimeout):
                    
                    await log_warning(f"Connection/Read Timeout error during {method.upper()} {url} (Attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay_seconds)
                        retry_delay_seconds *= 1.5 # Exponential backoff
                        continue # Try again
                    else:
                        await log_error(f"Max retries reached for {method.upper()} {url}. Giving up.")
                        raise ConnectionError(f"Cannot connect to Coddy API after multiple attempts: {e}") from e
                else:
                    # Other httpx.RequestError types (e.g., InvalidURL) are not retried by this logic
                    await log_error(f"Network or Client error during {method.upper()} {url}: {e}")
                    raise ConnectionError(f"Cannot connect to Coddy API: {e}") from e
            except httpx.HTTPStatusError as e:
                # HTTP 4xx/5xx errors are not retried by this logic, they indicate API issues
                detail = e.response.json().get("detail", e.response.text)
                await log_error(f"API Error ({e.response.status_code}) during {method.upper()} {url}: {detail}")
                raise ValueError(f"API Error ({e.response.status_code}): {detail}") from e
            except json.JSONDecodeError as e:
                await log_error(f"Error decoding JSON response from {url}: {e}")
                raise
            except Exception as e:
                await log_error(f"An unexpected error occurred during API request {method.upper()} {url}: {e}", exc_info=True)
                raise
        # This line should technically not be reached, but added for completeness
        raise Exception("Unexpected exit from _make_request retry loop.")


    async def store_memory(self, content: Dict[str, Any], tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Stores a new memory entry in the backend via the /api/memory/store endpoint.
        The content is expected to be a dictionary.
        """
        await log_info(f"Storing memory: {content.get('type', 'N/A')}")
        
        # Ensure content is a dictionary as expected by the backend's MemoryEntry Pydantic model
        if not isinstance(content, dict):
            await log_warning(f"Memory content expected dict, got {type(content)}. Wrapping in 'text' field.")
            content = {"text": str(content)}

        # The backend's MemoryEntry Pydantic model expects 'content' and 'tags' as top-level fields.
        # It expects session_id, user_id, timestamp to be part of the 'content' dict.
        final_payload = {
            "content": {
                **content, # Unpack existing content dict
                "session_id": self.session_id,
                "user_id": self.user_id,
                "timestamp": datetime.datetime.now().isoformat()
            },
            "tags": tags if tags is not None else []
        }

        try:
            # Use the /api/memory/store endpoint (POST)
            response = await self._make_request('POST', '/api/memory/store', data=final_payload)
            await log_info("Memory stored successfully via API.")
            return response
        except Exception as e:
            await log_error(f"Failed to store memory via API: {e}")
            raise
        
    async def retrieve_context(self, num_recent: int = 10, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieves recent memory entries either directly or via the /api/memory/retrieve_context endpoint.
        """
        await log_info(f"Retrieving context (recent: {num_recent}, query: {query})")
        request_data = {
            "query": query if query is not None else {},
            "num_recent": num_recent
        }
        if "user_id" not in request_data["query"]:
            request_data["query"]["user_id"] = self.user_id

        try:
            # 🧠 If inside the API process, avoid recursive HTTP call
            if self.running_inside_api:
                await log_warning("Avoiding recursive HTTP call — stubbed empty memory list returned.")
                # TODO: replace with a direct call to memory backend or in-memory store if available
                return []  # <-- Or implement real direct call here
            else:
                memories = await self._make_request('POST', '/api/memory/retrieve_context', data=request_data)
                await log_info(f"Retrieved {len(memories)} memories for context via API.")
                return memories

        except Exception as e:
            await log_error(f"Failed to retrieve context via API: {e}")
            raise

    async def load_memory(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Loads memory entries based on a specific query (e.g., for search) via the /api/memory/load endpoint (POST).
        """
        await log_info(f"Loading memories with query: {query}")
        request_data = {
            "query": query if query is not None else {}
        }
        # Ensure user_id is always part of the query for loading, as expected by backend
        if "user_id" not in request_data["query"]:
            request_data["query"]["user_id"] = self.user_id

        try:
            # Use the /api/memory/load endpoint (POST)
            memories = await self._make_request('POST', '/api/memory/load', data=request_data)
            await log_info(f"Loaded {len(memories)} memories via API.")
            return memories
        except Exception as e:
            await log_error(f"Failed to load memories via API: {e}")
            raise

    async def close(self):
        """Closes the HTTP client session."""
        await self.client.aclose()
        await log_info("MemoryService HTTP client closed.")

# Example Usage (for testing this module directly)
async def main_test_memory_service():
    print("\n--- Testing MemoryService ---")
    
    # Ensure the FastAPI backend is running before running these tests!
    # uvicorn Coddy.backend.main:app --host 0.0.0.0 --port 8000 --reload

    test_session_id = "test_cli_session"
    test_user_id = "test_cli_user"
    memory_service_instance = MemoryService(session_id=test_session_id, user_id=test_user_id)

    try:
        # Test storing a memory
        print("\nStoring a test memory...")
        await memory_service_instance.store_memory(
            content={"type": "cli_interaction", "command": "test_command", "message": "hello from cli test"},
            tags=["cli_test", "interaction"]
        )
        print("Memory stored.")

        # Test retrieving context
        print("\nRetrieving recent context...")
        context = await memory_service_instance.retrieve_context(num_recent=2, query={"user_id": test_user_id})
        print(f"Retrieved context: {context}")
        assert len(context) > 0, "Should retrieve at least one memory"

        # Test loading specific memories
        print("\nLoading memories with tag 'cli_test'...")
        loaded_memories = await memory_service_instance.load_memory(query={"tags": ["cli_test"], "user_id": test_user_id}) # Query tags should be a list
        print(f"Loaded memories: {loaded_memories}")
        assert any("cli_interaction" == mem.get('content', {}).get('type') for mem in loaded_memories), "Should find the stored memory"

    except Exception as e:
        print(f"MemoryService Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await memory_service_instance.close()
        print("\n--- End of MemoryService Tests ---")

if __name__ == "__main__":
    import traceback
    asyncio.run(main_test_memory_service())
