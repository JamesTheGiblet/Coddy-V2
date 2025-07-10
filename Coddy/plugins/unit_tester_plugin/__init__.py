# c:/Users/gilbe/Documents/GitHub/Coddy V2/Coddy/plugins/unit_tester_plugin/__init__.py

from .cli import unit_tester

def register():
    """Returns the command to be registered by the plugin manager."""
    return [unit_tester]