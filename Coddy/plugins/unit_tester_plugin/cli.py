# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\plugins\unit_tester_plugin\cli.py

import asyncio
import click
import traceback
from pathlib import Path

from core.code_generator import CodeGenerator
from backend.services import services # NEW: Import the centralized services dictionary

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
            
            # Retrieve initialized services
            llm_provider = services.get("llm_provider")
            memory_service = services.get("memory_service")
            vibe_engine = services.get("vibe_engine")
            user_profile_manager = services.get("user_profile_manager")

            if not llm_provider or not memory_service or not vibe_engine or not user_profile_manager:
                click.secho("Error: Core services (LLM, Memory, Vibe, UserProfile) are not initialized.", fg='red', err=True)
                click.secho("Ensure the Coddy backend API is running and services are loaded.", fg='red', err=True)
                return 1

            # MODIFIED: Initialize CodeGenerator with its dependencies
            code_gen = CodeGenerator(
                llm_provider=llm_provider,
                memory_service=memory_service,
                vibe_engine=vibe_engine,
                user_profile_manager=user_profile_manager
            )
            
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