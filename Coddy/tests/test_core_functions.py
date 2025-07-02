# Coddy/tests/test_core_functions.py
import unittest
import asyncio
import os
import sys
import shutil
from unittest.mock import patch, AsyncMock, MagicMock

import aiofiles
from core.utility_functions import (PROJECT_ROOT, execute_command,
                                            list_files, read_file, safe_path,
                                            write_file)
from ui.cli import handle_instruction

class TestCoreUtilityFunctions(unittest.IsolatedAsyncioTestCase):
    """
    Unit tests for core utility functions: safe_path, read_file, write_file,
    list_files, execute_command.
    """
    temp_dir = os.path.join(PROJECT_ROOT, "temp_test_data")
    test_file_path = "temp_test_data/test_file.txt"
    test_content = "This is a test content string."

    @classmethod
    def setUpClass(cls):
        """Create a temporary directory for file tests."""
        os.makedirs(cls.temp_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        """Clean up the temporary directory after all tests."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)

    async def asyncSetUp(self):
        """Ensure test file is clean before each test by deleting if exists."""
        full_path = os.path.join(PROJECT_ROOT, self.test_file_path)
        if os.path.exists(full_path):
            os.remove(full_path)

    async def test_safe_path(self):
        """Test safe_path function for valid and invalid paths."""
        valid_path = await safe_path("core/utility_functions.py")
        self.assertTrue(valid_path.startswith(PROJECT_ROOT))
        self.assertIn("utility_functions.py", valid_path)

        with self.assertRaises(ValueError):
            await safe_path("../../../some_illegal_path.txt") # Attempt to break out

    async def test_write_and_read_file(self):
        """Test write_file and read_file functions."""
        full_test_path = os.path.join(PROJECT_ROOT, self.test_file_path)

        # Test write_file
        await write_file(self.test_file_path, self.test_content)
        self.assertTrue(os.path.exists(full_test_path))

        # Test read_file
        read_data = await read_file(self.test_file_path)
        self.assertEqual(read_data, self.test_content)

        # Test reading non-existent file
        with self.assertRaises(FileNotFoundError):
            await read_file("non_existent_file.txt")

    async def test_list_files(self):
        """Test list_files function."""
        # Ensure test_file.txt and dummy.log exist for this test
        await write_file(self.test_file_path, "content") # Ensure test_file.txt is present for this test
        dummy_file = os.path.join(self.temp_dir, "dummy.log")
        async with aiofiles.open(dummy_file, "w") as f: # Use aiofiles for consistency
            await f.write("dummy content")

        listed_items = await list_files("temp_test_data")
        self.assertIn("test_file.txt", listed_items)
        self.assertIn("dummy.log", listed_items)
        self.assertIsInstance(listed_items, list)

        with self.assertRaises(FileNotFoundError):
            await list_files("non_existent_directory/")

    @patch('asyncio.create_subprocess_shell')
    async def test_execute_command(self, mock_create_subprocess_shell):
        """Test execute_command function with mocked subprocess."""
        # Mock a successful command execution
        mock_process = MagicMock()
        # Communicate needs to be an AsyncMock as it's awaited
        mock_process.communicate = AsyncMock(return_value=(b"mock stdout", b"mock stderr"))
        mock_process.returncode = 0
        mock_create_subprocess_shell.return_value = mock_process

        return_code, stdout, stderr = await execute_command("echo Hello")

        self.assertEqual(return_code, 0)
        self.assertEqual(stdout, "mock stdout")
        self.assertEqual(stderr, "mock stderr")
        mock_create_subprocess_shell.assert_called_once_with(
            "echo Hello",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=PROJECT_ROOT
        )

        # Mock a failed command execution
        mock_process_fail = MagicMock()
        mock_process_fail.communicate = AsyncMock(return_value=(b"", b"Error: Command failed"))
        mock_process_fail.returncode = 1
        mock_create_subprocess_shell.return_value = mock_process_fail
        mock_create_subprocess_shell.reset_mock() # Reset mock call count

        return_code_fail, stdout_fail, stderr_fail = await execute_command("false_command")
        self.assertEqual(return_code_fail, 1)
        self.assertEqual(stderr_fail, "Error: Command failed")


class TestCliInterface(unittest.IsolatedAsyncioTestCase):
    """
    Integration tests for the basic CLI interface (handle_instruction).
    Mocks standard I/O and file system interactions for isolation.
    """

    async def asyncSetUp(self):
        """Set up mocks for file operations and services."""
        # Patch the websocket sender to capture all output messages.
        patch_websocket = patch('ui.cli.send_to_websocket_server', new_callable=AsyncMock)
        self.mock_send_to_websocket_server = patch_websocket.start()
        self.addCleanup(patch_websocket.stop)

        # Patch services to avoid "not initialized" warnings and allow for testing interactions.
        patch_memory_service = patch('ui.cli.memory_service', new_callable=MagicMock)
        self.mock_memory_service = patch_memory_service.start()
        self.mock_memory_service.store_memory = AsyncMock()
        self.addCleanup(patch_memory_service.stop)

        patch_vibe_engine = patch('ui.cli.vibe_engine', new_callable=MagicMock)
        self.mock_vibe_engine = patch_vibe_engine.start()
        self.mock_vibe_engine.update_activity = AsyncMock()
        self.addCleanup(patch_vibe_engine.stop)
        
        # Mock the httpx.AsyncClient to intercept API calls from the CLI
        patch_httpx = patch('ui.cli.httpx.AsyncClient', new_callable=MagicMock)
        self.mock_async_client_class = patch_httpx.start()
        self.addCleanup(patch_httpx.stop)

        # Configure the mock client instance and its context manager
        self.mock_async_client_instance = self.mock_async_client_class.return_value
        self.mock_async_client_context = self.mock_async_client_instance.__aenter__.return_value

        # Mock for the 'exec' command remains the same
        self.mock_execute_command = AsyncMock(return_value=(0, "cmd output", ""))
        patch_exec = patch('ui.cli.execute_command', self.mock_execute_command)
        patch_exec.start()
        self.addCleanup(patch_exec.stop)

    async def test_handle_read_command(self):
        """Test `read` command in CLI."""
        # Configure mock response for the read API call
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"content": "file content"}
        self.mock_async_client_context.get = AsyncMock(return_value=mock_response)

        await handle_instruction("read test.txt")

        self.mock_async_client_context.get.assert_awaited_once_with(
            "http://127.0.0.1:8000/api/files/read", params={"path": "test.txt"}
        )
        sent_messages = [call.args[0]['text'] for call in self.mock_send_to_websocket_server.call_args_list]
        all_output = "\n".join(sent_messages)
        self.assertIn("Coddy> read test.txt", all_output)
        self.assertIn("Content of 'test.txt':\n---\nfile content\n---", all_output)
        self.assertIn("Successfully read 'test.txt'.", all_output)

    async def test_handle_write_command(self):
        """Test `write` command in CLI."""
        # Configure mock response for the write API call
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        self.mock_async_client_context.post = AsyncMock(return_value=mock_response)

        await handle_instruction("write new_file.txt Some content here.")

        self.mock_async_client_context.post.assert_awaited_once_with(
            "http://127.0.0.1:8000/api/files/write", json={"path": "new_file.txt", "content": "Some content here."}
        )
        sent_messages = [call.args[0]['text'] for call in self.mock_send_to_websocket_server.call_args_list]
        all_output = "\n".join(sent_messages)
        self.assertIn("Coddy> write new_file.txt Some content here.", all_output)
        self.assertIn("Successfully wrote content to 'new_file.txt'.", all_output)

    async def test_handle_list_command(self):
        """Test `list` command in CLI."""
        # Configure mock response for the list API call
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"items": ["file1.txt", "dir1/"]}
        self.mock_async_client_context.get = AsyncMock(return_value=mock_response)

        await handle_instruction("list my_dir/")

        self.mock_async_client_context.get.assert_awaited_once_with(
            "http://127.0.0.1:8000/api/files/list", params={"path": "my_dir/"}
        )
        sent_messages = [call.args[0]['text'] for call in self.mock_send_to_websocket_server.call_args_list]
        all_output = "\n".join(sent_messages)
        self.assertIn("Coddy> list my_dir/", all_output)
        self.assertIn("Files and directories in 'my_dir/':", all_output)
        self.assertIn("- file1.txt", all_output)

    async def test_handle_exec_command(self):
        """Test `exec` command in CLI."""
        await handle_instruction("exec echo hello")
        self.mock_execute_command.assert_called_once_with("echo hello")
        sent_messages = [call.args[0]['text'] for call in self.mock_send_to_websocket_server.call_args_list]
        all_output = "\n".join(sent_messages)
        self.assertIn("Coddy> exec echo hello", all_output)
        self.assertIn("Command 'echo hello' executed.", all_output)
        self.assertIn("STDOUT:\ncmd output", all_output)

    async def test_handle_unknown_command(self):
        """Test unknown command in CLI."""
        await handle_instruction("unrecognized_command arg1 arg2")
        sent_messages = [call.args[0]['text'] for call in self.mock_send_to_websocket_server.call_args_list]
        all_output = "\n".join(sent_messages)
        self.assertIn("Coddy> unrecognized_command arg1 arg2", all_output)
        self.assertIn("Unknown instruction: 'unrecognized_command'. Type 'help' for available commands.", all_output)

    @patch('sys.exit')
    async def test_handle_exit_command(self, mock_exit):
        """Test `exit` command in CLI."""
        await handle_instruction("exit")
        mock_exit.assert_called_once_with(0)
        sent_messages = [call.args[0]['text'] for call in self.mock_send_to_websocket_server.call_args_list]
        all_output = "\n".join(sent_messages)
        self.assertIn("Coddy> exit", all_output)
        self.assertIn("Exiting Coddy CLI. Goodbye!", all_output)


if __name__ == '__main__':
    # To run these tests:
    # 1. Ensure `aiofiles` is installed: `pip install aiofiles`
    # 2. Navigate to your project's root (where Coddy/ is located)
    # 3. Run: `python -m unittest discover tests`
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
