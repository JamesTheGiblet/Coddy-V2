import unittest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from click.testing import CliRunner
import os
import shutil
import io # Import io for StringIO
import logging # Needed for assertLogs

# Import the synchronous wrapper command from its canonical location
from plugins.test_thyself_plugin.cli import refactor_thyself_sync

# Corrected Path for CodeGenerator class: Patch it where it's imported/used in cli.py
CODE_GENERATOR_CLASS_PATH = "plugins.test_thyself_plugin.cli.CodeGenerator"

class TestRefactorThyselfPlugin(unittest.TestCase): # Use unittest.TestCase
    def setUp(self):
        self.runner = CliRunner()
        # Create a temporary directory for tests that need a real path (e.g., test_cli_invocation_no_py_files)
        self.temp_dir = Path("temp_test_coddy_dir")
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        # Store the resolved absolute path directly in self.test_dir
        self.test_dir = self.temp_dir.resolve()


    def tearDown(self):
        # Clean up the temporary directory after each test
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _create_mock_py_file(self, filename: str, content: str = "pass"):
        """Helper to create a MagicMock Path object mimicking a Python file."""
        mock_file = MagicMock(spec=Path)
        mock_file.name = filename
        # Ensure __str__ returns a sensible absolute path string for comparison with actual output
        mock_file.__str__.return_value = str(self.test_dir / filename) # Use self.test_dir (already resolved)

        # Mock file operations as MagicMocks, and set their return_value/side_effect
        # when they are called (synchronously) by asyncio.to_thread
        mock_file.read_text = MagicMock(return_value=content, side_effect=None)
        mock_file.rename = MagicMock(return_value=None)
        mock_file.write_text = MagicMock(return_value=None)

        # Mock with_suffix for backup path creation
        # Ensure the .name of the mock backup path is what's expected in the output string
        mock_backup_path = MagicMock(name="backup_path")
        mock_backup_path.name = filename + ".bak"
        mock_backup_path.__str__.return_value = str(self.test_dir / filename) + ".bak" # Use self.test_dir (already resolved)
        mock_file.with_suffix.return_value = mock_backup_path
        return mock_file

    def test_cli_invocation_missing_target(self):
        """
        Tests that the refactor_thyself command correctly handles a non-existent target path.
        """
        result = self.runner.invoke(
            refactor_thyself_sync, # Call the synchronous wrapper
            ["--instruction", "Do something", "non_existent_path_xyz"]
        )
        # Expected exit code is non-zero because the path doesn't exist (Click's default behavior)
        self.assertNotEqual(result.exit_code, 0)
        # The error message from Click's path validation is present in result.output (for CliRunner)
        self.assertIn("Directory 'non_existent_path_xyz' does not exist.", result.output)


    @patch("plugins.test_thyself_plugin.cli.Path.rglob") # Patch rglob as it's a class method
    def test_cli_invocation_no_py_files(self, mock_rglob):
        """
        Tests that the refactor_thyself command handles a directory with no Python files.
        """
        mock_rglob.return_value = [] # Simulate no Python files found

        result = self.runner.invoke(
            refactor_thyself_sync, # Call the synchronous wrapper
            ["--instruction", "Refactor", str(self.test_dir)] # Use str(self.test_dir) which is now resolved
        )
        # Expect exit code 1 as per cli.py's return 1 on no files.
        self.assertEqual(result.exit_code, 1)

        # Corrected assertion: Check for the presence of the exact string.
        # Ensure the full string match is correct including the resolved path and newline.
        self.assertIn(f"No Python files found in {str(self.test_dir)}\n", result.output)


    @patch(CODE_GENERATOR_CLASS_PATH)
    @patch("plugins.test_thyself_plugin.cli.Path.rglob") # Patch rglob
    def test_cli_invocation_with_py_files(self, mock_rglob, MockCodeGenerator):
        """
        Tests that the refactor_thyself command processes Python files correctly.
        """
        mock_py_file = self._create_mock_py_file("sample.py", content="print('hello')")
        mock_rglob.return_value = [mock_py_file] # rglob returns our mock file

        mock_code_generator_instance = MockCodeGenerator.return_value
        mock_code_generator_instance.refactor_code = AsyncMock(return_value="refactored content")

        result = self.runner.invoke(
            refactor_thyself_sync,
            ["--instruction", "Make it async", str(self.test_dir)]
        )

        self.assertEqual(result.exit_code, 0)
        
        # Verify internal calls on the mock_py_file and MockCodeGenerator
        mock_py_file.read_text.assert_called_once_with(encoding='utf-8')
        mock_code_generator_instance.refactor_code.assert_called_once_with("print('hello')", "Make it async")
        mock_py_file.rename.assert_called_once_with(mock_py_file.with_suffix.return_value)
        mock_py_file.write_text.assert_called_once_with("refactored content", encoding='utf-8')
        
        # Verify output messages
        self.assertIn("=== Refactor Summary ===", result.output)
        self.assertIn(f"Refactored {mock_py_file.name} (backup saved as {mock_py_file.with_suffix.return_value.name})", result.output)
        self.assertIn("Refactoring complete. Backups saved with .bak extension.", result.output)


    @patch(CODE_GENERATOR_CLASS_PATH)
    @patch("plugins.test_thyself_plugin.cli.Path.rglob") # Patch rglob
    def test_refactor_file_error_is_handled_gracefully(self, mock_rglob, MockCodeGenerator):
        """
        Tests that the command handles errors during file processing (read/refactor/write) gracefully.
        """
        mock_py_file = self._create_mock_py_file("fail.py")
        mock_py_file.read_text.side_effect = IOError("Simulated read error") # Simulate error during read_text

        mock_rglob.return_value = [mock_py_file]

        mock_code_generator_instance = MockCodeGenerator.return_value
        # This mock will not be called if read fails as expected
        mock_code_generator_instance.refactor_code = AsyncMock(return_value="some content") 

        result = self.runner.invoke(
            refactor_thyself_sync,
            ["--instruction", "Handle error", str(self.test_dir)]
        )

        self.assertEqual(result.exit_code, 0) # Command should still exit 0 if it handles individual file errors
        # Now assert the expected error message is present
        self.assertIn(f"Error reading {mock_py_file.name}: Simulated read error", result.output)
        self.assertIn("=== Refactor Summary ===", result.output)
        self.assertIn("Refactoring complete.", result.output) # Overall completion message

        mock_py_file.read_text.assert_called_once_with(encoding='utf-8')
        mock_code_generator_instance.refactor_code.assert_not_called() # Should not call refactor_code
        mock_py_file.rename.assert_not_called()
        mock_py_file.write_text.assert_not_called()

    @patch(CODE_GENERATOR_CLASS_PATH)
    @patch("plugins.test_thyself_plugin.cli.Path.rglob") # Patch rglob
    def test_cli_dry_run_mode(self, mock_rglob, MockCodeGenerator):
        """
        Tests that the dry-run mode works correctly and no files are changed.
        """
        mock_py_file = self._create_mock_py_file("sample.py", content="print('original')")
        mock_rglob.return_value = [mock_py_file]

        mock_code_generator_instance = MockCodeGenerator.return_value
        mock_code_generator_instance.refactor_code = AsyncMock(return_value="print('refactored')") # Refactored content

        result = self.runner.invoke(
            refactor_thyself_sync,
            ["--instruction", "Make it async", "--dry-run", str(self.test_dir)]
        )

        self.assertEqual(result.exit_code, 0) # Dry run is a success
        mock_py_file.read_text.assert_called_once_with(encoding='utf-8')
        mock_code_generator_instance.refactor_code.assert_called_once() # refactor_code should still be called in dry-run
        mock_py_file.rename.assert_not_called() # Crucial: no file operations in dry-run
        mock_py_file.write_text.assert_not_called() # Crucial: no file operations in dry-run

        self.assertIn("[DRY-RUN] Would update sample.py", result.output)
        self.assertIn("Dry-run mode: No files were changed.", result.output)

    @patch(CODE_GENERATOR_CLASS_PATH)
    @patch("plugins.test_thyself_plugin.cli.Path.rglob") # Patch rglob
    @patch("plugins.test_thyself_plugin.cli.logger.info") # Patch logger.info
    @patch("plugins.test_thyself_plugin.cli.logger.debug") # Patch logger.debug
    def test_verbose_logging_emits_debug(self, mock_debug_logger, mock_info_logger, mock_rglob, MockCodeGenerator): # Correct order of mocks
        """
        Tests that verbose logging (`-v` flag) correctly sets the logger level to DEBUG
        and emits debug messages.
        """
        mock_py_file = self._create_mock_py_file("sample_verbose.py", content="print('verbose content')")
        mock_rglob.return_value = [mock_py_file]

        mock_code_generator_instance = MockCodeGenerator.return_value
        mock_code_generator_instance.refactor_code = AsyncMock(return_value="refactored verbose content")

        result = self.runner.invoke(
            refactor_thyself_sync,
            ["--instruction", "Add docstring", "--verbose", str(self.test_dir)]
        )
        
        self.assertEqual(result.exit_code, 0)

        # Assert logger.info calls
        mock_info_logger.assert_any_call(f"Starting self-refactor on: {str(self.test_dir)}")
        mock_info_logger.assert_any_call(f"Found 1 Python files to analyze.")

        # Assert logger.debug calls
        mock_debug_logger.assert_any_call(f"Starting refactor for {str(self.test_dir / mock_py_file.name)}")


    @patch(CODE_GENERATOR_CLASS_PATH)
    @patch("plugins.test_thyself_plugin.cli.Path.rglob") # Patch rglob
    def test_backup_file_creation(self, mock_rglob, MockCodeGenerator):
        """
        Tests that refactor_file creates a backup and writes refactored content
        when called via the refactor_thyself_sync command.
        """
        mock_py_file = self._create_mock_py_file("sample_backup.py", content="original content")
        mock_rglob.return_value = [mock_py_file]

        mock_code_generator_instance = MockCodeGenerator.return_value
        mock_code_generator_instance.refactor_code = AsyncMock(return_value="refactored content")

        # Invoke the synchronous command wrapper
        result = self.runner.invoke(
            refactor_thyself_sync,
            ["--instruction", "Refactor instruction", str(self.test_dir)]
        )

        # Assert the command exited successfully
        self.assertEqual(result.exit_code, 0)

        # Assert the internal mocks were called as expected during the command's execution
        mock_py_file.read_text.assert_called_once_with(encoding='utf-8')
        mock_code_generator_instance.refactor_code.assert_called_once_with("original content", "Refactor instruction")
        mock_py_file.rename.assert_called_once_with(mock_py_file.with_suffix.return_value)
        mock_py_file.write_text.assert_called_once_with("refactored content", encoding='utf-8')

        # Assert the output messages from the command - now matching the structure with the mock's .name
        self.assertIn(f"Refactored {mock_py_file.name} (backup saved as {mock_py_file.with_suffix.return_value.name})", result.output)
        self.assertIn("Refactoring complete. Backups saved with .bak extension.", result.output)

if __name__ == "__main__":
    unittest.main()