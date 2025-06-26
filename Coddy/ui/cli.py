# Coddy/ui/cli.py
import asyncio
import sys
import os
import uuid # For generating session_id
import datetime # For timestamps (though MemoryService handles this)
from typing import Optional, List, Dict, Any # Added for type hints

# Corrected sys.path.insert for importing modules from Coddy/core and Coddy/vibe
# Add Coddy/core to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core')))
# Add Coddy root to the Python path to correctly import the 'vibe' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


try:
    from utility_functions import read_file, write_file, list_files, execute_command
    from memory_service import MemoryService
    from pattern_oracle import PatternOracle
    from websocket_server import send_to_websocket_server # Import WebSocket sender
    from vibe_mode import VibeModeEngine # Import VibeModeEngine from core
except ImportError as e:
    print(f"Error importing core modules: {e}")
    print("Please ensure all required Python modules exist and are correctly configured in Coddy/core/ and Coddy/vibe/.")
    sys.exit(1)

# Global instances for services
memory_service: Optional[MemoryService] = None
pattern_oracle: Optional[PatternOracle] = None
vibe_engine: Optional[VibeModeEngine] = None # Global instance for VibeModeEngine

current_user_id: str = "default_user" # Placeholder, will be replaced by actual user management
current_session_id: str = str(uuid.uuid4()) # Unique ID for each CLI session
adaptive_prompt_suggestion: str = "" # Stores dynamic prompt suggestions
session_context_memories: List[Dict[str, Any]] = [] # Stores loaded context for the current user

async def initialize_services():
    """Initializes global MemoryService, PatternOracle, and VibeModeEngine instances."""
    global memory_service, pattern_oracle, vibe_engine
    print("Initializing Coddy services...")
    
    memory_service = MemoryService(session_id=current_session_id, user_id=current_user_id)
    pattern_oracle = PatternOracle(memory_service)
    vibe_engine = VibeModeEngine(memory_service, user_id=current_user_id) # Pass memory_service to VibeModeEngine
    await vibe_engine.initialize() # Initialize VibeModeEngine to load its state

    print("Services initialized.")

async def log_and_stream_message(type: str, text: str, command_type: Optional[str] = None, raw_instruction: Optional[str] = None):
    """
    Logs messages to MemoryService (if it's a command) and streams all messages
    to the WebSocket server for real-time UI updates.
    """
    # Log to MemoryService if it's a command
    if command_type and raw_instruction:
        if memory_service:
            content = raw_instruction
            tags = ["cli_command", command_type]
            await memory_service.store_memory(content=content, tags=tags)
            # Also update VibeModeEngine with activity (only for core CLI commands)
            if vibe_engine and command_type in ["read", "write", "list", "exec"]:
                await vibe_engine.update_activity(raw_instruction)
        else:
            print("Warning: MemoryService not initialized, command not logged.")

    # Stream to WebSocket
    message_data = {
        "type": type,
        "text": text,
        "timestamp": datetime.datetime.now().isoformat(),
        "session_id": current_session_id,
        "user_id": current_user_id
    }
    await send_to_websocket_server(message_data)


async def update_adaptive_prompt_suggestion():
    """Analyzes command frequency and updates the adaptive prompt suggestion."""
    global adaptive_prompt_suggestion
    if pattern_oracle:
        try:
            # Analyze command frequency for the current user
            frequent_commands = await pattern_oracle.analyze_command_frequency(
                num_top_commands=1, user_id=current_user_id
            )
            if frequent_commands:
                most_frequent_cmd = frequent_commands[0]['command']
                # Avoid suggesting the current command being typed or generic ones
                if most_frequent_cmd not in ["read", "write", "list", "exec", "checkpoint", "show", "vibe"]:
                     adaptive_prompt_suggestion = f" (Try '{most_frequent_cmd}'?)"
                else:
                    adaptive_prompt_suggestion = ""
            else:
                adaptive_prompt_suggestion = ""
        except Exception as e:
            # Log error to WebSocket if possible
            await log_and_stream_message("error", f"Error updating adaptive prompt suggestion: {e}")
            adaptive_prompt_suggestion = ""
    else:
        adaptive_prompt_suggestion = ""

async def load_session_context():
    """
    Loads and displays past context for the current user, across all sessions.
    This provides a broader, more persistent "context" for the user.
    """
    global session_context_memories
    if memory_service:
        await log_and_stream_message("info", "Loading past context for user...")
        try:
            # Retrieve recent memories for the current user, NOT limited by current session_id
            session_context_memories = await memory_service.retrieve_context(
                num_recent=10, # Load up to 10 recent memories as context
                query={"user_id": current_user_id} # Only filter by user_id for persistent context
            )
            if session_context_memories:
                await log_and_stream_message("info", f"Loaded {len(session_context_memories)} recent memories for user '{current_user_id}'.")
            else:
                await log_and_stream_message("info", f"No past context found for user '{current_user_id}'.")
        except Exception as e:
            await log_and_stream_message("error", f"Error loading user context: {e}")
    else:
        await log_and_stream_message("warning", "MemoryService not initialized, cannot load context.")

async def handle_instruction(instruction: str):
    """
    Parses a user instruction and attempts to execute a corresponding action.
    """
    instruction = instruction.strip()
    if not instruction:
        return

    # User input commands are echoed first to the UI
    await log_and_stream_message("command", f"Coddy> {instruction}")

    command_logged = False
    command_lower = instruction.lower()

    if command_lower.startswith("read "):
        file_path = instruction[5:].strip()
        try:
            content = await read_file(file_path)
            await log_and_stream_message("response", f"Content of '{file_path}':\n---\n{content}\n---")
            await log_and_stream_message("info", f"Successfully read '{file_path}'.")
            await log_and_stream_message("status", f"Read '{file_path}'.", "read", instruction)
            command_logged = True
        except FileNotFoundError:
            await log_and_stream_message("error", f"Error: File '{file_path}' not found.")
        except Exception as e:
            await log_and_stream_message("error", f"An error occurred while reading '{file_path}': {e}")
    elif command_lower.startswith("write "):
        parts = instruction[6:].strip().split(' ', 1) # Split only on first space
        if len(parts) < 2:
            await log_and_stream_message("error", "Usage: write <file_path> <content>")
            return
        file_path, content = parts[0], parts[1]
        try:
            await write_file(file_path, content)
            await log_and_stream_message("success", f"Successfully wrote content to '{file_path}'.")
            await log_and_stream_message("status", f"Wrote to '{file_path}'.", "write", instruction)
            command_logged = True
        except Exception as e:
            await log_and_stream_message("error", f"An error occurred while writing to '{file_path}': {e}")
    elif command_lower.startswith("list "):
        directory_path = instruction[5:].strip() or './' # Default to current dir if no path given
        try:
            files = await list_files(directory_path)
            await log_and_stream_message("response", f"Files and directories in '{directory_path}':")
            for item in files:
                await log_and_stream_message("response", f"- {item}")
            await log_and_stream_message("info", f"Successfully listed '{directory_path}'.")
            await log_and_stream_message("status", f"Listed '{directory_path}'.", "list", instruction)
            command_logged = True
        except FileNotFoundError:
            await log_and_stream_message("error", f"Error: Directory '{directory_path}' not found.")
        except Exception as e:
            await log_and_stream_message("error", f"An error occurred while listing '{directory_path}': {e}")
    elif command_lower.startswith("exec "):
        command = instruction[5:].strip()
        try:
            return_code, stdout, stderr = await execute_command(command)
            await log_and_stream_message("response", f"Command '{command}' executed.")
            await log_and_stream_message("response", f"Return Code: {return_code}")
            if stdout:
                await log_and_stream_message("response", f"STDOUT:\n{stdout}")
            if stderr:
                await log_and_stream_message("response", f"STDERR:\n{stderr}")
            if return_code == 0:
                await log_and_stream_message("success", f"Command '{command}' executed successfully.")
            else:
                await log_and_stream_message("error", f"Command '{command}' failed with code {return_code}.")
            await log_and_stream_message("status", f"Executed '{command}'.", "exec", instruction)
            command_logged = True
        except Exception as e:
            await log_and_stream_message("error", f"An error occurred while executing command '{command}': {e}")
    elif command_lower.startswith("checkpoint save "):
        parts = instruction[len("checkpoint save "):].strip().split(' ', 1)
        checkpoint_name = parts[0]
        message = parts[1] if len(parts) > 1 else f"Checkpoint '{checkpoint_name}' saved."
        if memory_service:
            try:
                await memory_service.store_memory(
                    content={"type": "checkpoint", "name": checkpoint_name, "message": message},
                    tags=["checkpoint", checkpoint_name]
                )
                await log_and_stream_message("success", f"Checkpoint '{checkpoint_name}' saved successfully.")
                await load_session_context() # Refresh context in CLI's memory
            except Exception as e:
                await log_and_stream_message("error", f"Error saving checkpoint '{checkpoint_name}': {e}")
        else:
            await log_and_stream_message("warning", "MemoryService not initialized, cannot save checkpoint.")
    elif command_lower.startswith("checkpoint load "):
        checkpoint_name = instruction[len("checkpoint load "):].strip()
        if memory_service:
            await log_and_stream_message("info", f"Loading checkpoint '{checkpoint_name}'...")
            try:
                loaded_checkpoints = await memory_service.load_memory(
                    query={"tags": [checkpoint_name, "checkpoint"], "user_id": current_user_id}
                )
                if loaded_checkpoints:
                    await log_and_stream_message("response", f"--- Checkpoint '{checkpoint_name}' Details ---")
                    loaded_checkpoints.sort(key=lambda cp: cp.get('timestamp', ''), reverse=True)
                    
                    cp = loaded_checkpoints[0]
                    if isinstance(cp.get('content'), dict) and cp['content'].get('type') == 'checkpoint':
                        await log_and_stream_message("response", f"  Name: {cp['content'].get('name')}")
                        await log_and_stream_message("response", f"  Message: {cp['content'].get('message')}")
                        await log_and_stream_message("response", f"  Timestamp: {cp.get('timestamp')}")
                        await log_and_stream_message("response", f"  Session ID: {cp.get('session_id')}")
                    else:
                        await log_and_stream_message("response", f"  Raw Memory Content: {cp.get('content')}")
                    await log_and_stream_message("response", "---")
                else:
                    await log_and_stream_message("info", f"No checkpoint found with name '{checkpoint_name}' for user '{current_user_id}'.")
            except Exception as e:
                await log_and_stream_message("error", f"Error loading checkpoint '{checkpoint_name}': {e}")
        else:
            await log_and_stream_message("warning", "MemoryService not initialized, cannot load checkpoint.")
    elif command_lower == "show context":
        if session_context_memories:
            await log_and_stream_message("response", "\n--- Current User Context (Recent Memories) ---")
            for mem in session_context_memories:
                timestamp = mem.get('timestamp')
                formatted_time = ""
                if timestamp:
                    try:
                        dt_object = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_time = dt_object.strftime("%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        formatted_time = timestamp.split('T')[0]

                content_display = mem.get('content', 'N/A')
                if isinstance(content_display, dict):
                    content_display = str(content_display)

                await log_and_stream_message("response", f"  - [{formatted_time}] {content_display[:80]}{'...' if len(content_display) > 80 else ''}")
            await log_and_stream_message("response", "--- End Context ---")
        else:
            await log_and_stream_message("info", f"No recent context available for user '{current_user_id}'. Perform some commands to build context across sessions.")
    elif command_lower.startswith("vibe save "):
        parts = instruction[len("vibe save "):].strip().split(' ', 1)
        snapshot_name = parts[0]
        current_todos_for_snapshot = [] # Placeholder for actual TODOs
        if vibe_engine:
            try:
                # Include current vibe state for the snapshot
                # We need to explicitly pass the current vibe data and todos
                current_vibe_data = vibe_engine.get_current_vibe()
                current_vibe_data["todos"] = current_todos_for_snapshot # Add todos to the vibe data
                success = await vibe_engine.save_vibe_to_file(snapshot_name, current_todos=current_todos_for_snapshot) # Passes todos again, but this is handled by save_vibe_to_file
                if success:
                    await log_and_stream_message("success", f"Vibe snapshot '{snapshot_name}' saved to local file.")
                else:
                    await log_and_stream_message("error", f"Failed to save vibe snapshot '{snapshot_name}' to local file.")
            except Exception as e:
                await log_and_stream_message("error", f"Error saving vibe snapshot '{snapshot_name}': {e}")
        else:
            await log_and_stream_message("warning", "VibeModeEngine not initialized, cannot save vibe snapshot.")
    elif command_lower.startswith("vibe load "):
        snapshot_name = instruction[len("vibe load "):].strip()
        if vibe_engine:
            try:
                success = await vibe_engine.load_vibe_from_file(snapshot_name)
                if success:
                    await log_and_stream_message("success", f"Vibe snapshot '{snapshot_name}' loaded from local file.")
                    await load_session_context() # Refresh context after loading a vibe from file
                else:
                    await log_and_stream_message("error", f"Failed to load vibe snapshot '{snapshot_name}' from local file.")
            except Exception as e:
                await log_and_stream_message("error", f"Error loading vibe snapshot '{snapshot_name}': {e}")
        else:
            await log_and_stream_message("warning", "VibeModeEngine not initialized, cannot load vibe snapshot.")
    elif command_lower == "vibe list":
        if vibe_engine:
            try:
                snapshots = await vibe_engine.list_local_vibe_snapshots()
                if snapshots:
                    await log_and_stream_message("response", "--- Available Vibe Snapshots ---")
                    for s_name in snapshots:
                        await log_and_stream_message("response", f"- {s_name}")
                    await log_and_stream_message("response", "---")
                else:
                    await log_and_stream_message("info", "No local vibe snapshots found.")
            except Exception as e:
                await log_and_stream_message("error", f"Error listing vibe snapshots: {e}")
        else:
            await log_and_stream_message("warning", "VibeModeEngine not initialized, cannot list vibe snapshots.")
    elif command_lower in ["exit", "quit", "bye"]:
        await log_and_stream_message("info", "Exiting Coddy CLI. Goodbye!")
        sys.exit(0)
    else:
        await log_and_stream_message("error", "Unknown instruction. Supported commands: read <file>, write <file> <content>, list [directory], exec <command>, checkpoint save <name> [message], checkpoint load <name>, show context, vibe save <name>, vibe load <name>, vibe list, exit/quit.")

    if command_logged:
        await update_adaptive_prompt_suggestion()


async def start_cli():
    """
    Starts the main command-line interface loop for Coddy.
    """
    print("Welcome to Coddy V2 CLI (Phase 4 Prototype - Vibe Tools)!")
    print(f"User ID: {current_user_id}, Session ID: {current_session_id}")
    print("Type 'exit' or 'quit' to end the session.")
    print("Supported commands: read <file>, write <file> <content>, list [directory], exec <command>, checkpoint save <name> [message], checkpoint load <name>, show context, vibe save <name>, vibe load <name>, vibe list.")

    await initialize_services() # Initialize services at CLI startup
    await load_session_context() # Load past context for this user
    await update_adaptive_prompt_suggestion() # Initial suggestion

    while True:
        try:
            prompt_text = f"Coddy>{adaptive_prompt_suggestion} "
            # Use asyncio.to_thread for blocking input to prevent blocking the event loop
            instruction = await asyncio.to_thread(input, prompt_text)
            await handle_instruction(instruction)
        except EOFError: # Handles Ctrl+D
            await log_and_stream_message("info", "\nExiting Coddy CLI. Goodbye!")
            break
        except KeyboardInterrupt: # Handles Ctrl+C
            await log_and_stream_message("info", "\nOperation interrupted. Type 'exit' to quit.")
        except Exception as e:
            await log_and_stream_message("critical", f"An unexpected error occurred in CLI loop: {e}")

if __name__ == "__main__":
    # To run this CLI: python Coddy/ui/cli.py
    # Ensure your Node.js backend is running (npm start in Coddy/backend).
    # Ensure WebSocket server is running (python Coddy/core/websocket_server.py in a separate terminal).
    # Ensure `aiohttp` and `websockets` are installed: `pip install aiohttp websockets`.
    # Ensure `memory_service.py`, `pattern_oracle.py`, `websocket_server.py`, `vibe_mode.py` are in Coddy/core.
    # Ensure `vibe_file_manager.py` is in Coddy/vibe (now a package).
    try:
        asyncio.run(start_cli())
    except Exception as e:
        print(f"CLI startup failed: {e}")