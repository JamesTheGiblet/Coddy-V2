# plugins/ollama_llm_plugin/__init__.py
import click
import requests
import json

# Default Ollama API endpoint
OLLAMA_API_URL = "http://localhost:11434/api/generate"

@click.group(name="ollama")
def ollama_group():
    """Commands for interacting with a local Ollama LLM."""
    pass

@ollama_group.command()
@click.argument('prompt')
@click.option('--model', default='mistral', help='The Ollama model to use.')
def chat(prompt, model):
    """Sends a prompt to the local Ollama model and streams the response."""
    click.echo(f"Connecting to Ollama with model '{model}'...")
    
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True
    }

    try:
        with requests.post(OLLAMA_API_URL, json=payload, stream=True, timeout=60) as response:
            if response.status_code == 200:
                click.echo("Response: ", nl=False)
                for chunk in response.iter_lines():
                    if chunk:
                        try:
                            json_chunk = json.loads(chunk)
                            click.echo(json_chunk.get("response", ""), nl=False)
                            if json_chunk.get("done"):
                                click.echo() # Newline at the end
                        except json.JSONDecodeError:
                            click.echo(f"\n[Error decoding chunk: {chunk}]")
                click.secho("\nDone.", fg="green")
            else:
                click.secho(f"Error: Received status code {response.status_code}", fg="red")
                click.secho(response.text, fg="red")
    except requests.exceptions.ConnectionError:
        click.secho("Error: Could not connect to Ollama server at http://localhost:11434.", fg="red")
        click.secho("Please ensure Ollama is running.", fg="yellow")
    except requests.exceptions.RequestException as e:
        click.secho(f"An unexpected error occurred: {e}", fg="red")

def register() -> list[click.Command]:
    """Registers the commands provided by this plugin."""
    return [ollama_group]