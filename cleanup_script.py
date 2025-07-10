# C:\Users\gilbe\Documents\GitHub\Coddy_V2\cleanup_script.py 

import os
import shutil
from pathlib import Path
import click
import logging

# Configure basic logging for the script
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

@click.command(help="Finds and deletes common temporary files and cache directories.")
@click.argument('target_path', type=click.Path(exists=True, file_okay=False, dir_okay=True), default='.', required=False)
@click.option('--dry-run', is_flag=True, default=False, help="Show what would be deleted without actually deleting.")
@click.option('--verbose', '-v', is_flag=True, default=False, help="Show detailed log messages.")
def cleanup(target_path, dry_run, verbose):
    """
    Finds and deletes common temporary files and cache directories
    within the specified target_path.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    target_dir = Path(target_path).resolve()
    logger.info(f"Starting cleanup in: {target_dir}")
    if dry_run:
        logger.info("Running in DRY-RUN mode. No files will be deleted.")

    # Define patterns for files and directories to clean
    # Add or modify these patterns as needed for your project
    patterns_to_delete = {
        'files': [
            '*.pyc',    # Compiled Python bytecode
            '*.tmp',    # Generic temporary files
            '*.bak',    # Backup files (e.g., from refactor_thyself)
            '*.log',    # Log files
            '*.old',    # Old versions
        ],
        'dirs': [
            '__pycache__', # Python bytecode cache directories
            '.pytest_cache', # pytest cache
            '.mypy_cache',   # mypy cache
            '.vscode-test', # VS Code test environments
            # Add specific temporary directories created by your tests if any
            'temp_test_coddy_dir', # From test_refactor_thyself_plugin.py
        ]
    }

    deleted_count = 0
    deleted_size = 0 # In bytes

    # --- Clean up files matching patterns ---
    logger.debug("Searching for files to delete...")
    for pattern in patterns_to_delete['files']:
        for file_path in target_dir.rglob(pattern):
            if file_path.is_file():
                try:
                    file_size = file_path.stat().st_size
                    action = "Would delete" if dry_run else "Deleting"
                    logger.debug(f"{action} file: {file_path}")
                    if not dry_run:
                        os.remove(file_path)
                    deleted_count += 1
                    deleted_size += file_size
                except OSError as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")

    # --- Clean up directories matching patterns ---
    logger.debug("Searching for directories to delete...")
    for dir_name in patterns_to_delete['dirs']:
        # Use rglob to find all directories with this name, anywhere in the hierarchy
        for dir_path in target_dir.rglob(dir_name):
            if dir_path.is_dir():
                try:
                    # Calculate directory size only if not dry-run and if actually deleting
                    dir_size = 0
                    if not dry_run:
                        for entry in dir_path.rglob('*'):
                            if entry.is_file():
                                dir_size += entry.stat().st_size
                    
                    action = "Would delete" if dry_run else "Deleting"
                    logger.debug(f"{action} directory: {dir_path}")
                    if not dry_run:
                        shutil.rmtree(dir_path)
                    deleted_count += 1
                    deleted_size += dir_size
                except OSError as e:
                    logger.warning(f"Failed to process directory {dir_path}: {e}")

    # --- Summary ---
    summary_action = "would have been deleted" if dry_run else "deleted"
    logger.info(f"\nCleanup finished. {deleted_count} items {summary_action}.")
    logger.info(f"Total size {summary_action}: {deleted_size / (1024*1024):.2f} MB")

if __name__ == '__main__':
    cleanup()
