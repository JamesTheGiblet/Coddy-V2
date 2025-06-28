import sys
import click
import asyncio
from pathlib import Path
from core.code_generator import CodeGenerator
import logging

logger = logging.getLogger("Coddy")

async def refactor_file(file_path: Path, instruction: str, dry_run: bool) -> str:
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
        logger.error(f"Refactoring error for {file_path}: {e}")
        return f"Error refactoring {file_path.name}: {e}"

    if dry_run:
        return f"[DRY-RUN] Would update {file_path.name}"

    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    try:
        await asyncio.to_thread(file_path.rename, backup_path)
        await asyncio.to_thread(file_path.write_text, refactored_content, encoding='utf-8')
    except Exception as e:
        logger.error(f"Failed backup/write for {file_path}: {e}")
        return f"Error writing {file_path.name}: {e}"

    return f"Refactored {file_path.name} (backup saved as {backup_path.name})"


async def refactor_thyself(target_path, instruction, dry_run, verbose):
    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    target = Path(target_path).resolve()
    py_files = list(target.rglob("*.py"))

    if not py_files:
        click.echo(f"No Python files found in {target}")
        return 1

    results = await asyncio.gather(
        *(refactor_file(file_path, instruction, dry_run) for file_path in py_files)
    )

    click.echo("\n=== Refactor Summary ===")
    for line in results:
        click.echo(line)

    if dry_run:
        click.echo("\nDry-run mode: No files were changed.")
    else:
        click.echo("\nRefactoring complete. Backups saved with .bak extension.")

    sys.stdout.flush()
    sys.stderr.flush()

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
    "--instruction", "-i",
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
    # Run async function and exit with its code
    exit_code = asyncio.run(
        refactor_thyself(target_path, instruction, dry_run, verbose)
    )
    sys.exit(exit_code)
