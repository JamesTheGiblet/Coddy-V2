# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\execution_manager.py
import asyncio
import sys
import os
import httpx
from pathlib import Path
import shlex
import datetime  # Import datetime for _display_message
from typing import Optional, List, Dict, Any

from Coddy.core.logging_utility import log_debug, log_error, log_info, log_warning
from Coddy.core.websocket_server import send_to_websocket_server
from Coddy.core.utility_functions import (
    save_test_code,
    save_refactored_code
)

# Forward declarations to avoid circular imports during type hinting
if sys.version_info >= (3, 9):
    from typing import TYPE_CHECKING
    if TYPE_CHECKING:
        from core.memory_service import MemoryService
        from core.vibe_mode import VibeModeEngine
        from core.code_generator import CodeGenerator

# Configuration
API_BASE_URL = os.getenv("CODY_API_BASE_URL", "http://127.0.0.1:8000")

async def execute_command(command: str) -> tuple[int, str, str]:
    await log_debug(f"Executing command: {command}")
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    return_code = process.returncode

    stdout_str = stdout.decode().strip()
    stderr_str = stderr.decode().strip()

    await log_debug(f"Command '{command}' finished with exit code {return_code}")
    if stdout_str:
        await log_debug(f"STDOUT:\n{stdout_str}")
    if stderr_str:
        await log_error(f"STDERR:\n{stderr_str}")

    return return_code, stdout_str, stderr_str

class ExecutionManager:
    def __init__(self, 
                 memory_service: 'MemoryService', 
                 vibe_engine: 'VibeModeEngine', 
                 code_generator: 'CodeGenerator',
                 current_user_id: str,
                 current_session_id: str):

        self.memory_service = memory_service
        self.vibe_engine = vibe_engine
        self.code_generator = code_generator
        self.current_user_id = current_user_id
        self.current_session_id = current_session_id

    async def _display_message(self, message: str, message_type: str = "info"):
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

    async def execute_shell_command(self, full_command: str) -> tuple[int, str, str]:
        try:
            return_code, stdout, stderr = await execute_command(full_command)
            await self._display_message(f"Command '{full_command}' executed.", "response")
            if stdout:
                await self._display_message(f"STDOUT:\n{stdout}", "response")
            if stderr:
                await self._display_message(f"STDERR:\n{stderr}", "error")
                await log_warning(f"Command '{full_command}' produced STDERR: {stderr}")
            if return_code != 0:
                await self._display_message(f"Command '{full_command}' failed with exit code {return_code}.", "error")
                await log_error(f"Command '{full_command}' failed with exit code {return_code}.")
            else:
                await self._display_message(f"Command '{full_command}' executed successfully.", "success")
            return return_code, stdout, stderr
        except Exception as e:
            await self._display_message(f"Error executing command '{full_command}': {e}", "error")
            await log_error(f"Exception during command execution: {full_command}", exc_info=True)
            return 1, "", str(e)

    async def read_file_api(self, file_path: str) -> Optional[str]:
        api_url = f"{API_BASE_URL}/api/files/read"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, params={"path": file_path})
                await response.raise_for_status()
                data = response.json()
                content = data.get("content", "")
                await self._display_message(f"Content of '{file_path}':\n---\n{content}\n---", "response")
                await self._display_message(f"Successfully read '{file_path}'.", "success")
                return content
        except httpx.HTTPStatusError as e:
            data = e.response.json()
            error_detail = data.get("detail", e.response.text)
            await self._display_message(f"API Error reading '{file_path}': {error_detail}", "error")
            await log_error(f"API Error reading file: {file_path}", exc_info=True)
            return None
        except httpx.RequestError:
            await self._display_message(f"Connection Error: Could not connect to Coddy API to read '{file_path}'. Is the server running?", "error")
            await log_error(f"Connection Error reading file: {file_path}", exc_info=True)
            return None
        except Exception as e:
            await self._display_message(f"An unexpected error occurred while reading '{file_path}': {e}", "error")
            await log_error(f"Unexpected error reading file: {file_path}", exc_info=True)
            return None

    async def write_file_api(self, file_path: str, content: str) -> bool:
        api_url = f"{API_BASE_URL}/api/files/write"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, json={"path": file_path, "content": content})
                await response.raise_for_status()
                await self._display_message(f"Successfully wrote content to '{file_path}'.", "success")
                return True
        except httpx.HTTPStatusError as e:
            data = e.response.json()
            error_detail = data.get("detail", e.response.text)
            await self._display_message(f"API Error writing to '{file_path}': {error_detail}", "error")
            await log_error(f"API Error writing file: {file_path}", exc_info=True)
            return False
        except httpx.RequestError:
            await self._display_message(f"Connection Error: Could not connect to Coddy API to write to '{file_path}'. Is the server running?", "error")
            await log_error(f"Connection Error writing file: {file_path}", exc_info=True)
            return False
        except Exception as e:
            await self._display_message(f"An unexpected error occurred while writing to '{file_path}': {e}", "error")
            await log_error(f"Unexpected error writing file: {file_path}", exc_info=True)
            return False

    async def list_files_api(self, directory_path: str = './') -> Optional[List[str]]:
        api_url = f"{API_BASE_URL}/api/files/list"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(api_url, params={"path": directory_path})
                await response.raise_for_status()
                data = response.json()
                items = data.get("items", [])
                item_list_str = "\n".join([f"- {item}" for item in items])
                await self._display_message(f"Files and directories in '{directory_path}':\n{item_list_str}", "response")
                await self._display_message(f"Successfully listed '{directory_path}'.", "success")
                return items
        except httpx.HTTPStatusError as e:
            data = e.response.json()
            error_detail = data.get("detail", e.response.text)
            await self._display_message(f"API Error listing '{directory_path}': {error_detail}", "error")
            await log_error(f"API Error listing directory: {directory_path}", exc_info=True)
            return None
        except httpx.RequestError:
            await self._display_message(f"Connection Error: Could not connect to Coddy API to list '{directory_path}'. Is the server running?", "error")
            await log_error(f"Connection Error listing directory: {directory_path}", exc_info=True)
            return None
        except Exception as e:
            await self._display_message(f"An unexpected error occurred while listing '{directory_path}': {e}", "error")
            await log_error(f"Unexpected error listing directory: {directory_path}", exc_info=True)
            return None

    async def manage_unit_tests_and_correction(self, file_path: str, session_context_memories: List[Dict[str, Any]]) -> bool:
        from Coddy.core.utility_functions import save_test_code
        await self._display_message(f"Initiating unit test management for '{file_path}'...", "info")

        try:
            original_file_content = await self.read_file_api(file_path)
            if original_file_content is None or not original_file_content.strip():
                await self._display_message(f"File '{file_path}' is empty or unreadable.", "warning")
                return False

            current_vibe = self.vibe_engine.get_current_vibe()
            context_for_generation = {
                "file_content": original_file_content,
                "vibe_mode": current_vibe,
                "recent_memories": session_context_memories
            }

            generated_tests_code = await self.code_generator.generate_unit_tests(
                file_path=file_path,
                context=context_for_generation
            )

            test_file_name = f"test_{Path(file_path).stem}.py"
            test_file_path = os.path.join("Coddy_code", "Test_code", test_file_name)
            if not generated_tests_code:
                await self._display_message(f"Failed to write generated tests to '{test_file_path}'.", "error")
                return False

            await save_test_code(generated_tests_code, test_file_name)
            await self._display_message(f"Generated unit tests saved to '{test_file_path}'.", "success")
            await self._display_message(f"Content of '{test_file_path}':\n---\n{generated_tests_code}\n---", "response")

            max_attempts = 3
            current_code_to_test = original_file_content

            for attempt in range(1, max_attempts + 1):
                await self._display_message(f"Attempt {attempt}/{max_attempts}: Running tests for '{file_path}' using pytest...", "info")
                return_code, stdout, stderr = await execute_command(f"pytest {test_file_path}")

                await self._display_message(f"Test run results:\nSTDOUT:\n{stdout}", "response")
                if stderr:
                    await self._display_message(f"STDERR:\n{stderr}", "error")
                    await log_warning(f"Pytest for '{test_file_path}' produced STDERR: {stderr}")

                if return_code == 0:
                    await self._display_message("Tests passed successfully! Code is good.", "success")
                    return True
                else:
                    await self._display_message(f"Tests failed with exit code {return_code}. Attempting self-correction...", "warning")
                    await log_error(f"Pytest for '{test_file_path}' failed with exit code {return_code}. Error: {stderr}")

                    if attempt < max_attempts:
                        await self._display_message("Generating a fix for the failed tests...", "info")
                        correction_context = {
                            "original_code": current_code_to_test,
                            "failed_test_output_stdout": stdout,
                            "failed_test_output_stderr": stderr,
                            "vibe_mode": current_vibe,
                            "recent_memories": session_context_memories,
                            "problem_description": f"Tests failed for {file_path}. Please provide a corrected version of the code that passes these tests."
                        }

                        corrected_code = await self.code_generator.generate_code_fix(
                            file_path=file_path,
                            context=correction_context
                        )

                        if corrected_code:
                            if not await self.write_file_api(file_path, corrected_code):
                                await self._display_message(f"Failed to apply fix to '{file_path}'.", "error")
                                return False
                            await self._display_message("Fix applied. Re-running tests for verification.", "info")
                            current_code_to_test = corrected_code
                        else:
                            await self._display_message("Code generator failed to provide a fix.", "error")
                            return False
                    else:
                        await self._display_message(f"Maximum correction attempts reached for '{file_path}'. Tests still failing.", "error")
                        return False

            return False

        except Exception as e:
            await self._display_message(f"An unexpected error occurred during unit test management for '{file_path}': {e}", "error")
            await log_error(f"Unit Test Management Error for '{file_path}': {e}", exc_info=True)
            return False
