# Coddy/core/memory_service.py
import asyncio
import aiohttp # For making asynchronous HTTP requests
import json # For handling JSON data
import os # For environment variables
from typing import List, Dict, Optional, Any, Union # Added Union for content type

# Define the base URL for the backend API
# This should match where your Node.js Express server is running.
# In a real deployment, this would likely be an environment variable.
BACKEND_BASE_URL = os.environ.get('CODY_BACKEND_URL', 'http://localhost:3000')

class MemoryService:
    """
    Encapsulates asynchronous logic for interacting with Coddy V2 backend
    API endpoints related to memory and feedback, and now also patterns.
    """

    def __init__(self, session_id: str = None, user_id: str = None):
        """
        Initializes the MemoryService.

        Args:
            session_id: A unique identifier for the current session.
            user_id: A unique identifier for the current user.
        """
        self.session_id = session_id
        self.user_id = user_id
        # Note: aiohttp.ClientSession should ideally be managed by a context manager
        # or created once per application lifecycle for efficiency.
        # For simplicity in this module, we'll create it on demand or manage within methods.

    async def _make_request(self, method: str, endpoint: str, data: dict = None) -> dict:
        """
        Helper method to make asynchronous HTTP requests to the backend.

        Args:
            method: HTTP method (e.g., 'GET', 'POST').
            endpoint: The API endpoint (e.g., '/api/memory').
            data: Dictionary of data to send as JSON payload for POST requests.

        Returns:
            A dictionary containing the JSON response from the backend.

        Raises:
            aiohttp.ClientError: For network or HTTP-related errors.
            ValueError: If the response status is not 2xx.
        """
        url = f"{BACKEND_BASE_URL}{endpoint}"
        headers = {'Content-Type': 'application/json'}

        try:
            async with aiohttp.ClientSession() as session:
                if method == 'POST':
                    async with session.post(url, headers=headers, json=data) as response:
                        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
                        return await response.json()
                elif method == 'GET':
                    async with session.get(url, headers=headers) as response:
                        response.raise_for_status()
                        return await response.json()
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
        except aiohttp.ClientError as e:
            print(f"Network or Client error during {method} {url}: {e}")
            raise
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON response from {url}: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred during {method} {url}: {e}")
            raise

    async def store_memory(self, content: Union[str, dict], tags: list[str] = None) -> dict:
        """
        Stores a new memory fragment in the backend.
        Handles content that is a string or a dictionary (JSONifies dicts).

        Args:
            content: The main content of the memory (can be str or dict).
            tags: Optional list of tags for the memory.

        Returns:
            The JSON response from the backend after storing the memory.
        """
        # Ensure content for payload is a string (JSON if dict)
        content_for_payload = content
        if isinstance(content, dict):
            content_for_payload = json.dumps(content)

        # For display in print statement, convert to string safely
        display_content = str(content)
        if len(display_content) > 50:
            display_content = display_content[:50] + '...'

        print(f"Storing memory: '{display_content}' with tags: {tags}")
        payload = {
            "content": content_for_payload,
            "tags": tags if tags is not None else [],
            "session_id": self.session_id,
            "user_id": self.user_id # Include user_id in memory for tracking
        }
        try:
            response = await self._make_request('POST', '/api/memory', payload)
            print("Memory stored successfully.")
            return response
        except Exception as e:
            print(f"Failed to store memory: {e}")
            raise

    async def load_memory(self, query: dict = None) -> list[dict]:
        """
        Loads memory fragments from the backend based on a query.
        Attempts to parse content back into a dictionary if it's a JSON string.

        Args:
            query: Optional dictionary to filter memories (e.g., {"session_id": "xyz"}).

        Returns:
            A list of memory dictionaries, with content parsed if it was JSON.
        """
        print(f"Loading memories with query: {query}")
        endpoint = '/api/memory'
        # Backend /api/memory GET currently doesn't accept query params directly
        # So we fetch all and filter in Python.
        try:
            response = await self._make_request('GET', endpoint)
            all_memories = response.get('data', [])

            parsed_and_filtered_memories = []
            for mem in all_memories:
                content = mem.get('content')
                # Attempt to parse content if it looks like a JSON string
                if isinstance(content, str) and content.strip().startswith('{') and content.strip().endswith('}'):
                    try:
                        mem['content'] = json.loads(content)
                    except json.JSONDecodeError:
                        pass # Not a valid JSON string, keep as is

                # Apply in-memory filtering based on the query
                match = True
                if query:
                    # Specific handling for 'tags' filter: all query tags must be present in memory's tags
                    if "tags" in query:
                        query_tags = query["tags"]
                        if isinstance(query_tags, str): # Handle single tag string query
                            query_tags = [query_tags]
                        
                        mem_tags = mem.get('tags', [])
                        # Check if all query tags are present in the memory's tags
                        if not all(q_tag in mem_tags for q_tag in query_tags):
                            match = False
                    
                    # Handle other direct field matches
                    for key, value in query.items():
                        if key == "tags": # Already handled above
                            continue
                        # If a key is in query but not in memory, or values don't match
                        if key not in mem or mem.get(key) != value:
                            match = False
                            break
                if match:
                    parsed_and_filtered_memories.append(mem)

            print(f"Loaded {len(parsed_and_filtered_memories)} memories (filtered).")
            return parsed_and_filtered_memories
        except Exception as e:
            print(f"Failed to load memories: {e}")
            raise

    async def record_bug(self, message: str, metadata: dict = None) -> dict:
        """
        Records a bug report in the backend using the /api/feedback endpoint.

        Args:
            message: The bug description.
            metadata: Optional dictionary with additional context (e.g., stack trace).

        Returns:
            The JSON response from the backend after recording the bug.
        """
        print(f"Recording bug: '{message[:50]}...'")
        payload = {
            "type": "bug",
            "message": message,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": metadata if metadata is not None else {}
        }
        try:
            response = await self._make_request('POST', '/api/feedback', payload)
            print("Bug recorded successfully.")
            return response
        except Exception as e:
            print(f"Failed to record bug: {e}")
            raise

    async def store_pattern_data(self, pattern_type: str, description: str, data: Any, user_id: Optional[str] = None) -> dict:
        """
        Stores a detected pattern in the backend via the /api/pattern endpoint.

        Args:
            pattern_type: The type of pattern (e.g., 'frequent_command', 'common_tags').
            description: A human-readable description of the pattern.
            data: The actual pattern data (e.g., {"command": "ls", "count": 10}).
            user_id: Optional user ID associated with the pattern.

        Returns:
            The JSON response from the backend after storing the pattern.
        """
        print(f"Storing pattern: '{pattern_type}' - '{description[:50]}...'")
        payload = {
            "pattern_type": pattern_type,
            "description": description,
            "data": data,
            "user_id": user_id if user_id else self.user_id # Use instance's user_id if not provided
        }
        try:
            response = await self._make_request('POST', '/api/pattern', payload)
            print("Pattern stored successfully.")
            return response
        except Exception as e:
            print(f"Failed to store pattern: {e}")
            raise

    async def load_pattern_data(self, query: dict = None) -> List[Dict[str, Any]]:
        """
        Loads stored patterns from the backend via the /api/pattern endpoint.

        Args:
            query: Optional dictionary to filter patterns (e.g., {"pattern_type": "frequent_command"}).

        Returns:
            A list of pattern dictionaries.
        """
        print(f"Loading patterns with query: {query}")
        endpoint = '/api/pattern'
        try:
            response = await self._make_request('GET', endpoint)
            all_patterns = response.get('data', [])

            filtered_patterns = []
            for pattern in all_patterns:
                match = True
                if query:
                    for key, value in query.items():
                        if key not in pattern or pattern.get(key) != value:
                            match = False
                            break
                if match:
                    filtered_patterns.append(pattern)

            print(f"Loaded {len(filtered_patterns)} patterns (filtered).")
            return filtered_patterns
        except Exception as e:
            print(f"Failed to load patterns: {e}")
            raise

    async def retrieve_context(self, num_recent: int = 5, query: dict = None) -> list[dict]:
        """
        Retrieves recent or context-specific memories from the backend.
        This could be a subset of load_memory or more sophisticated.

        Args:
            num_recent: Number of most recent memories to retrieve.
            query: Optional dictionary to filter memories.

        Returns:
            A list of memory dictionaries representing the context.
        """
        print(f"Retrieving context (recent: {num_recent}, query: {query})")
        # For now, this will fetch all relevant memories and filter by recent and query in Python.
        # A more advanced backend would support these filters directly in the API.
        try:
            all_memories = await self.load_memory(query=query)
            # Sort by timestamp (most recent first)
            all_memories.sort(key=lambda m: m.get('timestamp', ''), reverse=True)
            context = all_memories[:num_recent]
            print(f"Retrieved {len(context)} context memories.")
            return context
        except Exception as e:
            print(f"Failed to retrieve context: {e}")
            raise

# Example Usage (for testing the MemoryService)
async def main_test_memory_service():
    print("\n--- Testing MemoryService ---")

    # Generate a simple session ID for testing
    import uuid
    test_session_id = str(uuid.uuid4())
    test_user_id = "test_user_001"

    memory_service = MemoryService(session_id=test_session_id, user_id=test_user_id)

    # Test store_memory with string content
    try:
        mem1 = await memory_service.store_memory("User asked to create a file.", tags=["cli", "file_op"])
        print(f"Stored String Memory 1: {mem1}")
    except Exception as e:
        print(f"Failed to store string memory: {e}")

    # Test store_memory with dictionary content
    try:
        dict_content = {"task_id": "phase_0_task_1", "status": "completed"}
        # Store with the specific tag that RoadmapManager will use
        mem2 = await memory_service.store_memory(dict_content, tags=["roadmap", "task_status", "roadmap_task_status"])
        print(f"Stored Dict Memory 2: {mem2}")
    except Exception as e:
        print(f"Failed to store dict memory: {e}")


    await asyncio.sleep(1) # Give time for DB write

    # Test load_memory (all)
    try:
        all_memories = await memory_service.load_memory()
        print(f"\nAll Memories: {len(all_memories)} items")
        for m in all_memories:
            print(f"- Content: {m.get('content')}, Session: {m.get('session_id')}, User: {m.get('user_id')}, Tags: {m.get('tags')}")
    except Exception as e:
        print(f"Failed to load all memories: {e}")

    # Test load_memory with session_id filter
    try:
        session_memories = await memory_service.load_memory(query={"session_id": test_session_id})
        print(f"\nMemories for session {test_session_id}: {len(session_memories)} items")
        for m in session_memories:
            print(f"- Content: {m.get('content')}")
    except Exception as e:
        print(f"Failed to load session memories: {e}")

    # Test load_memory with tag filter (using the specific tag 'roadmap_task_status')
    try:
        # This query will now correctly match the dictionary content stored above
        roadmap_status_memories = await memory_service.load_memory(query={"tags": "roadmap_task_status"})
        print(f"\nRoadmap Status Memories: {len(roadmap_status_memories)} items")
        for m in roadmap_status_memories:
            print(f"- Parsed Content (dict): {m.get('content')}")
    except Exception as e:
        print(f"Failed to load roadmap status memories: {e}")


    # Test retrieve_context
    try:
        context_memories = await memory_service.retrieve_context(num_recent=2, query={"session_id": test_session_id})
        print(f"\nRecent context for session {test_session_id}: {len(context_memories)} items")
        for m in context_memories:
            print(f"- Content: {m.get('content')}")
    except Exception as e:
        print(f"Failed to retrieve context memories: {e}")

    # Test record_bug
    try:
        bug_report = await memory_service.record_bug(
            message="CLI sometimes freezes after 'exec' command.",
            metadata={"cli_version": "2.0.0-alpha", "os": "Windows"}
        )
        print(f"\nBug Report: {bug_report}")
    except Exception as e:
        print(f"Failed to record bug: {e}")

    # --- New tests for pattern storage/loading ---
    print("\n--- Testing Pattern Data Storage/Loading ---")
    test_pattern_data = {"command": "git commit", "count": 15}
    try:
        stored_pattern = await memory_service.store_pattern_data(
            pattern_type="frequent_git_command",
            description="User frequently commits changes.",
            data=test_pattern_data,
            user_id=test_user_id
        )
        print(f"Stored Pattern: {stored_pattern}")
    except Exception as e:
        print(f"Failed to store pattern data: {e}")

    await asyncio.sleep(1) # Give time for DB write

    try:
        loaded_patterns = await memory_service.load_pattern_data(query={"pattern_type": "frequent_git_command"})
        print(f"Loaded Patterns (filtered by type): {loaded_patterns}")
    except Exception as e:
        print(f"Failed to load pattern data: {e}")

    print("\n--- End of MemoryService Tests ---")

if __name__ == "__main__":
    # To run this example:
    # 1. Ensure your Node.js backend is running (npm start in Coddy/backend).
    # 2. Ensure `aiohttp` is installed: `pip install aiohttp`
    # 3. You can set the backend URL via environment variable:
    #    For example (PowerShell): $env:CODY_BACKEND_URL="http://localhost:3000"
    #    For example (Bash/WSL): export CODY_BACKEND_URL="http://localhost:3000"
    # 4. Run this script: `python Coddy/core/memory_service.py`
    asyncio.run(main_test_memory_service())
