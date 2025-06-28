# tests/test_refactor_thyself_plugin.py
import unittest
import asyncio
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path
from click.testing import CliRunner
import os # Import os for temporary directory handling
import shutil # Import shutil for rmtree

# Assuming refactor_thyself is a Click command, so we need to import its callback
from plugins.test_thyself_plugin.cli import refactor_thyself

class TestRefactorThyselfPlugin(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.runner = CliRunner()
        # Create a temporary directory for tests that need a real path
        self.temp_dir = Path("temp_test_coddy_dir")
        self.temp_dir.mkdir(exist_ok=True, parents=True) # Ensure it exists for CliRunner
        self.test_dir = self.temp_dir # Use the temporary directory as the base
        self.test_file_1 = self.test_dir / "file1.py"
        self.test_file_2 = self.test_dir / "file2.py"

    def tearDown(self):
        # Clean up the temporary directory after each test
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir) # Use rmtree to delete directory and its contents

    # Patch click.echo at its source (assuming it's imported as `import click` and used as `click.echo`)
    @patch("plugins.test_thyself_plugin.cli.click.echo") # Reverted to specific patch target
    @patch("plugins.test_thyself_plugin.cli.Path.rglob")
    async def test_dry_run_refactor(self, mock_rglob, mock_echo): # Mocks order matters for args
        # Setup - mock files found
        mock_file1_path = MagicMock(spec=Path)
        mock_file1_path.name = self.test_file_1.name
        mock_file1_path.__str__.return_value = str(self.test_file_1)
        mock_file1_path.read_text = AsyncMock(return_value="def foo(): pass") # Mock read_text directly

        mock_file2_path = MagicMock(spec=Path)
        mock_file2_path.name = self.test_file_2.name
        mock_file2_path.__str__.return_value = str(self.test_file_2)
        mock_file2_path.read_text = AsyncMock(return_value="class Bar: pass") # Mock read_text directly

        mock_rglob.return_value = [mock_file1_path, mock_file2_path]

        # Mock asyncio.to_thread behavior
        with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
            async def side_effect_for_dry_run(func, *args, **kwargs):
                if func == mock_file1_path.read_text:
                    return await mock_file1_path.read_text.coro # Call the actual mock's coro
                elif func == mock_file2_path.read_text:
                    return await mock_file2_path.read_text.coro
                return None
            mock_to_thread.side_effect = side_effect_for_dry_run

            # Run dry-run mode
            result = await refactor_thyself.callback(
                target_path=str(self.test_dir),
                instruction="Add docstrings",
                dry_run=True,
                verbose=False,
            )

            echo_calls = [call.args[0] for call in mock_echo.call_args_list]
            print("\n--- Dry Run Echo Calls ---") # Keep debugging print
            for call in echo_calls:
                print(call)
            print("--------------------------\n")

            self.assertIn(f"[DRY-RUN] Would update {self.test_file_1.name}", echo_calls)
            self.assertIn(f"[DRY-RUN] Would update {self.test_file_2.name}", echo_calls)
            self.assertTrue(any("Dry-run mode" in s for s in echo_calls))
            self.assertEqual(result, 0)

    @patch("plugins.test_thyself_plugin.cli.click.echo") # Reverted to specific patch target
    @patch("plugins.test_thyself_plugin.cli.Path.rglob")
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    async def test_actual_refactor(self, mock_to_thread, mock_rglob, mock_echo):
        # Setup - mock files found
        mock_file1_path = MagicMock(spec=Path)
        mock_file1_path.name = self.test_file_1.name
        mock_file1_path.__str__.return_value = str(self.test_file_1)
        mock_file1_path.read_text = AsyncMock(return_value="def foo(): pass")
        mock_file1_path.rename = AsyncMock(return_value=None)
        mock_file1_path.write_text = AsyncMock(return_value=None)
        mock_rglob.return_value = [mock_file1_path]

        # Setup read_text, rename, write_text mocks using side_effect on mock_to_thread
        async def side_effect_for_actual_refactor(func, *args, **kwargs):
            if func == mock_file1_path.read_text:
                return await mock_file1_path.read_text.coro
            elif func == mock_file1_path.rename:
                return await mock_file1_path.rename.coro
            elif func == mock_file1_path.write_text:
                return await mock_file1_path.write_text.coro
            return None

        mock_to_thread.side_effect = side_effect_for_actual_refactor

        result = await refactor_thyself.callback(
            target_path=str(self.test_dir),
            instruction="Add type hints",
            dry_run=False,
            verbose=False,
        )

        echo_calls = [call.args[0] for call in mock_echo.call_args_list]
        print("\n--- Actual Refactor Echo Calls ---") # Keep debugging print
        for call in echo_calls:
            print(call)
        print("----------------------------------\n")

        self.assertIn(f"Refactored {self.test_file_1.name} (backup saved as {self.test_file_1.name}.bak)", echo_calls)
        self.assertTrue(any("Refactoring complete" in s for s in echo_calls))
        self.assertEqual(result, 0)

    @patch("plugins.test_thyself_plugin.cli.click.echo") # Reverted to specific patch target
    @patch("plugins.test_thyself_plugin.cli.Path.rglob")
    @patch("asyncio.to_thread", new_callable=AsyncMock)
    async def test_file_read_error(self, mock_to_thread, mock_rglob, mock_echo):
        # Create a mock Path object whose read_text will raise an error
        mock_file1_path = MagicMock(spec=Path)
        mock_file1_path.name = self.test_file_1.name
        mock_file1_path.__str__.return_value = str(self.test_file_1)
        mock_file1_path.read_text = AsyncMock(side_effect=IOError("Read error"))
        mock_rglob.return_value = [mock_file1_path]

        async def side_effect_for_read_error(func, *args, **kwargs):
            if func == mock_file1_path.read_text:
                return await mock_file1_path.read_text.coro
            return None

        mock_to_thread.side_effect = side_effect_for_read_error

        result = await refactor_thyself.callback(
            target_path=str(self.test_dir),
            instruction="Cleanup code",
            dry_run=False,
            verbose=False,
        )
        echo_calls = [call.args[0] for call in mock_echo.call_args_list]
        print("\n--- File Read Error Echo Calls ---") # Keep debugging print
        for call in echo_calls:
            print(call)
        print("----------------------------------\n")

        self.assertTrue(any("Error reading" in s for s in echo_calls))
        self.assertEqual(result, 0)

    def test_cli_invocation_missing_target(self):
        result = self.runner.invoke(
            refactor_thyself,
            ["--instruction", "Do something", "non_existent_path_xyz"]
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("does not exist", result.output)

    def test_cli_invocation_no_py_files(self):
        # Ensure a real temporary directory exists for the CLI call
        # and then mock rglob to return nothing inside it.
        with patch("plugins.test_thyself_plugin.cli.Path.rglob", return_value=[]):
            result = self.runner.invoke(
                refactor_thyself,
                ["--instruction", "Refactor", str(self.test_dir)]
            )
            # Assert that the command exits successfully (exit code 0) if no files are found
            # because the command likely considers this a valid, albeit inactive, run.
            self.assertEqual(result.exit_code, 0) # Changed to assertEqual
            self.assertIn("No Python files found", result.output)


if __name__ == "__main__":
    unittest.main()