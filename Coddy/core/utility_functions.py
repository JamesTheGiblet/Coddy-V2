# Coddy/core/utility_functions.py
import os
import asyncio
import aiofiles # For asynchronous file I/O
import subprocess # For executing external commands
import sys

# Define base project directory relative to where this script might be run
# Adjust this if your execution context differs significantly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

async def safe_path(relative_path: str) -> str:
    """
    Constructs a safe, absolute path within the Coddy project root.
    Prevents directory traversal attacks by ensuring the resulting path
    is always a child of the project root.

    Args:
        relative_path: The path relative to the Coddy project root.

    Returns:
        The validated absolute path.

    Raises:
        ValueError: If the path attempts to go outside the project root.
    """
    abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, relative_path))

    # Ensure the path is within the project root
    if not abs_path.startswith(PROJECT_ROOT):
        raise ValueError(f"Attempted path '{relative_path}' is outside the project root.")
    return abs_path

async def read_file(file_path: str) -> str:
    """
    Asynchronously reads the content of a specified file.

    Args:
        file_path: The path to the file to read (relative to project root).

    Returns:
        The content of the file as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: For other file I/O errors.
    """
    absolute_path = await safe_path(file_path)
    try:
        async with aiofiles.open(absolute_path, mode='r', encoding='utf-8') as f:
            content = await f.read()
            return content
    except FileNotFoundError:
        print(f"Error: File not found at '{absolute_path}'")
        raise
    except Exception as e:
        print(f"Error reading file '{absolute_path}': {e}")
        raise

async def write_file(file_path: str, content: str) -> None:
    """
    Asynchronously writes content to a specified file.
    Creates parent directories if they don't exist.

    Args:
        file_path: The path to the file to write (relative to project root).
        content: The string content to write to the file.

    Raises:
        IOError: For file I/O errors.
    """
    absolute_path = await safe_path(file_path)
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
    try:
        async with aiofiles.open(absolute_path, mode='w', encoding='utf-8') as f:
            await f.write(content)
        print(f"Successfully wrote to '{absolute_path}'")
    except Exception as e:
        print(f"Error writing to file '{absolute_path}': {e}")
        raise

async def list_files(directory_path: str = './') -> list[str]:
    """
    Asynchronously lists files and directories within a specified directory.

    Args:
        directory_path: The path to the directory to list (relative to project root).

    Returns:
        A list of strings, where each string is the name of a file or directory.

    Raises:
        FileNotFoundError: If the directory does not exist.
        IOError: For other file I/O errors.
    """
    absolute_path = await safe_path(directory_path)
    try:
        if not os.path.isdir(absolute_path):
            raise FileNotFoundError(f"Directory not found: '{absolute_path}'")
        return os.listdir(absolute_path)
    except FileNotFoundError:
        print(f"Error: Directory not found at '{absolute_path}'")
        raise
    except Exception as e:
        print(f"Error listing directory '{absolute_path}': {e}")
        raise

async def execute_command(command: str, cwd: str = PROJECT_ROOT) -> tuple[int, str, str]:
    """
    Asynchronously executes a shell command.

    Args:
        command: The command string to execute.
        cwd: The current working directory for the command. Defaults to project root.

    Returns:
        A tuple containing:
        - The return code (int) of the command.
        - The standard output (str) of the command.
        - The standard error (str) of the command.

    Raises:
        subprocess.CalledProcessError: If the command returns a non-zero exit status.
        Exception: For other errors during command execution.
    """
    try:
        # Use asyncio.create_subprocess_shell for async execution
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        stdout, stderr = await process.communicate()

        return_code = process.returncode
        stdout_str = stdout.decode('utf-8').strip()
        stderr_str = stderr.decode('utf-8').strip()

        if return_code != 0:
            print(f"Command '{command}' failed with exit code {return_code}")
            print(f"STDOUT:\n{stdout_str}")
            print(f"STDERR:\n{stderr_str}")
            # Optionally raise an error for failed commands
            # raise subprocess.CalledProcessError(return_code, command, stdout=stdout, stderr=stderr)

        return return_code, stdout_str, stderr_str

    except Exception as e:
        print(f"Error executing command '{command}': {e}")
        raise

# Example Usage (for testing the utility functions)
async def main_test_utilities():
    print("\n--- Testing Core Utility Functions ---")

    # Test safe_path
    try:
        safe_p = await safe_path("tests/temp_file.txt")
        print(f"Safe path for 'tests/temp_file.txt': {safe_p}")
        # This should raise an error
        # await safe_path("../illegal_file.txt")
    except ValueError as e:
        print(f"Caught expected error for unsafe path: {e}")

    # Test write_file and read_file
    test_file = "data/test_file.txt"
    test_content = "Hello, Coddy! This is a test file."
    try:
        await write_file(test_file, test_content)
        read_content = await read_file(test_file)
        print(f"Read content from '{test_file}': '{read_content}' (Matches: {read_content == test_content})")
    except Exception as e:
        print(f"File R/W Test Failed: {e}")

    # Test list_files
    try:
        print(f"\nListing files in 'Coddy/core/': {await list_files('core/')}")
        print(f"Listing files in 'Coddy/backend/': {await list_files('backend/')}")
        print(f"Listing files in 'Coddy/data/': {await list_files('data/')}")
    except Exception as e:
        print(f"List Files Test Failed: {e}")

    # Test execute_command
    print("\nExecuting 'ls -l' in project root:")
    return_code, stdout, stderr = await execute_command('ls -l', cwd=PROJECT_ROOT)
    print(f"Return Code: {return_code}")
    print(f"STDOUT:\n{stdout}")
    if stderr:
        print(f"STDERR:\n{stderr}")

    print("\nExecuting 'echo Hello from Coddy command!'")
    return_code, stdout, stderr = await execute_command('echo Hello from Coddy command!')
    print(f"Return Code: {return_code}")
    print(f"STDOUT:\n{stdout}")
    if stderr:
        print(f"STDERR:\n{stderr}")

    print("\n--- End of Utility Function Tests ---")

if __name__ == "__main__":
    # To run this, you need to have aiofiles installed: pip install aiofiles
    # Ensure you run the `coddy_setup.py` first to create the directories.
    print("Ensure you have `aiofiles` installed (`pip install aiofiles`) and")
    print("the `Coddy` directory structure created before running this directly.")
    # Uncomment the line below to run the tests
    # asyncio.run(main_test_utilities())
