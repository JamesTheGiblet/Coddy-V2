#tests/test_git_analyzer.py

import pytest
import asyncio
import os
import shutil
import subprocess
from unittest.mock import AsyncMock, patch

from core.git_analyzer import GitAnalyzer # Assuming core is in sys.path or accessible

# Fixture for a temporary Git repository
@pytest.fixture(scope="function")
def temp_git_repo(tmp_path):
    """
    Creates a temporary Git repository for testing.
    Initializes a git repo, makes a commit, and creates a new branch.
    This is a synchronous fixture to avoid issues with async fixture resolution.
    """
    repo_path = tmp_path / "test_repo" # tmp_path ensures this is cleaned up
    repo_path.mkdir()

    def run_git_command_sync(*args):
        process = subprocess.run(
            ["git", *args],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=False,
        )
        if process.returncode != 0:
            raise RuntimeError(f"Git command failed in fixture: git {' '.join(args)}\nSTDERR: {process.stderr}")

    # Initialize repo and set a deterministic default branch
    run_git_command_sync("init")
    run_git_command_sync("checkout", "-b", "main")
    run_git_command_sync("config", "user.email", "test@example.com")
    run_git_command_sync("config", "user.name", "Test User")

    # Initial commit
    (repo_path / "README.md").write_text("Hello, World!")
    run_git_command_sync("add", "README.md")
    run_git_command_sync("commit", "-m", "Initial commit")

    # Another commit
    (repo_path / "file1.txt").write_text("Content 1")
    run_git_command_sync("add", "file1.txt")
    run_git_command_sync("commit", "-m", "Add file1")

    # Create a new branch
    run_git_command_sync("branch", "feature-branch")

    return repo_path

@pytest.mark.asyncio
class TestGitAnalyzer:
    async def test_get_status_clean(self, temp_git_repo):
        analyzer = GitAnalyzer(repo_path=str(temp_git_repo))
        status = await analyzer.get_status()
        assert status == "" # Expect empty string for clean repo

    async def test_get_status_dirty(self, temp_git_repo):
        analyzer = GitAnalyzer(repo_path=str(temp_git_repo))
        (temp_git_repo / "new_file.txt").write_text("Unstaged content")
        status = await analyzer.get_status()
        assert "?? new_file.txt" in status

    async def test_get_branches(self, temp_git_repo):
        analyzer = GitAnalyzer(repo_path=str(temp_git_repo))
        branches = await analyzer.get_branches()
        assert "main" in branches
        assert "feature-branch" in branches
        assert len(branches) == 2

    async def test_get_current_branch(self, temp_git_repo):
        analyzer = GitAnalyzer(repo_path=str(temp_git_repo))
        current_branch = await analyzer.get_current_branch()
        assert current_branch == "main"

        # Checkout feature branch and test again
        process = await asyncio.create_subprocess_exec("git", "checkout", "feature-branch", cwd=temp_git_repo, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.wait()
        current_branch = await analyzer.get_current_branch()
        assert current_branch == "feature-branch"

    async def test_get_commit_logs(self, temp_git_repo):
        analyzer = GitAnalyzer(repo_path=str(temp_git_repo))
        commits = await analyzer.get_commit_logs(limit=2)
        assert len(commits) == 2
        assert "Add file1" in commits[0]["message"]
        assert "Initial commit" in commits[1]["message"]
        assert "hash" in commits[0]
        assert "author" in commits[0]
        assert "date" in commits[0]

    async def test_git_not_found(self, tmp_path):
        # Temporarily mock subprocess_exec to simulate git not found
        with patch('core.git_analyzer.GitAnalyzer._run_git_command', new=AsyncMock(side_effect=FileNotFoundError("Git command not found"))):
            analyzer = GitAnalyzer(repo_path=str(tmp_path))
            status = await analyzer.get_status()
            assert "Git command not found" in status

    async def test_not_a_git_repo(self, tmp_path):
        # Test with an existing directory that is not a Git repository
        not_a_repo_path = tmp_path / "not_a_repo"
        not_a_repo_path.mkdir()
        analyzer = GitAnalyzer(repo_path=str(not_a_repo_path))
        status = await analyzer.get_status()
        assert "not a git repository" in status.lower()

    async def test_git_command_error(self, temp_git_repo):
        analyzer = GitAnalyzer(repo_path=str(temp_git_repo))
        # Use a command that will surely fail (e.g., non-existent subcommand)
        with pytest.raises(subprocess.CalledProcessError) as excinfo:
            await analyzer._run_git_command(["non-existent-command"])
        error_output = excinfo.value.stderr.lower()
        assert "is not a git command" in error_output

    @patch('core.git_analyzer.IdeaSynthesizer') # Mock IdeaSynthesizer
    async def test_summarize_repo_activity(self, MockIdeaSynthesizer, temp_git_repo):
        # Setup mock IdeaSynthesizer instance and its summarize method
        mock_idea_synthesizer_instance = MockIdeaSynthesizer.return_value
        mock_idea_synthesizer_instance.summarize_text = AsyncMock(return_value="AI-generated summary of repo activity.")

        analyzer = GitAnalyzer(repo_path=str(temp_git_repo))
        
        # Ensure there are commits to summarize
        commits = await analyzer.get_commit_logs(limit=2)
        assert len(commits) > 0 # Verify commits were fetched

        summary = await analyzer.summarize_repo_activity(num_commits=2)
        
        # Assert that IdeaSynthesizer was called
        MockIdeaSynthesizer.assert_called_once()
        mock_idea_synthesizer_instance.summarize_text.assert_called_once()
        
        # Check if the summary is as expected from the mock
        assert summary == "AI-generated summary of repo activity."
