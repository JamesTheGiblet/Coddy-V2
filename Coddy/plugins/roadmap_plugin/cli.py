# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\plugins\roadmap_plugin\cli.py

import asyncio

import click
import httpx
from rich.console import Console
from rich.markdown import Markdown

from Coddy.core.config import API_BASE_URL # MODIFIED: Import API_BASE_URL from config.py

# REMOVED: API_BASE_URL = "http://127.0.0.1:8000"

async def fetch_and_print_roadmap():
    """Fetches roadmap from the API and prints it to the console."""
    console = Console()
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_BASE_URL}/api/roadmap")
            response.raise_for_status()   # Raise an exception for bad status codes (4xx or 5xx)
            data = response.json()
            content = data.get("content", "No roadmap content found.")
            markdown = Markdown(content)
            console.print(markdown)
    except httpx.RequestError as e:
        # This catches network-related errors like connection refused, timeout, etc.
        error_message = (
            f"Error connecting to the Coddy API at {API_BASE_URL}.\n"
            "Please ensure the API server is running.\n"
            f"Details: {e}"
        )
        click.secho(error_message, fg="red", err=True)
    except httpx.HTTPStatusError as e:
        # This catches errors for non-2xx responses
        error_message = (
            f"API returned an error: {e.response.status_code} {e.response.reason_phrase}\n"
            f"URL: {e.request.url}"
        )
        click.secho(error_message, fg="red", err=True)
    except Exception as e:
        click.secho(f"An unexpected error occurred: {e}", fg="red", err=True)


@click.command()
def roadmap():
    """Displays the project roadmap by fetching it from the Coddy API."""
    asyncio.run(fetch_and_print_roadmap())