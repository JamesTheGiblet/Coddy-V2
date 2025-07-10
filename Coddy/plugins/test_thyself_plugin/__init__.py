# c:/Users/gilbe/Documents/GitHub/Coddy V2/Coddy/plugins/test_thyself_plugin/__init__.py

from .cli import refactor_thyself, test_thyself

def register():
    """Returns the commands to be registered by the plugin manager."""
    return [refactor_thyself, test_thyself]