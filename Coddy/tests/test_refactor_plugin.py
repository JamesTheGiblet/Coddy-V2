# tests/test_refactor_plugin.py
import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from click.testing import CliRunner
from pathlib import Path
from core.llm_provider import LLMProvider # Import for type hinting the mock

# The plugin's entry point is the refactor command itself
from plugins.refactor_plugin.__init__ import refactor

class TestRefactorPlugin(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.test_file = Path("test_refactor_file.py")
        self.test_file.write_text("def hello():\n    pass")

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()

    @patch('core.llm_provider.get_llm_provider')
    @patch('plugins.refactor_plugin.__init__.CodeGenerator.refactor_code', new_callable=AsyncMock)
    def test_refactor_command_apply(self, mock_refactor_code, mock_get_llm_provider):
        """
        Tests the refactor command, simulating user confirmation ('y').
        """
        refactored_content = "def hello():\n    \"\"\"A docstring.\"\"\"\n    pass"
        mock_refactor_code.return_value = refactored_content

        # Ensure get_llm_provider returns a mock that doesn't raise an error
        mock_get_llm_provider.return_value = MagicMock(spec=LLMProvider)

        result = self.runner.invoke(
            refactor,
            [str(self.test_file), "add a docstring"],
            input='y\n'
        )
        self.assertEqual(result.exit_code, 0)
        self.assertIn("--- Refactored Code ---", result.output)
        self.assertIn("Do you want to apply these changes?", result.output)
        self.assertIn("Successfully applied refactoring", result.output)
        
        # Check that the file was actually changed
        self.assertEqual(self.test_file.read_text(), refactored_content)

    @patch('core.llm_provider.get_llm_provider')
    @patch('plugins.refactor_plugin.__init__.CodeGenerator.refactor_code', new_callable=AsyncMock)
    def test_refactor_command_cancel(self, mock_refactor_code, mock_get_llm_provider):
        """
        Tests the refactor command, simulating user cancellation ('n').
        """
        original_content = self.test_file.read_text()
        refactored_content = "def hello():\n    \"\"\"A docstring.\"\"\"\n    pass"
        mock_refactor_code.return_value = refactored_content

        mock_get_llm_provider.return_value = MagicMock(spec=LLMProvider)

        result = self.runner.invoke(
            refactor,
            [str(self.test_file), "add a docstring"],
            input='n\n'
        )
        
        # The command should exit gracefully on cancellation
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Refactoring cancelled.", result.output)
        
        # Check that the file was NOT changed
        self.assertEqual(self.test_file.read_text(), original_content)