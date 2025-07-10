# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\api\routers\files.py

import os
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

router = APIRouter()

# For better security and flexibility, consider making PROJECT_ROOT configurable,
# for example, by using an environment variable.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def is_safe_path(path: str) -> bool:
    """
    Check if the path is within the project directory to prevent traversal attacks.
    """
    try:
        resolved_path = Path(path).resolve()
        return resolved_path.is_relative_to(PROJECT_ROOT)
    except (ValueError, Exception):
        return False


@router.get("/api/files/list", response_model=Dict[str, Any])
async def list_files_or_get_details(path: str):
    """
    Lists files and directories at a given path, or provides details for a single file.
    """
    if not is_safe_path(path):
        raise HTTPException(status_code=400, detail="Invalid or unsafe path provided.")

    p = Path(path)

    if not p.exists():
        raise HTTPException(status_code=404, detail=f"Path does not exist: {path}")

    if p.is_dir():
        contents = [item.name for item in p.iterdir()]
        return {"path": str(p), "type": "directory", "contents": contents}
    elif p.is_file():
        stat = p.stat()
        return {"path": str(p), "type": "file", "size": stat.st_size, "last_modified": stat.st_mtime}
    else:
        raise HTTPException(status_code=400, detail="Path is not a regular file or directory.")