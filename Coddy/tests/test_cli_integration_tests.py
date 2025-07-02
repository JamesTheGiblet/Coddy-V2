# tests/test_cli_integration_tests.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import sys
from io import StringIO
from pathlib import Path # Import Path for path manipulation
import httpx
# Add the project root to sys.path to allow importing modules from the root.
# This assumes the test file is in 'coddy/tests/' and the main cli.py is in 'coddy/'.
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Corrected import path: assuming cli.py is directly in the project root
from cli import handle_instruction 

# Mock the API_BASE_URL for httpx calls in cli.py if needed,
# though the httpx.AsyncClient mock will intercept actual requests.
# You might need to set it if cli.py uses it directly for string formatting
# before the httpx call. For now, we'll rely on the httpx mock.

# Fixture to capture display_message output
@pytest.fixture
def mock_display_message():
    """Mocks the display_message function to capture output."""
    # The patch path should reflect where display_message is defined, which is cli.py
    with patch('cli.display_message', new_callable=AsyncMock) as mock_dm:
        yield mock_dm

# Fixture to mock the input function for interactive CLI
@pytest.fixture
def mock_input():
    """Mocks the built-in input function."""
    with patch('builtins.input', new_callable=AsyncMock) as mock_in:
        yield mock_in

# Test for 'read' command success
@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_cli_read_success(mock_async_client, mock_display_message):
    """
    Tests the 'read' CLI command with a successful API response.
    """
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"content": "Mock file content."}
    mock_response.raise_for_status.return_value = None # Ensure no exception is raised

    # Configure the mock AsyncClient to return our mock response
    mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response

    # Call the handle_instruction function directly
    await handle_instruction("read test_file.txt")

    # Assert that httpx.get was called correctly
    mock_async_client.return_value.__aenter__.return_value.get.assert_awaited_once_with(
        "http://127.0.0.1:8000/api/files/read", params={"path": "test_file.txt"}
    )

    # Assert that display_message was called with the correct output
    # Check for the content message
    mock_display_message.assert_any_call(
        "Content of 'test_file.txt':\n---\nMock file content.\n---", "response"
    )
    # Check for the success message
    mock_display_message.assert_any_call(
        "Successfully read 'test_file.txt'.", "success"
    )
    # Ensure the initial command echo is also there
    mock_display_message.assert_any_call("Coddy> read test_file.txt", "info")


# Test for 'read' command file not found error
@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_cli_read_file_not_found(mock_async_client, mock_display_message):
    """
    Tests the 'read' CLI command when the file is not found (404 API response).
    """
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.json.return_value = {"detail": "File not found: non_existent.txt"}
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=httpx.Request("GET", "http://example.com"), response=mock_response
    )

    mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response

    await handle_instruction("read non_existent.txt")

    mock_async_client.return_value.__aenter__.return_value.get.assert_awaited_once_with(
        "http://127.0.0.1:8000/api/files/read", params={"path": "non_existent.txt"}
    )
    mock_display_message.assert_any_call(
        "API Error reading 'non_existent.txt': File not found: non_existent.txt", "error"
    )

# Test for 'write' command success
@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_cli_write_success(mock_async_client, mock_display_message):
    """
    Tests the 'write' CLI command with a successful API response.
    """
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"message": "Successfully wrote to new_file.txt"}
    mock_response.raise_for_status.return_value = None

    mock_async_client.return_value.__aenter__.return_value.post.return_value = mock_response

    await handle_instruction("write new_file.txt Some content here.")

    mock_async_client.return_value.__aenter__.return_value.post.assert_awaited_once_with(
        "http://127.0.0.1:8000/api/files/write", json={"path": "new_file.txt", "content": "Some content here."}
    )
    mock_display_message.assert_any_call(
        "Successfully wrote content to 'new_file.txt'.", "success"
    )


# Test for 'list' command success
@pytest.mark.asyncio
@patch('httpx.AsyncClient')
async def test_cli_list_success(mock_async_client, mock_display_message):
    """
    Tests the 'list' CLI command with a successful API response.
    """
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": ["file1.txt", "dir1/", "file2.py"]}
    mock_response.raise_for_status.return_value = None

    mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response

    await handle_instruction("list .")

    mock_async_client.return_value.__aenter__.return_value.get.assert_awaited_once_with(
        "http://127.0.0.1:8000/api/files/list", params={"path": "."}
    )
    mock_display_message.assert_any_call(
        "Files and directories in '.':\n- file1.txt\n- dir1/\n- file2.py", "response"
    )
    mock_display_message.assert_any_call(
        "Successfully listed '.'.", "success"
    )

# Test for 'exit' command
@pytest.mark.asyncio
async def test_cli_exit_command(mock_display_message):
    """
    Tests that the 'exit' command correctly terminates the CLI.
    """
    with pytest.raises(SystemExit) as excinfo:
        await handle_instruction("exit")
    assert excinfo.value.code == 0
    mock_display_message.assert_any_call("Exiting Coddy CLI. Goodbye!", "info")

# Test for unknown command
@pytest.mark.asyncio
async def test_cli_unknown_command(mock_display_message):
    """
    Tests handling of an unrecognized command.
    """
    # Mock memory_service if it's used in the unknown command path
    # The patch path should reflect where memory_service is defined, which is cli.py
    with patch('cli.memory_service') as mock_ms: 
        mock_ms.store_memory = AsyncMock()
        await handle_instruction("unrecognized_command arg1")
        mock_display_message.assert_any_call(
            "Unknown instruction: 'unrecognized_command'. Type 'help' for available commands.", "warning"
        )
        mock_ms.store_memory.assert_awaited_once() # Ensure it tries to log the unknown command
