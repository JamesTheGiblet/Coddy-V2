# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\plugins\refactor_plugin\__init__.py
# NOTE: The file path in the comment is based on user's provided path, but content is for refactor_plugin.

import click
import asyncio
from core.code_generator import CodeGenerator
# MODIFIED: Correct import for write_file
from core.utility_functions import write_file # Changed from core.utils
# Import services from the backend. This assumes the plugin will run in an environment
# where these services are already initialized and accessible (e.g., via the FastAPI app).
from backend.services import services # NEW: Import the centralized services dictionary

@click.command()
@click.argument('file_path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.argument('instruction')
def refactor(file_path, instruction):
    """
    Refactors a Python file based on an instruction.

    FILE_PATH: Path to the Python file to refactor.
    INSTRUCTION: The natural language instruction for the refactoring.
    """
    click.echo(f"Refactoring '{file_path}'...")
    click.echo(f"Instruction: '{instruction}'")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
    except Exception as e:
        click.secho(f"Error reading file: {e}", fg='red')
        return

    async def do_refactor():
        # Retrieve initialized services
        llm_provider = services.get("llm_provider")
        memory_service = services.get("memory_service")
        vibe_engine = services.get("vibe_engine")
        user_profile_manager = services.get("user_profile_manager")

        if not llm_provider or not memory_service or not vibe_engine or not user_profile_manager:
            click.secho("Error: Core services (LLM, Memory, Vibe, UserProfile) are not initialized.", fg='red')
            click.secho("Ensure the Coddy backend API is running and services are loaded.", fg='red')
            return

        # MODIFIED: Initialize CodeGenerator with its dependencies
        code_gen = CodeGenerator(
            llm_provider=llm_provider,
            memory_service=memory_service,
            vibe_engine=vibe_engine,
            user_profile_manager=user_profile_manager
        )
        
        refactored_code = await code_gen.refactor_code(original_code, instruction)

        if original_code.strip() != refactored_code.strip() and not refactored_code.startswith("# Failed"):
            click.secho("\n--- Refactored Code ---", fg='yellow')
            click.echo(refactored_code)
            if click.confirm("\nDo you want to apply these changes?"):
                try:
                    await write_file(file_path, refactored_code) # write_file is async
                    click.secho(f"Successfully applied refactoring to '{file_path}'", fg='green')
                except Exception as write_e:
                    click.secho(f"Error writing refactored code to file: {write_e}", fg='red')
            else:
                click.secho("Refactoring cancelled.", fg='yellow')
        elif refactored_code.startswith("# Failed"):
            click.secho(f"Refactoring failed. LLM response:\n{refactored_code}", fg='red')
        else:
            click.secho("No changes detected after refactoring.", fg='yellow')

    asyncio.run(do_refactor())

def register() -> list[click.Command]:
    """
    Registers the commands provided by this plugin.
    """
    return [refactor]