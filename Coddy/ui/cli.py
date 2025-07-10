# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\ui\cli.py

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
import httpx
import json # Added for parsing JSON input for profile set command

# Add the project root to sys.path to allow imports from 'Coddy.core'
# This calculates the path to 'C:\Users\gilbe\Documents\GitHub\Coddy V2'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    # Updated import paths to be absolute from the project root
    from Coddy.core.code_generator import CodeGenerator
    from Coddy.core.task_decomposition_engine import TaskDecompositionEngine
    from Coddy.core.memory_service import MemoryService
    from Coddy.core.pattern_oracle import PatternOracle
    from Coddy.core.websocket_server import send_to_websocket_server
    from Coddy.core.vibe_mode import VibeModeEngine
    from Coddy.core.logging_utility import log_info, log_warning, log_error, log_debug
    from Coddy.core.git_analyzer import GitAnalyzer
    from Coddy.core.execution_manager import ExecutionManager, execute_command 
    from Coddy.core.autonomous_agent import AutonomousAgent 
    from Coddy.core.user_profile import UserProfile # NEW: Import UserProfile
    from Coddy.core.llm_provider import get_llm_provider # NEW: Import get_llm_provider
except ImportError as e:
    print(f"FATAL ERROR: Could not import core modules required for CLI: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Global instances for services
memory_service: Optional[MemoryService] = None
pattern_oracle: Optional[PatternOracle] = None
vibe_engine: Optional[VibeModeEngine] = None
git_analyzer: Optional[GitAnalyzer] = None
code_generator: Optional[CodeGenerator] = None
execution_manager: Optional[ExecutionManager] = None
autonomous_agent: Optional[AutonomousAgent] = None
user_profile_manager: Optional[UserProfile] = None # NEW: Global UserProfile instance
llm_provider: Optional[Any] = None # NEW: Global LLMProvider instance

current_user_id: str = "default_user"
current_session_id: str = str(uuid.uuid4())
adaptive_prompt_suggestion: str = ""
session_context_memories: List[Dict[str, Any]] = []

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
    await send_to_websocket_server(message_data)

    if message_type == "info":
        await log_info(message)
    elif message_type == "warning":
        await log_warning(message)
    elif message_type == "error":
        await log_error(message, exc_info=True if sys.exc_info()[0] is not None else False)
    elif message_type == "debug":
        await log_debug(message)


async def initialize_services():
    """Initializes global Coddy service instances."""
    global memory_service, pattern_oracle, vibe_engine, git_analyzer, code_generator, execution_manager, autonomous_agent, user_profile_manager, llm_provider
    await display_message("Initializing Coddy services...", "info")
    
    # Define LLM model and provider type for CLI
    LLM_MODEL_NAME = "gemini-1.5-flash-latest"
    LLM_PROVIDER_TYPE = "gemini" # Or "ollama" if you prefer

    try:
        memory_service = MemoryService(session_id=current_session_id, user_id=current_user_id)
        
        # NEW: Initialize UserProfile manager
        user_profile_manager = UserProfile(session_id=current_session_id, user_id=current_user_id)
        await user_profile_manager.initialize() # Load the user profile asynchronously

        # NEW: Initialize LLMProvider
        llm_provider = get_llm_provider(
            provider_name=LLM_PROVIDER_TYPE,
            config={"model": LLM_MODEL_NAME}
        )
        await display_message("LLMProvider initialized for CLI.", "info")

        # Pass user_profile_manager to VibeModeEngine
        vibe_engine = VibeModeEngine(memory_service, user_profile_manager=user_profile_manager)
        await vibe_engine.initialize() # Initialize VibeModeEngine to load its state

        # Pass user_profile_manager and llm_provider to CodeGenerator
        code_generator = CodeGenerator(
            llm_provider=llm_provider, # Pass the centralized LLMProvider
            memory_service=memory_service, # Assuming CodeGenerator also needs memory_service
            vibe_engine=vibe_engine, # Assuming CodeGenerator also needs vibe_engine
            user_profile_manager=user_profile_manager
        ) 
        
        pattern_oracle = PatternOracle(memory_service)
        
        execution_manager = ExecutionManager(
            memory_service=memory_service,
            vibe_engine=vibe_engine,
            code_generator=code_generator,
            current_user_id=current_user_id,
            current_session_id=current_session_id
        )

        # Pass user_profile_manager and llm_provider to AutonomousAgent
        autonomous_agent = AutonomousAgent(
            memory_service=memory_service,
            vibe_engine=vibe_engine,
            code_generator=code_generator,
            execution_manager=execution_manager,
            current_user_id=current_user_id,
            current_session_id=current_session_id,
            user_profile_manager=user_profile_manager,
            llm_provider=llm_provider # Pass the centralized LLMProvider
        )

        await display_message("Services initialized.", "info")
    except Exception as e:
        await display_message(f"Failed to initialize one or more Coddy services: {e}", "error")
        await log_error(f"Service Initialization Error: {e}", exc_info=True)
        sys.exit(1)


async def update_adaptive_prompt_suggestion():
    """Analyzes command frequency and updates the adaptive prompt suggestion."""
    global adaptive_prompt_suggestion
    if pattern_oracle:
        try:
            # This can eventually be enhanced by using user_profile_manager.profile.common_patterns
            # For now, it continues to use pattern_oracle's frequency analysis.
            frequent_commands = await pattern_oracle.analyze_command_frequency(
                num_top_commands=1, user_id=current_user_id
            )
            if frequent_commands:
                most_frequent_cmd = frequent_commands[0]['command']
                if most_frequent_cmd not in ["read", "write", "list", "exec", "checkpoint", "show", "vibe", "memory", "unit_tester", "help", "exit", "quit", "bye", "agent", "profile", "feedback"]:
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
            # MemoryService.retrieve_context will now use the correct API endpoint
            session_context_memories = await memory_service.retrieve_context(
                num_recent=10,
                query={"user_id": current_user_id}
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

    await display_message(f"Coddy> {instruction}", "info")

    command_logged = False
    original_instruction = instruction
    command_parts = shlex.split(instruction)
    command_name = command_parts[0].lower() if command_parts else ""
    args = command_parts[1:]

    try:
        # Delegate complex instructions to the AutonomousAgent
        if command_name == "agent":
            if not args:
                await display_message("Usage: agent <high_level_instruction>", "warning")
                return
            high_level_instruction = " ".join(args)
            if autonomous_agent:
                await autonomous_agent.execute_task(high_level_instruction)
                command_logged = True
            else:
                await display_message("AutonomousAgent not initialized.", "error")
            return

        # NEW: Handle 'profile' command
        elif command_name == "profile":
            if not user_profile_manager:
                await display_message("UserProfile service not initialized.", "error")
                return

            if not args:
                # Show current profile summary
                if user_profile_manager.profile:
                    profile_summary = user_profile_manager.profile.model_dump_json(indent=2)
                    await display_message(f"Your Current Profile:\n{profile_summary}", "response")
                else:
                    await display_message("User profile not loaded.", "info")
                command_logged = True
            elif args[0].lower() == "get":
                if len(args) < 2:
                    await display_message("Usage: profile get <key>", "warning")
                    return
                key = args[1]
                value = await user_profile_manager.get(key)
                if value is not None:
                    await display_message(f"Profile '{key}': {value}", "response")
                else:
                    await display_message(f"Profile key '{key}' not found or is None.", "info")
                command_logged = True
            elif args[0].lower() == "set":
                if len(args) < 3:
                    await display_message("Usage: profile set <key> <value>", "warning")
                    await display_message("Note: For lists/dicts, provide as JSON string (e.g., '[\"Python\"]' or '{\"indent\": 4}')", "info")
                    return
                key = args[1]
                value_str = " ".join(args[2:])
                try:
                    # Attempt to parse value as JSON (for lists/dicts)
                    value = json.loads(value_str)
                except json.JSONDecodeError:
                    # If not JSON, treat as a string or attempt type conversion
                    if value_str.lower() == 'true':
                        value = True
                    elif value_str.lower() == 'false':
                        value = False
                    elif value_str.isdigit():
                        value = int(value_str)
                    elif value_str.replace('.', '', 1).isdigit():
                        value = float(value_str)
                    else:
                        value = value_str # Keep as string
                
                await user_profile_manager.set(key, value)
                await display_message(f"Profile '{key}' set to '{value}'.", "success")
                command_logged = True
            elif args[0].lower() == "clear":
                await user_profile_manager.clear_profile()
                await display_message("User profile reset to default.", "success")
                command_logged = True
            else:
                await display_message("Usage: profile [get <key>|set <key> <value>|clear]", "warning")
            return # Exit after handling profile command

        # NEW: Handle 'feedback' command
        elif command_name == "feedback":
            if not user_profile_manager:
                await display_message("UserProfile service not initialized.", "error")
                return
            if not args or not args[0].isdigit():
                await display_message("Usage: feedback <rating (1-5)> [comment]", "warning")
                return
            
            rating = int(args[0])
            if not (1 <= rating <= 5):
                await display_message("Rating must be between 1 and 5.", "warning")
                return
            
            comment = " ".join(args[1:]) if len(args) > 1 else None
            
            await user_profile_manager.add_feedback(rating=rating, comment=comment)
            await display_message(f"Thank you for your feedback (Rating: {rating})!", "success")
            command_logged = True
            return # Exit after handling feedback command

        # Existing direct command handlers
        elif command_name == "read":
            if not args:
                await display_message("Usage: read <file_path>", "warning")
                return
            file_path = args[0]
            if execution_manager:
                await execution_manager.read_file_api(file_path)
                command_logged = True
            else:
                await display_message("ExecutionManager not initialized.", "error")

        elif command_name == "write":
            if len(args) < 2:
                await display_message("Usage: write <file_path> <content>", "warning")
                return
            file_path = args[0]
            content = " ".join(args[1:])
            if execution_manager:
                await execution_manager.write_file_api(file_path, content)
                command_logged = True
            else:
                await display_message("ExecutionManager not initialized.", "error")

        elif command_name == "list":
            directory_path = args[0] if args else './'
            if execution_manager:
                await execution_manager.list_files_api(directory_path)
                command_logged = True
            else:
                await display_message("ExecutionManager not initialized.", "error")

        elif command_name == "exec":
            if not args:
                await display_message("Usage: exec <command_string>", "warning")
                return
            full_command = shlex.join(args)
            if execution_manager:
                await execution_manager.execute_shell_command(full_command)
                command_logged = True
            else:
                await display_message("ExecutionManager not initialized.", "error")

        elif command_name == "exit" or command_name == "quit" or command_name == "bye":
            await display_message("Exiting Coddy CLI. Goodbye!", "info")
            sys.exit(0)

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
                        await load_session_context()
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
                                await display_message(f"    Name: {cp['content'].get('name')}", "response")
                                await display_message(f"    Message: {cp['content'].get('message')}", "response")
                                await display_message(f"    Timestamp: {cp.get('timestamp')}", "response")
                                await display_message(f"    Session ID: {cp.get('session_id')}", "response")
                            else:
                                await display_message(f"    Raw Memory Content: {cp.get('content')}", "response")
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
                        content_str = "\n".join([f"    - {k}: {v}" for k, v in content_display.items()])
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
                    # MemoryService.load_memory will now use the correct API endpoint
                    results = await memory_service.load_memory(query={"content": {"$regex": query_str, "$options": "i"}})
                    if results:
                        await display_message(f"Found {len(results)} memories:", "response")
                        for mem in results[:5]:
                             await display_message(f"- {mem.get('timestamp')}: {mem.get('content')}", "response")
                    else:
                        await display_message("No matching memories found.", "info")
                else:
                    await display_message("Usage: memory [search <query>]", "warning")
                command_logged = True
            else:
                await display_message("MemoryService not initialized.", "warning")
        
        elif command_name == "unit_tester":
            if not args:
                await display_message("Usage: unit_tester <file_path>", "warning")
                return
            file_path = args[0]
            if execution_manager:
                success = await execution_manager.manage_unit_tests_and_correction(file_path, session_context_memories)
                if success:
                    await display_message(f"Unit test process for '{file_path}' completed successfully.", "success")
                else:
                    await display_message(f"Unit test process for '{file_path}' encountered issues.", "error")
                command_logged = True
            else:
                await display_message("ExecutionManager not initialized.", "error")

        elif command_name == "help":
            await display_message("\n--- Coddy Commands ---", "response")
            await display_message("    agent <instruction>       - Execute a high-level instruction using the autonomous agent.", "response")
            await display_message("    read <file>               - Read the content of a file.", "response")
            await display_message("    write <file> <content>    - Write content to a file.", "response")
            await display_message("    list [directory]          - List files in a directory.", "response")
            await display_message("    exec <command>            - Execute a shell command.", "response")
            await display_message("    checkpoint save|load <name> - Save or load a session checkpoint.", "response")
            await display_message("    show context              - Display the loaded user context.", "response")
            await display_message("    vibe [set <description>|clear] - Manage the current vibe/focus.", "response")
            await display_message("    memory [search <query>]   - Interact with long-term memory.", "response")
            await display_message("    profile [get <key>|set <key> <value>|clear] - Manage your user profile preferences.", "response") # NEW: Profile help
            await display_message("    feedback <rating (1-5)> [comment] - Provide feedback on Coddy's last interaction.", "response") # NEW: Feedback help
            await display_message("    unit_tester <file>        - Generate and optionally run unit tests for a file.", "response")
            await display_message("    help                      - Show this help message.", "response")
            await display_message("    exit, quit, bye           - Exit the CLI.", "response")
            await display_message("---", "response")
            command_logged = True

        else:
            await display_message(f"Instruction '{instruction}' not a direct command. Attempting to pass to Autonomous Agent...", "info")
            if autonomous_agent:
                await autonomous_agent.execute_task(instruction)
                command_logged = True
            else:
                await display_message("AutonomousAgent not initialized. Cannot process unknown instruction.", "error")


    except Exception as e:
        await display_message(f"An unexpected error occurred while handling instruction: {e}", "error")
        await log_error(f"Instruction Handler Error for '{original_instruction}'", exc_info=True)

    finally:
        if not command_logged and memory_service:
            try:
                await memory_service.store_memory(
                    content={"type": "command", "command": command_name, "full_instruction": original_instruction},
                    tags=["cli_command", command_name]
                )
            except Exception as e:
                await display_message(f"Failed to log command to memory: {e}", "error")
                await log_error(f"Memory logging failed for command: {original_instruction}", exc_info=True)
        elif command_logged and memory_service:
            if original_instruction != instruction:
                # This block seems to be intended for logging the outcome of a top-level command
                # if it was transformed or delegated. Ensure it's correctly logging the *original* instruction.
                try:
                    await memory_service.store_memory(
                        content={"type": "top_level_command_outcome", "command": command_name, "full_instruction": original_instruction},
                        tags=["cli_command", "top_level", command_name]
                    )
                except Exception as e:
                    await display_message(f"Failed to log original command to memory: {e}", "error")
                    await log_error(f"Memory logging failed for original command: {original_instruction}", exc_info=True)


async def start_cli():
    """
    The main asynchronous function to start and run the Coddy CLI.
    """
    await initialize_services()
    await load_session_context()

    await display_message("🚀 Coddy CLI (v2.0.0) - Your Async Dev Companion, Reimagined.", "info")
    await display_message("Type 'exit' to quit.", "info")
    await display_message(f"User ID: {current_user_id}, Session ID: {current_session_id}", "info")

    try:
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
    finally: # NEW: Ensure services are closed on exit
        if memory_service:
            await memory_service.close()
        if user_profile_manager:
            await user_profile_manager.close()

