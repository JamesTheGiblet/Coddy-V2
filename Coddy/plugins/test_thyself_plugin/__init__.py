# C:\Users\gilbe\Documents\GitHub\Coddy V2\Coddy\plugins\test_thyself_plugin\__init__.py

import asyncio
import click
import logging
from pathlib import Path
import shutil

logger = logging.getLogger("Coddy")

# plugins/test_thyself_plugin/__init__.py

from .cli import refactor_thyself

def register(cli):
    cli.add_command(refactor_thyself)
    logging.getLogger("Coddy").info("Loaded refactor_thyself plugin.")
def is_command_available(cmd):
    return shutil.which(cmd) is not None

async def refactor_file(file_path: Path, instruction: str, dry_run: bool) -> str:
    """
    Async function to refactor a single file based on the instruction.
    Returns a summary string of the action taken.
    """
    logger.debug(f"Starting refactor for {file_path}")

    try:
        original_code = await asyncio.to_thread(file_path.read_text)
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return f"Error reading {file_path.name}: {e}"

    if dry_run:
        return f"[DRY-RUN] Would update {file_path.name}"

    backup_path = file_path.with_suffix(file_path.suffix + ".bak")

    try:
        # Backup original file asynchronously
        await asyncio.to_thread(file_path.rename, backup_path)
    except Exception as e:
        logger.error(f"Failed to backup {file_path}: {e}")
        return f"Error backing up {file_path.name}: {e}"

    # Dummy refactor logic: prepend instruction comment
    new_code = f"# Refactor instruction applied:\n# {instruction}\n\n{original_code}"

    try:
        await asyncio.to_thread(file_path.write_text, new_code)
    except Exception as e:
        logger.error(f"Failed to write refactored code to {file_path}: {e}")
        return f"Error writing {file_path.name}: {e}"

    return f"Refactored {file_path.name} (backup saved as {backup_path.name})"


@click.command(
    "refactor_thyself",
    help="Analyze and refactor Coddy's own codebase based on instructions."
)
@click.argument(
    "target_path",
    type=click.Path(exists=True),
    default="Coddy",
    required=False,
)
@click.option(
    "--instruction",
    "-i",
    type=str,
    required=True,
    help="Refactoring instruction describing desired improvements or changes."
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show planned changes without applying them."
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Show detailed logs."
)
async def refactor_thyself(target_path, instruction, dry_run, verbose):
    """
    Runs an AI-powered refactor pass over the specified codebase path,
    applying or simulating improvements based on the instruction text.
    """

    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    target = Path(target_path).resolve()
    logger.info(f"Starting self-refactor on: {target}")
    logger.info(f"Instruction: {instruction}")

    if not target.exists():
        click.echo(f"Error: target path does not exist: {target}", err=True)
        return 1

    py_files = list(target.rglob("*.py"))
    if not py_files:
        click.echo(f"No Python files found in {target}", err=True)
        return 1

    logger.info(f"Found {len(py_files)} Python files to analyze.")

    # Schedule refactoring tasks concurrently
    tasks = [
        refactor_file(file_path, instruction, dry_run)
        for file_path in py_files
    ]
    results = await asyncio.gather(*tasks)

    click.echo("\n=== Refactor Summary ===")
    for line in results:
        click.echo(line)

    if dry_run:
        click.echo("\nDry-run mode: No files were changed.")
    else:
        click.echo("\nRefactoring complete. Backups saved with .bak extension.")

    return 0


def register(cli):
    """
    Registers the refactor_thyself command with the Coddy CLI.
    """
    cli.add_command(refactor_thyself)
    logger.info("Loaded refactor_thyself plugin.")
