# c:/Users/gilbe/Documents/GitHub/Coddy V2/Coddy/plugins/roadmap_plugin/__init__.py

from .cli import roadmap

def register():
    """Returns the roadmap command to be registered."""
    return [roadmap]