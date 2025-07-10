# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\pattern_oracle.py

import asyncio
import sys
import os
from collections import Counter
from typing import List, Dict, Any, Optional

# Add Coddy/core to the Python path for importing memory_service
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

try:
    from memory_service import MemoryService
except ImportError as e:
    print(f"Error importing MemoryService: {e}")
    print("Ensure Coddy/core is in the Python path and memory_service.py exists.")
    sys.exit(1)

# Define the base URL for the backend API, same as MemoryService
BACKEND_BASE_URL = os.environ.get('CODY_BACKEND_URL', 'http://localhost:3000')


class PatternOracle:
    """
    Analyzes session logs (memories) for recurring patterns and habits.
    Leverages MemoryService for data retrieval and pattern storage.
    """

    def __init__(self, memory_service: MemoryService):
        """
        Initializes the PatternOracle.

        Args:
            memory_service: An instance of MemoryService to retrieve and store data.
        """
        self.memory_service = memory_service

    async def _store_pattern(self, pattern_type: str, description: str, data: Any, user_id: Optional[str] = None) -> dict:
        """
        Stores a detected pattern in the backend via the /api/pattern endpoint
        using the MemoryService.

        Args:
            pattern_type: The type of pattern (e.g., 'frequent_command', 'common_tags').
            description: A human-readable description of the pattern.
            data: The actual pattern data (e.g., {"command": "ls", "count": 10}).
            user_id: Optional user ID associated with the pattern.

        Returns:
            The JSON response from the backend after storing the pattern.
        """
        print(f"--- PatternOracle: Attempting to store pattern: {pattern_type} ---")
        print(f"  Description: {description}")
        print(f"  Data: {data}")
        try:
            response = await self.memory_service.store_pattern_data(
                pattern_type=pattern_type,
                description=description,
                data=data,
                user_id=user_id # Pass user_id to store_pattern_data
            )
            return response
        except Exception as e:
            print(f"Failed to store pattern via MemoryService: {e}")
            raise


    async def analyze_command_frequency(self, num_top_commands: int = 5, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Analyzes memory logs to find the most frequently used commands.

        Args:
            num_top_commands: The number of top commands to return.
            user_id: Optional user ID to filter memories for analysis.

        Returns:
            A list of dictionaries, each containing 'command' and 'count'.
        """
        print(f"Analyzing command frequency (top {num_top_commands})...")
        query = {"tags": "cli_command"}
        if user_id:
            query["user_id"] = user_id
        all_memories = await self.memory_service.load_memory(query=query)

        command_phrases = []
        for mem in all_memories:
            content = mem.get('content')
            if isinstance(content, str):
                content_lower = content.lower()
                if content_lower.startswith("exec "):
                    command_phrases.append(content_lower[5:].strip().split(' ')[0]) # Get the first word of the command
                elif content_lower.startswith("read ") or content_lower.startswith("write ") or content_lower.startswith("list "):
                    command_phrases.append(content_lower.split(' ')[0]) # Get the command itself (read, write, list)

        if not command_phrases:
            print("No command memories found for analysis.")
            return []

        command_counts = Counter(command_phrases)
        top_commands = command_counts.most_common(num_top_commands)

        patterns = []
        for cmd, count in top_commands:
            pattern_data = {"command": cmd, "count": count}
            description = f"Frequently used command: '{cmd}' ({count} times)"
            patterns.append(pattern_data)
            # Pass user_id to _store_pattern
            await self._store_pattern("frequent_command", description, pattern_data, user_id if user_id else self.memory_service.user_id)

        print(f"Found {len(patterns)} frequent command patterns.")
        return patterns

    async def analyze_tag_co_occurrence(self, min_co_occurrence: int = 2, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Analyzes memory tags to find frequently co-occurring tags.

        Args:
            min_co_occurrence: Minimum number of times tags must appear together to be considered.
            user_id: Optional user ID to filter memories for analysis.

        Returns:
            A list of dictionaries, each containing 'tags' (a sorted tuple of co-occurring tags) and 'count'.
        """
        print(f"Analyzing tag co-occurrence (min_co_occurrence: {min_co_occurrence})...")
        query = {}
        if user_id:
            query["user_id"] = user_id
        all_memories = await self.memory_service.load_memory(query=query) # Fetch all memories (optionally filtered by user_id)

        tag_pairs_counter = Counter()
        for mem in all_memories:
            tags = mem.get('tags', [])
            if len(tags) >= 2:
                # Generate all unique pairs of tags
                for i in range(len(tags)):
                    for j in range(i + 1, len(tags)):
                        pair = tuple(sorted((tags[i], tags[j])))
                        tag_pairs_counter[pair] += 1

        co_occurring_patterns = []
        for pair, count in tag_pairs_counter.items():
            if count >= min_co_occurrence:
                pattern_data = {"tags": list(pair), "count": count}
                description = f"Tags '{pair[0]}' and '{pair[1]}' frequently co-occur ({count} times)"
                co_occurring_patterns.append(pattern_data)
                # Pass user_id to _store_pattern
                await self._store_pattern("co_occurring_tags", description, pattern_data, user_id if user_id else self.memory_service.user_id)

        print(f"Found {len(co_occurring_patterns)} co-occurring tag patterns.")
        return co_occurring_patterns

    async def get_all_patterns(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Retrieves all previously stored patterns from MemoryService.

        Args:
            user_id: Optional user ID to filter patterns by.

        Returns:
            A list of pattern dictionaries.
        """
        print(f"Retrieving all patterns for user: {user_id if user_id else 'all'}...")
        query = {}
        if user_id:
            query["user_id"] = user_id
        all_stored_patterns = await self.memory_service.load_pattern_data(query=query)
        print(f"Retrieved {len(all_stored_patterns)} patterns.")
        return all_stored_patterns

# Example Usage (for testing the PatternOracle)
async def main_test_pattern_oracle():
    print("\n--- Testing PatternOracle ---")

    import uuid
    test_session_id = str(uuid.uuid4())
    test_user_id = "oracle_test_user_001" # Using a distinct user_id for this test run

    # Initialize MemoryService with user_id
    memory_service = MemoryService(session_id=test_session_id, user_id=test_user_id)
    pattern_oracle = PatternOracle(memory_service)

    # --- Populate some test memories ---
    print(f"\nPopulating test memories for analysis (User: {test_user_id})...")
    # Removed user_id argument as it's passed via MemoryService constructor
    await memory_service.store_memory("exec ls -l", tags=["cli_command", "file_op"])
    await memory_service.store_memory("read config.json", tags=["cli_command", "config"])
    await memory_service.store_memory("exec npm install", tags=["cli_command", "project_setup"])
    await memory_service.store_memory("exec ls -a", tags=["cli_command", "file_op"])
    await memory_service.store_memory("write temp.txt Hello world", tags=["cli_command", "file_op", "draft"])
    await memory_service.store_memory("read data.csv", tags=["cli_command", "data_analysis"])
    await memory_service.store_memory("Bug: broken file saving", tags=["bug_report", "file_op"])
    await asyncio.sleep(1) # Give time for DB writes

    # --- Test analyze_command_frequency ---
    print("\n--- Analyzing Command Frequency ---")
    frequent_commands = await pattern_oracle.analyze_command_frequency(num_top_commands=3, user_id=test_user_id)
    if frequent_commands:
        print("Top 3 Frequent Commands:")
        for cmd_pattern in frequent_commands:
            print(f"- Command: '{cmd_pattern['command']}', Count: {cmd_pattern['count']}")
    else:
        print("No frequent commands found.")

    # --- Test analyze_tag_co_occurrence ---
    print("\n--- Analyzing Tag Co-occurrence ---")
    co_occurring_tags = await pattern_oracle.analyze_tag_co_occurrence(min_co_occurrence=2, user_id=test_user_id)
    if co_occurring_tags:
        print("Co-occurring Tags:")
        for tag_pattern in co_occurring_tags:
            print(f"- Tags: {tag_pattern['tags']}, Count: {tag_pattern['count']}")
    else:
        print("No co-occurring tags found.")

    # --- Test get_all_patterns (now pulls from backend) ---
    print("\n--- Retrieving All Patterns (from Backend) ---")
    all_stored_patterns = await pattern_oracle.get_all_patterns(user_id=test_user_id)
    if all_stored_patterns:
        print("All Stored Patterns:")
        for pattern in all_stored_patterns:
            print(f"- Type: {pattern.get('pattern_type')}, Desc: {pattern.get('description')}, Data: {pattern.get('data')}")
    else:
        print("No patterns retrieved.")

    print("\n--- End of PatternOracle Tests ---")

if __name__ == "__main__":
    # To run this example:
    # 1. Ensure your Node.js backend is running (npm start in Coddy/backend).
    # 2. Ensure `aiohttp` is installed: `pip install aiohttp`
    # 3. Ensure `memory_service.py` is in Coddy/core.
    # 4. Run this script: `python Coddy/core/pattern_oracle.py`
    asyncio.run(main_test_pattern_oracle())
