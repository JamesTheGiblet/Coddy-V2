# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\autonomous_agent.py

import asyncio
import shlex
import sys
import datetime
from typing import Optional, List, Dict, Any

# Import core components that the agent will orchestrate
from core.task_decomposition_engine import TaskDecompositionEngine
from core.execution_manager import ExecutionManager # For executing commands and managing tests
from core.memory_service import MemoryService # For accessing memory context
from core.vibe_mode import VibeModeEngine # For accessing current vibe
from core.code_generator import CodeGenerator  # For direct code generation if needed by agent

# Assuming these are available from the core module or passed in
from core.websocket_server import send_to_websocket_server
from core.logging_utility import log_info, log_warning, log_error, log_debug
from core.user_profile import UserProfile  # Import UserProfile to fix the error

class AutonomousAgent:
    """
    The AutonomousAgent orchestrates task decomposition, command execution,
    and self-correction to achieve high-level user instructions.
    It acts as the brain that connects Coddy's various intelligent components.
    """
    def __init__(self,
                 memory_service: MemoryService,
                 vibe_engine: VibeModeEngine,
                 code_generator: CodeGenerator,
                 execution_manager: ExecutionManager,
                 current_user_id: str,
                 current_session_id: str):

        self.memory_service = memory_service
        self.vibe_engine = vibe_engine
        self.code_generator = code_generator
        self.execution_manager = execution_manager
        self.task_decomposition_engine = TaskDecompositionEngine(llm_provider=self.code_generator.llm_provider) # Agent owns its decomposition engine
        self.current_user_id = current_user_id
        self.current_session_id = current_session_id
        self.last_generated_code: Optional[str] = None # NEW: State to hold recently generated code

    async def _display_message(self, message: str, message_type: str = "info"):
        """
        Internal helper to display messages, ensuring consistent output and logging.
        """
        message_data = {
            "type": message_type,
            "text": message,
            "timestamp": datetime.datetime.now().isoformat(),
            "session_id": self.current_session_id,
            "user_id": self.current_user_id
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

    async def execute_task(self, high_level_instruction: str) -> bool:
        """
        Executes a high-level instruction by decomposing it into subtasks,
        executing them, and attempting self-correction if necessary.

        Args:
            high_level_instruction: The user's high-level instruction (e.g., "Implement a new feature").

        Returns:
            True if the task is completed successfully, False otherwise.
        """
        await self._display_message(
            f"Agent received high-level instruction: '{high_level_instruction}'",
            "info",
        )
        await log_debug(f"Starting task execution for: '{high_level_instruction}'")

        # Reset state for the new task execution
        
        # 1. Store the initial instruction in memory
        await self.memory_service.store_memory(
            content={"type": "high_level_instruction", "instruction": high_level_instruction},
            tags=["agent_task", "new_task"]
        )

        # Load user profile to pass to the decomposition engine
        user_profile_manager = UserProfile(session_id=self.current_session_id, user_id=self.current_user_id, memory_service=self.memory_service)
        await user_profile_manager.initialize()
        user_profile_data = user_profile_manager.profile.model_dump() if user_profile_manager.profile else {}
        await log_debug(f"Loaded user profile: {user_profile_data}")

        # We don't close the user_profile_manager here, as the memory_service is shared.
        # The creator of the agent is responsible for the lifecycle of the memory_service.

        # 2. Decompose the high-level instruction into subtasks
        await self._display_message("Decomposing high-level instruction...", "info")
        await log_debug(f"Decomposing instruction: '{high_level_instruction}'")
        subtasks = await self.task_decomposition_engine.decompose(high_level_instruction, user_profile=user_profile_data)

        await log_debug(f"Decomposition result: {subtasks}")
        if not subtasks or (len(subtasks) == 1 and "Error:" in subtasks[0]):
            await self._display_message(f"Failed to decompose instruction: {subtasks[0] if subtasks else 'No subtasks generated'}", "error")
            await self.memory_service.store_memory(
                content={"type": "task_decomposition_failed", "instruction": high_level_instruction, "reason": subtasks[0] if subtasks else "No subtasks"},
                tags=["agent_task", "failure"]
            )
            return False

        # Filter out non-essential subtasks like README generation based on user feedback.
        original_subtask_count = len(subtasks)
        def _is_readme_generation_task(task: str) -> bool:
            try:
                parts = shlex.split(task)
                # Check if it's a 'generate_code' command and the last argument is 'README.md'
                return (parts and
                        parts[0].lower() == 'generate_code' and
                        len(parts) > 1 and
                        parts[-1].lower().strip("'\"") == 'readme.md')
            except ValueError:
                return False # Malformed command, don't filter

        subtasks = [task for task in subtasks if not _is_readme_generation_task(task)]

        if len(subtasks) < original_subtask_count:
            await self._display_message("Filtered out non-essential subtasks (e.g., README generation).", "info")

        await self._display_message("Instruction decomposed into the following subtasks:", "info")
        if not subtasks:
            await self._display_message("No executable subtasks remain after filtering. Aborting task.", "warning")
            return False

        for i, subtask in enumerate(subtasks):
            await log_debug(f"Subtask {i+1}: {subtask}")
            await self._display_message(f"  {i+1}. {subtask}", "response")
            
            # Store each subtask in memory
            await self.memory_service.store_memory(
                content={"type": "subtask_generated", "subtask": subtask, "parent_instruction": high_level_instruction},
                tags=["agent_task", "subtask"]
            )

        # 3. Execute subtasks sequentially
        await self._display_message("Starting subtask execution...", "info")
        await log_debug("Starting subtask execution")
        task_successful = True
        for i, subtask in enumerate(subtasks):
            message = f"\n--- Executing Subtask {i+1}/{len(subtasks)}: '{subtask}' ---"
            await self._display_message(message, "info")
            await log_debug(message)

            try:
                # Determine the type of subtask and delegate to ExecutionManager or other services.
                # This is a simplified parsing. A more robust agent might use an LLM to map subtasks to tools.
                subtask_parts = shlex.split(subtask)
                command_name = subtask_parts[0].lower() if subtask_parts else ""
                subtask_args = subtask_parts[1:]

                subtask_status = False  # Assume failure until proven otherwise

                if command_name == "read":
                    if subtask_args:
                        file_path_to_read = subtask_args[0]
                        # Try to read the file first.
                        await log_debug(f"Attempting to read file: '{file_path_to_read}'")
                        content = await self.execution_manager.read_file_api(file_path_to_read)
                        if content is not None:
                            subtask_status = True
                        # If read fails (e.g., 404 Not Found) and we have code in memory,
                        # it's likely the plan missed a 'write' step. Let's fix that.
                        elif self.last_generated_code:
                            await self._display_message(f"Read failed for '{file_path_to_read}'. Attempting to write from memory before retrying.", "debug")
                            await log_debug(f"Read failed, attempting to write from memory: '{file_path_to_read}'")
                            # Write the file from memory
                            write_success = await self.execution_manager.write_file_api(file_path_to_read, self.last_generated_code)
                            if write_success:
                                await self._display_message(f"Successfully wrote '{file_path_to_read}' from memory. Considering 'read' task complete.", "debug")
                                self.last_generated_code = None  # Consume the code
                                # The write was successful, so we consider the subtask complete without a redundant re-read.
                                subtask_status = True
                                await log_debug(f"Successfully wrote '{file_path_to_read}' from memory.")
                            else:
                                # The write operation itself failed.
                                subtask_status = False
                        else:
                            # The read failed and there's no code in memory to help.
                            subtask_status = False
                    else:
                        await self._display_message("Subtask 'read' requires a file path.", "warning")
                elif command_name == "write":
                    if len(subtask_args) >= 2:
                        file_path = subtask_args[0]
                        content = " ".join(subtask_args[1:])

                        # NEW: Check for placeholder content and use in-memory code if available
                        if "Here is the code from the previous step" in content and self.last_generated_code:
                            await self._display_message(f"Detected placeholder. Using recently generated code for '{file_path}'.", "debug")
                            content = self.last_generated_code
                            self.last_generated_code = None  # Consume the code so it's not used again
                            await log_debug(f"Using in-memory code for write operation to: '{file_path}'")

                        subtask_status = await self.execution_manager.write_file_api(file_path, content)
                    else:
                        await self._display_message("Subtask 'write' requires a file path and content.", "warning")
                elif command_name == "list":
                    subtask_status = await self.execution_manager.list_files_api(subtask_args[0] if subtask_args else './') is not None
                elif command_name == "exec":
                    if subtask_args:
                        return_code, _, _ = await self.execution_manager.execute_shell_command(shlex.join(subtask_args))
                        subtask_status = (return_code == 0)
                    else:
                        await self._display_message("Subtask 'exec' requires a command string.", "warning")
                elif command_name == "unit_tester":
                    await log_debug(f"Executing unit tests for: {subtask_args[0] if subtask_args else 'unknown file'}")
                    if subtask_args:
                        # This method already includes self-correction logic
                        subtask_status = await self.execution_manager.manage_unit_tests_and_correction(
                            subtask_args[0], await self.memory_service.retrieve_context(num_recent=10, query={"user_id": self.current_user_id})
                        )
                    else:
                        await self._display_message("Subtask 'unit_tester' requires a file path.", "warning")
                elif command_name == "generate_code":
                    if len(subtask_args) >= 1:  # Can now be called with just a prompt
                        prompt = subtask_args[0]
                        # Handle optional output file
                        output_file = subtask_args[1] if len(subtask_args) >= 2 else None

                        if output_file:
                            await self._display_message(f"Generating code with prompt: '{prompt}' and saving to '{output_file}'...", "info")
                        else:
                            await self._display_message(f"Generating code with prompt: '{prompt}' (in-memory)...", "info")
                        await log_debug(f"Generating code. Prompt: '{prompt}', Output File: '{output_file or 'in-memory'}'")

                        # Re-initialize user profile manager for this specific task to get fresh data
                        user_profile_manager = UserProfile(session_id=self.current_session_id, user_id=self.current_user_id, memory_service=self.memory_service)
                        await user_profile_manager.initialize()
                        user_profile_data = user_profile_manager.profile.model_dump() if user_profile_manager.profile else {}

                        # Retrieve recent context from memory to aid generation. This is crucial for multi-step tasks
                        # where one generation step depends on the output of a previous one (e.g., writing a test for new code).
                        recent_context = await self.memory_service.retrieve_context(
                            num_recent=15,  # Providing a larger context window
                            query={"user_id": self.current_user_id}
                        )

                        generated_code = await self.code_generator.generate_code(
                            prompt=prompt,  
                            output_file=output_file,  # Will be None if not provided
                            user_profile=user_profile_data,
                            context=recent_context  # Pass the retrieved context to the generator
                        )

                        if generated_code and not generated_code.startswith("# Error"):
                            if output_file:
                                await self._display_message(f"Code generated and saved to '{output_file}'.", "success")
                                # Store the generated content in memory for potential use by subsequent subtasks
                                await self.memory_service.store_memory(
                                    content={"type": "generated_code", "file_path": output_file, "content": generated_code},
                                    tags=["agent_task", "code_generation", "file_content"]
                                )
                                await log_debug(f"Code generated and saved to: '{output_file}'")
                            else:
                                # NEW: Store in agent's state if no output file
                                self.last_generated_code = generated_code
                                await self._display_message("Code generated and stored in memory for the next step.", "success")

                            subtask_status = True
                        else:
                            await self._display_message(f"Code generation failed for prompt: '{prompt}'.", "error")
                            subtask_status = False
                    else:
                        await self._display_message("Subtask 'generate_code' requires at least a prompt.", "warning")
                else:
                    await self._display_message(f"Agent does not know how to handle subtask command: '{command_name}'.", "error")
                    subtask_status = False  # Mark as failure

            except ValueError as e:
                error_message = f"Error parsing subtask '{subtask}': {e}. Please check for correct syntax and quoting."
                await self._display_message(error_message, "error")
                subtask_status = False

            if subtask_status:
                await self._display_message(f"Subtask '{subtask}' completed successfully.", "success")
                await self.memory_service.store_memory(
                    content={"type": "subtask_completed", "subtask": subtask, "status": "success"},
                    tags=["agent_task", "subtask_success"]
                )
            else:
                await self._display_message(f"Subtask '{subtask}' failed.", "error")
                await self.memory_service.store_memory(
                    content={"type": "subtask_completed", "subtask": subtask, "status": "failure"},
                    tags=["agent_task", "subtask_failure"]
                )
                task_successful = False
                # Agent could implement more sophisticated retry/re-plan logic here
                break # For now, break on first subtask failure

        if task_successful:
            await self._display_message(f"High-level instruction '{high_level_instruction}' completed successfully!", "success")
            await self.memory_service.store_memory(
                content={"type": "high_level_task_outcome", "instruction": high_level_instruction, "status": "success"},
                tags=["agent_task", "task_success"]
            )
        else:
            await self._display_message(f"High-level instruction '{high_level_instruction}' failed during execution.", "error")
            await self.memory_service.store_memory(
                content={"type": "high_level_task_outcome", "instruction": high_level_instruction, "status": "failure"},
                tags=["agent_task", "task_failure"]
            )
        
        return task_successful
