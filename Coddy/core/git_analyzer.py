# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\git_analyzer.py

import asyncio
import subprocess
from typing import Optional, List, Dict
import os
from core.idea_synth import IdeaSynthesizer # Assuming IdeaSynthesizer is in core

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
            commits = await self.get_commit_logs(limit=num_commits)
            if not commits:
                return "No recent commits to summarize."

            # Format commit messages into a single string for IdeaSynthesizer
            commit_messages = "\n".join([c['message'] for c in commits])
            
            prompt = (
                "Summarize the following recent Git commit messages to provide a high-level overview "
                "of the repository's recent activity and progress. Focus on key changes and new features.\n\n"
                f"Commit Messages:\n{commit_messages}"
            )
            
            # Initialize IdeaSynthesizer and get summary
            idea_synthesizer = IdeaSynthesizer()
            summary = await idea_synthesizer.summarize_text(prompt)
            return summary
        except Exception as e:
            print(f"Error summarizing repository activity: {e}")
            return f"Could not generate summary: {e}"

# Example usage (for testing purposes, typically called by other modules)
async def main():
    # You might want to initialize a temporary Git repo here for testing the main function
    # For now, assumes current directory is a Git repo
    analyzer = GitAnalyzer()
    print(f"Current repository path: {analyzer.repo_path}")

    # Test get_status
    status = await analyzer.get_status()
    print("\n--- Git Status ---")
    print(status if status else "No changes in working directory.")

    # Test get_branches
    branches = await analyzer.get_branches()
    print("\n--- Git Branches ---")
    if branches:
        for branch in branches:
            print(f"- {branch}")
    else:
        print("No branches found.")

    # Test get_current_branch
    current_branch = await analyzer.get_current_branch()
    print("\n--- Current Branch ---")
    print(current_branch if current_branch else "Detached HEAD or no branch.")

    # Test get_commit_logs
    commits = await analyzer.get_commit_logs(limit=3)
    print("\n--- Recent Commits ---")
    if commits:
        for commit in commits:
            print(f"Hash: {commit['hash']}")
            print(f"Author: {commit['author']}")
            print(f"Date: {commit['date']}")
            print(f"Message: {commit['message']}\n")
    else:
        print("No commits found.")

    # Test summarize_repo_activity
    repo_summary = await analyzer.summarize_repo_activity(num_commits=5)
    print("\n--- Repository Activity Summary (AI-Generated) ---")
    print(repo_summary)


if __name__ == "__main__":
    # To run this example, ensure you are in a Git repository or set repo_path
    # You would typically set up a dummy git repo for testing this locally
    # asyncio.run(main())
    pass # Keep pass to avoid running on import by default
