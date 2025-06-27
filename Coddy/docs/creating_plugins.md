# Creating Coddy Plugins

This guide provides instructions on how to create a new plugin for Coddy. Plugins are the primary way to extend Coddy's functionality by adding new CLI commands.

## Plugin Structure

A plugin is a directory within the `plugins/` folder. The directory name should be descriptive of the plugin's function (e.g., `refactor_plugin`).

At a minimum, a plugin must contain an `__init__.py` file.

```
plugins/
└── my_new_plugin/
    └── __init__.py
```

## The `__init__.py` File

This file is the entry point for your plugin. It must contain two key components:

1.  A `click` command or group.
2.  A `register()` function that returns the `click` object.

### Example `__init__.py`

Here is a simple example for a plugin that adds a `hello` command.

```python
# plugins/hello_plugin/__init__.py
import click

@click.command()
@click.argument('name', default='World')
def hello(name):
    """A simple command that says hello."""
    click.echo(f"Hello, {name}!")

def register():
    """Registers the 'hello' command."""
    return hello
```

## How Plugins are Loaded

The `PluginManager` scans the `plugins/` directory for subdirectories. For each subdirectory, it attempts to import the `__init__.py` module and call its `register()` function.

The object returned by `register()` is then added to Coddy's main CLI command group.

## Testing Your Plugin

It is crucial to add tests for your new plugin. Create a new test file in the `tests/` directory, for example `tests/test_hello_plugin.py`.

Use `click.testing.CliRunner` to invoke your command and assert its output.

### Example `test_hello_plugin.py`

```python
# tests/test_hello_plugin.py
import unittest
from click.testing import CliRunner
from plugins.hello_plugin.__init__ import hello

class TestHelloPlugin(unittest.TestCase):

    def test_hello_command_default(self):
        runner = CliRunner()
        result = runner.invoke(hello)
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Hello, World!", result.output)

    def test_hello_command_with_name(self):
        runner = CliRunner()
        result = runner.invoke(hello, ['Coddy'])
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Hello, Coddy!", result.output)
```

By following this structure, you can easily add new, isolated, and testable functionality to Coddy.