import os
import asyncio
import aiofiles
import sys
from datetime import datetime
from typing import Optional

# Define base project directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Define Coddy_code customer-facing base directory
CUSTOMER_CODE_BASE_DIR = os.path.normpath(os.path.join(PROJECT_ROOT, "..", "Coddy_code"))

async def safe_path(relative_path: str) -> str:
    abs_path = os.path.abspath(os.path.join(PROJECT_ROOT, relative_path))
    if not abs_path.startswith(PROJECT_ROOT):
        raise ValueError(f"Attempted path '{relative_path}' is outside the project root.")
    return abs_path

async def read_file(file_path: str) -> str:
    absolute_path = await safe_path(file_path)
    try:
        async with aiofiles.open(absolute_path, mode='r', encoding='utf-8') as f:
            return await f.read()
    except FileNotFoundError:
        print(f"Error: File not found at '{absolute_path}'")
        raise
    except Exception as e:
        print(f"Error reading file '{absolute_path}': {e}")
        raise

async def write_file(file_path: str, content: str) -> None:
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

async def list_files_in_directory_recursive(directory_path: str) -> list[str]:
    absolute_path = await safe_path(directory_path)
    try:
        if not os.path.isdir(absolute_path):
            raise FileNotFoundError(f"Directory not found: '{absolute_path}'")
        all_files = []
        for root, _, files in os.walk(absolute_path):
            for name in files:
                file_abs_path = os.path.join(root, name)
                relative_to_root = os.path.relpath(file_abs_path, PROJECT_ROOT)
                all_files.append(relative_to_root.replace('\\', '/'))
        return all_files
    except FileNotFoundError:
        print(f"Error: Directory not found at '{absolute_path}'")
        raise
    except Exception as e:
        print(f"Error listing directory recursively '{absolute_path}': {e}")
        raise

# === New Coddy_code Helpers ===

async def save_generated_code(content: str, filename: str):
    """Save AI-generated code to Coddy_code/Auto_gen_code/"""
    target_path = os.path.join("Coddy_code", "Auto_gen_code", filename)
    await write_file(target_path, content)

async def save_refactored_code(content: str, filename: str):
    """Save refactored code to Coddy_code/Refactored_code/"""
    target_path = os.path.join("Coddy_code", "Refactored_code", filename)
    await write_file(target_path, content)

async def save_written_code(content: str, filename: str):
    """Save user-written code to Coddy_code/Written_code/"""
    target_path = os.path.join("Coddy_code", "Written_code", filename)
    await write_file(target_path, content)

async def save_test_code(content: str, filename: str):
    """Save test code to Coddy_code/Test_code/"""
    target_path = os.path.join("Coddy_code", "Test_code", filename)
    await write_file(target_path, content)

async def save_to_coddy_code_folder(content: str, filename: str, category: str):
    """Dispatch save to correct Coddy_code subfolder by category."""
    folder_map = {
        "auto": "Auto_gen_code",
        "refactor": "Refactored_code",
        "write": "Written_code",
        "test": "Test_code"
    }
    if category not in folder_map:
        raise ValueError(f"Invalid category '{category}'. Must be one of {list(folder_map.keys())}")
    target_path = os.path.join("Coddy_code", folder_map[category], filename)
    await write_file(target_path, content)

# === Existing save_generated_file (for documentation etc) ===

async def save_generated_file(content: str, file_name: str, category: str, project_name: Optional[str] = None):
    try:
        base_output_dir = "generated_output"
        if project_name:
            target_dir = os.path.join(base_output_dir, project_name)
            full_file_path = os.path.join(target_dir, file_name)
            print(f"Saving to project-specific directory: {target_dir}")
        else:
            file_name_without_ext = os.path.splitext(file_name)[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            category_dir = os.path.join(base_output_dir, category)
            target_dir = os.path.join(category_dir, f"{file_name_without_ext}_{timestamp}")
            full_file_path = os.path.join(target_dir, file_name)
            print(f"Saving to timestamped category directory: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)
        await write_file(full_file_path, content)
        print(f"File saved to {full_file_path}")
    except Exception as e:
        print(f"Error saving file '{file_name}' in category '{category}' (Project: {project_name}): {e}")
        raise

# === Optional CLI Test Driver ===

async def main_test_utilities():
    print("\n--- Testing Core Utility Functions ---")

    # Test write/read
    test_file = "data/test_file.txt"
    test_content = "Hello, Coddy! This is a test file."
    await write_file(test_file, test_content)
    read_back = await read_file(test_file)
    print(f"Read back: {read_back} == Original: {read_back == test_content}")

    # Save test files to Coddy_code folders
    await save_generated_code("# auto gen", "auto_example.py")
    await save_refactored_code("# refactored", "refactor_example.py")
    await save_written_code("# written", "written_example.py")
    await save_test_code("def test(): pass", "test_example.py")

    # Generic dispatcher
    await save_to_coddy_code_folder("print('dispatcher')", "dispatcher_example.py", "auto")

    # Save doc to generated_output
    await save_generated_file("This is a README", "README.md", "readmes", project_name="coddy_v2")

if __name__ == "__main__":
    print("Running Coddy utility function tests...")
    asyncio.run(main_test_utilities())
