# Coddy/core/roadmap_manager.py
import os
import asyncio
from typing import List, Dict, Optional, Any
import re
import sys
import json # Added for JSON handling

# Add Coddy/core to the Python path for importing memory_service and utility_functions
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

try:
    from memory_service import MemoryService
except ImportError as e:
    print(f"Error importing MemoryService: {e}")
    print("Ensure Coddy/core is in the Python path and memory_service.py exists.")
    sys.exit(1)

# Try importing utility_functions; if not available, provide a fallback
try:
    from utility_functions import read_file
except ImportError:
    print("Warning: utility_functions.py not found. Using standard file reading.")
    async def read_file(file_path: str) -> str:
        """Fallback synchronous file reader."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise
        except Exception as e:
            raise IOError(f"Error reading file '{file_path}': {e}")


# Define the root path for the Coddy project, assuming roadmap.md is at the root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ROADMAP_FILE_PATH = os.path.join(PROJECT_ROOT, 'roadmap.md')

class RoadmapManager:
    """
    Manages the project roadmap, parsing it from roadmap.md and persisting
    task statuses using MemoryService.
    """

    def __init__(self, memory_service: MemoryService, roadmap_file: str = ROADMAP_FILE_PATH):
        self.memory_service = memory_service
        self.roadmap_file = roadmap_file
        self._parsed_roadmap = None # Cache for the parsed roadmap structure
        self._task_statuses = {}    # Cache for task statuses loaded from memory

    async def _parse_roadmap_md(self) -> Dict[str, Any]:
        """
        Asynchronously parses the roadmap.md file into a structured dictionary.
        """
        roadmap_content = ""
        try:
            # Use utility_functions.read_file for consistency
            roadmap_content = await read_file(os.path.relpath(self.roadmap_file, start=PROJECT_ROOT))
        except FileNotFoundError:
            print(f"Error: Roadmap file not found at {self.roadmap_file}")
            return {}
        except Exception as e:
            print(f"Error reading roadmap.md: {e}")
            return {}

        parsed_data = {
            "phases": []
        }
        current_phase = None
        current_section = None # 'goal', 'success', 'tasks', 'evaluation'

        lines = roadmap_content.split('\n')
        for line in lines:
            line = line.strip()

            # Match Phase headings (### Phase X: Title)
            phase_match = re.match(r'###\s*Phase\s*(\d+):\s*(.*)', line)
            if phase_match:
                if current_phase:
                    parsed_data["phases"].append(current_phase)
                phase_number = int(phase_match.group(1))
                phase_title = phase_match.group(2).strip()
                current_phase = {
                    "number": phase_number,
                    "title": phase_title,
                    "goal": "",
                    "success": "",
                    "tasks": [],
                    "evaluation": {
                        "tests_created": [],
                        "my_evaluation": ""
                    }
                }
                current_section = None # Reset section for new phase
                continue

            if not current_phase:
                continue # Skip lines before the first phase

            # Match sub-sections (Goal, Success, Tasks, AI-Guided Quality & Value Evaluation)
            if line.startswith('**Goal:**'):
                current_phase["goal"] = line[len('**Goal:**'):].strip()
                current_section = 'goal'
            elif line.startswith('**Success:**'):
                current_phase["success"] = line[len('**Success:**'):].strip()
                current_section = 'success'
            elif line.startswith('**Tasks:**'):
                current_section = 'tasks'
            elif line.startswith('#### AI-Guided Quality & Value Evaluation:'):
                current_section = 'evaluation_header' # Special header for evaluation
                current_phase["evaluation"]["tests_created"] = [] # Reset for new parsing
                current_phase["evaluation"]["my_evaluation"] = ""
            elif line.startswith('* **Tests Created:**'):
                current_phase["evaluation"]["tests_created"].append(line[len('* **Tests Created:**'):].strip())
                current_section = 'evaluation_tests'
            elif line.startswith('* **My Evaluation:**'):
                current_phase["evaluation"]["my_evaluation"] = line[len('* **My Evaluation:**'):].strip()
                current_section = 'evaluation_my_eval'
            # UPDATED REGEX: To correctly match tasks which start with a space before [ ]
            # Also capture the full task description after the bracket
            task_line_match = re.match(r'^\s*\[([x ])\]\s*(.*)', line) # Capture 'x' or ' ' and the rest of the line
            if task_line_match:
                if current_section == 'tasks':
                    task_status_char = task_line_match.group(1)
                    task_status = 'completed' if task_status_char == 'x' else 'pending'
                    task_description = task_line_match.group(2).strip() # Get the full description
                    # Generate a stable ID for the task using the full description
                    task_id = f"phase_{current_phase['number']}_task_{hash(task_description) % 10000}"
                    current_phase["tasks"].append({
                        "id": task_id,
                        "description": task_description,
                        "status": task_status
                    })
                elif current_section == 'evaluation_tests':
                    # Handle multi-line test descriptions under "Tests Created"
                    # Append to the last added test description
                    if current_phase["evaluation"]["tests_created"]:
                        current_phase["evaluation"]["tests_created"][-1] += (" " + line.strip())
            else:
                # Append to current section if not a new section header
                if current_section == 'goal' and current_phase["goal"]:
                    current_phase["goal"] += (" " + line)
                elif current_section == 'success' and current_phase["success"]:
                    current_phase["success"] += (" " + line)
                elif current_section == 'evaluation_my_eval' and current_phase["evaluation"]["my_evaluation"]:
                    current_phase["evaluation"]["my_evaluation"] += (" " + line)

        if current_phase: # Add the last phase
            parsed_data["phases"].append(current_phase)

        return parsed_data

    async def _load_task_statuses(self) -> None:
        """Loads task statuses from MemoryService."""
        # Query for memories specifically tagged as 'roadmap_task_status'
        # The 'content' will be a parsed dictionary thanks to MemoryService update
        roadmap_status_memories = await self.memory_service.load_memory(query={"tags": "roadmap_task_status"})

        self._task_statuses = {}
        for mem in roadmap_status_memories:
            content = mem.get('content')
            if isinstance(content, dict) and 'task_id' in content and 'status' in content:
                self._task_statuses[content['task_id']] = content['status']
        print(f"Loaded {len(self._task_statuses)} task statuses from memory.")


    async def _save_task_status(self, task_id: str, status: str) -> dict:
        """Saves a single task status to MemoryService."""
        # Store content as a dictionary, MemoryService will JSONify it.
        return await self.memory_service.store_memory(
            content={"task_id": task_id, "status": status},
            tags=["roadmap", "task_status", "roadmap_task_status"] # Use specific tag for filtering
        )
        # No need to update _task_statuses cache here, it will be reloaded on initialize/next load


    async def initialize(self) -> None:
        """Initializes the RoadmapManager by parsing the roadmap and loading statuses."""
        self._parsed_roadmap = await self._parse_roadmap_md()
        await self._load_task_statuses()
        # Update tasks in the parsed roadmap with loaded statuses
        if self._parsed_roadmap:
            for phase in self._parsed_roadmap.get("phases", []):
                for task in phase.get("tasks", []):
                    if task['id'] in self._task_statuses:
                        task['status'] = self._task_statuses[task['id']]
                        # print(f"Initialized task '{task['id']}' with status '{task['status']}' from memory.")
        print("RoadmapManager initialized.")

    def get_roadmap(self) -> Optional[Dict[str, Any]]:
        """Returns the current parsed roadmap with updated statuses."""
        return self._parsed_roadmap

    async def update_task_status(self, phase_number: int, task_description_snippet: str, new_status: str) -> bool:
        """
        Updates the status of a specific task in the roadmap and persists it.

        Args:
            phase_number: The number of the phase the task belongs to.
            task_description_snippet: A part of the task's description (for fuzzy matching).
            new_status: The new status ('pending', 'completed').

        Returns:
            True if the task was found and updated, False otherwise.
        """
        if not self._parsed_roadmap:
            await self.initialize() # Ensure roadmap is loaded

        found_and_updated = False
        for phase in self._parsed_roadmap.get("phases", []):
            if phase.get("number") == phase_number:
                for task in phase.get("tasks", []):
                    # Use a robust check for description snippet
                    if task_description_snippet.lower() in task['description'].lower():
                        if task['status'] != new_status: # Only update if status changed
                            task['status'] = new_status
                            await self._save_task_status(task['id'], new_status)
                            # After saving, reload statuses to ensure _task_statuses is up-to-date
                            await self._load_task_statuses()
                            print(f"Updated status of '{task['description']}' in Phase {phase_number} to '{new_status}'.")
                        else:
                            print(f"Task '{task['description']}' in Phase {phase_number} already has status '{new_status}'. No update needed.")
                        found_and_updated = True
                        break # Found task, break from inner loop
            if found_and_updated:
                break # Break from outer loop if task found and updated

        if not found_and_updated:
            print(f"Task matching '{task_description_snippet}' not found in Phase {phase_number}.")
        return found_and_updated

    async def get_current_tasks(self, status: Optional[str] = None, phase_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieves a list of tasks, optionally filtered by status and phase number.
        """
        if not self._parsed_roadmap:
            await self.initialize()

        current_tasks = []
        for phase in self._parsed_roadmap.get("phases", []):
            if phase_number is None or phase.get("number") == phase_number:
                for task in phase.get("tasks", []):
                    if status is None or task['status'] == status:
                        current_tasks.append({
                            "phase_number": phase.get("number"),
                            "phase_title": phase.get("title"),
                            "description": task['description'],
                            "status": task['status']
                        })
        return current_tasks

# Example Usage (for testing the RoadmapManager)
async def main_test_roadmap_manager():
    print("\n--- Testing RoadmapManager ---")

    # Assuming MemoryService and backend are running
    import uuid
    test_session_id = str(uuid.uuid4())
    test_user_id = "test_user_roadmap"
    memory_service = MemoryService(session_id=test_session_id, user_id=test_user_id)

    # Initialize RoadmapManager
    roadmap_manager = RoadmapManager(memory_service)
    await roadmap_manager.initialize()

    # Get and print the full roadmap
    full_roadmap = roadmap_manager.get_roadmap()
    if full_roadmap:
        print("\nParsed Roadmap Structure (Initial State):")
        for phase in full_roadmap["phases"]:
            print(f"Phase {phase['number']}: {phase['title']}")
            for task in phase['tasks']:
                print(f"  - [{'X' if task['status'] == 'completed' else ' '}] {task['description']} (ID: {task['id']}, Status: {task['status']})")
    else:
        print("Failed to parse roadmap.")
        return

    # Test updating a task status
    print("\n--- Updating a Task ---")
    # Let's find a task to update, e.g., the first task in Phase 0
    # Make sure to pick a snippet that uniquely identifies a task in Phase 0
    task_description_snippet = "Define Coddy’s Philosophy and Vision"
    if full_roadmap and full_roadmap["phases"]:
        # Find Phase 0
        phase_0 = next((p for p in full_roadmap["phases"] if p["number"] == 0), None)
        if phase_0 and phase_0["tasks"]:
            success = await roadmap_manager.update_task_status(0, task_description_snippet, "completed")
            print(f"Attempted to update '{task_description_snippet}': {success}")
        else:
            print("No tasks found in Phase 0 to update.")
    else:
        print("Roadmap not found or empty.")


    # Test updating another task in a different phase (e.g., Phase 1, first task)
    print("\n--- Updating another Task (Phase 1) ---")
    task_description_snippet_phase1 = "Spin up Express server + MongoDB integration"
    success_phase1 = await roadmap_manager.update_task_status(1, task_description_snippet_phase1, "completed")
    print(f"Attempted to update '{task_description_snippet_phase1}' in Phase 1: {success_phase1}")


    # Re-initialize RoadmapManager to check if statuses persist from memory
    print("\n--- Re-initializing RoadmapManager to check persistence ---")
    new_roadmap_manager = RoadmapManager(memory_service)
    await new_roadmap_manager.initialize()
    updated_roadmap = new_roadmap_manager.get_roadmap()
    if updated_roadmap:
        print("\nUpdated Roadmap Structure (after re-init):")
        for phase in updated_roadmap["phases"]:
            if phase.get("number") == 0 or phase.get("number") == 1: # Check Phase 0 and 1
                print(f"Phase {phase['number']}: {phase['title']}")
                for task in phase['tasks']:
                    if task_description_snippet.lower() in task['description'].lower() or \
                       task_description_snippet_phase1.lower() in task['description'].lower():
                        print(f"  - [{'X' if task['status'] == 'completed' else ' '}] {task['description']} (ID: {task['id']}, Status: {task['status']})")
    else:
        print("Failed to parse roadmap after re-init.")


    # Test retrieving current tasks
    print("\n--- Current Tasks (All) ---")
    all_current_tasks = await roadmap_manager.get_current_tasks()
    for task in all_current_tasks:
        print(f"Phase {task['phase_number']} - {task['description']} [{task['status']}]")

    print("\n--- Current Tasks (Pending) ---")
    pending_tasks = await roadmap_manager.get_current_tasks(status="pending")
    for task in pending_tasks:
        print(f"Phase {task['phase_number']} - {task['description']} [{task['status']}]")

    print("\n--- Current Tasks (Completed) ---")
    completed_tasks = await roadmap_manager.get_current_tasks(status="completed")
    for task in completed_tasks:
        print(f"Phase {task['phase_number']} - {task['description']} [{task['status']}]")

    print("\n--- End of RoadmapManager Tests ---")

if __name__ == "__main__":
    # To run this example:
    # 1. Ensure your Node.js backend is running (npm start in Coddy/backend).
    # 2. Ensure `aiohttp` is installed: `pip install aiohttp`
    # 3. Ensure `memory_service.py` is in Coddy/core.
    # 4. Ensure `roadmap.md` is in your Coddy project root.
    # 5. Run this script: `python Coddy/core/roadmap_manager.py`
    asyncio.run(main_test_roadmap_manager())
