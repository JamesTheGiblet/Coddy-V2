# Coddy/ui/cli.py
import asyncio
import sys
import os
import uuid # For generating session_id
import datetime # For timestamps (though MemoryService handles this)
from typing import Optional, List, Dict, Any # Added for type hints
import shlex # For robust command parsing
import traceback # For detailed exception information

# Corrected sys.path.insert for importing modules from Coddy/core and Coddy/vibe
# Add Coddy/core to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core')))
# Add Coddy root to the Python path to correctly import the 'vibe' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


try:
    from utility_functions import read_file, write_file, list_files, execute_command
    from memory_service import MemoryService # Assuming memory_service.py is in core
    from pattern_oracle import PatternOracle # Assuming pattern_oracle.py is in core
    from websocket_server import send_to_websocket_server # Assuming websocket_server.py is in core
    from vibe_mode import VibeModeEngine # Assuming vibe_mode.py is in core
    from logging_utility import log_info, log_warning, log_error, log_debug # Import the new logging utility
except ImportError as e:
    # This block handles critical import errors at startup
    print(f"FATAL ERROR: Could not import core modules required for CLI: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Global instances for services
memory_service: Optional[MemoryService] = None
pattern_oracle: Optional[PatternOracle] = None
vibe_engine: Optional[VibeModeEngine] = None # Global instance for VibeModeEngine

current_user_id: str = "default_user" # Placeholder, will be replaced by actual user management
current_session_id: str = str(uuid.uuid4()) # Unique ID for each CLI session
adaptive_prompt_suggestion: str = "" # Stores dynamic prompt suggestions
session_context_memories: List[Dict[str, Any]] = [] # Stores loaded context for the current user

async def display_message(message: str, message_type: str = "info"):
    """
    Standardized way to display messages to the user (via WebSocket/console) and log them.
    Leverages the new logging_utility.
    """
    message_data = {
        "type": message_type,
        "text": message,
        "timestamp": datetime.datetime.now().isoformat(),
        "session_id": current_session_id,
        "user_id": current_user_id
    }
    await send_to_websocket_server(message_data) # Always send to WebSocket for UI

    # Log messages using the new logging utility
    if message_type == "info":
        await log_info(message)
    elif message_type == "warning":
        await log_warning(message)
    elif message_type == "error":
        # For errors, log the message. If an exception is being handled, exc_info=True
        # will capture the current exception's traceback.
        await log_error(message, exc_info=True if sys.exc_info()[0] is not None else False)
    elif message_type == "debug":
        await log_debug(message)


async def initialize_services():
    """Initializes global MemoryService, PatternOracle, and VibeModeEngine instances."""
    global memory_service, pattern_oracle, vibe_engine
    await display_message("Initializing Coddy services...", "info")
    
    try:
        memory_service = MemoryService(session_id=current_session_id, user_id=current_user_id)
        pattern_oracle = PatternOracle(memory_service)
        vibe_engine = VibeModeEngine(memory_service, user_id=current_user_id) # Pass memory_service to VibeModeEngine
        await vibe_engine.initialize() # Initialize VibeModeEngine to load its state
        await display_message("Services initialized.", "info")
    except Exception as e:
        await display_message(f"Failed to initialize one or more Coddy services: {e}", "error")
        await log_error(f"Service Initialization Error: {e}", exc_info=True)
        # It's critical to halt if core services can't initialize
        sys.exit(1)


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
                if most_frequent_cmd not in ["read", "write", "list", "exec", "checkpoint", "show", "vibe", "memory"]:
                    adaptive_prompt_suggestion = f" (Try '{most_frequent_cmd}'?)"
                else:
                    adaptive_prompt_suggestion = ""
            else:
                adaptive_prompt_suggestion = ""
        except Exception as e:
            await display_message(f"Error updating adaptive prompt suggestion: {e}", "error")
            await log_error(f"Adaptive Prompt Error: {e}", exc_info=True)
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
        await display_message("Loading past context for user...", "info")
        try:
            # Retrieve recent memories for the current user, NOT limited by current session_id
            session_context_memories = await memory_service.retrieve_context(
                num_recent=10, # Load up to 10 recent memories as context
                query={"user_id": current_user_id} # Only filter by user_id for persistent context
            )
            if session_context_memories:
                await display_message(f"Loaded {len(session_context_memories)} recent memories for user '{current_user_id}'.", "info")
            else:
                await display_message(f"No past context found for user '{current_user_id}'.", "info")
        except Exception as e:
            await display_message(f"Error loading user context: {e}", "error")
            await log_error(f"Context Loading Error: {e}", exc_info=True)
    else:
        await display_message("MemoryService not initialized, cannot load context.", "warning")

async def handle_instruction(instruction: str):
    """
    Parses a user instruction and attempts to execute a corresponding action.
    Includes robust error handling and logging for each command block.
    """
    instruction = instruction.strip()
    if not instruction:
        return

    # User input command is echoed first to the UI/log
    await display_message(f"Coddy> {instruction}", "info")

    command_logged = False
    command_parts = shlex.split(instruction) # Use shlex for robust parsing
    command_name = command_parts[0].lower() if command_parts else ""
    args = command_parts[1:]

    try:
        if command_name == "read":
            if not args:
                await display_message("Usage: read <file_path>", "warning")
                return
            file_path = args[0]
            try:
                content = await read_file(file_path)
                await display_message(f"Content of '{file_path}':\n---\n{content}\n---", "response")
                await display_message(f"Successfully read '{file_path}'.", "success")
                command_logged = True
            except FileNotFoundError:
                await display_message(f"File '{file_path}' not found.", "error")
            except ValueError as e: # Catch safe_path errors
                await display_message(f"Invalid file path: {file_path}. Error: {e}", "error")
            except Exception as e:
                await display_message(f"An unexpected error occurred while reading '{file_path}': {e}", "error")
            await log_error(f"Failed to read file: {file_path}", exc_info=True)


        elif command_name == "write":
            if len(args) < 2:
                await display_message("Usage: write <file_path> <content>", "warning")
                return
            file_path = args[0]
            content = " ".join(args[1:]) # Join remaining args as content
            try:
                await write_file(file_path, content)
                await display_message(f"Successfully wrote content to '{file_path}'.", "success")
                command_logged = True
            except ValueError as e: # Catch safe_path errors
                await display_message(f"Invalid file path: {file_path}. Error: {e}", "error")
            except Exception as e:
                await display_message(f"An unexpected error occurred while writing to '{file_path}': {e}", "error")
            await log_error(f"Failed to write file: {file_path}", exc_info=True)


        elif command_name == "list":
            directory_path = args[0] if args else './' # Default to current dir if no path given
            try:
                items = await list_files(directory_path)
                item_list_str = "\n".join([f"- {item}" for item in items])
                await display_message(f"Files and directories in '{directory_path}':\n{item_list_str}", "response")
                await display_message(f"Successfully listed '{directory_path}'.", "success")
                command_logged = True
            except FileNotFoundError:
                await display_message(f"Directory '{directory_path}' not found.", "error")
            except ValueError as e: # Catch safe_path errors
                await display_message(f"Invalid directory path: {directory_path}. Error: {e}", "error")
            except Exception as e:
                await display_message(f"An unexpected error occurred while listing '{directory_path}': {e}", "error")
            await log_error(f"Failed to list directory: {directory_path}", exc_info=True)


        elif command_name == "exec":
            if not args:
                await display_message("Usage: exec <command_string>", "warning")
                return
            full_command = shlex.join(args) # Reconstruct command with shlex for safety
            try:
                return_code, stdout, stderr = await execute_command(full_command)
                await display_message(f"Command '{full_command}' executed.", "response")
                if stdout:
                    await display_message(f"STDOUT:\n{stdout}", "response")
                if stderr:
                    await display_message(f"STDERR:\n{stderr}", "error")
                    # Log stderr to file without full traceback unless it's an actual Python exception
                    await log_warning(f"Command '{full_command}' produced STDERR: {stderr}")
                if return_code != 0:
                    await display_message(f"Command '{full_command}' failed with exit code {return_code}.", "error")
                    await log_error(f"Command '{full_command}' failed with exit code {return_code}.")
                else:
                    await display_message(f"Command '{full_command}' executed successfully.", "success")
                command_logged = True
            except Exception as e:
                await display_message(f"Error executing command '{full_command}': {e}", "error")
                await log_error(f"Exception during command execution: {full_command}", exc_info=True)


        elif command_name == "exit" or command_name == "quit" or command_name == "bye":
            await display_message("Exiting Coddy CLI. Goodbye!", "info")
            sys.exit(0)

        # --- Placeholder/Existing Command Handlers ---
        elif command_name == "checkpoint":
            if len(args) >= 2 and args[0].lower() == "save":
                checkpoint_name = args[1]
                message = " ".join(args[2:]) if len(args) > 2 else f"Checkpoint '{checkpoint_name}' saved."
                if memory_service:
                    try:
                        await memory_service.store_memory(
                            content={"type": "checkpoint", "name": checkpoint_name, "message": message},
                            tags=["checkpoint", checkpoint_name]
                        )
                        await display_message(f"Checkpoint '{checkpoint_name}' saved successfully.", "success")
                        await load_session_context() # Refresh context in CLI's memory
                        command_logged = True
                    except Exception as e:
                        await display_message(f"Error saving checkpoint '{checkpoint_name}': {e}", "error")
                        await log_error(f"Checkpoint save error: {e}", exc_info=True)
                else:
                    await display_message("MemoryService not initialized, cannot save checkpoint.", "warning")
            elif len(args) >= 1 and args[0].lower() == "load":
                checkpoint_name = args[1] if len(args) > 1 else ""
                if not checkpoint_name:
                    await display_message("Usage: checkpoint load <name>", "warning")
                    return
                if memory_service:
                    await display_message(f"Loading checkpoint '{checkpoint_name}'...", "info")
                    try:
                        loaded_checkpoints = await memory_service.load_memory(
                            query={"tags": [checkpoint_name, "checkpoint"], "user_id": current_user_id}
                        )
                        if loaded_checkpoints:
                            await display_message(f"--- Checkpoint '{checkpoint_name}' Details ---", "response")
                            loaded_checkpoints.sort(key=lambda cp: cp.get('timestamp', ''), reverse=True)
                            
                            cp = loaded_checkpoints[0]
                            if isinstance(cp.get('content'), dict) and cp['content'].get('type') == 'checkpoint':
                                await display_message(f"  Name: {cp['content'].get('name')}", "response")
                                await display_message(f"  Message: {cp['content'].get('message')}", "response")
                                await display_message(f"  Timestamp: {cp.get('timestamp')}", "response")
                                await display_message(f"  Session ID: {cp.get('session_id')}", "response")
                            else:
                                await display_message(f"  Raw Memory Content: {cp.get('content')}", "response")
                            await display_message("---", "response")
                            command_logged = True
                        else:
                            await display_message(f"No checkpoint found with name '{checkpoint_name}' for user '{current_user_id}'.", "info")
                    except Exception as e:
                        await display_message(f"Error loading checkpoint '{checkpoint_name}': {e}", "error")
                        await log_error(f"Checkpoint load error: {e}", exc_info=True)
                else:
                    await display_message("MemoryService not initialized, cannot load checkpoint.", "warning")
            else:
                await display_message("Usage: checkpoint save <name> [message] or checkpoint load <name>", "warning")


        elif command_name == "show" and len(args) == 1 and args[0].lower() == "context":
            if session_context_memories:
                await display_message("\n--- Current User Context (Recent Memories) ---", "response")
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

                    await display_message(f"  - [{formatted_time}] {content_display[:80]}{'...' if len(content_display) > 80 else ''}", "response")
                await display_message("--- End Context ---", "response")
                command_logged = True
            else:
                await display_message(f"No recent context available for user '{current_user_id}'. Perform some commands to build context across sessions.", "info")


        elif command_name == "vibe":
            if len(args) >= 2 and args[0].lower() == "save":
                snapshot_name = args[1]
                # Placeholder for actual TODOs and vibe data extraction
                current_todos_for_snapshot = [] 
                if vibe_engine:
                    try:
                        current_vibe_data = vibe_engine.get_current_vibe() # Get latest vibe state
                        current_vibe_data["todos"] = current_todos_for_snapshot # Add todos placeholder
                        success = await vibe_engine.save_vibe_to_file(snapshot_name, current_vibe_data)
                        if success:
                            await display_message(f"Vibe snapshot '{snapshot_name}' saved to local file.", "success")
                            command_logged = True
                        else:
                            await display_message(f"Failed to save vibe snapshot '{snapshot_name}' to local file.", "error")
                    except Exception as e:
                        await display_message(f"Error saving vibe snapshot '{snapshot_name}': {e}", "error")
                        await log_error(f"Vibe save error: {e}", exc_info=True)
                else:
                    await display_message("VibeModeEngine not initialized, cannot save vibe snapshot.", "warning")
            elif len(args) >= 2 and args[0].lower() == "load":
                snapshot_name = args[1]
                if vibe_engine:
                    try:
                        success = await vibe_engine.load_vibe_from_file(snapshot_name)
                        if success:
                            await display_message(f"Vibe snapshot '{snapshot_name}' loaded from local file.", "success")
                            await load_session_context() # Refresh context after loading a vibe from file
                            command_logged = True
                        else:
                            await display_message(f"Failed to load vibe snapshot '{snapshot_name}' from local file.", "error")
                    except FileNotFoundError:
                        await display_message(f"Vibe snapshot '{snapshot_name}' not found.", "error")
                    except Exception as e:
                        await display_message(f"Error loading vibe snapshot '{snapshot_name}': {e}", "error")
                        await log_error(f"Vibe load error: {e}", exc_info=True)
                else:
                    await display_message("VibeModeEngine not initialized, cannot load vibe snapshot.", "warning")
            elif len(args) == 1 and args[0].lower() == "list":
                if vibe_engine:
                    try:
                        snapshots = await vibe_engine.list_local_vibe_snapshots()
                        if snapshots:
                            await display_message("--- Available Vibe Snapshots ---", "response")
                            for s_name in snapshots:
                                await display_message(f"- {s_name}", "response")
                            await display_message("---", "response")
                            command_logged = True
                        else:
                            await display_message("No local vibe snapshots found.", "info")
                    except Exception as e:
                        await display_message(f"Error listing vibe snapshots: {e}", "error")
                        await log_error(f"Vibe list error: {e}", exc_info=True)
                else:
                    await display_message("VibeModeEngine not initialized, cannot list vibe snapshots.", "warning")
            else:
                await display_message("Usage: vibe save <name> | vibe load <name> | vibe list", "warning")


        elif command_name == "memory":
            if len(args) >= 1 and args[0].lower() == "show":
                # Assuming 'memory show' might display recent raw memories or summary
                if memory_service:
                    await display_message("Showing recent raw memories (placeholder)...", "info")
                    try:
                        recent_mems = await memory_service.retrieve_context(num_recent=5)
                        if recent_mems:
                            for mem in recent_mems:
                                await display_message(f"- {mem.get('content', 'N/A')}", "response")
                        else:
                            await display_message("No recent memories to show.", "info")
                        command_logged = True
                    except Exception as e:
                        await display_message(f"Error showing memories: {e}", "error")
                        await log_error(f"Memory show error: {e}", exc_info=True)
                else:
                    await display_message("MemoryService not initialized, cannot show memories.", "warning")
            else:
                await display_message("Usage: memory show (more commands to come)", "warning")


        else:
            await display_message("Unknown instruction. Supported commands: read <file>, write <file> <content>, list [directory], exec <command>, checkpoint save <name> [message], checkpoint load <name>, show context, vibe save <name>, vibe load <name>, vibe list, memory show, exit/quit.", "warning")
            await log_warning(f"Unknown instruction received: '{instruction}'")

    except ValueError as e: # Catch safe_path or other validation errors that might be raised by utility functions
        await display_message(f"Invalid input or operation: {e}", "error")
        await log_error(f"Input validation error for instruction '{instruction}': {e}", exc_info=True)
    except Exception as e:
        # Generic catch-all for any unhandled exceptions during instruction processing
        await display_message(f"An unexpected error occurred while processing instruction: {e}", "error")
        await log_error(f"Unhandled exception processing instruction '{instruction}': {e}", exc_info=True)

    finally:
        # Always update adaptive prompt suggestion after a command is processed (if it was valid)
        if command_logged:
            await update_adaptive_prompt_suggestion()


async def start_cli():
    """
    Main loop for the Coddy CLI.
    Initializes services and handles user input with comprehensive error handling.
    """
    # Attempt to initialize services. If this fails, the app will exit.
    await initialize_services() 
    await load_session_context() # Load past context for this user
    await update_adaptive_prompt_suggestion() # Initial suggestion

    await display_message("🚀 Coddy CLI (v2.0.0) - Your Async Dev Companion, Reimagined.", "info")
    await display_message("Type 'exit' to quit.", "info")
    await display_message(f"User ID: {current_user_id}, Session ID: {current_session_id}", "info")


    while True:
        try:
            prompt_text = f"Coddy>{adaptive_prompt_suggestion} "
            # Use asyncio.to_thread for blocking input to prevent blocking the event loop
            instruction = await asyncio.to_thread(input, prompt_text)
            if not instruction.strip():
                continue
            await handle_instruction(instruction)
        except EOFError: # Handles Ctrl+D
            await display_message("\nReceived EOF. Exiting Coddy CLI. Goodbye!", "info")
            sys.exit(0)
        except KeyboardInterrupt: # Handles Ctrl+C
            await display_message("\nOperation interrupted. Exiting Coddy CLI. Goodbye!", "info")
            sys.exit(0) # Exit gracefully on Ctrl+C
        except Exception as e:
            # This catches errors in the input() call or if asyncio.to_thread fails
            await display_message(f"An unexpected error occurred in the CLI loop: {e}", "error")
            await log_error(f"Unhandled error in CLI input loop: {e}", exc_info=True)
            # If an error occurs here, it's severe enough to exit
            sys.exit(1)


if __name__ == "__main__":
    # Ensure PROJECT_ROOT is correctly set for standalone execution/testing of cli.py
    # This might be redundant if cli.py is always run as part of a larger Coddy system init.
    # However, for direct testing, it's safer.
    # Assuming cli.py is in Coddy/ui/, then '..' to Coddy/, and then parent dir is project root
    # Corrected: PROJECT_ROOT defined in utility_functions.py is the Coddy/ directory.
    # So when cli.py imports utility_functions, it gets the correct PROJECT_ROOT.
    # No need to redefine it here.
    
    # Final catch-all for any unhandled exceptions that escape the CLI loop,
    # specifically for the initial asyncio.run(start_cli()) call.
    try:
        asyncio.run(start_cli())
    except Exception as e:
        print(f"\nFATAL ERROR: Coddy CLI terminated unexpectedly: {e}", file=sys.stderr)
        # Log the critical error with full traceback
        # We need to run this in a new event loop if the previous one is closed
        try:
            asyncio.run(log_error(f"FATAL CLI termination: {e}", exc_info=True))
        except RuntimeError: # Catch if event loop is already closed/running
            import logging
            logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
            logging.error(f"FATAL CLI termination (RuntimeError during async logging): {e}", exc_info=True)
        sys.exit(1)
