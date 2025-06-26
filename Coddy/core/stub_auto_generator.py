# Coddy/core/stub_auto_generator.py

import os
import asyncio
import re
from typing import List, Tuple, Optional

class StubAutoGenerator:
    """
    Analyzes Python files asynchronously to identify incomplete functions
    and adds inline # TODO: comments or basic stubs.
    Designed for non-blocking I/O operations to align with Coddy's async-first philosophy.
    """

    # Regex to find function definitions followed by no code or just 'pass', '...'
    # It attempts to capture the function signature and its current body indentation.
    INCOMPLETE_FUNCTION_PATTERN = re.compile(
        r"^(?P<indent>\s*)def\s+(?P<func_name>\w+)\s*\((?P<args>[^)]*)\):\s*$" # function definition
        r"(?!^\s*#\s*TODO:.*$)" # Exclude if it already has a TODO immediately after
        r"(?!^\s*(?:return|raise|yield|pass|...)(?:\s*#.*)?$)", # Exclude if it has a return/raise/yield/pass/... statement
        re.MULTILINE | re.DOTALL
    )
    # This pattern specifically targets functions ending with just 'pass' or '...' for replacement
    PASS_OR_ELLIPSIS_PATTERN = re.compile(
        r"^(?P<indent>\s*)(?:pass|\.{3})\s*(#.*)?$", re.MULTILINE
    )

    async def _read_file_async(self, file_path: str) -> Optional[str]:
        """Asynchronously reads the content of a file."""
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._sync_read_file, file_path)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def _sync_read_file(self, file_path: str) -> str:
        """Synchronous helper for file reading, to be run in executor."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    async def _write_file_async(self, file_path: str, content: str):
        """Asynchronously writes content to a file."""
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._sync_write_file, file_path, content)
        except Exception as e:
            print(f"Error writing to file {file_path}: {e}")

    def _sync_write_file(self, file_path: str, content: str):
        """Synchronous helper for file writing, to be run in executor."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content) # Corrected line from previous interaction

    def _generate_stub(self, indent: str, func_name: str, args: str) -> str:
        """Generates a Python stub based on the function's indentation and signature."""
        stub_indent = indent + "    " # Add one level of indentation for the stub body
        # Basic stub structure
        stub = f"{stub_indent}# TODO: Implement functionality for {func_name}\n"
        stub += f"{stub_indent}# Parameters: {args if args else 'None'}\n"
        stub += f"{stub_indent}pass\n" # Always end with pass to ensure valid syntax
        return stub

    async def process_file(self, file_path: str) -> bool:
        """
        Asynchronously processes a single Python file to add or update stubs.
        Returns True if the file was modified, False otherwise.
        """
        if not file_path.endswith('.py') or not os.path.exists(file_path):
            return False

        original_content = await self._read_file_async(file_path)
        if original_content is None:
            return False

        updated_content = []
        lines = original_content.splitlines()
        modified = False
        i = 0
        while i < len(lines):
            line = lines[i]
            match = self.INCOMPLETE_FUNCTION_PATTERN.match(line)
            if match:
                # Add the function definition line
                updated_content.append(line)
                indent = match.group('indent')
                func_name = match.group('func_name')
                args = match.group('args')

                # Check the next line for immediate 'pass' or '...' or empty line
                if i + 1 < len(lines):
                    next_line_stripped = lines[i+1].strip()
                    next_line_indent = lines[i+1].split(next_line_stripped)[0] if next_line_stripped else ''

                    if not next_line_stripped or self.PASS_OR_ELLIPSIS_PATTERN.match(lines[i+1]):
                        # If the next line is empty or just 'pass'/'...' with correct indentation
                        if len(next_line_indent) == len(indent) + 4: # Standard 4-space indentation
                             # Replace or add stub
                            stub = self._generate_stub(indent, func_name, args)
                            updated_content.extend(stub.strip().splitlines()) # Add stub lines
                            modified = True
                            if next_line_stripped: # If it was 'pass' or '...' skip original next line
                                i += 1
                        else: # If indentation is off, just add a TODO, don't replace
                            updated_content.append(f"{indent}    # TODO: Implement {func_name} - indentation might be off here.\n")
                            modified = True
                    else: # If there's actual code or comments immediately after, just add a TODO above it
                        updated_content.append(f"{indent}    # TODO: Implement {func_name}\n")
                        modified = True
                else: # If it's the last line of the file and an incomplete function
                    stub = self._generate_stub(indent, func_name, args)
                    updated_content.extend(stub.strip().splitlines())
                    modified = True
            else:
                updated_content.append(line)
            i += 1

        if modified:
            new_content = "\n".join(updated_content)
            if new_content != original_content:
                await self._write_file_async(file_path, new_content)
                print(f"Stubbed incomplete functions in: {file_path}")
                return True
        return False

    async def scan_directory(self, directory_path: str) -> List[str]:
        """
        Asynchronously scans a directory for Python files and processes them.
        Returns a list of file paths that were modified.
        """
        modified_files = []
        # Store (coroutine, file_path) pairs
        tasks_with_paths = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    tasks_with_paths.append((self.process_file(file_path), file_path))

        # Separate tasks and paths for asyncio.gather
        tasks = [task for task, _ in tasks_with_paths]
        file_paths_order = [path for _, path in tasks_with_paths]

        results = await asyncio.gather(*tasks)

        for i, was_modified in enumerate(results):
            if was_modified:
                modified_files.append(file_paths_order[i]) # Use the stored file path
        
        return modified_files
