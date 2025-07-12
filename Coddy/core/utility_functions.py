# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\utility_functions.py

import os
import asyncio
import aiofiles # For asynchronous file I/O
import sys
from datetime import datetime # NEW: Import datetime for timestamps

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

    dir_path = os.path.dirname(absolute_path)
    if dir_path and not os.path.exists(dir_path):
        try:
            os.makedirs(dir_path, exist_ok=True)
        except OSError as e:
            print(f"Failed to create directory for path '{absolute_path}': {e}")
            raise

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

async def save_file_in_timestamped_folder(content: str, file_path: str, category: str):
    """
    Saves content to a file within a timestamped directory, categorized by type.
    This function is designed to be generic for various generated outputs.
    
    Args:
        content (str): The content to save to the file.
        file_path (str): The desired filename, including its extension (e.g., "CHANGELOG.md").
        category (str): A string representing the category of the file (e.g., "changelogs", "roadmaps", "readmes", "requirements", "code").
    """
    try:
        # Extract filename from the provided file_path
        output_filename = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(output_filename)[0]

        # Generate a timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Define the base output directory
        base_output_dir = "generated_output" 

        # Create a category-specific subfolder
        category_dir = os.path.join(base_output_dir, category)

        # Create the timestamped directory within the category folder
        timestamped_dir = os.path.join(category_dir, f"{file_name_without_ext}_{timestamp}")
        os.makedirs(timestamped_dir, exist_ok=True)
        # log_info is not available directly here, use print for now
        print(f"Created directory: {timestamped_dir}")

        # Construct the full file path
        full_file_path = os.path.join(timestamped_dir, output_filename)

        await write_file(full_file_path, content)
        print(f"File saved to {full_file_path}")
    except Exception as e:
        print(f"Error saving file to {file_path} in category {category}: {e}")
        raise

# Removed execute_command function as it has been moved to core/execution_manager.py

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

    # Test save_file_in_timestamped_folder
    test_content_timestamped = "This content should be in a timestamped folder."
    try:
        await save_file_in_timestamped_folder(test_content_timestamped, "test_doc.md", "documents")
        await save_file_in_timestamped_folder("Another test for code.", "my_script.py", "code")
    except Exception as e:
        print(f"Timestamped Save Test Failed: {e}")

    print("\n--- End of Utility Function Tests ---")

if __name__ == "__main__":
    # To run this, you need to have aiofiles installed: pip install aiofiles
    # Ensure you run the `coddy_setup.py` first to create the directories.
    print("Ensure you have `aiofiles` installed (`pip install aiofiles`) and")
    print("the `Coddy` directory structure created before running this directly.")
    # Uncomment the line below to run the tests
    # asyncio.run(main_test_utilities())
