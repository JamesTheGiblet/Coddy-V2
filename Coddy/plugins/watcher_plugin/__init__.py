# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\plugins\watcher_plugin\__init__.py

import asyncio
import click
from core.file_watcher import FileWatcher

@click.command('watch')
@click.argument('path', default='.', type=click.Path(exists=True, file_okay=False, resolve_path=True))
def watch(path):
    """
    Monitors a directory for file changes and provides proactive suggestions.
    
    This command runs a background process that watches for file modifications
    in the specified directory (or the current directory by default).
    """
    click.secho(f"Starting file watcher for directory: {path}", fg='cyan')
    click.secho("Press Ctrl+C to stop.", fg='yellow')

    try:
        loop = asyncio.get_event_loop()
        watcher = FileWatcher(path=path, loop=loop)
        watcher.start()
    except KeyboardInterrupt:
        click.echo("\nWatcher stopped by user.")
    

def register():
    """Registers the 'watch' command."""
    return [watch]