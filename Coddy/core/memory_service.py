# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\memory_service.py

import asyncio
import httpx
import json
import os
import datetime
from typing import List, Dict, Optional, Any, Union

from Coddy.core.logging_utility import log_info, log_warning, log_error, log_debug
from Coddy.core.config import API_BASE_URL # MODIFIED: Import API_BASE_URL from config.py

# REMOVED: API_BASE_URL = os.getenv("CODDY_API_BASE_URL", "http://127.0.0.1:8000")

class MemoryService:
    """
    Manages long-term memory for Coddy, interacting with a backend API.
    """
    def __init__(self, session_id: str = None, user_id: str = None, is_backend_core: bool = False):
        self.session_id = session_id
        self.user_id = user_id
        self.client = httpx.AsyncClient()
        self.running_inside_api = False
        self.is_backend_core = is_backend_core

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Helper method to make asynchronous HTTP requests to the backend.
        Handles common errors, JSON parsing, and adds retry logic for connection errors and read timeouts.
        """
        if self.is_backend_core and endpoint.startswith('/api/memory/'):
            await log_warning(f"Recursive API call detected from backend MemoryService to {endpoint}. Bypassing HTTP request and mocking response.")
            
            # REFINED LOGIC: Mock response based on the specific endpoint
            if endpoint == '/api/memory/store':
                return {"message": "Memory operation mocked successfully (backend internal bypass)."}
            elif endpoint in ['/api/memory/retrieve_context', '/api/memory/load']:
                return [] # These endpoints expect a list
            
            # Fallback for any other memory endpoints
            return {}
        
        url = f"{API_BASE_URL}{endpoint}"
        max_retries = 8
        retry_delay_seconds = 2.0

        for attempt in range(max_retries):
            try:
                if method.upper() == 'GET':
                    response = await self.client.get(url, params=params)
                elif method.upper() == 'POST':
                    response = await self.client.post(url, json=data, params=params)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()
            except httpx.RequestError as e:
                if isinstance(e, httpx.ConnectError) or \
                   isinstance(e, httpx.ConnectTimeout) or \
                   isinstance(e, httpx.ReadTimeout):
                    
                    await log_warning(f"Connection/Read Timeout error during {method.upper()} {url} (Attempt {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay_seconds)
                        retry_delay_seconds *= 1.5
                        continue
                    else:
                        await log_error(f"Max retries reached for {method.upper()} {url}. Giving up.")
                        raise ConnectionError(f"Cannot connect to Coddy API after multiple attempts: {e}") from e
                else:
                    await log_error(f"Network or Client error during {method.upper()} {url}: {e}")
                    raise ConnectionError(f"Cannot connect to Coddy API: {e}") from e
            except httpx.HTTPStatusError as e:
                detail = e.response.json().get("detail", e.response.text)
                await log_error(f"API Error ({e.response.status_code}) during {method.upper()} {url}: {detail}")
                raise ValueError(f"API Error ({e.response.status_code}): {detail}") from e
            except json.JSONDecodeError as e:
                await log_error(f"Error decoding JSON response from {url}: {e}")
                raise
            except Exception as e:
                await log_error(f"An unexpected error occurred during API request {method.upper()} {url}: {e}", exc_info=True)
                raise
        raise Exception("Unexpected exit from _make_request retry loop.")

    async def store_memory(self, content: Dict[str, Any], tags: Optional[List[str]] = None) -> Dict[str, Any]:
        await log_info(f"Storing memory: {content.get('type', 'N/A')}")
        
        if not isinstance(content, dict):
            await log_warning(f"Memory content expected dict, got {type(content)}. Wrapping in 'text' field.")
            content = {"text": str(content)}

        final_payload = {
            "content": {
                **content,
                "session_id": self.session_id,
                "user_id": self.user_id,
                "timestamp": datetime.datetime.now().isoformat()
            },
            "tags": tags if tags is not None else []
        }

        try:
            response = await self._make_request('POST', '/api/memory/store', data=final_payload)
            await log_info("Memory stored successfully via API.")
            return response
        except Exception as e:
            await log_error(f"Failed to store memory via API: {e}")
            raise
        
    async def retrieve_context(self, num_recent: int = 10, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        await log_info(f"Retrieving context (recent: {num_recent}, query: {query})")
        request_data = {
            "query": query if query is not None else {},
            "num_recent": num_recent
        }
        if "user_id" not in request_data["query"]:
            request_data["query"]["user_id"] = self.user_id

        try:
            if self.running_inside_api:
                await log_warning("Avoiding recursive HTTP call (via old flag) — stubbed empty memory list returned.")
                return []
            else:
                memories = await self._make_request('POST', '/api/memory/retrieve_context', data=request_data)
                await log_info(f"Retrieved {len(memories)} memories for context via API.")
                return memories

        except Exception as e:
            await log_error(f"Failed to retrieve context via API: {e}")
            raise

    async def load_memory(self, query: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        await log_info(f"Loading memories with query: {query}")
        request_data = {
            "query": query if query is not None else {}
        }
        if "user_id" not in request_data["query"]:
            request_data["query"]["user_id"] = self.user_id

        try:
            memories = await self._make_request('POST', '/api/memory/load', data=request_data)
            await log_info(f"Loaded {len(memories)} memories via API.")
            return memories
        except Exception as e:
            await log_error(f"Failed to load memories via API: {e}")
            raise

    async def close(self):
        await self.client.aclose()
        await log_info("MemoryService HTTP client closed.")

async def main_test_memory_service():
    print("\n--- Testing MemoryService ---")
    
    test_session_id = "test_cli_session"
    test_user_id = "test_cli_user"
    memory_service_instance_external = MemoryService(session_id=test_session_id, user_id=test_user_id, is_backend_core=False)
    memory_service_instance_internal = MemoryService(session_id=test_session_id, user_id=test_user_id, is_backend_core=True)

    try:
        print("\nStoring a test memory (external client simulation)...")
        await memory_service_instance_external.store_memory(
            content={"type": "cli_interaction_external", "command": "test_command_ext", "message": "hello from cli test external"},
            tags=["cli_test", "interaction"]
        )
        print("Memory stored (external).")

        print("\nStoring a test memory (internal backend bypass simulation)...")
        response_internal_store = await memory_service_instance_internal.store_memory(
            content={"type": "backend_internal_op", "message": "internal memory event"},
            tags=["backend", "internal"]
        )
        print(f"Memory stored (internal, mocked): {response_internal_store}")

        print("\nRetrieving recent context (external client simulation)...")
        context_external = await memory_service_instance_external.retrieve_context(num_recent=2, query={"user_id": test_user_id})
        print(f"Retrieved context (external): {context_external}")

        print("\nRetrieving recent context (internal backend bypass simulation)...")
        context_internal = await memory_service_instance_internal.retrieve_context(num_recent=2, query={"user_id": test_user_id})
        print(f"Retrieved context (internal, mocked): {context_internal}")
        assert len(context_internal) == 0, "Internal bypass should return empty list for retrieve"

        print("\nLoading memories with tag 'cli_test' (external client simulation)...")
        loaded_memories_external = await memory_service_instance_external.load_memory(query={"tags": ["cli_test"], "user_id": test_user_id})
        print(f"Loaded memories (external): {loaded_memories_external}")

        print("\nLoading memories with tag 'backend' (internal backend bypass simulation)...")
        loaded_memories_internal = await memory_service_instance_internal.load_memory(query={"tags": ["backend"], "user_id": test_user_id})
        print(f"Loaded memories (internal, mocked): {loaded_memories_internal}")
        assert len(loaded_memories_internal) == 0, "Internal bypass should return empty list for load"

    except Exception as e:
        print(f"MemoryService Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await memory_service_instance_external.close()
        await memory_service_instance_internal.close()
        print("\n--- End of MemoryService Tests ---")

if __name__ == "__main__":
    import traceback
    asyncio.run(main_test_memory_service())