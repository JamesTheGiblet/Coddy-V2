# c:/Users/gilbe/Documents/GitHub/Coddy V2/Coddy/core/roadmap_manager.py

from pathlib import Path
import os
import asyncio # Import asyncio for async operations
# MODIFIED: Import save_file_in_timestamped_folder from utility_functions
from core.utility_functions import save_file_in_timestamped_folder
from core.logging_utility import log_info, log_error, log_warning # Import logging utilities

class RoadmapManager:
    def __init__(self, roadmap_path: str = "roadmap.md"):
        # Assumes roadmap.md is in the project root, a parent of the 'core' directory.
        self.roadmap_file = Path(os.path.dirname(__file__)).parent / roadmap_path
        # Removed the FileNotFoundError check from __init__ as it's not strictly necessary
        # for a manager that might also be responsible for creating the roadmap.

    def get_roadmap_content(self) -> str:
        """Reads and returns the raw content of the roadmap.md file."""
        # Add a check to ensure the file exists before reading
        if not self.roadmap_file.exists():
            log_warning(f"Roadmap file not found at {self.roadmap_file}. Returning empty string.")
            return ""
        return self.roadmap_file.read_text(encoding='utf-8')

    async def save_roadmap(self, content: str, output_file_name: str = "roadmap.md") -> None:
        """
        Saves the generated roadmap content into a timestamped folder.

        Args:
            content (str): The Markdown content of the roadmap.
            output_file_name (str): The desired filename for the roadmap (e.g., "roadmap.md").
        """
        try:
            await save_file_in_timestamped_folder(
                content=content,
                file_path=output_file_name,
                category="roadmaps"
            )
            await log_info(f"Roadmap saved successfully to a timestamped folder: {output_file_name}")
        except Exception as e:
            await log_error(f"Failed to save roadmap: {e}", exc_info=True)
            raise # Re-raise the exception after logging
