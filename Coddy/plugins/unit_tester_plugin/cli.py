import asyncio
import click
import traceback
from pathlib import Path

from core.code_generator import CodeGenerator

@click.command("unit-tester")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False))
def unit_tester(file_path: str):
    """
    Generates pytest unit tests for a given Python source file.
    """
    async def run_unit_tester_async(file_path_str: str):
        """Async logic to generate unit tests for a given file."""
        click.echo(f"Generating unit tests for: {file_path_str}...")
        target_file = Path(file_path_str)

        try:
            source_code = await asyncio.to_thread(target_file.read_text, encoding='utf-8')
            code_gen = CodeGenerator()
            # MODIFIED: Pass target_file to generate_tests_for_file
            test_code = await code_gen.generate_tests_for_file(source_code, target_file) 

            # Determine output path (e.g., Coddy/module.py -> Coddy/tests/test_module.py)
            test_dir = Path("tests")
            test_dir.mkdir(exist_ok=True)
            output_path = test_dir / f"test_{target_file.name}"

            await asyncio.to_thread(output_path.write_text, test_code, encoding='utf-8')
            click.secho(f"✅ Successfully generated test file at: {output_path}", fg="green")
            return 0
        except Exception as e:
            click.secho(f"An error occurred during test generation: {e}", fg="red", err=True)
            traceback.print_exc()
            return 1

    exit_code = asyncio.run(run_unit_tester_async(file_path))
    raise SystemExit(exit_code)