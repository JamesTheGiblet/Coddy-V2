# tests/test_code_generator.py
import unittest
import asyncio
from unittest.mock import patch, AsyncMock

from core.code_generator import CodeGenerator

class TestCodeGenerator(unittest.TestCase):

    def test_refactor_code(self):
        """
        Tests the refactor_code method to ensure it correctly processes
        a mocked LLM response, including stripping markdown.
        """
        original_code = "def old_function():\n    pass"
        instruction = "add a docstring"
        
        # Mock the LLM response to include markdown, which should be stripped
        mock_llm_response = """
```python
def old_function():
    \"\"\"This is a new docstring.\"\"\"
    pass
```
"""
        expected_refactored_code = 'def old_function():\n    """This is a new docstring."""\n    pass'

        # Patch the IdeaSynthesizer's summarize_text method
        with patch('core.idea_synth.IdeaSynthesizer.summarize_text', new_callable=AsyncMock) as mock_summarize:
            mock_summarize.return_value = mock_llm_response

            code_gen = CodeGenerator()
            
            # Run the async method using asyncio.run
            refactored_code = asyncio.run(code_gen.refactor_code(original_code, instruction))

            # Assert that the summarize_text was called
            mock_summarize.assert_called_once()
            
            # Assert that the output is correctly stripped and matches the expected code
            self.assertEqual(refactored_code.strip(), expected_refactored_code.strip())

    def test_generate_function(self):
        """
        Tests the generate_function method.
        """
        description = "A test function."
        function_name = "my_test_func"
        mock_llm_response = f"def {function_name}():\n    \"\"\"{description}\"\"\"\n    pass"

        with patch('core.idea_synth.IdeaSynthesizer.summarize_text', new_callable=AsyncMock) as mock_summarize:
            mock_summarize.return_value = mock_llm_response

            code_gen = CodeGenerator()
            generated_code = asyncio.run(code_gen.generate_function(description, function_name))

            mock_summarize.assert_called_once()
            self.assertIn(f"def {function_name}", generated_code)
            self.assertIn(description, generated_code)