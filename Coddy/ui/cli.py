# cli.py
import asyncio
import sys
import os
import pytest
import uuid # For generating session_id
import datetime # For timestamps (though MemoryService handles this)
from typing import Optional, List, Dict, Any # Added for type hints
import shlex # For robust command parsing
import traceback # For detailed exception information
from pathlib import Path # For robust path manipulation

# Corrected sys.path.insert for importing modules from Coddy/core and Coddy/vibe
# Add Coddy/core to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core')))
# Add Coddy root to the Python path to correctly import the 'vibe' package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


try:
    from code_generator import CodeGenerator # For test generation
    from utility_functions import read_file, write_file, list_files, execute_command
    from memory_service import MemoryService # Assuming memory_service.py is in core
    from pattern_oracle import PatternOracle # Assuming pattern_oracle.py is in core
    from websocket_server import send_to_websocket_server # Assuming websocket_server.py is in core
    from vibe_mode import VibeModeEngine # Assuming vibe_mode.py is in core
    from logging_utility import log_info, log_warning, log_error, log_debug # Import the new logging utility
    from git_analyzer import GitAnalyzer # Import GitAnalyzer for current branch display
except ImportError as e:
    # This block handles critical import errors at startup
    print(f"FATAL ERROR: Could not import core modules required for CLI: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Global instances for services
memory_service: Optional[MemoryService] = None
pattern_oracle: Optional[PatternOracle] = None
vibe_engine: Optional[VibeModeEngine] = None # Global instance for VibeModeEngine
git_analyzer: Optional[GitAnalyzer] = None # Global instance for GitAnalyzer

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
    global memory_service, pattern_oracle, vibe_engine, git_analyzer
    await display_message("Initializing Coddy services...", "info")
    
    try:
        memory_service = MemoryService(session_id=current_session_id, user_id=current_user_id)
        pattern_oracle = PatternOracle(memory_service)
        vibe_engine = VibeModeEngine(memory_service, user_id=current_user_id) # Pass memory_service to VibeModeEngine
        git_analyzer = GitAnalyzer() # Initialize GitAnalyzer
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

async def _get_cli_prompt() -> str:
    """
    Dynamically generates the CLI prompt, including Git branch information.
    This is a separate function to be called by start_cli.
    """
    branch_info = ""
    if git_analyzer:
        try:
            current_branch = await git_analyzer.get_current_branch()
            if current_branch and current_branch != "Not a Git repository":
                branch_info = f"({current_branch})"
        except Exception as e:
            await log_warning(f"Could not get Git branch for prompt: {e}")
            branch_info = "(git-error)"
    
    return f"Coddy{branch_info}{adaptive_prompt_suggestion} > "


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
                                await display_message(f"   Name: {cp['content'].get('name')}", "response")
                                await display_message(f"   Message: {cp['content'].get('message')}", "response")
                                await display_message(f"   Timestamp: {cp.get('timestamp')}", "response")
                                await display_message(f"   Session ID: {cp.get('session_id')}", "response")
                            else:
                                await display_message(f"   Raw Memory Content: {cp.get('content')}", "response")
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
                    # Pretty print content if it's a dictionary
                    if isinstance(content_display, dict):
                        content_str = "\n".join([f"     - {k}: {v}" for k, v in content_display.items()])
                        await display_message(f"  [{formatted_time}] \n{content_str}", "response")
                    else:
                        await display_message(f"  [{formatted_time}] {content_display}", "response")
                await display_message("--- End of Context ---", "response")
            else:
                await display_message("No context loaded for the current session.", "info")
            command_logged = True

        elif command_name == "vibe":
            if vibe_engine:
                if not args:
                    current_vibe = vibe_engine.get_current_vibe()
                    await display_message(f"Current Vibe: {current_vibe}", "response")
                elif args[0].lower() == "set":
                    if len(args) > 1:
                        new_vibe = " ".join(args[1:])
                        await vibe_engine.set_vibe(new_vibe)
                        await display_message(f"Vibe set to: {new_vibe}", "success")
                    else:
                        await display_message("Usage: vibe set <description>", "warning")
                elif args[0].lower() == "clear":
                    await vibe_engine.clear_vibe()
                    await display_message("Vibe cleared.", "success")
                else:
                    await display_message("Usage: vibe [set <description>|clear]", "warning")
                command_logged = True
            else:
                await display_message("VibeModeEngine not initialized.", "warning")

        elif command_name == "memory":
            if memory_service:
                if not args or args[0].lower() == "search":
                    query_str = " ".join(args[1:]) if len(args) > 1 else ""
                    await display_message(f"Searching memory for: '{query_str}'...", "info")
                    results = await memory_service.load_memory(query={"content": {"$regex": query_str, "$options": "i"}})
                    if results:
                        await display_message(f"Found {len(results)} memories:", "response")
                        for mem in results[:5]: # Show top 5
                             await display_message(f"- {mem.get('timestamp')}: {mem.get('content')}", "response")
                    else:
                        await display_message("No matching memories found.", "info")
                else:
                    await display_message("Usage: memory [search <query>]", "warning")
                command_logged = True
            else:
                await display_message("MemoryService not initialized.", "warning")

        elif command_name == "help":
            await display_message("\n--- Coddy Commands ---", "response")
            await display_message("  read <file>              - Read the content of a file.", "response")
            await display_message("  write <file> <content>   - Write content to a file.", "response")
            await display_message("  list [directory]         - List files in a directory.", "response")
            await display_message("  exec <command>           - Execute a shell command.", "response")
            await display_message("  checkpoint save|load <name> - Save or load a session checkpoint.", "response")
            await display_message("  show context             - Display the loaded user context.", "response")
            await display_message("  vibe [set|clear]         - Manage the current vibe/focus.", "response")
            await display_message("  memory [search]          - Interact with long-term memory.", "response")
            await display_message("  unit_tester <file>       - Generate unit tests for a file.", "response")
            await display_message("  help                     - Show this help message.", "response")
            await display_message("  exit, quit, bye          - Exit the CLI.", "response")
            await display_message("---", "response")
            command_logged = True

        else:
            await display_message(f"Unknown instruction: '{command_name}'. Type 'help' for available commands.", "warning")
            if memory_service:
                await memory_service.store_memory(
                    content={"type": "unrecognized_command", "command": instruction},
                    tags=["cli_command", "unrecognized"]
                )

    except Exception as e:
        await display_message(f"An unexpected error occurred while handling instruction: {e}", "error")
        await log_error(f"Instruction Handler Error for '{instruction}'", exc_info=True)

    finally:
        if command_logged and memory_service:
            try:
                await memory_service.store_memory(
                    content={"type": "command", "command": command_name, "full_instruction": instruction},
                    tags=["cli_command", command_name]
                )
            except Exception as e:
                await display_message(f"Failed to log command to memory: {e}", "error")
                await log_error(f"Memory logging failed for command: {instruction}", exc_info=True)


async def start_cli():
    """
    The main asynchronous function to start and run the Coddy CLI.
    """
    await initialize_services()
    await load_session_context()

    await display_message("🚀 Coddy CLI (v2.0.0) - Your Async Dev Companion, Reimagined.", "info")
    await display_message("Type 'exit' to quit.", "info")
    await display_message(f"User ID: {current_user_id}, Session ID: {current_session_id}", "info")

    while True:
        try:
            prompt_text = await _get_cli_prompt()
            instruction = await asyncio.to_thread(input, prompt_text)
            await handle_instruction(instruction)
            await update_adaptive_prompt_suggestion()
        except (KeyboardInterrupt, EOFError):
            await display_message("\nExiting Coddy CLI. Goodbye!", "info")
            break
        except Exception as e:
            await display_message(f"\nAn unexpected error occurred in the main loop: {e}", "error")
            await log_error("Main CLI loop error", exc_info=True)
            break
