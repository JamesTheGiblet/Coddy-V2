import asyncio
import os
from typing import Any, Optional, List, Dict
import re

# FIX: Changed import path for execute_command
from Coddy.core.execution_manager import execute_command
# Removed: from utility_functions import execute_command, write_file # execute_command is moved, write_file is used directly or from utility_functions
from Coddy.core.utility_functions import write_file # Ensure write_file is imported if used directly here
from Coddy.core.logging_utility import log_info, log_warning, log_error, log_debug
from Coddy.core.user_profile import UserProfile # NEW: Import UserProfile

class ChangelogGenerator:
    """
    Generates a Markdown changelog from Git commit history.
    Supports commit categorization, tag ranges, and GitHub linking.
    """

    def __init__(self, memory_service: Any, git_analyzer: Any, user_profile_manager: Optional[UserProfile] = None): # NEW: Accept user_profile_manager
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

    async def _get_git_tags(self) -> List[str]:
        """
        Returns a list of Git tags sorted by creation order.
        """
        try:
            # Use the execute_command from ExecutionManager
            retcode, stdout, stderr = await execute_command("git tag --sort=creatordate")
            if retcode != 0:
                await log_warning(f"Failed to retrieve tags: {stderr}")
                return []
            return stdout.strip().splitlines()
        except Exception as e:
            await log_error(f"Error fetching git tags: {e}", exc_info=True)
            return []

    async def _get_git_log(self, since_tag: Optional[str] = None, until_tag: Optional[str] = None, num_commits: Optional[int] = None) -> List[Dict[str, str]]:
        log_format = "%H%n%an%n%ad%n%s%n%b%x00"
        command_parts = ["git", "log", "--no-merges", f"--pretty=format:{log_format}"]

        if since_tag and until_tag:
            command_parts.append(f"{since_tag}..{until_tag}")
        elif since_tag:
            command_parts.append(since_tag)

        if num_commits:
            command_parts.append(f"-n {num_commits}")

        try:
            # Use the execute_command from ExecutionManager
            return_code, stdout, stderr = await execute_command(" ".join(command_parts))

            if return_code != 0:
                await log_error(f"Git log command failed with exit code {return_code}: {stderr}")
                return []

            commits_raw = stdout.strip().split('\x00')
            commits_data = []

            for commit_raw in commits_raw:
                if not commit_raw.strip():
                    continue

                parts = commit_raw.split('\n', 4)
                if len(parts) >= 4:
                    commit_hash = parts[0].strip()
                    if not commit_hash:
                        # Skip commits with missing hash
                        continue
                    author = parts[1].strip()
                    date = parts[2].strip()
                    subject = parts[3].strip()
                    body = parts[4].strip() if len(parts) > 4 else ""

                    commits_data.append({
                        "hash": commit_hash,
                        "author": author,
                        "date": date,
                        "subject": subject,
                        "body": body
                    })
            return commits_data
        except Exception as e:
            await log_error(f"Error fetching Git log: {e}", exc_info=True)
            return []

    async def generate_changelog(self, *, since_tag: Optional[str] = None, until_tag: Optional[str] = None, num_commits: Optional[int] = None, repo_url: Optional[str] = None, user_profile: Optional[Dict[str, Any]] = None, output_file: str = "CHANGELOG.md") -> str: # NEW: Accept user_profile and output_file
        await log_info("Generating changelog...")
        commits = await self._get_git_log(since_tag=since_tag, until_tag=until_tag, num_commits=num_commits)

        if not commits:
            await log_warning("No commits found to generate changelog.")
            return "# Changelog\n\n_No changes found._"

        # Personalization hints for the LLM (if we were using an LLM for formatting)
        personalization_hints = await self._get_personalization_hints(user_profile)
        if personalization_hints:
            await log_info(f"Applying personalization hints for changelog: {personalization_hints}")

        categories = {
            "feat": ("✨ Features", []),
            "fix": ("🐛 Bug Fixes", []),
            "docs": ("📝 Documentation", []),
            "refactor": ("♻️ Refactoring", []),
            "test": ("✅ Tests", []),
            "chore": ("🧹 Chores", []),
            "other": ("🔄 Other", [])
        }

        for commit in commits:
            subject = commit['subject'].strip()
            if not subject:
                subject = commit['hash']  # fallback if subject empty

            # Remove all leading/trailing asterisks, including multiple '**'
            subject = re.sub(r'^\*+|\*+$', '', subject).strip()
            # Collapse multiple spaces
            subject = re.sub(r'\s+', ' ', subject)

            body = commit['body']
            match = re.match(r"^(feat|fix|docs|refactor|test|chore)(\(.+?\))?:\s+(.*)", subject, re.IGNORECASE)

            key = "other"
            message = subject

            if match:
                key = match.group(1).lower()
                message = match.group(3)

            full_hash = commit['hash']
            short_hash = full_hash[:7]
            commit_link = f"[`{short_hash}`]({repo_url}/commit/{full_hash})" if repo_url else f"`{short_hash}`"
            author = commit['author']
            date = commit['date'].split(' ')[0]  # ISO date or first token

            linked_body = re.sub(r"#(\d+)", rf"[#\1]({repo_url}/issues/\1)" if repo_url else r"#\1", body)

            entry = f"- **{message}:** ([`{short_hash}`]({repo_url}/commit/{full_hash}) by {author} on {date})"
            if linked_body:
                indented_body = "\n".join([f"  {line}" for line in linked_body.splitlines()])
                entry += f"\n{indented_body}\n"

            categories.setdefault(key, ("🔄 Other", []))[1].append(entry)

        changelog_lines = ["# Changelog\n"]

        for key, (title, items) in categories.items():
            if items:
                changelog_lines.append(f"## {title}\n")
                changelog_lines.extend(items)
                changelog_lines.append("")

        changelog_content = "\n".join(changelog_lines)
        
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

