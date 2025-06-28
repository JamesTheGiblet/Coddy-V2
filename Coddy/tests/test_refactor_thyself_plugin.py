import unittest
from unittest.mock import patch, AsyncMock
from pathlib import Path
from click.testing import CliRunner
import shutil

from plugins.test_thyself_plugin.cli import refactor_thyself_sync

# Async mock function for refactor_file
async def fake_refactor_file(*args, **kwargs):
    return "Refactored sample.py (backup saved as sample.py.bak)"

class TestRefactorThyselfPlugin(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.temp_dir = Path("temp_test_coddy_dir")
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        self.test_dir = self.temp_dir

    def tearDown(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_cli_invocation_missing_target(self):
        # Let CliRunner catch exceptions (default behavior)
        result = self.runner.invoke(
            refactor_thyself_sync,
            ["--instruction", "Do something", "non_existent_path_xyz"]
        )
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("Directory 'non_existent_path_xyz' does not exist.", result.output)

    @patch("plugins.test_thyself_plugin.cli.Path.rglob", return_value=[])
    def test_cli_invocation_no_py_files(self, mock_rglob):
        result = self.runner.invoke(
            refactor_thyself_sync,
            ["--instruction", "Refactor", str(self.test_dir)]
        )
        self.assertEqual(result.exit_code, 1)
        self.assertIn("No Python files found", result.output)

    @patch("plugins.test_thyself_plugin.cli.refactor_file", new_callable=AsyncMock)
    @patch("plugins.test_thyself_plugin.cli.Path.rglob")
    def test_cli_invocation_with_py_files(self, mock_rglob, mock_refactor_file):
        py_file = self.test_dir / "sample.py"
        py_file.write_text("print('hello')")
        mock_rglob.return_value = [py_file]
        mock_refactor_file.return_value = "Refactored sample.py (backup saved as sample.py.bak)"

        result = self.runner.invoke(
            refactor_thyself_sync,
            ["--instruction", "Make it async", str(self.test_dir)]
        )

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(mock_refactor_file.called, "Expected refactor_file() to be called.")
        self.assertIn("=== Refactor Summary ===", result.output)
        self.assertIn("Refactored sample.py", result.output)

    # ✅ NEW TEST: Graceful handling of file read/refactor failure
    @patch("plugins.test_thyself_plugin.cli.refactor_file", new_callable=AsyncMock)
    @patch("plugins.test_thyself_plugin.cli.Path.rglob")
    def test_refactor_file_error_is_handled_gracefully(self, mock_rglob, mock_refactor_file):
        py_file = self.test_dir / "fail.py"
        py_file.write_text("raise Exception()")
        mock_rglob.return_value = [py_file]
        mock_refactor_file.return_value = "Error reading fail.py: Simulated failure"

        result = self.runner.invoke(
            refactor_thyself_sync,
            ["--instruction", "Handle error", str(self.test_dir)]
        )

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Error reading fail.py", result.output)
        self.assertIn("=== Refactor Summary ===", result.output)

    @patch("plugins.test_thyself_plugin.cli.refactor_file", new_callable=AsyncMock)
    @patch("plugins.test_thyself_plugin.cli.Path.rglob")
    def test_cli_dry_run_mode(self, mock_rglob, mock_refactor_file):
        py_file = self.test_dir / "sample.py"
        py_file.write_text("print('original')")
        mock_rglob.return_value = [py_file]
        mock_refactor_file.return_value = "[DRY-RUN] Would update sample.py"

        result = self.runner.invoke(
            refactor_thyself_sync,
            ["--instruction", "Make it async", "--dry-run", str(self.test_dir)]
        )

        self.assertEqual(result.exit_code, 0)
        self.assertTrue(mock_refactor_file.called)
        self.assertIn("[DRY-RUN] Would update sample.py", result.output)
        self.assertIn("Dry-run mode: No files were changed.", result.output)

    @patch("plugins.test_thyself_plugin.cli.Path.rglob")
    def test_verbose_logging_emits_debug(self, mock_rglob):
        py_file = self.test_dir / "sample_verbose.py"
        py_file.write_text("print('verbose')")
        mock_rglob.return_value = [py_file]

        with self.assertLogs("Coddy", level="DEBUG") as log_cm:
            result = self.runner.invoke(
                refactor_thyself_sync,
                ["--instruction", "Add docstring", "--verbose", str(self.test_dir)]
            )
    
        self.assertEqual(result.exit_code, 0)

        # Check that at least one debug log contains the filename
        debug_logs = log_cm.output
        self.assertTrue(
            any("sample_verbose.py" in message for message in debug_logs),
            "Expected debug log mentioning sample_verbose.py"
        )

    from unittest.mock import MagicMock

    @patch("plugins.test_thyself_plugin.cli.Path.rename", new_callable=MagicMock)
    @patch("plugins.test_thyself_plugin.cli.Path.write_text", new_callable=MagicMock)
    @patch("plugins.test_thyself_plugin.cli.CodeGenerator.refactor_code", new_callable=AsyncMock)
    async def test_backup_file_creation(self, mock_refactor_code, mock_write_text, mock_rename):
        # Setup the refactor_code mock to return refactored content
        mock_refactor_code.return_value = "refactored content"

        py_file = self.test_dir / "sample_backup.py"
        py_file.write_text("print('original')")

        from plugins.test_thyself_plugin.cli import refactor_file

        # Call the async function directly
        result = await refactor_file(py_file, "Refactor instruction", dry_run=False)

        # Assert the rename and write_text methods were called as expected
        mock_rename.assert_called_once()
        mock_write_text.assert_called_once_with("refactored content", encoding='utf-8')

        # Result message should mention backup
        self.assertIn(".bak", result)


if __name__ == "__main__":
    unittest.main()
