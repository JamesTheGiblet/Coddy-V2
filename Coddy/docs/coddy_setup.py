# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\docs\coddy_setup.py

import os
import shutil
import json
from datetime import datetime
from typing import Dict

# Define the path for genesis_log.json - should be in Coddy/genesis_log.json
# Corrected path to place it inside the Coddy directory
GENESIS_LOG_PATH = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), "genesis_log.json")
# VIBE_DIR_PATH remains the same as it's where .vibe files are stored
VIBE_DIR_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", ".vibe")


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

            # Always log Python files
            if name.endswith('.py'):
                # Pass the path relative to the Coddy root for logging
                # Example: Coddy/core/my_module.py -> core/my_module.py
                relative_to_coddy_root = os.path.relpath(path, start=os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))
                
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
        "genesis_log.json": None, # This file will be managed by the logging function
        ".vibe": { # This directory is for data files (.vibe snapshots)
            ".gitkeep": None, # Ensure .gitkeep is created
            "vibe_file_manager.py": None
        },
        "vibe": { # This is the Python package for vibe-related modules
            "__init__.py": None, # Make it a Python package
        },
        "docs": {
            "banner.png": None,
            "coddy_setup.py": None,
            "system-diagram.png": None,
            "walkthrough-script.md": None
        },
        "models": {
            "user_profile_model.py": None
        },
        "core": {
            "changelog_generator.py": None,
            "code_generator.py": None,
            "git_analyzer.py": None,
            "idea_synth.py": None,
            "logging_utility.py": None,
            "memory_service.py": None,
            "pattern_oracle.py": None,
            "roadmap_manager.py": None,
            "stub_auto_generator.py": None,
            "ui_generator.py": None,
            "utility_functions.py": None,
            "utils.py": None,
            "vibe_file_manager.py": None,
            "vibe_mode.py": None,
            "websocket_server.py": None,
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
                    "TabButton.js": None, # Kept as None as it's a simple component and will be handled by App.js content
                    "RoadmapDisplay.js": None, # New file for Phase 7
                    "GitHistoryDisplay.js": None, # New file for Phase 7
                    "IdeaSynthesizerPlayground.js": None, # New file for Phase 7
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
            "cli.py": None, 
            ".gitkeep": None
        },
        "data": {
            ".gitkeep": None
        },
        "tests": {
            "test_core_functions.py": None,
            "test_cli.py": None,
            "test_git_analyzer.py": None,
            "test_code_generator.py": None,
            "test_plugin_manager.py": None,
            "test_refactor_plugin.py": None,
            "test_ollama_llm_plugin.py": None,
            ".gitkeep": None
        },
        "plugins": {
            ".gitkeep": None,
            "refactor_plugin": {
                "__init__.py": None
            },
            "ollama_llm_plugin": {
                "__init__.py": None
            }
        },
        "backend": {
            "tests": {
                "server.test.js": None,
                ".gitkeep": None
            },
            ".gitkeep": None
        },
        "roadmap.md": None
    }

    create_structure(coddy_path, coddy_structure)
    print("✅ Coddy scaffold complete.")
