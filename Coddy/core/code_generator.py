# Coddy/core/code_generator.py
from __future__ import annotations # Enable postponed evaluation of type annotations
import asyncio
import os
import sys
from typing import Dict, Any, Optional, List
import json # Added for json.dumps in prompt formatting
import uuid # NEW: For generating unique context_ids for interactions
from datetime import datetime # NEW: For timestamping interactions

# Add the project root to sys.path to allow imports from 'Coddy.core'
# This calculates the path to 'C:\Users\gilbe\Documents\GitHub\Coddy V2'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    # IMPORTANT: Ensure these import paths are absolute, starting with 'Coddy.'
    from Coddy.core.idea_synth import IdeaSynthesizer 
    from Coddy.core.memory_service import MemoryService 
    from Coddy.core.vibe_mode import VibeModeEngine 
    from Coddy.core.logging_utility import log_info, log_warning, log_error, log_debug
    from Coddy.core.user_profile import UserProfile # NEW: Import UserProfile
except ImportError as e:
    print(f"FATAL ERROR: Could not import core modules required for CodeGenerator: {e}", file=sys.stderr)
    # Set UserProfile to None if import fails to prevent NameError, though it's critical for this feature.
    UserProfile = None
    sys.exit(1)

class CodeGenerator:
    """
    Generates code based on instructions, leveraging IdeaSynthesizer (LLM)
    and incorporating UserProfile for personalized generation and interaction logging.
    """
    def __init__(self, memory_service: Optional[MemoryService] = None, 
                 vibe_engine: Optional[VibeModeEngine] = None,
                 user_profile_manager: Optional[Any] = None): # NEW: Accept UserProfileManager
        self.user_profile_manager = user_profile_manager # Store the user profile manager
        # Pass user_profile_manager to IdeaSynthesizer
        self.idea_synthesizer = IdeaSynthesizer(user_profile_manager=self.user_profile_manager) 
        self.memory_service = memory_service
        self.vibe_engine = vibe_engine

    async def initialize(self):
        """
        Asynchronously initializes the CodeGenerator, performing any async setup.
        This method should be called after the CodeGenerator instance is created.
        """
        await log_info("CodeGenerator initialized.") # Now correctly awaited

    async def _get_personalization_hints(self, user_profile: Optional[Dict[str, Any]]) -> str:
        """
        Constructs a string of personalization hints for the LLM based on the user profile.
        """
        hints = []
        if user_profile:
            coding_style = user_profile.get('coding_style_preferences', {})
            preferred_languages = user_profile.get('preferred_languages', [])
            persona = user_profile.get('idea_synth_persona', 'default')
            creativity = user_profile.get('idea_synth_creativity', 0.7)

            hints.append(f"User Persona/Tone Preference: {persona}.")
            hints.append(f"Creativity Level: {creativity}.")

            if coding_style:
                hints.append(f"Adhere to the user's preferred coding style: {json.dumps(coding_style)}.")
            if preferred_languages:
                hints.append(f"Prioritize these languages: {', '.join(preferred_languages)}.")
        
        # Add current vibe if available
        if self.vibe_engine:
            current_vibe = self.vibe_engine.get_current_vibe()
            if current_vibe:
                hints.append(f"Current Vibe/Focus: {current_vibe}.")

        return "\n".join(hints) if hints else ""


    async def generate_code(self, prompt: str, context: Optional[Dict[str, Any]] = None, 
                            user_profile: Optional[Dict[str, Any]] = None) -> str: # NEW: Accept user_profile
        """
        Generates general code based on a prompt and optional context,
        tailoring the output based on the user's profile.
        Logs a summary of the interaction to the user's profile.
        """
        await log_info(f"Generating code for prompt: {prompt[:100]}...")
        
        personalization_hints = await self._get_personalization_hints(user_profile)

        full_prompt = f"""
        Generate code based on the following request: {prompt}

        {personalization_hints}

        """
        if context:
            full_prompt += f"Additional Context: {json.dumps(context)}\n"
        
        generated_code = ""
        interaction_context_id = str(uuid.uuid4()) # Generate a unique ID for this interaction

        try:
            # Pass user_profile to IdeaSynthesizer for deeper personalization
            generated_code = await self.idea_synthesizer.synthesize_idea(full_prompt, user_profile=user_profile)
            await log_info("Code generation complete.")
        except Exception as e:
            await log_error(f"Error during code generation: {e}", exc_info=True)
            generated_code = f"# Error generating code: {e}"
        finally:
            # Store a summary of the last AI interaction in the user profile
            if self.user_profile_manager and self.user_profile_manager.profile:
                summary = {
                    "type": "code_generation",
                    "prompt_summary": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    "output_summary": generated_code[:200] + "..." if len(generated_code) > 200 else generated_code,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_id": interaction_context_id,
                    "model_used": user_profile.get('llm_provider_config', {}).get('model_name', 'gemini-pro') if user_profile else 'gemini-pro'
                }
                await self.user_profile_manager.update_last_interaction_summary(summary)
            return generated_code

    async def generate_unit_tests(self, file_path: str, context: Optional[Dict[str, Any]] = None,
                                  user_profile: Optional[Dict[str, Any]] = None) -> str: # NEW: Accept user_profile
        """
        Generates unit tests for a given file, using its content and additional context,
        tailoring the output based on the user's profile.
        Logs a summary of the interaction to the user's profile.
        """
        await log_info(f"Generating unit tests for file: {file_path}")
        
        file_content = context.get("file_content", "No file content provided.")
        recent_memories = context.get("recent_memories", [])

        personalization_hints = await self._get_personalization_hints(user_profile)

        prompt = f"""
        Generate comprehensive unit tests for the following Python code from '{file_path}':

        ```python
        {file_content}
        ```

        {personalization_hints}

        """
        if recent_memories:
            prompt += f"Also consider these recent interactions/memories: {json.dumps(recent_memories[:3])}\n" # Limit for prompt size
        
        prompt += "Ensure the tests cover edge cases and common scenarios. Provide only the Python code for the tests."

        generated_tests = ""
        interaction_context_id = str(uuid.uuid4()) # Generate a unique ID for this interaction

        try:
            # Pass user_profile to IdeaSynthesizer for deeper personalization
            generated_tests = await self.idea_synthesizer.synthesize_idea(prompt, user_profile=user_profile)
            await log_info("Unit test generation complete.")
        except Exception as e:
            await log_error(f"Error during unit test generation: {e}", exc_info=True)
            generated_tests = f"# Error generating unit tests: {e}"
        finally:
            # Store a summary of the last AI interaction in the user profile
            if self.user_profile_manager and self.user_profile_manager.profile:
                summary = {
                    "type": "unit_test_generation",
                    "prompt_summary": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    "output_summary": generated_tests[:200] + "..." if len(generated_tests) > 200 else generated_tests,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_id": interaction_context_id,
                    "model_used": user_profile.get('llm_provider_config', {}).get('model_name', 'gemini-pro') if user_profile else 'gemini-pro'
                }
                await self.user_profile_manager.update_last_interaction_summary(summary)
            return generated_tests

    async def generate_code_fix(self, file_path: str, context: Optional[Dict[str, Any]] = None,
                                user_profile: Optional[Dict[str, Any]] = None) -> str: # NEW: Accept user_profile
        """
        Generates a code fix for a given file based on failed test output,
        tailoring the output based on the user's profile.
        Logs a summary of the interaction to the user's profile.
        """
        await log_info(f"Generating code fix for file: {file_path}")

        original_code = context.get("original_code", "No original code provided.")
        failed_test_output_stdout = context.get("failed_test_output_stdout", "")
        failed_test_output_stderr = context.get("failed_test_output_stderr", "")
        problem_description = context.get("problem_description", "Tests are failing.")
        recent_memories = context.get("recent_memories", [])

        personalization_hints = await self._get_personalization_hints(user_profile)

        prompt = f"""
        The following Python code from '{file_path}' has failing tests:

        ```python
        {original_code}
        ```

        Problem: {problem_description}
        """
        if failed_test_output_stdout:
            prompt += f"Test STDOUT:\n```\n{failed_test_output_stdout}\n```\n"
        if failed_test_output_stderr:
            prompt += f"Test STDERR:\n```\n{failed_test_output_stderr}\n```\n"
        
        prompt += f"""
        {personalization_hints}

        """
        if recent_memories:
            prompt += f"Recent interactions/memories: {json.dumps(recent_memories[:3])}\n"
        
        prompt += "Please provide a corrected version of ONLY the Python code that addresses the test failures. Do not include any explanations or markdown formatting outside the code block."

        corrected_code = ""
        interaction_context_id = str(uuid.uuid4()) # Generate a unique ID for this interaction

        try:
            # Pass user_profile to IdeaSynthesizer for deeper personalization
            corrected_code = await self.idea_synthesizer.synthesize_idea(prompt, user_profile=user_profile)
            await log_info("Code fix generation complete.")
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
                    "model_used": user_profile.get('llm_provider_config', {}).get('model_name', 'gemini-pro') if user_profile else 'gemini-pro'
                }
                await self.user_profile_manager.update_last_interaction_summary(summary)
            return corrected_code
