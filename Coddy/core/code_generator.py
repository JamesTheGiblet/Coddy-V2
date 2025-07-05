# Coddy/core/code_generator.py
import asyncio
import os
import sys
from typing import Dict, Any, Optional, List
import json # Added for json.dumps in prompt formatting

# Add the project root to sys.path to allow imports from 'Coddy.core'
# This calculates the path to 'C:\Users\gilbe\Documents\GitHub\Coddy V2'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    # IMPORTANT: Ensure these import paths are absolute, starting with 'Coddy.'
    from Coddy.core.idea_synth import IdeaSynthesizer 
    from Coddy.core.memory_service import MemoryService 
    from Coddy.core.vibe_mode import VibeModeEngine 
    from Coddy.core.logging_utility import log_info, log_warning, log_error, log_debug
except ImportError as e:
    print(f"FATAL ERROR: Could not import core modules required for CodeGenerator: {e}", file=sys.stderr)
    sys.exit(1)

class CodeGenerator:
    """
    Generates code based on instructions, leveraging IdeaSynthesizer (LLM)
    and potentially VibeModeEngine for contextual generation.
    """
    def __init__(self, memory_service: Optional[MemoryService] = None, vibe_engine: Optional[VibeModeEngine] = None):
        # NOTE: If CodeGenerator was previously initialized without these,
        # you need to ensure its __init__ method accepts them.
        # Based on previous tracebacks, it seems it was not accepting them.
        # For now, I'm adding them as optional arguments.
        # If your actual CodeGenerator.py does not have these parameters,
        # you will need to remove them from the initialization calls in cli.py and backend/main.py.
        self.idea_synthesizer = IdeaSynthesizer()
        self.memory_service = memory_service
        self.vibe_engine = vibe_engine
        # Removed: log_info("CodeGenerator initialized.")
        # Initialization logging moved to the async initialize() method.

    async def initialize(self):
        """
        Asynchronously initializes the CodeGenerator, performing any async setup.
        This method should be called after the CodeGenerator instance is created.
        """
        await log_info("CodeGenerator initialized.") # Now correctly awaited

    async def generate_code(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates general code based on a prompt and optional context.
        """
        await log_info(f"Generating code for prompt: {prompt[:100]}...")
        full_prompt = f"Generate code based on the following request: {prompt}\n"
        if context:
            full_prompt += f"Context: {json.dumps(context)}\n"
        
        # Add vibe mode to prompt if available
        if self.vibe_engine:
            current_vibe = self.vibe_engine.get_current_vibe()
            if current_vibe:
                full_prompt += f"Current Vibe/Focus: {current_vibe}\n"

        generated_code = await self.idea_synthesizer.synthesize_idea(full_prompt)
        await log_info("Code generation complete.")
        return generated_code

    async def generate_unit_tests(self, file_path: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates unit tests for a given file, using its content and additional context.
        """
        await log_info(f"Generating unit tests for file: {file_path}")
        
        file_content = context.get("file_content", "No file content provided.")
        vibe_mode = context.get("vibe_mode", "default")
        recent_memories = context.get("recent_memories", [])

        prompt = f"Generate comprehensive unit tests for the following Python code from '{file_path}':\n\n"
        prompt += f"```python\n{file_content}\n```\n\n"
        prompt += f"Consider the current vibe/focus: {vibe_mode}.\n"
        if recent_memories:
            prompt += f"Also consider these recent interactions/memories: {json.dumps(recent_memories[:3])}\n" # Limit for prompt size
        prompt += "Ensure the tests cover edge cases and common scenarios. Provide only the Python code for the tests."

        generated_tests = await self.idea_synthesizer.synthesize_idea(prompt)
        await log_info("Unit test generation complete.")
        return generated_tests

    async def generate_code_fix(self, file_path: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a code fix for a given file based on failed test output.
        """
        await log_info(f"Generating code fix for file: {file_path}")

        original_code = context.get("original_code", "No original code provided.")
        failed_test_output_stdout = context.get("failed_test_output_stdout", "")
        failed_test_output_stderr = context.get("failed_test_output_stderr", "")
        vibe_mode = context.get("vibe_mode", "default")
        recent_memories = context.get("recent_memories", [])
        problem_description = context.get("problem_description", "Tests are failing.")

        prompt = f"The following Python code from '{file_path}' has failing tests:\n\n"
        prompt += f"```python\n{original_code}\n```\n\n"
        prompt += f"Problem: {problem_description}\n"
        if failed_test_output_stdout:
            prompt += f"Test STDOUT:\n```\n{failed_test_output_stdout}\n```\n"
        if failed_test_output_stderr:
            prompt += f"Test STDERR:\n```\n{failed_test_output_stderr}\n```\n"
        
        prompt += f"Current Vibe/Focus: {vibe_mode}.\n"
        if recent_memories:
            prompt += f"Recent interactions/memories: {json.dumps(recent_memories[:3])}\n"
        
        prompt += "Please provide a corrected version of ONLY the Python code that addresses the test failures. Do not include any explanations or markdown formatting outside the code block."

        corrected_code = await self.idea_synthesizer.synthesize_idea(prompt)
        await log_info("Code fix generation complete.")
        return corrected_code
