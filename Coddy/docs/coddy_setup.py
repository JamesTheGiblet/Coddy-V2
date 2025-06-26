# coddy_setup.py
import os
import shutil
import json
from datetime import datetime
from typing import Dict

# Define the path for genesis_log.json - should be in Coddy/genesis_log.json
# Corrected path to place it inside the Coddy directory
GENESIS_LOG_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "Coddy")), "genesis_log.json")
# VIBE_DIR_PATH remains the same as it's where .vibe files are stored
VIBE_DIR_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "Coddy", ".vibe")


def _update_genesis_log(file_entry: Dict[str, str]):
    """
    Appends a new file entry to the genesis_log.json.
    Handles creation of the log file if it doesn't exist.
    """
    log_data = []
    try:
        # Ensure the directory for GENESIS_LOG_PATH exists before opening
        os.makedirs(os.path.dirname(GENESIS_LOG_PATH), exist_ok=True)
        with open(GENESIS_LOG_PATH, 'r', encoding='utf-8') as f:
            log_data = json.load(f)
    except FileNotFoundError:
        pass
    except json.JSONDecodeError:
        print(f"Warning: {GENESIS_LOG_PATH} is corrupted or empty. Starting new log.")
        log_data = []

    if not any(entry['location'] == file_entry['location'] and entry['name'] == file_entry['name'] for entry in log_data):
        log_data.append(file_entry)
        with open(GENESIS_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2)
        print(f"📄 Logged to genesis_log.json: {file_entry['name']}")
    else:
        print(f"📄 File already logged: {file_entry['name']}")


def create_structure(base_path, structure):
    """Recursively creates a directory structure from a nested dictionary."""
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            # It's a directory
            os.makedirs(path, exist_ok=True)
            print(f"📁 Created folder: {path}")
            create_structure(path, content)
            
            # Ensure .gitkeep is always present in empty directories
            if not os.listdir(path):
                gitkeep_path = os.path.join(path, ".gitkeep")
                if not os.path.exists(gitkeep_path):
                    with open(gitkeep_path, "w", encoding="utf-8") as f:
                        f.write("")
                    print(f"📄 Created .gitkeep in: {path}")
        else:
            write_content = False
            if not os.path.exists(path):
                write_content = True
            elif content is not None:
                write_content = True

            if write_content:
                with open(path, "w", encoding="utf-8") as f:
                    if content is not None:
                        f.write(content)
                print(f"📄 Created file: {path}")
            else:
                print(f"📄 File already exists, skipped: {path}")

            if name.endswith('.py'):
                # Pass the path relative to the Coddy root for logging
                # Example: Coddy/core/my_module.py -> core/my_module.py
                relative_to_coddy_root = os.path.relpath(path, start=os.path.join(os.path.abspath(os.path.dirname(__file__)), "Coddy"))
                
                file_entry = {
                    "location": os.path.dirname(relative_to_coddy_root).replace(os.sep, '/'), # Convert backslashes to forward
                    "name": os.path.basename(relative_to_coddy_root),
                    "type": "python_module",
                    "logged_at": datetime.now().isoformat()
                }
                _update_genesis_log(file_entry)


if __name__ == "__main__":
    base = os.getcwd()
    coddy_path = os.path.join(base, "Coddy")
    os.makedirs(coddy_path, exist_ok=True)
    print(f"🚀 Bootstrapping project structure at: {coddy_path}")

    coddy_structure = {
        "README.md": None,
        "roadmap.md": None,
        "genesis_log.json": None, # This file will be managed by the logging function
        ".vibe": { # This directory is for data files (.vibe snapshots)
            ".gitkeep": None # Ensure .gitkeep is created
        },
        "vibe": { # This is the Python package for vibe-related modules
            "__init__.py": None, # Make it a Python package
            "vibe_file_manager.py": """# Coddy/vibe/vibe_file_manager.py
import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Define the root path for the Coddy project from a known stable point (relative to this setup script)
# Assumes the setup script is in the root directory where Coddy/ is.
PROJECT_ROOT_FROM_VIBE_FILE_MANAGER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class VibeFileManager:
    \"\"\"
    Manages local file operations for VibeModeEngine snapshots.
    Stores and loads vibe states as JSON files in the dedicated .vibe directory.
    \"\"\"
    # Explicitly define the .vibe directory relative to PROJECT_ROOT_FROM_VIBE_FILE_MANAGER
    VIBE_DATA_DIR = os.path.join(PROJECT_ROOT_FROM_VIBE_FILE_MANAGER, '.vibe')


    def __init__(self):
        # Ensure the vibe data directory exists
        os.makedirs(self.VIBE_DATA_DIR, exist_ok=True)
        print(f"VibeFileManager initialized. Vibe data directory: {self.VIBE_DATA_DIR}")

    async def save_vibe_snapshot(self, snapshot_name: str, data: Dict[str, Any]) -> bool:
        \"\"\"
        Saves the given data as a JSON file in the vibe data directory.
        \"\"\"
        file_path = os.path.join(self.VIBE_DATA_DIR, f"{snapshot_name}.vibe")
        try:
            await asyncio.to_thread(self._write_json_file, file_path, data)
            return True
        except Exception as e:
            print(f"Error saving vibe snapshot '{snapshot_name}': {e}")
            return False

    async def load_vibe_snapshot(self, snapshot_name: str) -> Optional[Dict[str, Any]]:
        \"\"\"
        Loads data from a JSON file in the vibe data directory.
        \"\"\"
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
        \"\"\"
        Lists all available vibe snapshot names in the vibe directory.
        \"\"\"
        try:
            files = await asyncio.to_thread(os.listdir, self.VIBE_DATA_DIR)
            snapshots = [f.replace('.vibe', '') for f in files if f.endswith('.vibe')]
            return snapshots
        except Exception as e:
            print(f"Error listing vibe snapshots: {e}")
            return []

    def _write_json_file(self, file_path: str, data: Dict[str, Any]):
        \"\"\"Synchronously writes JSON data to a file.\"\"\"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def _read_json_file(self, file_path: str) -> Dict[str, Any]:
        \"\"\"Synchronously reads JSON data from a file.\"\"\"
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
""", # Content for vibe_file_manager.py moved to Coddy/vibe
        },
        "docs": {
            "banner.png": None,
            "system-diagram.png": None,
            "walkthrough-script.md": None
        },
        "core": {
            "roadmap_manager.py": None,
            "pattern_oracle.py": None,
            "idea_synth.py": None,
            "websocket_server.py": None,
            "vibe_mode.py": None,
            # ADDED: stub_auto_generator.py content
            "stub_auto_generator.py": """# Coddy/core/stub_auto_generator.py

import os
import asyncio
import re
from typing import List, Tuple, Optional

class StubAutoGenerator:
    \"\"\"
    Analyzes Python files asynchronously to identify incomplete functions
    and adds inline # TODO: comments or basic stubs.
    Designed for non-blocking I/O operations to align with Coddy's async-first philosophy.
    \"\"\"

    # Regex to find function definitions followed by no code or just 'pass', '...'
    # It attempts to capture the function signature and its current body indentation.
    INCOMPLETE_FUNCTION_PATTERN = re.compile(
        r"^(?P<indent>\\s*)def\\s+(?P<func_name>\\w+)\\s*\\((?P<args>[^)]*)\\):\\s*$" # function definition
        r"(?!^\\s*#\\s*TODO:.*$)" # Exclude if it already has a TODO immediately after
        r"(?!^\\s*(?:return|raise|yield|pass|...)(?:\\s*#.*)?$)", # Exclude if it has a return/raise/yield/pass/... statement
        re.MULTILINE | re.DOTALL
    )
    # This pattern specifically targets functions ending with just 'pass' or '...' for replacement
    PASS_OR_ELLIPSIS_PATTERN = re.compile(
        r"^(?P<indent>\\s*)(?:pass|\\.{3})\\s*(#.*)?$", re.MULTILINE
    )

    async def _read_file_async(self, file_path: str) -> Optional[str]:
        \"\"\"Asynchronously reads the content of a file.\"\"\"
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._sync_read_file, file_path)
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None

    def _sync_read_file(self, file_path: str) -> str:
        \"\"\"Synchronous helper for file reading, to be run in executor.\"\"\"
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    async def _write_file_async(self, file_path: str, content: str):
        \"\"\"Asynchronously writes content to a file.\"\"\"
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._sync_write_file, file_path, content)
        except Exception as e:
            print(f"Error writing to file {file_path}: {e}")

    def _sync_write_file(self, file_path: str, content: str):
        \"\"\"Synchronous helper for file writing, to be run in executor.\"\"\"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content) # Corrected line from previous interaction

    def _generate_stub(self, indent: str, func_name: str, args: str) -> str:
        \"\"\"Generates a Python stub based on the function's indentation and signature.\"\"\"
        stub_indent = indent + "    " # Add one level of indentation for the stub body
        # Basic stub structure
        stub = f"{stub_indent}# TODO: Implement functionality for {func_name}\\n"
        stub += f"{stub_indent}# Parameters: {args if args else 'None'}\\n"
        stub += f"{stub_indent}pass\\n" # Always end with pass to ensure valid syntax
        return stub

    async def process_file(self, file_path: str) -> bool:
        \"\"\"
        Asynchronously processes a single Python file to add or update stubs.
        Returns True if the file was modified, False otherwise.
        \"\"\"
        if not file_path.endswith('.py') or not os.path.exists(file_path):
            return False

        original_content = await self._read_file_async(file_path)
        if original_content is None:
            return False

        updated_content = []
        lines = original_content.splitlines()
        modified = False
        i = 0
        while i < len(lines):
            line = lines[i]
            match = self.INCOMPLETE_FUNCTION_PATTERN.match(line)
            if match:
                # Add the function definition line
                updated_content.append(line)
                indent = match.group('indent')
                func_name = match.group('func_name')
                args = match.group('args')

                # Check the next line for immediate 'pass' or '...' or empty line
                if i + 1 < len(lines):
                    next_line_stripped = lines[i+1].strip()
                    next_line_indent = lines[i+1].split(next_line_stripped)[0] if next_line_stripped else ''

                    if not next_line_stripped or self.PASS_OR_ELLIPSIS_PATTERN.match(lines[i+1]):
                        # If the next line is empty or just 'pass'/'...' with correct indentation
                        if len(next_line_indent) == len(indent) + 4: # Standard 4-space indentation
                             # Replace or add stub
                            stub = self._generate_stub(indent, func_name, args)
                            updated_content.extend(stub.strip().splitlines()) # Add stub lines
                            modified = True
                            if next_line_stripped: # If it was 'pass' or '...' skip original next line
                                i += 1
                        else: # If indentation is off, just add a TODO, don't replace
                            updated_content.append(f"{indent}    # TODO: Implement {func_name} - indentation might be off here.\\n")
                            modified = True
                    else: # If there's actual code or comments immediately after, just add a TODO above it
                        updated_content.append(f"{indent}    # TODO: Implement {func_name}\\n")
                        modified = True
                else: # If it's the last line of the file and an incomplete function
                    stub = self._generate_stub(indent, func_name, args)
                    updated_content.extend(stub.strip().splitlines())
                    modified = True
            else:
                updated_content.append(line)
            i += 1

        if modified:
            new_content = "\\n".join(updated_content)
            if new_content != original_content:
                await self._write_file_async(file_path, new_content)
                print(f"Stubbed incomplete functions in: {file_path}")
                return True
        return False

    async def scan_directory(self, directory_path: str) -> List[str]:
        \"\"\"
        Asynchronously scans a directory for Python files and processes them.
        Returns a list of file paths that were modified.
        \"\"\"
        modified_files = []
        # Store (coroutine, file_path) pairs
        tasks_with_paths = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    tasks_with_paths.append((self.process_file(file_path), file_path))

        # Separate tasks and paths for asyncio.gather
        tasks = [task for task, _ in tasks_with_paths]
        file_paths_order = [path for _, path in tasks_with_paths]

        results = await asyncio.gather(*tasks)

        for i, was_modified in enumerate(results):
            if was_modified:
                modified_files.append(file_paths_order[i]) # Use the stored file path
        
        return modified_files
"""
        },
        "ui": {
            "react-app": {
                "public": {
                    "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta
      name="description"
      content="Coddy V2 React UI"
    />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <title>Coddy V2 UI</title>
    <!-- Tailwind CSS CDN -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
      body {
        font-family: 'Inter', sans-serif;
      }
    </style>
</head>
<body class="bg-gray-900 text-gray-100 antialiased">
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
</body>
</html>
""",
                    "favicon.ico": None,
                    "logo192.png": None,
                    "manifest.json": None,
                },
                "src": {
                    "App.js": None,
                    "index.js": """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
""",
                    "index.css": """/* You can add global styles here, but Tailwind is preferred */
@tailwind base;
@tailwind components;
@tailwind utilities;
""",
                    "TabButton.js": """import React from 'react';

const TabButton = ({ icon, label, active, onClick }) => (
  <button
    onClick={onClick}
    className={`p-2 rounded-md flex flex-col items-center justify-center text-xs font-medium transition-all duration-200 ${
      active ? 'bg-indigo-700 text-white shadow-md' : 'text-gray-400 hover:bg-gray-700 hover:text-indigo-300'
    }`}
  >
    {icon}
    <span className="mt-1">{label}</span>
  </button>
);

export default TabButton;
"""
                },
                "package.json": """{
  "name": "react-app",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "react-scripts": "^5.0.1"
  }
}
""",
            },
            ".gitkeep": None
        },
        "data": {
            ".gitkeep": None
        },
        "tests": {
            "test_core_functions.py": None,
            "test_cli.py": None,
            ".gitkeep": None
        },
        "backend": {
            "tests": {
                "server.test.js": None,
                ".gitkeep": None
            },
            ".gitkeep": None
        }
    }

    create_structure(coddy_path, coddy_structure)
    print("✅ Coddy scaffold complete.")
