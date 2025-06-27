# Coddy/core/idea_synth.py

import asyncio
import os
import re
from typing import List, Dict, Any, Optional

from core.llm_provider import LLMProvider, get_llm_provider
from core.logging_utility import log_info, log_error, logger # Import logger for sync use

# Load environment variables from .env file
# dotenv.load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env')) # Handled by main entry point

# No longer needed as LLMProvider handles API key management
# API_KEY = os.environ.get('GEMINI_API_KEY', "")
# GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"

class IdeaSynthesizer:
    """
    Generates creative ideas and solutions using a large language model (LLM).
    Supports standard and 'weird' (creative/chaotic) modes, and can incorporate constraints.#
    Also provides a general text summarization/generation capability.

    """

    def __init__(self, user_id: str = "default_user_synth"):
        """
        Initializes the IdeaSynthesizer.

        Args:
            user_id: An identifier for the current user, useful for logging or personalization.
        """
        self.user_id: str = user_id
        # TODO: Load provider and config from user profile.
        # For now, default to Gemini for backward compatibility.
        # This can be made configurable via user profile in Phase 15/19
        provider_name: str = "gemini" 
        provider_config: Dict[str, Any] = {} # Empty config uses env vars for Gemini
        try:
            self.llm_provider: LLMProvider = get_llm_provider(provider_name, provider_config)
        except ValueError as e:
            # Use the synchronous logger here as __init__ cannot be async
            logger.error(f"Failed to initialize LLM provider: {e}. This may be due to a missing API key.")
            # Depending on desired behavior, could raise, or use a dummy provider
            raise


    async def generate_idea(
        self,
        base_idea: str,
        weird_mode: bool = False,
        constraints: Optional[List[str]] = None,
        num_solutions: int = 1
    ) -> List[str]:
        """
        Generates creative ideas based on a base idea, with optional 'weird mode' and constraints.

        Args:
            base_idea: The initial concept or problem statement.
            weird_mode: If True, encourages more unconventional and chaotic ideas.
            constraints: A list of strings defining limitations or requirements.
            num_solutions: The number of distinct ideas to generate.

        Returns:
            A list of generated ideas/solutions.
        """
        await log_info(f"Generating idea for: '{base_idea}' (Weird Mode: {weird_mode}, Constraints: {constraints})...")

        prompt_template = "Generate an idea for: '{base_idea}'.\n"
        if constraints:
            prompt_template += "Consider the following constraints: {constraints}.\n"
        if weird_mode:
            prompt_template += "Make it exceptionally creative, unconventional, and push the boundaries of typical solutions. Embrace chaotic and surprising elements."
            temperature = 0.9
            top_p = 0.95
        else:
            prompt_template += "Provide a practical and innovative solution."
            temperature = 0.7
            top_p = 0.9

        if num_solutions > 1:
            # Instruct the LLM to provide a numbered list for easier parsing
            prompt_template += f"\nGenerate {num_solutions} distinct solutions, presented as a numbered list (1., 2., 3., etc.) without any introductory or concluding remarks, just the list items."

        final_prompt = prompt_template.format(
            base_idea=base_idea,
            constraints=", ".join(constraints) if constraints else ""
        )

        generated_ideas = []
        try:
            raw_response = await self.llm_provider.generate_text(final_prompt, temperature=temperature, top_p=top_p)
            
            if num_solutions > 1:
                # Use re.findall to capture content of each numbered list item
                # This regex looks for "digit. " at the start of a line and captures everything
                # until the next "digit. " or the end of the string.
                # re.MULTILINE makes '^' match the start of lines, re.DOTALL makes '.' match newlines.
                item_regex = r'^\s*\d+\.\s*(.*?)(?=\n\s*\d+\.\s*|$)'
                
                extracted_ideas = re.findall(item_regex, raw_response, re.MULTILINE | re.DOTALL)
                
                # Clean up extracted ideas: strip whitespace, remove any remaining markdown list/heading prefixes
                cleaned_ideas = [
                    re.sub(r'#+\s*|[-*]\s*', '', idea.strip()).strip() # Remove common markdown list/heading prefixes if any remain
                    for idea in extracted_ideas if idea.strip() # Ensure it's not empty
                ]
                generated_ideas.extend(cleaned_ideas)
            else:
                generated_ideas.append(raw_response.strip())
        except Exception as e:
            await log_error(f"Error generating idea: {e}", exc_info=True)
            generated_ideas.append(f"Failed to generate idea: {e}")

        # Deduplicate and limit to requested number if generation created more
        if num_solutions > 1:
            generated_ideas = list(dict.fromkeys(generated_ideas))[:num_solutions]
        
        await log_info("Idea generation complete.")
        return generated_ideas

    async def summarize_text(self, prompt: str, temperature: float = 0.5, top_p: float = 0.95) -> str:
        """
        Generates a summary for a given text using the LLM.

        Args:
            prompt: The text prompt to send to the LLM for summarization.
            temperature: Controls the randomness of the output. Lower is better for summaries.
            top_p: The nucleus sampling parameter.

        Returns:
            The generated summary text from the LLM.
        """
        await log_info(f"Generating summary for prompt: '{prompt[:70]}...'")
        summary = await self.llm_provider.generate_text(prompt, temperature=temperature, top_p=top_p)
        return summary


# Example Usage (for testing the IdeaSynthesizer)
async def main_test_idea_synth():
    await log_info("\n--- Testing IdeaSynthesizer ---")

    try:
        idea_synth = IdeaSynthesizer(user_id="test_user_synth")
    except ValueError as e:
        await log_error(f"Could not start IdeaSynthesizer test: {e}")
        return

    # Test Standard Mode
    await log_info("\n--- Standard Idea Generation (Single) ---")
    standard_ideas = await idea_synth.generate_idea(
        base_idea="a new note-taking app",
        num_solutions=1
    )
    for idea in standard_ideas:


    # Test Weird Mode (Single)
        print("\n--- Weird Mode Idea Generation (Single) ---")
    weird_ideas = await idea_synth.generate_idea(
        base_idea="a new note-taking app",
        weird_mode=True,
        num_solutions=1
    )
    for idea in weird_ideas:
        print(f"Weird Idea: {idea}")

    # Test Standard Mode with Constraints (Multiple)
    print("\n--- Standard Idea Generation with Constraints (Multiple) ---")
    constrained_ideas = await idea_synth.generate_idea(
        base_idea="a new command-line tool",
        constraints=["must be written in Python", "must interact with local files"],
        num_solutions=2
    )
    for i, idea in enumerate(constrained_ideas):
        print(f"Constrained Idea {i+1}: {idea}")

    # Test Weird Mode with Constraints (Multiple)
    print("\n--- Weird Mode Idea Generation with Constraints (Multiple) ---")
    weird_constrained_ideas = await idea_synth.generate_idea(
        base_idea="a new productivity tool for developers",
        weird_mode=True,
        constraints=["must use AI", "must be visual", "should feel like a companion"],
        num_solutions=3
    )
    for i, idea in enumerate(weird_constrained_ideas):
        print(f"Weird & Constrained Idea {i+1}: {idea}")

    print("\n--- End of IdeaSynthesizer Tests ---")

if __name__ == "__main__":
    # To run this example:
    # 1. Create a .env file in your Coddy project root (e.g., Coddy/.env)
    #    and add your Gemini API key: GEMINI_API_KEY="YOUR_API_KEY_HERE"
    # 2. Ensure `python-dotenv` is installed: `pip install python-dotenv`
    # 3. Ensure you have network access to the Gemini API.
    # 4. Run this script: `python Coddy/core/idea_synth.py`
    asyncio.run(main_test_idea_synth())
