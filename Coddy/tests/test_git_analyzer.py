import pytest
import asyncio
import os
import shutil
import subprocess
from unittest.mock import AsyncMock, patch

from core.git_analyzer import GitAnalyzer # Assuming core is in sys.path or accessible

# Fixture for a temporary Git repository
@pytest.fixture
async def temp_git_repo(tmp_path):
    """
    Creates a temporary Git repository for testing.
    Initializes a git repo, makes a commit, and creates a new branch.
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    original_cwd = os.getcwd()
    os.chdir(repo_path) # Change CWD to perform git commands

    try:
        # Initialize repo
        await asyncio.create_subprocess_exec("git", "init", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE).wait()
        await asyncio.create_subprocess_exec("git", "config", "user.email", "test@example.com", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE).wait()
        await asyncio.create_subprocess_exec("git", "config", "user.name", "Test User", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE).wait()

        # Initial commit
        (repo_path / "README.md").write_text("Hello, World!")
        await asyncio.create_subprocess_exec("git", "add", "README.md", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE).wait()
        await asyncio.create_subprocess_exec("git", "commit", "-m", "Initial commit", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE).wait()

        # Another commit
        (repo_path / "file1.txt").write_text("Content 1")
        await asyncio.create_subprocess_exec("git", "add", "file1.txt", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE).wait()
        await asyncio.create_subprocess_exec("git", "commit", "-m", "Add file1", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE).wait()

        # Create a new branch
        await asyncio.create_subprocess_exec("git", "branch", "feature-branch", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE).wait()

        yield repo_path

    finally:
        os.chdir(original_cwd) # Revert CWD
        shutil.rmtree(repo_path) # Clean up

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
        assert "main" in branches or "master" in branches # Depending on git default branch name
        assert "feature-branch" in branches
        assert len(branches) >= 2 # At least main/master and feature-branch

    async def test_get_current_branch(self, temp_git_repo):
        analyzer = GitAnalyzer(repo_path=str(temp_git_repo))
        current_branch = await analyzer.get_current_branch()
        assert current_branch == "main" or current_branch == "master" # Depending on git default

        # Checkout feature branch and test again
        await asyncio.create_subprocess_exec("git", "checkout", "feature-branch", cwd=temp_git_repo, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE).wait()
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
        with patch('asyncio.create_subprocess_exec', new=AsyncMock(side_effect=FileNotFoundError)):
            analyzer = GitAnalyzer(repo_path=str(tmp_path))
            with pytest.raises(FileNotFoundError, match="Git command not found"):
                await analyzer.get_status()

    async def test_invalid_repo_path(self, tmp_path):
        # Test with a non-existent directory
        non_existent_path = tmp_path / "non_existent_repo"
        analyzer = GitAnalyzer(repo_path=str(non_existent_path))
        status = await analyzer.get_status()
        assert "not a git repository" in status.lower() or "fatal: not a git repository" in status.lower()

    async def test_git_command_error(self, temp_git_repo):
        analyzer = GitAnalyzer(repo_path=str(temp_git_repo))
        # Use a command that will surely fail (e.g., non-existent subcommand)
        status = await analyzer._run_git_command(["non-existent-command"])
        assert "usage:" in status.lower() or "unknown command" in status.lower()

    @pytest.mark.asyncio
    @patch('core.git_analyzer.IdeaSynthesizer') # Mock IdeaSynthesizer
    async def test_summarize_repo_activity(self, MockIdeaSynthesizer, temp_git_repo):
        # Setup mock IdeaSynthesizer instance and its summarize method
        mock_idea_synthesizer_instance = MockIdeaSynthesizer.return_value
        mock_idea_synthesizer_instance.summarize_text.return_value = "AI-generated summary of repo activity."

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
