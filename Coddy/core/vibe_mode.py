# Coddy/core/vibe_mode.py
import asyncio
import sys
import os
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

# Add Coddy/core to the Python path for importing MemoryService
# Corrected import path for VibeFileManager from the 'vibe' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.'))) # For MemoryService, etc.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # Add Coddy root to path to import 'vibe' package


try:
    from memory_service import MemoryService
    from utility_functions import list_files # To track open files/directory changes
    from vibe.vibe_file_manager import VibeFileManager # Corrected import from 'vibe' package
except ImportError as e:
    print(f"Error importing core modules for VibeModeEngine: {e}")
    print("Please ensure 'memory_service.py', 'utility_functions.py' (in core), and 'vibe/vibe_file_manager.py' exist and are correctly configured.")
    sys.exit(1)

class VibeModeEngine:
    """
    Tracks the user's current "vibe" or focus, including recent commands,
    actively viewed files/directories, and can suggest next tasks based on context.
    Integrates with MemoryService for persistence and VibeFileManager for local snapshots.
    """
    # A simple definition of "active focus"
    FOCUS_WINDOW_SECONDS = 300 # 5 minutes

    def __init__(self, memory_service: MemoryService, user_id: str = "default_user"):
        """
        Initializes the VibeModeEngine.

        Args:
            memory_service: An instance of MemoryService for data persistence.
            user_id: The ID of the current user.
        """
        self.memory_service = memory_service
        self.user_id = user_id
        # Initialize VibeFileManager. Its vibe_dir is set internally in VibeFileManager now.
        self.vibe_file_manager = VibeFileManager() 
        self._current_focus: Optional[str] = None # E.g., 'coding', 'planning', 'debugging'
        self._last_activity_timestamp: Optional[datetime] = None
        self._last_commands: List[Dict[str, Any]] = [] # Recent commands logged by CLI
        self._tracked_files: Dict[str, datetime] = {} # {file_path: last_accessed_time}
        self._current_directory: str = os.getcwd() # Track current working directory

        # Internal state to hold the 'vibe' data for persistence
        self._vibe_data: Dict[str, Any] = {
            "current_focus": None,
            "last_activity": None,
            "last_commands": [],
            "tracked_files": {},
            "current_directory": os.getcwd()
        }
        print("VibeModeEngine initialized.")

    async def initialize(self):
        """Loads previous vibe state from memory if available."""
        print("VibeModeEngine: Loading previous vibe state from MongoDB...")
        try:
            vibe_memories = await self.memory_service.load_memory(
                query={"tags": "vibe_state", "user_id": self.user_id}
            )
            if vibe_memories:
                # Get the most recent vibe state
                vibe_memories.sort(key=lambda m: m.get('timestamp', ''), reverse=True)
                latest_vibe = vibe_memories[0].get('content')
                
                if isinstance(latest_vibe, dict):
                    self._vibe_data = latest_vibe
                    self._current_focus = self._vibe_data.get("current_focus")
                    self._last_activity_timestamp = datetime.fromisoformat(self._vibe_data["last_activity"]) if self._vibe_data.get("last_activity") else None
                    # Ensure recent_commands' timestamps are converted back
                    self._last_commands = [
                        {"command": cmd["command"], "timestamp": datetime.fromisoformat(cmd["timestamp"])}
                        for cmd in self._vibe_data.get("last_commands", [])
                    ] if self._vibe_data.get("last_commands") else []
                    
                    # Convert tracked_files timestamps back from string to datetime objects
                    self._tracked_files = {
                        f: datetime.fromisoformat(ts) for f, ts in self._vibe_data.get("tracked_files", {}).items()
                    }
                    self._current_directory = self._vibe_data.get("current_directory", os.getcwd())
                    print("VibeModeEngine: Previous vibe state loaded from MongoDB.")
                else:
                    print("VibeModeEngine: Found vibe memory in MongoDB but content was not a dict.")
            else:
                print("VibeModeEngine: No previous vibe state found in MongoDB.")
        except Exception as e:
            print(f"VibeModeEngine: Error loading vibe state from MongoDB: {e}")

    async def _persist_vibe_state(self):
        """Persists the current vibe state to MemoryService (MongoDB)."""
        # Convert datetime objects in _tracked_files to ISO 8601 strings for JSON serialization
        serializable_tracked_files = {
            f: ts.isoformat() for f, ts in self._tracked_files.items()
        }
        # Convert datetime objects in _last_commands to ISO 8601 strings
        serializable_last_commands = [
            {"command": cmd["command"], "timestamp": cmd["timestamp"].isoformat() if isinstance(cmd["timestamp"], datetime) else cmd["timestamp"]}
            for cmd in self._last_commands
        ]


        self._vibe_data = {
            "current_focus": self._current_focus,
            "last_activity": self._last_activity_timestamp.isoformat() if self._last_activity_timestamp else None,
            "last_commands": serializable_last_commands,
            "tracked_files": serializable_tracked_files, # Use serializable version
            "current_directory": self._current_directory
        }
        try:
            await self.memory_service.store_memory(
                content=self._vibe_data,
                tags=["vibe_state", "user_context"],
                # user_id and session_id already handled by MemoryService instance
            )
            print("VibeModeEngine: Vibe state persisted to MongoDB.")
        except Exception as e:
            print(f"VibeModeEngine: Failed to persist vibe state to MongoDB: {e}")

    async def update_activity(self, command: str, file_path: Optional[str] = None):
        """
        Updates the vibe engine with recent user activity (command execution, file access).
        """
        self._last_activity_timestamp = datetime.now()
        
        # Add command to recent commands (keep a limited history)
        if len(self._last_commands) >= 5: # Keep last 5 commands
            self._last_commands.pop(0)
        self._last_commands.append({"command": command, "timestamp": self._last_activity_timestamp}) # Store datetime object

        # Track accessed files
        if file_path:
            self._tracked_files[file_path] = self._last_activity_timestamp
            # Clean up old tracked files if too many or too old
            self._tracked_files = {
                f: ts for f, ts in self._tracked_files.items()
                if datetime.now() - ts < timedelta(hours=1) # Keep files active for 1 hour
            }
        
        # Check current directory
        new_cwd = os.getcwd()
        if new_cwd != self._current_directory:
            self._current_directory = new_cwd
            print(f"VibeModeEngine: Current directory changed to {self._current_directory}")

        print(f"VibeModeEngine: Activity updated. Last command: '{command[:50]}...'")
        await self._persist_vibe_state()

    def get_current_vibe(self) -> Dict[str, Any]:
        """
        Returns a summary of the current user's vibe/focus.
        This data is prepared to be JSON serializable for storage or display.
        """
        is_active = False
        if self._last_activity_timestamp:
            time_since_last_activity = datetime.now() - self._last_activity_timestamp
            if time_since_last_activity.total_seconds() < self.FOCUS_WINDOW_SECONDS:
                is_active = True

        # Ensure datetime objects are converted to string for external consumption/return value
        serializable_recent_commands = [
            {"command": cmd_data["command"], "timestamp": cmd_data["timestamp"].isoformat() if isinstance(cmd_data["timestamp"], datetime) else cmd_data["timestamp"]}
            for cmd_data in self._last_commands
        ]
        serializable_tracked_files = {
            f: ts.isoformat() if isinstance(ts, datetime) else ts for f, ts in self._tracked_files.items()
        }


        return {
            "is_active": is_active,
            "current_focus": self._current_focus,
            "last_activity_at": self._last_activity_timestamp.isoformat() if self._last_activity_timestamp else None,
            "recent_commands": serializable_recent_commands,
            "tracked_files": serializable_tracked_files, # Return as dict for consistency
            "current_directory": self._current_directory
        }

    async def set_focus(self, focus_area: str):
        """Manually sets the current focus area."""
        self._current_focus = focus_area
        self._last_activity_timestamp = datetime.now() # Setting focus is also an activity
        print(f"VibeModeEngine: Focus set to '{focus_area}'.")
        await self._persist_vibe_state()

    async def suggest_next_task(self, roadmap_manager: Any) -> Optional[Dict[str, Any]]:
        """
        Suggests a next task based on current vibe, recent activities, and roadmap.
        (Requires RoadmapManager integration for real suggestions)
        """
        print("VibeModeEngine: Suggesting next task...")
        # For simplicity, suggest the next pending task from Phase 2
        # In a real scenario, this would use PatternOracle, file context, LLM, etc.
        try:
            # We need the actual roadmap_manager instance passed correctly, not just a mock
            # If roadmap_manager is not initialized (e.g. from cli), it might fail.
            pending_tasks = await roadmap_manager.get_current_tasks(status="pending", phase_number=2)
            if pending_tasks:
                # Find the very first pending task in Phase 2 for a simple suggestion
                # Sort by phase number and then by their original order in the roadmap
                pending_tasks.sort(key=lambda t: (t['phase_number'], t.get('order_in_phase', 0))) # Assuming 'order_in_phase' can be added in roadmap_manager if needed
                first_pending_task = pending_tasks[0] # Simply take the first one after sorting

                return {
                    "suggestion": f"Consider working on: '{first_pending_task['description']}' (Phase {first_pending_task['phase_number']})",
                    "task_details": first_pending_task
                }
            else:
                return {"suggestion": "All known tasks are complete or no pending tasks found in Phase 2. What's next?"}
        except Exception as e:
            print(f"VibeModeEngine: Error suggesting task: {e}")
            return {"suggestion": f"Unable to suggest a task due to an error: {e}"}

    async def save_vibe_to_file(self, snapshot_name: str, current_todos: Optional[List[str]] = None) -> bool:
        """
        Saves the current detailed vibe state (including context and TODOs) to a local .vibe file.

        Args:
            snapshot_name: The name for the local snapshot file.
            current_todos: A list of current TODOs to include in the snapshot.

        Returns:
            True if the snapshot was saved successfully, False otherwise.
        """
        print(f"VibeModeEngine: Saving vibe state to local file '{snapshot_name}.vibe'...")
        vibe_data_to_save = self.get_current_vibe() # Get the serializable vibe state
        vibe_data_to_save["todos"] = current_todos if current_todos is not None else []
        
        success = await self.vibe_file_manager.save_vibe_snapshot(snapshot_name, vibe_data_to_save)
        if success:
            print(f"VibeModeEngine: Local vibe snapshot '{snapshot_name}.vibe' saved.")
        else:
            print(f"VibeModeEngine: Failed to save local vibe snapshot '{snapshot_name}'.")
        return success

    async def load_vibe_from_file(self, snapshot_name: str) -> bool:
        """
        Loads a vibe state from a local .vibe file and applies it to the engine,
        also persisting the loaded state to MongoDB.

        Args:
            snapshot_name: The name of the local snapshot file to load.

        Returns:
            True if the snapshot was loaded and applied successfully, False otherwise.
        """
        print(f"VibeModeEngine: Loading vibe state from local file '{snapshot_name}.vibe'...")
        loaded_vibe_data = await self.vibe_file_manager.load_vibe_snapshot(snapshot_name)
        if loaded_vibe_data:
            # Apply loaded data to internal state
            self._current_focus = loaded_vibe_data.get("current_focus")
            self._last_activity_timestamp = datetime.fromisoformat(loaded_vibe_data["last_activity_at"]) if loaded_vibe_data.get("last_activity_at") else None
            # Convert timestamps back for recent_commands
            self._last_commands = [
                {"command": cmd["command"], "timestamp": datetime.fromisoformat(cmd["timestamp"])}
                for cmd in loaded_vibe_data.get("recent_commands", [])
            ] if loaded_vibe_data.get("recent_commands") else []

            # Convert tracked_files back (keys are already str, values need datetime conversion)
            self._tracked_files = {
                f: datetime.fromisoformat(ts) for f, ts in loaded_vibe_data.get("tracked_files", {}).items()
            } if loaded_vibe_data.get("tracked_files") else {}
            
            self._current_directory = loaded_vibe_data.get("current_directory", os.getcwd())
            self._vibe_data = loaded_vibe_data # Update internal _vibe_data cache

            print(f"VibeModeEngine: Vibe state loaded from '{snapshot_name}.vibe'. Persisting to MongoDB...")
            # Also persist this newly loaded state to MongoDB to keep it in long-term memory
            await self._persist_vibe_state()
            print("VibeModeEngine: Loaded vibe state also persisted to MongoDB.")
            return True
        else:
            print(f"VibeModeEngine: Failed to load vibe snapshot '{snapshot_name}.vibe'.")
            return False

    async def list_local_vibe_snapshots(self) -> List[str]:
        """
        Lists available local .vibe snapshots.

        Returns:
            A list of snapshot names.
        """
        return await self.vibe_file_manager.list_vibe_snapshots()


# --- Test Integration ---
async def main_test_vibe_mode_engine():
    print("\n--- Testing VibeModeEngine with VibeFileManager Integration ---")

    import uuid
    test_session_id = str(uuid.uuid4())
    test_user_id = "vibe_test_user_002" # Using a new user ID for this test

    memory_service = MemoryService(session_id=test_session_id, user_id=test_user_id)
    vibe_engine = VibeModeEngine(memory_service, user_id=test_user_id)

    # Initialize VibeModeEngine (load past state)
    await vibe_engine.initialize()

    # Test initial vibe
    current_vibe = vibe_engine.get_current_vibe()
    print(f"\nInitial Vibe: {current_vibe}")

    # Simulate some activity
    print("\n--- Simulating Activity ---")
    await vibe_engine.update_activity("exec git status", file_path=os.path.join(os.getcwd(), "README.md"))
    await asyncio.sleep(1)
    await vibe_engine.update_activity("write new_feature.py initial code", file_path=os.path.join(os.getcwd(), "new_feature.py"))
    await asyncio.sleep(1) # Simulate a short delay
    await vibe_engine.set_focus("refactoring-utils")
    await asyncio.sleep(1) # Simulate a short delay
    await vibe_engine.update_activity("exec npm install", file_path=None)

    current_vibe = vibe_engine.get_current_vibe()
    print(f"\nVibe after activities: {current_vibe}")

    # --- Test saving to .vibe file ---
    print("\n--- Test Saving Vibe to Local File ---")
    todos = ["Finish Phase 4 tasks", "Review UI feedback"]
    save_success = await vibe_engine.save_vibe_to_file("my_coding_flow", current_todos=todos)
    print(f"Save to file success: {save_success}")

    # --- Test listing local snapshots ---
    print("\n--- Test Listing Local Snapshots ---")
    local_snapshots = await vibe_engine.list_local_vibe_snapshots()
    print(f"Available Snapshots: {local_snapshots}")
    assert "my_coding_flow" in local_snapshots
    print("Local snapshot listing test passed.")

    # --- Test loading from .vibe file (simulate restart by creating new VibeModeEngine) ---
    print("\n--- Test Loading Vibe from Local File ---")
    
    new_vibe_engine_for_load = VibeModeEngine(memory_service, user_id=test_user_id)
    await new_vibe_engine_for_load.initialize() 
    print(f"\nBefore loading from file, new engine vibe: {new_vibe_engine_for_load.get_current_vibe()}")

    load_success = await new_vibe_engine_for_load.load_vibe_from_file("my_coding_flow")
    print(f"Load from file success: {load_success}")
    if load_success:
        loaded_vibe = new_vibe_engine_for_load.get_current_vibe()
        print(f"\nVibe after loading from file: {loaded_vibe}")
        # Assertions to verify content
        assert loaded_vibe.get("current_focus") == "refactoring-utils"
        assert "Finish Phase 4 tasks" in loaded_vibe.get("todos", [])
        assert any("exec git status" in cmd['command'] for cmd in loaded_vibe.get("recent_commands", []))
        print("Load from file test passed.")
    else:
        print("Load from file test failed.")

    # --- Clean up test files (optional, but good for isolated testing) ---
    vibe_file_manager_for_cleanup = VibeFileManager(vibe_dir=vibe_engine.vibe_file_manager.VIBE_DATA_DIR) # Use VIBE_DATA_DIR
    snapshots_to_remove = await vibe_file_manager_for_cleanup.list_vibe_snapshots()
    for s_name in snapshots_to_remove:
        file_path = os.path.join(vibe_file_manager_for_cleanup.VIBE_DATA_DIR, f"{s_name}.vibe")
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Cleaned up local .vibe file: {file_path}")

    print("\n--- End of VibeModeEngine with VibeFileManager Integration Tests ---")

if __name__ == "__main__":
    # To run this example:
    # 1. Ensure your Node.js backend is running (npm start in Coddy/backend).
    # 2. Ensure `aiohttp` is installed: `pip install aiohttp`.
    # 3. Ensure `memory_service.py`, `utility_functions.py` in Coddy/core.
    # 4. Ensure `vibe_file_manager.py` in Coddy/vibe (now a package).
    # 5. Run this script: `python Coddy/core/vibe_mode.py`
    asyncio.run(main_test_vibe_mode_engine())
