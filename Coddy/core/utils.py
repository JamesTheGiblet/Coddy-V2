# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\utils.py
import os

def write_file(file_path: str, content: str):
    """
    Writes content to a file, creating parent directories if they don't exist.
    """
    dir_path = os.path.dirname(file_path)
    if dir_path: # Only create directories if a directory path is specified
        os.makedirs(dir_path, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)