# cli.py
import asyncio
import json
import click
from cli import start_cli
from plugin_manager import PluginManager
from core.user_profile import UserProfile
from ui_generator import UIGenerator
from utils import write_file

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """
    Coddy V2: Your AI Dev Companion.
    Run without a command to enter the interactive shell.
    """
    if ctx.invoked_subcommand is None:
        asyncio.run(start_cli())

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

@click.group()
def profile():
    """Manage your Coddy user profile."""
    pass

@profile.command(name='get')
@click.argument('key', required=False)
def profile_get(key):
    """
    Get a specific setting or view the entire user profile.

    KEY: The profile setting to retrieve (e.g., 'idea_synth_persona').
    """
    user_profile = UserProfile()
    if key:
        value = getattr(user_profile.profile, key, None)
        if value is not None:
            click.echo(f"{key}: {value}")
        else:
            click.secho(f"Setting '{key}' not found in profile.", fg='red')
    else:
        click.echo(user_profile.profile.model_dump_json(indent=2))

@profile.command(name='set')
@click.argument('key')
@click.argument('value')
def profile_set(key, value):
    """
    Set a value for a specific profile setting.

    KEY: The profile setting to update (e.g., 'idea_synth_creativity').
    VALUE: The new value for the setting.
    """
    user_profile = UserProfile()
    try:
        # Attempt to convert value to a more appropriate type
        try:
            typed_value = float(value)
        except ValueError:
            try:
                typed_value = int(value)
            except ValueError:
                typed_value = value

        user_profile.set(key, typed_value)
        click.secho(f"Successfully set '{key}' to '{value}'.", fg='green')
    except AttributeError as e:
        click.secho(str(e), fg='red')
    except Exception as e:
        click.secho(f"An error occurred: {e}", fg='red')

cli.add_command(build)
cli.add_command(profile)

if __name__ == '__main__':
    # Discover and load plugins before running the CLI
    plugin_manager = PluginManager()
    plugin_manager.add_plugins_to_cli(cli)
    cli()