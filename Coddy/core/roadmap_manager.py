# c:/Users/gilbe/Documents/GitHub/Coddy V2/Coddy/core/roadmap_manager.py

from pathlib import Path
import os

class RoadmapManager:
    def __init__(self, roadmap_path: str = "roadmap.md"):
        # Assumes roadmap.md is in the project root, a parent of the 'core' directory.
        self.roadmap_file = Path(os.path.dirname(__file__)).parent / roadmap_path
        if not self.roadmap_file.exists():
            raise FileNotFoundError(f"Roadmap file not found at {self.roadmap_file}")

    def get_roadmap_content(self) -> str:
        """Reads and returns the raw content of the roadmap.md file."""
        return self.roadmap_file.read_text(encoding='utf-8')