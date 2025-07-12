# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\logging_utility.py

import asyncio
import logging
import os
from datetime import datetime
import sys
import traceback # To capture stack traces

# Define the log directory relative to Coddy's root
# Assuming this file is in Coddy/core/, then '..' points to Coddy/
LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
LOG_FILE = os.path.join(LOG_DIR, f"coddy_log_{datetime.now().strftime('%Y-%m-%d')}.log")

def setup_logging():
    """
    Sets up a basic logger for Coddy, directing output to both console and a file.
    """
    os.makedirs(LOG_DIR, exist_ok=True) # Ensure log directory exists

    # Create a logger
    logger = logging.getLogger('coddy_logger')
    logger.setLevel(logging.INFO) # Set default logging level

    # Prevent duplicate handlers if setup_logging is called multiple times
    if not logger.handlers:
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO) # INFO and above to console
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File Handler
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG) # DEBUG and above to file
        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

# Initialize the logger instance
logger = setup_logging()

async def log_info(message: str):
    """Logs an informational message."""
    logger.info(message)

async def log_warning(message: str):
    """Logs a warning message."""
    logger.warning(message)

async def log_error(message: str, exc_info: bool = False):
    """Logs an error message, optionally including exception info."""
    if exc_info:
        logger.error(message, exc_info=True) # exc_info=True captures current exception traceback
    else:
        logger.error(message)

async def log_debug(message: str):
    """Logs a debug message."""
    logger.debug(message)

# Example Usage (for testing the logging utility)
async def main_logging_test():
    await log_info("This is an info message from Coddy.")
    await log_warning("This is a warning message about something.")
    await log_debug("This is a debug message, only visible in the log file normally.")

    try:
        raise ValueError("Something went wrong!")
    except ValueError as e:
        await log_error(f"An expected error occurred: {e}", exc_info=True)

    await log_info(f"Check the log file at: {LOG_FILE}")

if __name__ == "__main__":
    # Ensure log directory exists before running direct example
    os.makedirs(LOG_DIR, exist_ok=True)
    asyncio.run(main_logging_test())