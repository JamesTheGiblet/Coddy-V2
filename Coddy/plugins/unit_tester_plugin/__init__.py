import click
import asyncio
from core.code_generator import CodeGenerator

@click.command('unit_test')
@click.argument('file_path', type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.pass_context
def unit_tester(ctx, file_path):
    """
    Generates unit tests for a given Python source file.
    """
    asyncio.run(_unit_tester_async(ctx, file_path))

async def _unit_tester_async(ctx, file_path):
    click.echo(f"Generating unit tests for {file_path}...")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        code_gen = CodeGenerator(user_id='default_user')
        generated_tests = await code_gen.generate_tests(source_code)

        click.echo("\n--- Generated Tests ---")
        click.echo(generated_tests)

    except Exception as e:
        click.echo(f"Error generating tests: {e}", err=True)
        ctx.exit(1)

def register():
    return unit_tester
