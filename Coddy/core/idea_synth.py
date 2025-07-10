# c:\Users\gilbe\Documents\GitHub\Coddy V2\Coddy/core/idea_synth.py
from __future__ import annotations # NEW: Enable postponed evaluation of type annotations
import asyncio
import os
from dotenv import load_dotenv
# REMOVED: from langchain_google_genai import ChatGoogleGenerativeAI # No longer instantiate here
from langchain_core.messages import HumanMessage, SystemMessage # Keep for potential future use or if other parts rely on it for message formatting
from typing import Dict, Any, Optional # Added for type hints
import json # Added for json.dumps in prompt formatting
import uuid # NEW: For generating unique context_ids for interactions
from datetime import datetime # NEW: For timestamping interactions

# Add the project root to sys.path to allow imports from 'Coddy.core'
# This is a fallback for local testing; production environment might handle paths differently.
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from typing import TYPE_CHECKING
try:
    from Coddy.core.user_profile import UserProfile # NEW: Import UserProfile
    # Only import LLMProvider for type checking to avoid runtime errors
    if TYPE_CHECKING:
        from Coddy.core.llm_provider import LLMProvider # type: ignore
except ImportError as e:
    print(f"FATAL ERROR: Could not import UserProfile or LLMProvider in IdeaSynthesizer: {e}", file=sys.stderr)
    UserProfile = None
    sys.exit(1)

load_dotenv() # Load environment variables, including API keys

class IdeaSynthesizer:
    """
    Synthesizes ideas and generates content using a large language model.
    This class is intended to be the primary interface for LLM interactions,
    now incorporating user profile for personalization and logging.
    """
    # MODIFIED: Accept llm_provider instance directly
    def __init__(self, llm_provider: "LLMProvider", user_profile_manager: Optional[Any] = None):
        """
        Initializes the IdeaSynthesizer with an LLM provider and UserProfileManager.
        """
        self.llm_provider = llm_provider # Store the LLMProvider instance
        self.user_profile_manager = user_profile_manager

    async def synthesize_idea(self, prompt: str, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a response based on the given prompt, dynamically adjusting LLM parameters
        and prompt content based on the user's profile. It also logs a summary of the
        interaction to the user's profile.

        Args:
            prompt (str): The main instruction or query for the LLM.
            user_profile (Optional[Dict[str, Any]]): The user's personalization profile,
                                                      containing preferences like coding style,
                                                      preferred languages, persona, and creativity.

        Returns:
            str: The generated content from the LLM.
        """
        system_message_content = ""
        llm_temperature = 0.7 # Default temperature
        # Get model name from the injected provider for logging purposes
        llm_model_name_for_logging = self.llm_provider.model_name if hasattr(self.llm_provider, 'model_name') else "unknown_model"

        if user_profile:
            # Extract personalization settings
            persona = user_profile.get('idea_synth_persona', 'default')
            creativity = user_profile.get('idea_synth_creativity', 0.7)
            coding_style = user_profile.get('coding_style_preferences', {})
            preferred_languages = user_profile.get('preferred_languages', [])
            # llm_provider_config = user_profile.get('llm_provider_config', {}) # No longer needed to get model_name here

            # Adjust LLM temperature based on user's creativity preference
            llm_temperature = float(creativity) # Ensure it's a float

            # Construct a system message to guide the LLM's behavior and style
            system_message_content = f"""
            You are Coddy, an AI software development companion.
            Your responses should be tailored to the user's preferences.
            User Persona/Tone Preference: {persona}.
            """
            if coding_style:
                system_message_content += f"Adhere to the user's preferred coding style: {json.dumps(coding_style)}.\n"
            if preferred_languages:
                system_message_content += f"Prioritize these languages in your responses: {', '.join(preferred_languages)}.\n"
            
            # The model is now set at the LLMProvider instance level, not here.
            # We just use it for logging if available.
            llm_model_name_for_logging = user_profile.get('llm_provider_config', {}).get('model_name', llm_model_name_for_logging)

        # Combine system message and prompt for the LLMProvider
        # LLMProvider's generate_text expects a single prompt string.
        # We'll prepend the system message to the prompt.
        full_llm_prompt = ""
        if system_message_content:
            full_llm_prompt += f"System Message: {system_message_content}\n\n"
        full_llm_prompt += f"Human Message: {prompt}"

        generated_content = ""
        interaction_context_id = str(uuid.uuid4()) # Generate a unique ID for this interaction

        try:
            # Use the injected llm_provider to generate text
            generated_content = await self.llm_provider.generate_text(
                prompt=full_llm_prompt, # Pass the combined prompt
                temperature=llm_temperature
                # max_tokens and top_p can be passed if llm_provider.generate_text supports them
                # and if you want to expose them from IdeaSynthesizer
            )
            
            # Simple cleanup: remove markdown code block delimiters if they wrap the entire response
            if generated_content.startswith('```') and generated_content.endswith('```'):
                first_newline = generated_content.find('\n')
                last_newline = generated_content.rfind('\n')
                if first_newline != -1 and last_newline != -1 and last_newline > first_newline:
                    generated_content = generated_content[first_newline + 1:last_newline].strip()

        except Exception as e:
            print(f"Error during LLM synthesis: {e}")
            generated_content = f"# Error: Could not synthesize idea. Please check API key or prompt. Details: {e}"
        finally:
            # Store a summary of the last AI interaction in the user profile
            if self.user_profile_manager and self.user_profile_manager.profile:
                summary = {
                    "type": "idea_synthesis",
                    "prompt_summary": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                    "output_summary": generated_content[:200] + "..." if len(generated_content) > 200 else generated_content,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context_id": interaction_context_id,
                    "model_used": llm_model_name_for_logging # Use the dynamically determined model name for logging
                }
                await self.user_profile_manager.update_last_interaction_summary(summary)
                # print(f"Logged idea synthesis interaction with ID: {interaction_context_id}") # For debug

            return generated_content

