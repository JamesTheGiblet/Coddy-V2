import logging
from .cli import refactor_thyself_sync

logger = logging.getLogger("Coddy")

def register(cli):
    cli.add_command(refactor_thyself_sync)
    logger.info("Loaded refactor_thyself_sync plugin.")
