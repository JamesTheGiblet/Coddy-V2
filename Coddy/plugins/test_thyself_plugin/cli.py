import asyncio
import click
import logging
from pathlib import Path
import pytest

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
    "refactor-thyself",
    help="Refactors Coddy's own codebase using an instruction."
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
def refactor_thyself(target_path, instruction, dry_run, verbose):
    """
    Synchronous wrapper for the async refactor_thyself command,
    to allow it to be called from standard Click CLI entry points.
    """
    exit_code = asyncio.run(
        _refactor_thyself_async_impl(target_path, instruction, dry_run, verbose)
    )
    raise SystemExit(exit_code)  # <-- Key fix to ensure correct CLI exit behavior

@click.command(
    "test-thyself",
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
    Executes Coddy's internal unit tests using pytest.
    This is more robust and consistent with the main CLI entry point.
    """
    click.echo(f"Starting Coddy's self-test suite from: {test_path}")

    # Pytest handles its own output capturing, so we don't need to redirect stdout/stderr.
    # It returns an exit code directly.
    exit_code = pytest.main([test_path])

    if exit_code == 0:
        click.echo("\nCoddy self-test: ALL TESTS PASSED! ✅")
    else:
        click.echo(f"\nCoddy self-test: TESTS FAILED! ❌ (exit code: {exit_code})")

    # The command should exit with the same code as pytest.
    raise SystemExit(exit_code)
