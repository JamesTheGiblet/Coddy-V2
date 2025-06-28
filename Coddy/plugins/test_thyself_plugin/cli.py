import asyncio
import io
import click
import logging
from pathlib import Path
import shutil
import unittest
import sys

from core.code_generator import CodeGenerator

logger = logging.getLogger("Coddy")

async def refactor_file(file_path: Path, instruction: str, dry_run: bool) -> str:
    """
    Async function to refactor a single file based on the instruction.
    Uses CodeGenerator for actual refactoring.
    Returns a summary string of the action taken.
    """
    logger.debug(f"Starting refactor for {file_path}")

    try:
        original_code = await asyncio.to_thread(file_path.read_text, encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return f"Error reading {file_path.name}: {e}"

    try:
        code_generator_instance = CodeGenerator()
        refactored_content = await code_generator_instance.refactor_code(original_code, instruction)
    except Exception as e:
        logger.error(f"Failed to get refactored code from LLM for {file_path}: {e}")
        return f"Error refactoring {file_path.name}: {e}"

    if dry_run:
        return f"[DRY-RUN] Would update {file_path.name}"

    backup_path = file_path.with_suffix(file_path.suffix + ".bak")

    try:
        await asyncio.to_thread(file_path.rename, backup_path)
        await asyncio.to_thread(file_path.write_text, refactored_content, encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed to backup or write refactored code to {file_path}: {e}")
        return f"Error backing up or writing {file_path.name}: {e}"

    return f"Refactored {file_path.name} (backup saved as {backup_path.name})"

async def _refactor_thyself_async_impl(target_path, instruction, dry_run, verbose):
    """
    Asynchronous implementation of the refactor_thyself logic.
    """
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    target = Path(target_path).resolve()
    logger.info(f"Starting self-refactor on: {target}")
    logger.info(f"Instruction: {instruction}")

    py_files = list(target.rglob("*.py"))
    if not py_files:
        click.echo(f"No Python files found in {target}", err=True)
        return 1

    logger.info(f"Found {len(py_files)} Python files to analyze.")

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

@click.command(
    "refactor_thyself_sync",
    help="Sync wrapper for async refactor_thyself command"
)
@click.argument(
    "target_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
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
def refactor_thyself_sync(target_path, instruction, dry_run, verbose):
    """
    Synchronous wrapper for the async refactor_thyself command,
    to allow it to be called from standard Click CLI entry points.
    """
    exit_code = asyncio.run(
        _refactor_thyself_async_impl(target_path, instruction, dry_run, verbose)
    )
    raise SystemExit(exit_code)  # <-- Key fix to ensure correct CLI exit behavior

@click.command(
    "test_thyself",
    help="Autonomously execute Coddy's internal test suite."
)
@click.option(
    "--test-path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default="tests",
    help="Path to the test directory to discover tests from."
)
def test_thyself(test_path):
    """
    Executes Coddy's internal unit tests using unittest discovery.
    """
    click.echo(f"Starting Coddy's self-test suite from: {test_path}")

    _original_stdout = sys.stdout
    _original_stderr = sys.stderr

    captured_stdout = io.StringIO()
    captured_stderr = io.StringIO()
    sys.stdout = captured_stdout
    sys.stderr = captured_stderr

    test_result = None
    try:
        suite = unittest.TestLoader().discover(test_path)
        runner = unittest.TextTestRunner(stream=captured_stdout, verbosity=1)
        test_result = runner.run(suite)
    except SystemExit as e:
        exit_code = e.code
    finally:
        sys.stdout = _original_stdout
        sys.stderr = _original_stderr

        click.echo("\n=== Test Output ===")
        click.echo(captured_stdout.getvalue())
        if captured_stderr.getvalue():
            click.echo("\n=== Test Errors ===")
            click.echo(captured_stderr.getvalue(), err=True)

        if test_result and test_result.wasSuccessful():
            click.echo("\nCoddy self-test: ALL TESTS PASSED! ✅")
            raise SystemExit(0)
        else:
            click.echo("\nCoddy self-test: TESTS FAILED! ❌")
            raise SystemExit(1)
