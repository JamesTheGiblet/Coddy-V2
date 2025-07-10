# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\vibe\vibe_file_manager.py

import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Define the root path for the Coddy project from a known stable point (relative to this setup script)
# Assumes the setup script is in the root directory where Coddy/ is.
PROJECT_ROOT_FROM_VIBE_FILE_MANAGER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class VibeFileManager:
    """
    Manages local file operations for VibeModeEngine snapshots.
    Stores and loads vibe states as JSON files in the dedicated .vibe directory.
    """
    # Explicitly define the .vibe directory relative to PROJECT_ROOT_FROM_VIBE_FILE_MANAGER
    VIBE_DATA_DIR = os.path.join(PROJECT_ROOT_FROM_VIBE_FILE_MANAGER, '.vibe')


    def __init__(self):
        # Ensure the vibe data directory exists
        os.makedirs(self.VIBE_DATA_DIR, exist_ok=True)
        print(f"VibeFileManager initialized. Vibe data directory: {self.VIBE_DATA_DIR}")

    async def save_vibe_snapshot(self, snapshot_name: str, data: Dict[str, Any]) -> bool:
        """
        Saves the given data as a JSON file in the vibe data directory.
        """
        file_path = os.path.join(self.VIBE_DATA_DIR, f"{snapshot_name}.vibe")
        try:
            await asyncio.to_thread(self._write_json_file, file_path, data)
            return True
        except Exception as e:
            print(f"Error saving vibe snapshot '{snapshot_name}': {e}")
            return False

    async def load_vibe_snapshot(self, snapshot_name: str) -> Optional[Dict[str, Any]]:
        """
        Loads data from a JSON file in the vibe data directory.
        """
        file_path = os.path.join(self.VIBE_DATA_DIR, f"{snapshot_name}.vibe")
        try:
            data = await asyncio.to_thread(self._read_json_file, file_path)
            return data
        except FileNotFoundError:
            print(f"Vibe snapshot '{snapshot_name}.vibe' not found at {file_path}.")
            return None
        except Exception as e:
            print(f"Error loading vibe snapshot '{snapshot_name}': {e}")
            return None

    async def list_vibe_snapshots(self) -> List[str]:
        """
        Lists all available vibe snapshot names in the vibe directory.
        """
        try:
            files = await asyncio.to_thread(os.listdir, self.VIBE_DATA_DIR)
            snapshots = [f.replace('.vibe', '') for f in files if f.endswith('.vibe')]
            return snapshots
        except Exception as e:
            print(f"Error listing vibe snapshots: {e}")
            return []

    def _write_json_file(self, file_path: str, data: Dict[str, Any]):
        """Synchronously writes JSON data to a file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def _read_json_file(self, file_path: str) -> Dict[str, Any]:
        """Synchronously reads JSON data from a file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
