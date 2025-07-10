# Coddy/core/changelog_generator.py

from __future__ import annotations # Enable postponed evaluation of type annotations
import asyncio
import os
import json
from typing import Any, Optional, List, Dict

# Use absolute imports from the project root for consistency
from core.utility_functions import write_file
from core.logging_utility import log_info, log_warning, log_error, log_debug
from core.user_profile import UserProfile
from core.git_analyzer import GitAnalyzer
# REMOVED: from langchain_google_genai import ChatGoogleGenerativeAI # No longer instantiate here
from core.llm_provider import LLMProvider # NEW: Import LLMProvider base class for type hinting

class ChangelogGenerator:
    """
    Generates a Markdown changelog from Git commit history.
    Supports commit categorization, tag ranges, and GitHub linking.
    """
    # MODIFIED: Accept llm_provider instance directly instead of model_name
    def __init__(self, llm_provider: LLMProvider, memory_service: Any, git_analyzer: GitAnalyzer, user_profile_manager: Optional[UserProfile] = None):
        self.llm_provider = llm_provider # Store the LLMProvider instance
        self.memory_service = memory_service
        self.git_analyzer = git_analyzer
        self.user_profile_manager = user_profile_manager # Store the user profile manager

    async def _get_personalization_hints(self, user_profile: Optional[Dict[str, Any]]) -> str:
        """
        Constructs a string of personalization hints for the LLM based on the user profile.
        (Similar to IdeaSynthesizer/CodeGenerator, but simplified for Changelog context)
        """
        hints = []
        if user_profile:
            preferred_languages = user_profile.get('preferred_languages', [])
            if preferred_languages:
                hints.append(f"Consider the user's preferred languages: {', '.join(preferred_languages)}.")
            # Add other relevant profile aspects for changelog generation if needed
            # e.g., tone, verbosity, specific formatting preferences.
        return "\n".join(hints) if hints else ""

    async def generate_changelog(self, *, since_tag: Optional[str] = None, until_tag: Optional[str] = None, num_commits: Optional[int] = None, repo_url: Optional[str] = None, user_profile: Optional[Dict[str, Any]] = None, output_file: str = "CHANGELOG.md") -> str:
        await log_info("Generating changelog...")
        # Use the GitAnalyzer dependency to fetch logs
        commits = await self.git_analyzer.get_commit_logs(
            since_tag=since_tag, until_tag=until_tag, num_commits=num_commits
        )

        if not commits:
            await log_warning("No commits found to generate changelog.")
            return "# Changelog\n\n_No changes found._"

        # Use the LLM to generate the changelog content
        personalization_hints = await self._get_personalization_hints(user_profile)
        
        prompt = f"""
        You are an expert at writing software changelogs in Markdown format.
        Based on the following git commits, generate a changelog.
        
        Instructions:
        1. Categorize the changes into sections like 'Features', 'Bug Fixes', 'Refactoring', 'Documentation', 'Tests', and 'Chores'.
        2. Use conventional commit prefixes (e.g., 'feat:', 'fix:', 'docs:') from the commit subjects to guide categorization.
        3. For each entry, include the commit message (subject), a link to the commit, the author, and the date.
        4. If the repository URL is provided, use it to create full commit and issue links.
        5. If personalization hints are provided, consider them in the tone and style of the changelog.
        
        Repository URL for links: {repo_url or 'Not provided'}
        Personalization Hints: {personalization_hints or 'None'}
        
        Raw Commit Data (JSON):
        {json.dumps(commits, indent=2)}
        
        Generate only the Markdown content for the changelog.
        """

        try:
            # MODIFIED: Use the injected llm_provider to generate text
            changelog_content = await self.llm_provider.generate_text(
                prompt=prompt,
                temperature=0.2 # Keep a low temperature for factual generation
            )
        except Exception as e:
            await log_error(f"LLM failed to generate changelog: {e}", exc_info=True)
            return f"# Changelog Generation Failed\n\nAn error occurred: {e}"

        # Save to file
        await self.save_changelog_to_file(changelog_content=changelog_content, file_path=output_file)

        await log_info(f"Changelog generated with {len(commits)} commits.")
        return changelog_content

    async def save_changelog_to_file(self, *, changelog_content: str, file_path: str = "CHANGELOG.md"):
        try:
            await write_file(file_path, changelog_content)
            await log_info(f"Changelog saved to {file_path}")
        except Exception as e:
            await log_error(f"Error saving changelog to file {file_path}: {e}", exc_info=True)

async def main_changelog_test():
    # This test setup needs to be updated to pass dependencies
    # For now, it will likely fail if run directly without a proper service setup.
    # This is a placeholder for a more comprehensive integration test.
    pass

if __name__ == "__main__":
    # This block is for direct execution and testing.
    # In a real application, ChangelogGenerator would be initialized by the FastAPI app.
    # To run this test, you'd need to mock or provide the dependencies.
    # asyncio.run(main_changelog_test())
    print("Run tests via the FastAPI application's lifespan or dedicated test suite.")
