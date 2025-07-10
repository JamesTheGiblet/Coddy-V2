# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\plugins\ollama_llm_plugin\__init__.py

import click
import asyncio
from core.code_generator import CodeGenerator
from core.utils import write_file

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
        code_gen = CodeGenerator()
        refactored_code = await code_gen.refactor_code(original_code, instruction)

        if original_code.strip() != refactored_code.strip() and not refactored_code.startswith("# Failed"):
            click.secho("\n--- Refactored Code ---", fg='yellow')
            click.echo(refactored_code)
            if click.confirm("\nDo you want to apply these changes?"):
                write_file(file_path, refactored_code)
                click.secho(f"Successfully applied refactoring to '{file_path}'", fg='green')
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