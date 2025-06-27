# main.py
import click
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

cli.add_command(build)

if __name__ == '__main__':
    # Discover and load plugins before running the CLI
    plugin_manager = PluginManager()
    plugin_manager.add_plugins_to_cli(cli)
    cli()