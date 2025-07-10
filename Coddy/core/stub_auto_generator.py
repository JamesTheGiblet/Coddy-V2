# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\stub_auto_generator.py

from __future__ import annotations # NEW: Enable postponed evaluation of type annotations
from datetime import datetime
import os
import asyncio
import re
from typing import List, Tuple, Optional, Any, Dict # Added Any, Dict for user_profile
import json # Added for json operations for user_profile

# Add the project root to sys.path to allow imports from 'Coddy.core'
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from Coddy.core.logging_utility import log_info, log_warning, log_error, log_debug
    from Coddy.core.utility_functions import read_file, write_file # Use utility_functions for file I/O
    # Using 'Any' for type hints in __init__ to avoid 'Variable not allowed in type expression' error.
    # Ideally, direct class names would work with 'from __future__ import annotations'.
    from Coddy.core.code_generator import CodeGenerator as AnyCodeGenerator # Alias to avoid direct type hint conflict
    from Coddy.core.user_profile import UserProfile as AnyUserProfile # Alias to avoid direct type hint conflict
except ImportError as e:
    print(f"FATAL ERROR: Could not import core modules for StubAutoGenerator: {e}", file=sys.stderr)
    # Set UserProfile and CodeGenerator to None if import fails to prevent NameError,
    # though their absence will limit functionality.
    AnyUserProfile = None
    AnyCodeGenerator = None
    sys.exit(1)


class StubAutoGenerator:
    """
    Analyzes Python files asynchronously to identify incomplete functions
    and adds inline # TODO: comments or basic stubs, potentially leveraging an LLM
    for more intelligent stub generation.
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

    # Using 'Any' for type hints in __init__ to avoid 'Variable not allowed in type expression' error.
    # Ideally, direct class names would work with 'from __future__ import annotations'.
    def __init__(self, memory_service: Any, code_generator: Any, user_profile_manager: Optional[Any] = None): # FIX: Use Any for type hints
        self.memory_service = memory_service
        self.code_generator = code_generator # Store CodeGenerator instance
        self.user_profile_manager = user_profile_manager # Store UserProfileManager

    async def _read_file_async(self, file_path: str) -> Optional[str]:
        """Asynchronously reads the content of a file using utility_functions."""
        try:
            return await read_file(file_path)
        except Exception as e:
            await log_error(f"Error reading file {file_path} in StubAutoGenerator: {e}")
            return None

    async def _write_file_async(self, file_path: str, content: str):
        """Asynchronously writes content to a file using utility_functions."""
        try:
            await write_file(file_path, content)
        except Exception as e:
            await log_error(f"Error writing to file {file_path} in StubAutoGenerator: {e}")

    async def _generate_llm_stub(self, func_signature: str, current_file_content: str, user_profile: Optional[Dict[str, Any]]) -> str:
        """
        Generates a more intelligent stub using the LLM (via CodeGenerator).
        """
        if not self.code_generator:
            await log_warning("CodeGenerator not available for LLM stub generation. Falling back to basic stub.")
            return ""

        prompt = f"""
        Generate a concise Python code stub for the following function signature.
        The stub should include a docstring explaining its purpose and parameters, and a 'pass' statement.
        The function is part of the following file content (for context):
        ```python
        {current_file_content}
        ```
        Function signature to stub: `{func_signature}`

        Provide only the code for the stub, including indentation. Do not include any explanations outside the code.
        """
        try:
            # Use CodeGenerator to get LLM-generated stub
            llm_generated_stub = await self.code_generator.generate_code(
                prompt=prompt,
                context={"function_signature": func_signature, "file_content_context": current_file_content},
                user_profile=user_profile # Pass user profile for personalization
            )
            # The LLM might return more than just the stub, try to extract just the relevant part
            # This is a heuristic and might need refinement based on LLM behavior
            stub_lines = [line for line in llm_generated_stub.splitlines() if line.strip() and not line.strip().startswith('# Error')]
            if stub_lines:
                # Assuming the first non-comment line is the start of the stub body
                # We need to ensure it's properly indented relative to the function def.
                # For now, we'll just return the raw LLM output, hoping it's well-formatted.
                return "\n".join(stub_lines)
            return "" # Return empty if LLM didn't produce a useful stub
        except Exception as e:
            await log_error(f"Error generating LLM stub for '{func_signature}': {e}")
            return ""

    async def process_file(self, file_path: str, user_profile: Optional[Dict[str, Any]] = None) -> bool: # NEW: Accept user_profile
        """
        Asynchronously processes a single Python file to add or update stubs.
        Can use LLM for more intelligent stub generation if CodeGenerator is available.
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
                func_signature = f"def {func_name}({args}):" # Reconstruct signature for LLM

                # Check the next line for immediate 'pass' or '...' or empty line
                next_line_exists = (i + 1 < len(lines))
                next_line = lines[i+1] if next_line_exists else ""
                next_line_stripped = next_line.strip()
                next_line_indent = next_line.split(next_line_stripped)[0] if next_line_stripped else ''

                should_replace_stub = False
                if next_line_exists and (not next_line_stripped or self.PASS_OR_ELLIPSIS_PATTERN.match(next_line)):
                    # Check if the next line is indented correctly for a function body
                    if len(next_line_indent) == len(indent) + 4: # Standard 4-space indentation
                        should_replace_stub = True

                if should_replace_stub:
                    # Attempt LLM-based stub generation
                    llm_stub = await self._generate_llm_stub(func_signature, original_content, user_profile)
                    if llm_stub:
                        # Ensure the LLM stub is correctly indented relative to the function definition
                        llm_stub_lines = llm_stub.splitlines()
                        # Adjust indentation of LLM stub to match the function's expected body indentation
                        adjusted_llm_stub_lines = [indent + "    " + l.lstrip() for l in llm_stub_lines]
                        updated_content.extend(adjusted_llm_stub_lines)
                        modified = True
                        if next_line_stripped: # If it was 'pass' or '...' skip original next line
                            i += 1
                    else: # Fallback to basic stub if LLM fails or returns empty
                        basic_stub = self._generate_basic_stub(indent, func_name, args)
                        updated_content.extend(basic_stub.strip().splitlines())
                        modified = True
                        if next_line_stripped:
                            i += 1
                else: # If there's actual code or comments immediately after, just add a TODO above it
                    updated_content.append(f"{indent}    # TODO: Implement {func_name}\n")
                    modified = True
            else:
                updated_content.append(line)
            i += 1

        if modified:
            new_content = "\n".join(updated_content)
            if new_content != original_content:
                await self._write_file_async(file_path, new_content)
                await log_info(f"Stubbed incomplete functions in: {file_path}")
                return True
        return False

    def _generate_basic_stub(self, indent: str, func_name: str, args: str) -> str:
        """Generates a basic Python stub based on the function's indentation and signature."""
        stub_indent = indent + "    " # Add one level of indentation for the stub body
        # Basic stub structure
        stub = f"{stub_indent}# TODO: Implement functionality for {func_name}\n"
        stub += f"{stub_indent}# Parameters: {args if args else 'None'}\n"
        stub += f"{stub_indent}pass\n" # Always end with pass to ensure valid syntax
        return stub

    async def generate_todo_stubs(self, scan_path: str, output_file: str, user_profile: Optional[Dict[str, Any]] = None) -> str: # NEW: Accept user_profile
        """
        Scans files for TODO comments and incomplete functions, generates detailed stubs
        or issues, and writes them to an output file.
        """
        await log_info(f"Generating TODO stubs for path: {scan_path}")
        
        all_todo_items = []
        
        # Scan for existing TODOs and incomplete functions
        modified_files = await self.scan_directory(scan_path, user_profile=user_profile) # Pass user_profile to scan_directory

        # For a more comprehensive TODO stub generation, we might want to
        # read the modified files again and extract all TODOs, or
        # use a dedicated LLM call to summarize/categorize them.
        # For now, we'll just report on modified files.
        
        stubs_content_lines = [f"# TODO Stubs and Incomplete Functions Report ({datetime.now().isoformat()})\n"]
        if modified_files:
            stubs_content_lines.append("\n## Modified Files (Stubs Added/Updated):\n")
            for f in modified_files:
                stubs_content_lines.append(f"- `{f}`")
        else:
            stubs_content_lines.append("\n## No incomplete functions found or modified files.\n")

        # This part could be enhanced by actually reading the TODOs from files
        # and using an LLM to categorize/prioritize them, leveraging user_profile.
        
        stubs_content = "\n".join(stubs_content_lines)
        
        # Save to output file
        await self._write_file_async(output_file, stubs_content)
        await log_info(f"TODO stubs report saved to {output_file}")
        
        return stubs_content

    async def scan_directory(self, directory_path: str, user_profile: Optional[Dict[str, Any]] = None) -> List[str]: # NEW: Accept user_profile
        """
        Asynchronously scans a directory for Python files and processes them.
        Returns a list of file paths that were modified.
        """
        modified_files = []
        tasks_with_paths = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    # Pass user_profile to process_file
                    tasks_with_paths.append((self.process_file(file_path, user_profile=user_profile), file_path))

        tasks = [task for task, _ in tasks_with_paths]
        file_paths_order = [path for _, path in tasks_with_paths]

        results = await asyncio.gather(*tasks)

        for i, was_modified in enumerate(results):
            if was_modified:
                modified_files.append(file_paths_order[i])
        
        return modified_files

