# main.py
import click
import asyncio
from core.ui_generator import UIGenerator
from core.utils import write_file
from core.plugin_manager import PluginManager

@click.group()
def cli():
    """Coddy V2: Your AI Dev Companion"""
    pass

@click.group()
def build():
    """Build various project artifacts."""
    pass

@build.command(name='ui')
@click.argument('source_file', type=click.Path(exists=True, dir_okay=False))
@click.argument('output_file', type=click.Path(dir_okay=False))
def build_ui(source_file, output_file):
    """
    Generates a Streamlit UI from a Python data class.

    SOURCE_FILE: Path to the Python file with a data class (e.g., models/user_profile_model.py).
    OUTPUT_FILE: Path to write the generated Streamlit app (e.g., generated_ui.py).
    """
    click.echo(f"Building UI from '{source_file}'...")
    generator = UIGenerator()
    ui_code = generator.generate_from_file(source_file)
    write_file(output_file, ui_code)
    click.secho(f"Successfully generated UI at '{output_file}'", fg='green')
    click.echo("To run it, make sure you have streamlit installed (`pip install streamlit pydantic`) and then run:")
    click.secho(f"streamlit run {output_file}", fg='cyan')

@cli.command()
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

cli.add_command(build)

if __name__ == '__main__':
    # Discover and load plugins before running the CLI
    plugin_manager = PluginManager()
    plugin_manager.add_plugins_to_cli(cli)
    cli()