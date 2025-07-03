# tests/test_cli_integration_tests.py
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock 
import sys
from io import StringIO
from pathlib import Path 
import httpx

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ui.cli import handle_instruction 

@pytest.fixture
def mock_display_message():
    with patch('ui.cli.display_message', new_callable=AsyncMock) as mock_dm:
        yield mock_dm

@pytest.fixture
def mock_input():
    with patch('builtins.input', new_callable=AsyncMock) as mock_in:
        yield mock_in

# Test for 'read' command success (still using fixture for httpx.AsyncClient as it's not explicitly requested to change)
@pytest.mark.asyncio
@patch('ui.cli.httpx.AsyncClient') # This patch is for this specific test, not the global fixture one
async def test_cli_read_success(mock_async_client, mock_display_message):
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value={"content": "Mock file content."})
    mock_response.raise_for_status = AsyncMock(return_value=None) 
    
    mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response

    await handle_instruction("read test_file.txt")

    mock_async_client.return_value.__aenter__.return_value.get.assert_awaited_once_with(
        "http://127.0.0.1:8000/api/files/read", params={"path": "test_file.txt"}
    )
    mock_display_message.assert_any_call(
        "Content of 'test_file.txt':\n---\nMock file content.\n---", "response"
    )
    mock_display_message.assert_any_call(
        "Successfully read 'test_file.txt'.", "success"
    )
    mock_display_message.assert_any_call("Coddy> read test_file.txt", "info")


# Test for 'read' command file not found error - Patching as decorators as requested
@pytest.mark.asyncio
@patch('ui.cli.httpx.AsyncClient') # Patch the class directly
@patch('ui.cli.display_message', new_callable=AsyncMock) # Patch display_message
async def test_cli_read_file_not_found(mock_display_message, mock_httpx_async_client_class): # Order matters for decorators
    # Recreate the context manager setup manually as per patching httpx.AsyncClient directly
    mock_client_instance_for_context = AsyncMock() 
    mock_httpx_async_client_class.return_value = mock_client_instance_for_context

    mock_context_manager_instance = AsyncMock() 
    mock_client_instance_for_context.__aenter__.return_value = mock_context_manager_instance
    # Ensure __aexit__ is also an awaitable mock
    mock_client_instance_for_context.__aexit__.return_value = AsyncMock() 

    # Create a specific mock response object to be used inside the HTTPStatusError
    # This mock will have an awaitable .json() method
    mock_error_response_in_exception = MagicMock(spec=httpx.Response)
    mock_error_response_in_exception.status_code = 404
    # The .json() method on an httpx.Response is sync, not async
    mock_error_response_in_exception.json = MagicMock(return_value={"detail": "File not found: non_existent.txt"})
    
    # Configure the response returned by client.get for this error scenario
    # The response object itself is synchronous, even if returned from an async method.
    mock_response_from_get_call = MagicMock(spec=httpx.Response)
    mock_response_from_get_call.status_code = 404
    # Set its raise_for_status to raise the HTTPStatusError with our custom mock_error_response
    mock_response_from_get_call.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", 
        request=httpx.Request("GET", "http://example.com"), 
        response=mock_error_response_in_exception # Pass the specially crafted mock here
    )

    # Use the manually configured context manager instance for get
    mock_context_manager_instance.get.return_value = mock_response_from_get_call 

    await handle_instruction("read non_existent.txt")

    mock_context_manager_instance.get.assert_awaited_once_with(
        "http://127.0.0.1:8000/api/files/read", params={"path": "non_existent.txt"}
    )
    mock_display_message.assert_any_call(
        "API Error reading 'non_existent.txt': File not found: non_existent.txt", "error"
    )

# Test for 'write' command success (still using fixture)
@pytest.mark.asyncio
@patch('ui.cli.httpx.AsyncClient')
async def test_cli_write_success(mock_async_client, mock_display_message):
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value={"message": "Successfully wrote to new_file.txt"}) 
    mock_response.raise_for_status = AsyncMock(return_value=None) 

    mock_async_client.return_value.__aenter__.return_value.post.return_value = mock_response

    await handle_instruction("write new_file.txt Some content here.")

    mock_async_client.return_value.__aenter__.return_value.post.assert_awaited_once_with(
        "http://127.0.0.1:8000/api/files/write", json={"path": "new_file.txt", "content": "Some content here."}
    )
    mock_display_message.assert_any_call(
        "Successfully wrote content to 'new_file.txt'.", "success"
    )


# Test for 'list' command success (still using fixture)
@pytest.mark.asyncio
@patch('ui.cli.httpx.AsyncClient')
async def test_cli_list_success(mock_async_client, mock_display_message):
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = AsyncMock(return_value={"items": ["file1.txt", "dir1/", "file2.py"]})
    mock_response.raise_for_status = AsyncMock(return_value=None)

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
    with patch('ui.cli.memory_service') as mock_ms: 
        mock_ms.store_memory = AsyncMock()
        await handle_instruction("unrecognized_command arg1")
        mock_display_message.assert_any_call(
            "Unknown instruction: 'unrecognized_command'. Type 'help' for available commands.", "warning"
        )
        mock_ms.store_memory.assert_awaited_once()