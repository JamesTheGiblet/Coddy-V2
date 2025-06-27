# tests/test_ollama_llm_plugin.py
import unittest
from unittest.mock import patch, MagicMock
import json
from click.testing import CliRunner
import requests

from plugins.ollama_llm_plugin.__init__ import ollama_group

class TestOllamaLlmPlugin(unittest.TestCase):

    def setUp(self):
        self.runner = CliRunner()

    @patch('plugins.ollama_llm_plugin.__init__.requests.post')
    def test_ollama_chat_success(self, mock_post):
        """
        Tests the 'ollama chat' command with a successful, mocked API response.
        """
        # Mock the streaming response
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Simulate the streaming chunks from Ollama
        chunks = [
            json.dumps({"response": "Hello"}).encode('utf-8'),
            json.dumps({"response": ", "}).encode('utf-8'),
            json.dumps({"response": "world!", "done": True}).encode('utf-8'),
        ]
        mock_response.iter_lines.return_value = chunks
        
        # The context manager `with requests.post(...) as response:` needs this
        mock_post.return_value.__enter__.return_value = mock_response

        result = self.runner.invoke(ollama_group, ['chat', 'say hello'])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Connecting to Ollama with model 'mistral'...", result.output)
        # The final output should be concatenated without newlines until the end
        self.assertIn("Response: Hello, world!", result.output)
        self.assertIn("Done.", result.output)
        mock_post.assert_called_once()

    @patch('plugins.ollama_llm_plugin.__init__.requests.post')
    def test_ollama_chat_connection_error(self, mock_post):
        """
        Tests the 'ollama chat' command when a connection error occurs.
        """
        mock_post.side_effect = requests.exceptions.ConnectionError("Test connection error")

        result = self.runner.invoke(ollama_group, ['chat', 'say hello'])

        self.assertEqual(result.exit_code, 0) # The command handles the error gracefully
        self.assertIn("Error: Could not connect to Ollama server", result.output)
        self.assertIn("Please ensure Ollama is running.", result.output)