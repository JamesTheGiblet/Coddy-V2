# c:/Users/gilbe/Documents/GitHub/Coddy V2/Coddy/conftest.py
import os
import sys

# Add the project root directory (which is the directory this file is in) to the Python path.
# This allows for absolute imports from the project root, e.g., `from backend.core import ...`
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))