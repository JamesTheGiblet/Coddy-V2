# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\plugin_manager.py

import importlib.util
import os
from pathlib import Path
from typing import List
import click

class PluginManager:
    """
    Discovers, loads, and manages plugins from the 'plugins' directory.
    """

    def __init__(self, plugin_folder: str = "plugins"):
        self.plugin_folder = Path(plugin_folder)
        self.commands: List[click.Command] = []
        self.discover_plugins()

    def discover_plugins(self):
        """
        Scans the plugin directory and loads any valid plugins.
        A valid plugin is a directory containing an __init__.py file
        with a 'register' function that returns a list of click.Command objects.
        """
        if not self.plugin_folder.is_dir():
            print(f"Plugin folder '{self.plugin_folder}' not found. Creating it.")
            self.plugin_folder.mkdir(exist_ok=True)
            return

        for potential_plugin in self.plugin_folder.iterdir():
            if potential_plugin.is_dir():
                init_file = potential_plugin / "__init__.py"
                if init_file.is_file():
                    try:
                        module_name = f"plugins.{potential_plugin.name}"
                        spec = importlib.util.spec_from_file_location(module_name, init_file)
                        if spec and spec.loader:
                            plugin_module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(plugin_module)
                            if hasattr(plugin_module, "register"):
                                self.commands.extend(plugin_module.register())
                                print(f"Successfully loaded plugin: {potential_plugin.name}")
                    except Exception as e:
                        print(f"Error loading plugin '{potential_plugin.name}': {e}")

    def add_plugins_to_cli(self, cli_group: click.Group):
        """Adds all discovered plugin commands to the main CLI group."""
        for command in self.commands:
            cli_group.add_command(command)