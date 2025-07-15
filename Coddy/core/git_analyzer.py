# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\git_analyzer.py

import asyncio
import subprocess
from typing import Optional, List, Dict
import os
import shutil # For rmtree # NEW
from core.idea_synth import IdeaSynthesizer # Assuming IdeaSynthesizer is in core
from backend.services import services # NEW: Import the centralized services dictionary

class GitAnalyzer:
    """
    A class to interact with Git repositories and provide analysis.
    This class aims to be asynchronous where possible to avoid blocking operations.
    """

    def __init__(self, repo_path: Optional[str] = None):
        """
        Initializes the GitAnalyzer.

        Args:
            repo_path (Optional[str]): The path to the Git repository. If None,
                                        it defaults to the current working directory.
        """
        self.repo_path = repo_path if repo_path else os.getcwd()

    async def _run_git_command(self, command: List[str]) -> str:
        """
        Runs a Git command asynchronously and returns its stdout.

        Args:
            command (List[str]): A list of strings representing the Git command and its arguments.

        Returns:
            str: The standard output of the Git command.

        Raises:
            subprocess.CalledProcessError: If the Git command returns a non-zero exit code.
            FileNotFoundError: If 'git' command is not found.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "git",
                *command,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                # Log stderr for debugging purposes, but only raise error if stderr exists
                error_message = stderr.decode(errors='ignore').strip()
                if error_message:
                    raise subprocess.CalledProcessError(
                        process.returncode,
                        f"git {' '.join(command)}",
                        stderr=error_message
                    )
                else:
                    # If stderr is empty but returncode is not 0, raise a generic error
                    raise subprocess.CalledProcessError(
                        process.returncode,
                        f"git {' '.join(command)}",
                        stderr="Unknown Git command error."
                    )
            return stdout.decode(errors='ignore').strip()
        except FileNotFoundError:
            raise FileNotFoundError("Git command not found. Please ensure Git is installed and in your PATH.")
        except Exception as e:
            print(f"Error running Git command: {' '.join(command)} - {e}")
            raise

    async def get_status(self) -> str:
        """
        Asynchronously gets the current Git repository status.

        Returns:
            str: The output of 'git status --short'.
        """
        try:
            return await self._run_git_command(["status", "--short"])
        except subprocess.CalledProcessError as e:
            # For status, it's more useful to return the stderr message
            return e.stderr
        except Exception as e:
            # Return an informative error message instead of re-raising for status
            return f"Error getting Git status: {e}"

    async def get_branches(self) -> List[str]:
        """
        Asynchronously gets a list of local Git branches.

        Returns:
            List[str]: A list of branch names.
        """
        try:
            output = await self._run_git_command(["branch", "--format=%(refname:short)"])
            return [branch.strip() for branch in output.split('\n') if branch.strip()]
        except Exception as e:
            print(f"Error getting Git branches: {e}")
            return []

    async def get_current_branch(self) -> Optional[str]:
        """
        Asynchronously gets the name of the current Git branch.

        Returns:
            Optional[str]: The name of the current branch, or None if not on a branch.
        """
        try:
            return await self._run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
        except subprocess.CalledProcessError as e:
            # This specific error likely means "not a git repo" or "detached HEAD"
            if "not a git repository" in e.stderr.lower():
                return "Not a Git repository"
            return "Detached HEAD or no branch"
        except Exception as e:
            print(f"Error getting current Git branch: {e}")
            return None

    async def get_commit_logs(self, num_commits: Optional[int] = None, since_tag: Optional[str] = None, until_tag: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Asynchronously retrieves recent commit logs.

        Args:
            num_commits (Optional[int]): The maximum number of commit logs to retrieve.
            since_tag (Optional[str]): The starting tag or commit for the log range.
            until_tag (Optional[str]): The ending tag or commit for the log range.

        Returns:
            List[Dict[str, str]]: A list of dictionaries, each representing a commit
                                    with 'hash', 'author', 'date', 'subject', and 'body'.
        """
        try:
            # Use null byte as a separator for robustness
            log_format = "%H%n%an%n%ad%n%s%n%b%x00"
            command = ["log", "--no-merges", f"--pretty=format:{log_format}"]
            if since_tag and until_tag:
                command.append(f"{since_tag}..{until_tag}")
            elif since_tag:
                command.append(since_tag)
            if num_commits:
                command.append(f"-n{num_commits}")

            output = await self._run_git_command(command)

            commits = []
            commit_raw_entries = [entry for entry in output.strip().split('\x00') if entry.strip()]

            for commit_raw in commit_raw_entries:
                parts = commit_raw.strip().split('\n', 4)
                if len(parts) >= 4 and parts[0]:
                    commits.append({
                        "hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "subject": parts[3],
                        "body": parts[4].strip() if len(parts) > 4 else ""
                    })
            return commits
        except Exception as e:
            print(f"Error getting Git commit logs: {e}")
            return []

    async def summarize_repo_activity(self, num_commits: int = 5) -> str:
        """
        Asynchronously generates an AI-powered summary of recent repository activity
        based on commit logs.

        Args:
            num_commits (int): The number of recent commits to consider for the summary.

        Returns:
            str: An AI-generated summary of the repository activity.
        """
        try:
            commits = await self.get_commit_logs(num_commits=num_commits) # Changed limit to num_commits
            if not commits:
                return "No recent commits to summarize."

            # Format commit messages into a single string for IdeaSynthesizer
            # Assuming 'subject' is the main message for now
            commit_messages = "\n".join([c['subject'] + "\n" + c['body'] for c in commits]) # Include body
            
            prompt = (
                "Summarize the following recent Git commit messages to provide a high-level overview "
                "of the repository's recent activity and progress. Focus on key changes and new features.\n\n"
                f"Commit Messages:\n{commit_messages}"
            )
            
            # MODIFIED: Initialize IdeaSynthesizer with dependencies from services
            llm_provider = services.get("llm_provider")
            memory_service = services.get("memory_service")
            user_profile_manager = services.get("user_profile_manager")

            if not llm_provider or not memory_service or not user_profile_manager:
                return "Error: LLM services not available for summarizing repository activity."

            idea_synthesizer = IdeaSynthesizer(
                llm_provider=llm_provider,
                memory_service=memory_service,
                user_profile_manager=user_profile_manager
            )
            summary = await idea_synthesizer.synthesize_idea(
                prompt=prompt,
                user_profile=user_profile_manager.profile.model_dump() if user_profile_manager.profile else {}
            ) # Changed summarize_text to synthesize_idea, assuming it's a general text generation method
            
            return summary.get("idea", "Could not generate summary.") # Assuming synthesize_idea returns dict with 'idea' key
        except Exception as e:
            print(f"Error summarizing repository activity: {e}")
            return f"Could not generate summary: {e}"

# Example usage for testing purposes - Renamed from main to main_test_git_analyzer
async def main_test_git_analyzer():
    print("\n--- Testing GitAnalyzer with Temporary Repo ---")
    
    test_repo_dir = "temp_test_git_repo"
    if os.path.exists(test_repo_dir):
        shutil.rmtree(test_repo_dir) # Clean up previous test repo if it exists
    os.makedirs(test_repo_dir)
    original_cwd = os.getcwd()
    os.chdir(test_repo_dir) # Change to temporary directory

    try:
        # Initialize a temporary Git repo
        print(f"Initializing Git repo in {os.getcwd()}")
        await asyncio.create_subprocess_shell("git init -b main") # Initialize on 'main' branch directly
        await asyncio.create_subprocess_shell("git config user.email 'test@example.com'")
        await asyncio.create_subprocess_shell("git config user.name 'Test User'")

        # Create some dummy files and commits
        with open("file1.txt", "w") as f:
            f.write("Initial content")
        await asyncio.create_subprocess_shell("git add file1.txt")
        await asyncio.create_subprocess_shell("git commit -m 'feat: Initial commit with file1'")

        with open("file2.txt", "w") as f:
            f.write("Second file content")
        await asyncio.create_subprocess_shell("git add file2.txt")
        await asyncio.create_subprocess_shell("git commit -m 'fix: Add file2'")

        with open("file1.txt", "a") as f:
            f.write("\nAppended content")
        await asyncio.create_subprocess_shell("git add file1.txt")
        await asyncio.create_subprocess_shell("git commit -m 'docs: Update file1 with more info'")

        analyzer = GitAnalyzer()
        print(f"Current repository path: {analyzer.repo_path}")

        # Test get_status
        status = await analyzer.get_status()
        print("\n--- Git Status ---")
        print(status if status else "No changes in working directory.")
        assert "no changes" in status.lower() # Should be clean after commits

        # Test get_branches
        branches = await analyzer.get_branches()
        print("\n--- Git Branches ---")
        if branches:
            for branch in branches:
                print(f"- {branch}")
            assert "main" in branches
        else:
            print("No branches found.")

        # Test get_current_branch
        current_branch = await analyzer.get_current_branch()
        print("\n--- Current Branch ---")
        print(current_branch if current_branch else "Detached HEAD or no branch.")
        assert current_branch == "main"

        # Test get_commit_logs
        commits = await analyzer.get_commit_logs(num_commits=3)
        print("\n--- Recent Commits ---")
        if commits:
            for commit in commits:
                print(f"Hash: {commit['hash']}")
                print(f"Author: {commit['author']}")
                print(f"Date: {commit['date']}")
                print(f"Subject: {commit['subject']}")
                print(f"Body: {commit['body']}\n")
            assert len(commits) == 3
            assert "feat: Initial commit" in commits[2]['subject'] # Check oldest commit
        else:
            print("No commits found.")

        # Test summarize_repo_activity (requires LLM services to be initialized in backend)
        # This part of the test might need the actual backend/main.py running.
        # For an isolated test, mock IdeaSynthesizer's LLM interaction.
        print("\n--- Repository Activity Summary (AI-Generated) ---")
        # Ensure services are set up for this standalone test if needed
        # (This block assumes services are manually setup or mocked for test context)
        from core.llm_provider import MockLLMProvider # Assuming a mock LLM provider exists
        from core.memory_service import MemoryService # Used by UserProfile
        from core.user_profile import UserProfile # Used by IdeaSynthesizer

        _temp_memory_service = MemoryService(session_id="test_git_llm_session", user_id="test_git_llm_user")
        _temp_user_profile = UserProfile(session_id="test_git_llm_session", user_id="test_git_llm_user", memory_service=_temp_memory_service)
        await _temp_user_profile.initialize()
        _temp_llm_provider = MockLLMProvider() # Use the mock here

        # Manually populate services dict just for this test
        services['llm_provider'] = _temp_llm_provider
        services['memory_service'] = _temp_memory_service
        services['user_profile_manager'] = _temp_user_profile

        repo_summary = await analyzer.summarize_repo_activity(num_commits=3)
        print(repo_summary)
        # Assert that the summary contains expected mock text or format
        assert "mock-llm generated response" in repo_summary or "Could not generate summary" in repo_summary
        
    except FileNotFoundError as e:
        print(f"Test Setup Error: {e}. Please ensure Git is installed.")
    except Exception as e:
        print(f"GitAnalyzer Test Failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        os.chdir(original_cwd) # Change back to original directory
        if os.path.exists(test_repo_dir):
            shutil.rmtree(test_repo_dir) # Clean up temporary directory
            print(f"\nCleaned up temporary repo: {test_repo_dir}")
        
    print("\n--- End of GitAnalyzer Tests ---")


if __name__ == "__main__":
    asyncio.run(main_test_git_analyzer())