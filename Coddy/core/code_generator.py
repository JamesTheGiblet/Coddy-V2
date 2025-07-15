from __future__ import annotations # Enable postponed evaluation of type annotations
import asyncio
import os
import ast # NEW: For validating Python code syntax
import sys
from typing import Dict, Any, Optional, List
import json # Added for json.dumps in prompt formatting
import uuid # NEW: For generating unique context_ids for interactions
from datetime import datetime # NEW: For timestamping interactions

# Add the project root to sys.path to allow imports from 'Coddy.core'
# This calculates the path to 'C:\Users\gilbe\Documents\GitHub\Coddy V2'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    # Use absolute imports from the project root for consistency
    from core.idea_synth import IdeaSynthesizer
    from core.memory_service import MemoryService
    from core.vibe_mode import VibeModeEngine
    from core.logging_utility import log_info, log_warning, log_error, log_debug
    from core.user_profile import UserProfile
    from core.llm_provider import LLMProvider # NEW: Import LLMProvider for type hinting
    from core.utility_functions import save_generated_file # MODIFIED: Renamed import
    
except ImportError as e:
    print(f"FATAL ERROR: Could not import core modules required for CodeGenerator: {e}", file=sys.stderr)
    # Set UserProfile to None if import fails to prevent NameError, though it's critical for this feature.
    UserProfile = None
    LLMProvider = Any # Fallback if import fails
    sys.exit(1)

class CodeGenerator:
    """
    Generates code based on instructions, leveraging IdeaSynthesizer (LLM)
    and incorporating UserProfile for personalized generation and interaction logging.
    """
    # MODIFIED: Accept llm_provider instance directly and remove model_name
    def __init__(self, llm_provider: Any,
                 memory_service: Optional[MemoryService] = None,
                 vibe_engine: Optional[VibeModeEngine] = None,
                 user_profile_manager: Optional[Any] = None):
        self.user_profile_manager = user_profile_manager # Store the user profile manager
        self.llm_provider = llm_provider # Store the LLMProvider instance
        
        # MODIFIED: Pass llm_provider to IdeaSynthesizer
        self.idea_synthesizer = IdeaSynthesizer(
            llm_provider=self.llm_provider, # Pass the centralized LLMProvider
            user_profile_manager=self.user_profile_manager
        )
        self.memory_service = memory_service
        self.vibe_engine = vibe_engine

    async def initialize(self):
        """
        Asynchronously initializes the CodeGenerator, performing any async setup.
        This method should be called after the CodeGenerator instance is created.
        """
        await log_info("CodeGenerator initialized.") # Now correctly awaited

    def _extract_code_from_markdown(self, content: str) -> str:
        """
        Extracts the first code block from a string that might contain markdown.
        If no markdown code block is found, it returns the original content stripped.
        This is useful because LLMs often wrap their code output in markdown blocks.
        """
        # Find the start of a code block
        start_marker = content.find('```')
        if start_marker == -1:
            return content.strip()

        # Find the end of the code block, starting after the initial marker
        end_marker = content.find('```', start_marker + 3)
        if end_marker == -1:
            # If there's a start but no end, assume the rest is code
            code_block = content[start_marker + 3:]
        else:
            # Extract the content within the block
            code_block = content[start_marker + 3:end_marker]

        # The first line might be the language hint (e.g., 'python').
        # We remove it to get just the raw code.
        first_newline = code_block.find('\n')
        return code_block[first_newline + 1:].strip() if first_newline != -1 else code_block.strip()

    def _is_valid_python_code(self, code: str) -> bool:
        """
        Checks if the given string is valid Python code by trying to parse it.
        """
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            # Using log_debug for less noise, but indicating a syntax issue.
            log_debug(f"Generated code has a syntax error: {e}")
            return False

    async def _generate_and_validate_code(self, initial_prompt: str, user_profile: Optional[Dict[str, Any]]) -> str:
        """
        Generates code, validates its syntax, and attempts to self-correct if needed.
        """
        # First attempt
        raw_content = await self.idea_synthesizer.synthesize_idea(initial_prompt, user_profile=user_profile)
        generated_code = self._extract_code_from_markdown(raw_content)

        # If syntax is invalid, try to self-correct once.
        if not self._is_valid_python_code(generated_code):
            await log_warning("Initial code generation failed syntax check. Attempting to self-correct.")
            correction_prompt = (
                f"The following code has a syntax error. Please fix it and provide only the corrected, complete Python code.\n\n"
                f"Faulty Code:\n```python\n{generated_code}\n```\n\n"
                f"The corrected code should be a direct, runnable replacement, including all necessary imports and definitions."
            )
            raw_content = await self.idea_synthesizer.synthesize_idea(correction_prompt, user_profile=user_profile)
            generated_code = self._extract_code_from_markdown(raw_content)

            # Final check
            if not self._is_valid_python_code(generated_code):
                await log_error("Self-correction also failed syntax check. Returning faulty code.")

        return generated_code

    async def generate_code(self, prompt: str, output_file: Optional[str] = None, 
                            context: Optional[Dict[str, Any]] = None, 
                            user_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates general code based on a prompt and optional context,
        validates it, and saves it if an output file is provided.
        """
        await log_info(f"Generating code for prompt: {prompt[:100]}...")
        
        # Add more explicit instructions to the prompt for better results.
        full_prompt = (
            f"Generate syntactically correct, complete, importable, and runnable Python code "
            f"based on the following request: {prompt}. "
            f"Include all necessary imports at the top of the file. "
            f"Provide only the raw code, without any surrounding text or explanations, "
            f"and without nested markdown blocks."
        )
        if context:
            full_prompt += f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        try:
            generated_content = await self._generate_and_validate_code(full_prompt, user_profile)
            await log_info("Code generation complete.")

            if output_file:
                # Determine category based on file name
                category = "code" # Default category for general code
                
                # Extract project_name and actual filename from output_file path
                # output_file is expected to be "project_name/filename.ext"
                # If it's just "filename.ext", project_name will be None
                project_name = None
                actual_filename = output_file
                
                if os.sep in output_file:
                    parts = output_file.split(os.sep)
                    project_name = parts[0]
                    actual_filename = os.sep.join(parts[1:]) # Rejoin remaining parts for filename

                if actual_filename.lower() == "readme.md":
                    category = "readmes"
                elif actual_filename.lower() == "requirements.txt":
                    category = "requirements"
                elif actual_filename.lower() == "roadmap.md": # Added roadmap.md
                    category = "roadmaps"
                # For other code files, 'code' category is fine.

                await save_generated_file(
                    content=generated_content,
                    file_name=actual_filename, # Pass just the filename
                    category=category,
                    project_name=project_name # Pass the extracted project_name
                )
                await log_info(f"Generated content saved to {output_file} under '{category}' for project '{project_name}'.")
            
            return generated_content
        except Exception as e:
            await log_error(f"Error during code generation: {e}", exc_info=True)
            return f"# Error generating code: {e}"

    async def generate_code_fix(self, file_path: str, output_file: Optional[str] = None, 
                                context: Optional[Dict[str, Any]] = None,
                                user_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a code fix, delegating personalization and logging to IdeaSynthesizer.
        If output_file is provided, saves the generated content to a timestamped folder.
        """
        await log_info(f"Generating code fix for file: {file_path}")

        original_code = context.get("original_code", "No original code provided.")
        problem_description = context.get("problem_description", "Tests are failing.")

        prompt = (
            f"The following Python code from '{file_path}' has failing tests:\n\n"
            f"{original_code}\n\n"
            f"Problem: {problem_description}\n"
        )
        if context.get("failed_test_output_stdout"):
            prompt += f"Test STDOUT:\n{context.get('failed_test_output_stdout')}\n"
        if context.get("failed_test_output_stderr"):
            prompt += f"Test STDERR:\n{context.get('failed_test_output_stderr')}\n"
        
        prompt += "Please provide a corrected, syntactically valid version of ONLY the Python code that addresses the test failures. Do not include any explanations or markdown formatting outside the code block."

        interaction_context_id = str(uuid.uuid4()) # Generate a unique ID for this interaction

        try:
            # Use the new generation/validation helper
            corrected_code = await self._generate_and_validate_code(prompt, user_profile)
            await log_info("Code fix generation complete.")
            
            if output_file:
                # Extract project_name and actual filename from output_file path
                project_name = None
                actual_filename = output_file
                if os.sep in output_file:
                    parts = output_file.split(os.sep)
                    project_name = parts[0]
                    actual_filename = os.sep.join(parts[1:])

                await save_generated_file(corrected_code, actual_filename, "fixes", project_name) # New category "fixes"
                await log_info(f"Generated code fix saved to {output_file} under 'fixes' for project '{project_name}'.")
        except Exception as e:
            await log_error(f"Error during code fix generation: {e}", exc_info=True)
            corrected_code = f"# Error generating code fix: {e}"
        finally:
            # Store a summary of the last AI interaction in the user profile
            if self.user_profile_manager and self.user_profile_manager.profile:
                summary = {
                    "type": "code_fix_generation",
                    "prompt_summary": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    "output_summary": corrected_code[:200] + "..." if len(corrected_code) > 200 else corrected_code,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_id": interaction_context_id,
                    "model_used": self.llm_provider.model_name if hasattr(self.llm_provider, 'model_name') else 'unknown_model' # Use the model name from the injected provider
                }
                await self.user_profile_manager.update_last_interaction_summary(summary)
            return corrected_code
