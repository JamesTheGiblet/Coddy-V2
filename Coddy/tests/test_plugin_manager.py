# tests/test_plugin_manager.py
import unittest
from unittest.mock import patch, MagicMock
import os
import shutil
from pathlib import Path
import click

from core.plugin_manager import PluginManager

class TestPluginManager(unittest.TestCase):

    def setUp(self):
        self.test_plugins_dir = Path("temp_test_plugins")
        self.test_plugins_dir.mkdir(exist_ok=True)

        # Create a valid plugin
        self.valid_plugin_dir = self.test_plugins_dir / "valid_plugin"
        self.valid_plugin_dir.mkdir()
        with open(self.valid_plugin_dir / "__init__.py", "w") as f:
            f.write( # Explicitly name the command to avoid ambiguity
                "import click\n"
                "@click.command(name='valid_command')\n"
                "def valid_command():\n"
                "    click.echo('valid command executed')\n"
                "def register():\n"
                "    return [valid_command]\n"
            )

        # Create a plugin with no register function
        self.no_register_plugin_dir = self.test_plugins_dir / "no_register_plugin"
        self.no_register_plugin_dir.mkdir()
        with open(self.no_register_plugin_dir / "__init__.py", "w") as f:
            f.write("print('I have no register function')")

        # Create a plugin that raises an error
        self.error_plugin_dir = self.test_plugins_dir / "error_plugin"
        self.error_plugin_dir.mkdir()
        with open(self.error_plugin_dir / "__init__.py", "w") as f:
            f.write("raise ImportError('This plugin fails to load')")

        # Create a file that is not a directory
        with open(self.test_plugins_dir / "not_a_plugin.txt", "w") as f:
            f.write("I am not a plugin.")

    def tearDown(self):
        shutil.rmtree(self.test_plugins_dir)

    def test_discover_plugins(self):
        """
        Tests that the PluginManager correctly discovers valid plugins and ignores invalid ones.
        """
        manager = PluginManager(plugin_folder=str(self.test_plugins_dir))
        
        # Should discover one command from the valid plugin
        self.assertEqual(len(manager.commands), 1)
        self.assertEqual(manager.commands[0].name, "valid_command")

    def test_add_plugins_to_cli(self):
        """
        Tests that discovered plugin commands are correctly added to a Click group.
        """
        manager = PluginManager(plugin_folder=str(self.test_plugins_dir))
        
        mock_cli_group = click.Group()
        manager.add_plugins_to_cli(mock_cli_group)
        
        self.assertIn("valid_command", mock_cli_group.commands)
        self.assertEqual(len(mock_cli_group.commands), 1)