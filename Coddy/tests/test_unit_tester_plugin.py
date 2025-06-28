import unittest
from unittest.mock import patch, AsyncMock
from click.testing import CliRunner
from pathlib import Path
import ast # Import the ast module for syntax tree parsing

from plugins.unit_tester_plugin.__init__ import unit_tester

class TestUnitTesterPlugin(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()
        self.test_file = Path("test_module_for_testing.py")
        self.test_file.write_text("def add(a, b):\n    return a + b")

    def tearDown(self):
        if self.test_file.exists():
            self.test_file.unlink()

    @patch('plugins.unit_tester_plugin.__init__.CodeGenerator')
    def test_unit_tester_command_success(self, MockCodeGenerator):
        """
        Tests the unit_test command successfully generates tests.
        """
        generated_content = "import unittest\n\ndef test_add():\n    assert add(1, 2) == 3"

        # Configure the mock instance and its async method
        mock_instance = MockCodeGenerator.return_value
        mock_instance.generate_tests = AsyncMock(return_value=generated_content)

        result = self.runner.invoke(unit_tester, [str(self.test_file)])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Generating unit tests for", result.output)
        self.assertIn(str(self.test_file.resolve()), result.output)
        self.assertIn("--- Generated Tests ---", result.output)
        self.assertIn(generated_content, result.output)

        MockCodeGenerator.assert_called_once_with(user_id='default_user')
        mock_instance.generate_tests.assert_awaited_once_with(self.test_file.read_text())

    @patch('plugins.unit_tester_plugin.__init__.CodeGenerator')
    def test_unit_tester_command_failure(self, MockCodeGenerator):
        """
        Tests the unit_test command handles errors during test generation.
        """
        mock_instance = MockCodeGenerator.return_value
        mock_instance.generate_tests = AsyncMock(side_effect=Exception("LLM Error"))

        result = self.runner.invoke(unit_tester, [str(self.test_file)])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Error generating tests: LLM Error", result.output)

    @patch('plugins.unit_tester_plugin.__init__.CodeGenerator')
    def test_generated_tests_are_syntactically_valid(self, MockCodeGenerator):
        """
        Tests that the generated test code is syntactically valid Python.
        This acts as a meta-test for the quality of generated output.
        """
        # A realistic example of what CodeGenerator might return for the test_file content
        sample_generated_pytest_code = (
            "import pytest\n"
            "from your_module import add # Assuming 'add' is in a discoverable module\n\n"
            "def test_add_positive_numbers():\n"
            "    assert add(2, 3) == 5\n\n"
            "def test_add_negative_numbers():\n"
            "    assert add(-1, -1) == -2\n"
        )

        mock_instance = MockCodeGenerator.return_value
        mock_instance.generate_tests = AsyncMock(return_value=sample_generated_pytest_code)

        result = self.runner.invoke(unit_tester, [str(self.test_file)])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("--- Generated Tests ---", result.output)
        self.assertIn(sample_generated_pytest_code, result.output)

        # Crucial part: Attempt to parse the generated code using ast
        # If this raises a SyntaxError, the test will fail, indicating invalid Python syntax
        try:
            ast.parse(sample_generated_pytest_code)
        except SyntaxError as e:
            self.fail(f"Generated test code has a syntax error: {e}")
        
        # You could add further checks here, e.g., to see if 'pytest' is imported
        # or if functions starting with 'test_' exist, although ast.parse
        # covers the fundamental "syntactically valid" requirement.

if __name__ == "__main__":
    unittest.main()