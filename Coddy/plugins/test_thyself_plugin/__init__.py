# Coddy/plugins/test_thyself_plugin/__init__.py

import logging

# Import both commands from the .cli module
from .cli import refactor_thyself_sync, test_thyself

# Get the logger instance for this __init__.py file
logger = logging.getLogger("Coddy")

def register(cli):
    """
    Registers the refactor_thyself_sync and test_thyself commands with the Coddy CLI.
    """
    cli.add_command(refactor_thyself_sync)
    cli.add_command(test_thyself) # Register the new command
    logger.info("Loaded refactor_thyself and test_thyself plugins.")

