# c:\Users\gilbe\Documents\GitHub\Coddy V2\Coddy/core/idea_synth.py
from __future__ import annotations # NEW: Enable postponed evaluation of type annotations
import asyncio
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, Optional # Added for type hints
import json # Added for json.dumps in prompt formatting
import uuid # NEW: For generating unique context_ids for interactions
from datetime import datetime # NEW: For timestamping interactions

# Add the project root to sys.path to allow imports from 'Coddy.core'
# This is a fallback for local testing; production environment might handle paths differently.
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from Coddy.core.user_profile import UserProfile # NEW: Import UserProfile
except ImportError as e:
    print(f"FATAL ERROR: Could not import UserProfile in IdeaSynthesizer: {e}", file=sys.stderr)
    # This error should ideally be handled gracefully or prevent startup if UserProfile is critical.
    # For now, we'll allow it to pass, but functionality depending on UserProfile will fail.
    UserProfile = None # Set to None if import fails to prevent NameError

load_dotenv() # Load environment variables, including API keys

class IdeaSynthesizer:
    """
    Synthesizes ideas and generates content using a large language model.
    This class is intended to be the primary interface for LLM interactions,
    now incorporating user profile for personalization and logging.
    """
    # Using 'Any' as a fallback for type hinting due to persistent 'Variable not allowed in type expression' error.
    # Ideally, 'Optional[UserProfile]' should work with 'from __future__ import annotations'.
    def __init__(self, user_profile_manager: Optional[Any] = None): # FIX: Use Any to avoid variable in type expression
        """
        Initializes the LLM and stores the UserProfileManager for logging.
        The LLM's model and temperature can be overridden dynamically based on user profile settings.
        """
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-pro", # Default model
            temperature=0.7,    # Default creativity/randomness, overridden later
            google_api_key=os.getenv("GEMINI_API_KEY")
        )
        if not os.getenv("GEMINI_API_KEY"):
            print("Warning: GEMINI_API_KEY not found in environment variables. LLM calls may fail.")
        
        self.user_profile_manager = user_profile_manager # Store the user profile manager

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
        llm_model = "gemini-pro" # Default model

        if user_profile:
            # Extract personalization settings
            persona = user_profile.get('idea_synth_persona', 'default')
            creativity = user_profile.get('idea_synth_creativity', 0.7)
            coding_style = user_profile.get('coding_style_preferences', {})
            preferred_languages = user_profile.get('preferred_languages', [])
            llm_provider_config = user_profile.get('llm_provider_config', {})

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
            
            # Apply LLM provider specific configurations if available (e.g., model name)
            llm_model = llm_provider_config.get('model_name', "gemini-pro")
        
        # Re-initialize LLM with potentially updated parameters for this specific call
        self.llm = ChatGoogleGenerativeAI(
            model=llm_model,
            temperature=llm_temperature,
            google_api_key=os.getenv("GEMINI_API_KEY")
        )

        messages = []
        if system_message_content:
            messages.append(SystemMessage(content=system_message_content))
        
        messages.append(HumanMessage(content=prompt))

        generated_content = ""
        interaction_context_id = str(uuid.uuid4()) # Generate a unique ID for this interaction

        try:
            # Make the asynchronous call to the LLM
            response = await self.llm.ainvoke(messages)
            
            # Extract the content from the LLM response object
            generated_content = response.content if hasattr(response, 'content') else str(response)
            
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
                    "model_used": llm_model
                }
                await self.user_profile_manager.update_last_interaction_summary(summary)
                # print(f"Logged idea synthesis interaction with ID: {interaction_context_id}") # For debug

            return generated_content
