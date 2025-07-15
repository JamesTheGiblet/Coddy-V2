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
    from Coddy.core.utility_functions import read_file, write_file, list_files_in_directory_recursive # Use utility_functions for file I/O
    # Using 'Any' for type hints in __init__ to avoid 'Variable not allowed in type expression' error.
    # Ideally, direct class names would work with 'from __future__ import annotations'.
    from Coddy.core.code_generator import CodeGenerator as AnyCodeGenerator # Alias to avoid direct type hint conflict
    from Coddy.core.user_profile import UserProfile as AnyUserProfile # Alias to avoid direct type hint conflict
    from backend.services import services # NEW: Import services for better LLM integration if needed
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
    
    # NEW: Regex to extract content from a markdown code block
    MARKDOWN_CODE_BLOCK_PATTERN = re.compile(r"```python\n(.*?)\n```", re.DOTALL)


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

        Provide only the code for the stub, including indentation.
        Wrap the generated code ONLY within a markdown Python code block (```python...```).
        Do not include any explanations or extra text outside the code block.
        """
        try:
            # Use CodeGenerator to get LLM-generated stub
            llm_generated_output = await self.code_generator.generate_code(
                prompt=prompt,
                context={"function_signature": func_signature, "file_content_context": current_file_content},
                user_profile=user_profile # Pass user profile for personalization
            )
            
            # MODIFIED: Extract code from markdown block
            response_text = llm_generated_output.get("code", "")
            match = self.MARKDOWN_CODE_BLOCK_PATTERN.search(response_text)
            if match:
                llm_stub = match.group(1).strip()
                return llm_stub
            
            await log_warning(f"LLM generated stub for '{func_signature}' did not contain expected markdown code block.")
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
                        adjusted_llm_stub_lines = [indent + "    " + l.lstrip() for l in llm_stub_lines]
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
                    updated_content.append(f"{indent}    # TODO: Implement {func_name}\n")
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
        stub_indent = indent + "    " # Add one level of indentation for the stub body
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
        
        # Scan for existing TODOs and incomplete functions (and apply stubs)
        modified_files = await self.scan_directory(scan_path, user_profile=user_profile) # Pass user_profile to scan_directory

        # NEW: Comprehensive TODO reporting using LLM
        all_todo_comments = []
        all_files_to_scan = []
        if os.path.isdir(scan_path):
            all_files_to_scan = await list_files_in_directory_recursive(scan_path, include_dirs=False)
            all_files_to_scan = [f for f in all_files_to_scan if f.endswith('.py') or f.endswith('.md')] # Include markdown for general TODOs
        elif os.path.isfile(scan_path):
            all_files_to_scan = [scan_path]
        
        for f_path in all_files_to_scan:
            content = await self._read_file_async(f_path)
            if content:
                for line_num, line in enumerate(content.splitlines()):
                    if "# TODO:" in line:
                        all_todo_comments.append(f"File: {f_path}, Line {line_num + 1}: {line.strip()}")
        
        stubs_content_lines = [f"# TODO Stubs and Incomplete Functions Report ({datetime.now().isoformat()})\n"]
        stubs_content_lines.append("\n## Files with Stubs Added/Updated:\n")
        if modified_files:
            for f in modified_files:
                stubs_content_lines.append(f"- `{f}`")
        else:
            stubs_content_lines.append("- None\n")

        if all_todo_comments and self.code_generator and services.get("llm_provider") and services.get("user_profile_manager"):
            await log_info("Using LLM to categorize and prioritize TODOs.")
            llm_prompt = f"""
            Analyze the following list of TODO comments and incomplete function markers from a codebase.
            Your goal is to categorize them by theme (e.g., "Refactoring", "New Feature", "Bug Fix", "Documentation", "Optimization", "Testing") and prioritize them.
            For each category, list the related TODOs. Also, provide an overall prioritized list of the top 5 most critical or next-to-do items across all categories.

            TODO Items:
            {json.dumps(all_todo_comments, indent=2)}

            Format your response as a JSON object with two top-level keys:
            1. "categorized_todos": A dictionary where keys are categories and values are lists of related TODO strings.
            2. "prioritized_list": A list of strings representing the top 5 prioritized TODO items.

            Example JSON output:
            {{
              "categorized_todos": {{
                "New Feature": ["File: feature.py, Line 10: # TODO: Implement login logic"],
                "Refactoring": ["File: old_code.py, Line 50: # TODO: Refactor utility function"]
              }},
              "prioritized_list": ["Implement login logic", "Fix database connection bug"]
            }}
            """
            try:
                llm_categorized_output = await self.code_generator.generate_code(
                    prompt=llm_prompt,
                    user_profile=user_profile if user_profile else {}
                )
                response_text = llm_categorized_output.get("code", "")
                
                # Extract JSON from markdown code block
                match = self.MARKDOWN_CODE_BLOCK_PATTERN.search(response_text)
                if match:
                    json_string = match.group(1).strip()
                    categorized_data = json.loads(json_string)
                    
                    stubs_content_lines.append("\n## Categorized TODOs (AI-Generated):\n")
                    for category, items in categorized_data.get("categorized_todos", {}).items():
                        stubs_content_lines.append(f"### {category}\n")
                        for item in items:
                            stubs_content_lines.append(f"- {item}")
                        stubs_content_lines.append("\n") # Add newline after each category
                    
                    stubs_content_lines.append("\n## Prioritized Next Steps (AI-Generated):\n")
                    for item in categorized_data.get("prioritized_list", []):
                        stubs_content_lines.append(f"- {item}")
                else:
                    stubs_content_lines.append("\n## AI-Generated TODO Analysis (Raw LLM Output):\n")
                    stubs_content_lines.append(response_text)
            except Exception as e:
                await log_error(f"Error getting LLM-categorized TODOs: {e}")
                stubs_content_lines.append("\n## AI-Generated TODO Analysis (Failed):\n")
                stubs_content_lines.append(f"Failed to generate categorized TODOs: {e}")
        elif all_todo_comments: # If LLM not available but TODOs exist
            stubs_content_lines.append("\n## All Found TODO Comments:\n")
            for item in all_todo_comments:
                stubs_content_lines.append(f"- {item}")
        else:
            stubs_content_lines.append("\n## No explicit # TODO: comments found in scanned files.\n")
            
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