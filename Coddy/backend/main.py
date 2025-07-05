# Coddy/backend/main.py
import asyncio
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# Add the project root to sys.path to allow imports from 'core'
# Assuming the script is run from the project root (e.g., Coddy V2/)
# or that 'Coddy/backend/main.py' is the path.
# This calculates the path to 'C:\Users\gilbe\Documents\GitHub\Coddy V2'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


from fastapi import FastAPI, APIRouter, HTTPException, Body, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Import core services that the API will interact with
try:
    from Coddy.core.memory_service import MemoryService # Updated import path
    from Coddy.core.utility_functions import read_file, write_file, list_files # Updated import path
    from Coddy.core.logging_utility import log_info, log_warning, log_error, log_debug # Updated import path
    from Coddy.core.vibe_mode import VibeModeEngine # Updated import path
    from Coddy.core.code_generator import CodeGenerator # Updated import path
    from Coddy.core.task_decomposition_engine import TaskDecompositionEngine # Updated import path
    from Coddy.core.git_analyzer import GitAnalyzer # Updated import path
except ImportError as e:
    print(f"FATAL ERROR: Could not import core modules required for FastAPI backend: {e}", file=sys.stderr)
    sys.exit(1)

# --- FastAPI App Initialization ---
app = FastAPI(
    title="Coddy Backend API",
    description="API for Coddy: The Sentient Loop, managing file operations, memory, and autonomous agent tasks.",
    version="2.0.0",
)

# --- Global Service Instances (initialized on startup) ---
# These will be shared across all API requests
memory_service: Optional[MemoryService] = None
vibe_engine: Optional[VibeModeEngine] = None
code_generator: Optional[CodeGenerator] = None
task_decomposition_engine: Optional[TaskDecompositionEngine] = None
git_analyzer: Optional[GitAnalyzer] = None

# Placeholder for user/session IDs for API context.
# In a real application, these would be managed per authenticated user/session.
DEFAULT_USER_ID = "api_user"
DEFAULT_SESSION_ID = "api_session_default" # A single session for the API

@app.on_event("startup")
async def startup_event():
    """
    Initializes core services when the FastAPI application starts.
    """
    global memory_service, vibe_engine, code_generator, task_decomposition_engine, git_analyzer
    await log_info("Coddy Backend API: Initializing core services...")
    try:
        # Initialize services with placeholder IDs for now.
        # In a production setup, these would be managed per authenticated user/session.
        memory_service = MemoryService(session_id=DEFAULT_SESSION_ID, user_id=DEFAULT_USER_ID)
        vibe_engine = VibeModeEngine(memory_service, user_id=DEFAULT_USER_ID)
        code_generator = CodeGenerator() 
        task_decomposition_engine = TaskDecompositionEngine() # Does not need other services in constructor
        git_analyzer = GitAnalyzer()

        # Removed: await vibe_engine.initialize() # This was causing the circular dependency/race condition during startup
        await code_generator.initialize() 

        await log_info("Coddy Backend API: Core services initialized successfully.")
    except Exception as e:
        await log_error(f"Coddy Backend API: Failed to initialize core services: {e}", exc_info=True)
        # It's critical to exit if core services can't initialize
        sys.exit(1)

# --- API Router for /api prefix ---
api_router = APIRouter(prefix="/api")

# --- Pydantic Models for Request/Response Bodies ---
class FilePath(BaseModel):
    path: str = Field(..., example="my_file.py")

class FileContent(FilePath):
    content: str = Field(..., example="print('Hello, Coddy!')")

class MessageResponse(BaseModel):
    message: str = Field(..., example="Operation successful.")

class ListItem(BaseModel):
    items: List[str] = Field(..., example=["file1.txt", "dir1/"])

class MemoryEntry(BaseModel):
    content: Dict[str, Any] = Field(..., example={"type": "command", "command": "read", "file": "test.txt"})
    tags: Optional[List[str]] = Field(None, example=["cli_command", "read_op"])

class MemoryQuery(BaseModel):
    query: Dict[str, Any] = Field(..., example={"tags": ["checkpoint"]})
    num_recent: Optional[int] = Field(None, example=5)


# --- API Endpoints ---

@api_router.get("/roadmap", response_model=Dict[str, str])
async def get_roadmap_endpoint():
    """
    Fetches the project roadmap content.
    """
    try:
        # Assuming roadmap.md is in the project root or accessible via read_file
        # You might want to move roadmap.md to a data/ or docs/ folder
        roadmap_content = await read_file("roadmap.md")
        return {"content": roadmap_content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Roadmap file not found.")
    except Exception as e:
        await log_error(f"Error fetching roadmap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.get("/files/list", response_model=ListItem)
async def list_files_endpoint(path: str = "."):
    """
    Lists files and directories at a given path.
    """
    try:
        items = await list_files(path)
        return {"items": items}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
    except ValueError as e: # From safe_path
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await log_error(f"Error listing files for path '{path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.get("/files/read", response_model=FileContent)
async def read_file_endpoint(path: str):
    """
    Reads the content of a specified file.
    """
    try:
        content = await read_file(path)
        return {"path": path, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found.")
    except ValueError as e: # From safe_path
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await log_error(f"Error reading file '{path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.post("/files/write", response_model=MessageResponse)
async def write_file_endpoint(file_data: FileContent):
    """
    Writes content to a specified file. Creates parent directories if they don't exist.
    """
    try:
        await write_file(file_data.path, file_data.content)
        return {"message": f"Successfully wrote to {file_data.path}"}
    except ValueError as e: # From safe_path
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await log_error(f"Error writing to file '{file_data.path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

# --- Memory Service Endpoints (The missing piece!) ---

@api_router.post("/memory/store", response_model=MessageResponse)
async def store_memory_endpoint(memory_entry: MemoryEntry):
    """
    Stores a new memory entry.
    """
    if not memory_service:
        await log_error("MemoryService not initialized when /api/memory/store was called.")
        raise HTTPException(status_code=503, detail="Memory service not available.")
    try:
        # The MemoryService handles session_id and user_id internally from its initialization
        await memory_service.store_memory(
            content=memory_entry.content,
            tags=memory_entry.tags
        )
        return {"message": "Memory stored successfully."}
    except Exception as e:
        await log_error(f"Error storing memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.post("/memory/retrieve_context", response_model=List[Dict[str, Any]])
async def retrieve_memory_context_endpoint(query_data: MemoryQuery):
    """
    Retrieves recent memory entries based on a query.
    """
    if not memory_service:
        await log_error("MemoryService not initialized when /api/memory/retrieve_context was called.")
        raise HTTPException(status_code=503, detail="Memory service not available.")
    try:
        # Ensure user_id is part of the query for context retrieval
        query_params = query_data.query.copy()
        if "user_id" not in query_params:
            query_params["user_id"] = DEFAULT_USER_ID # Fallback if not explicitly provided

        memories = await memory_service.retrieve_context(
            num_recent=query_data.num_recent,
            query=query_params
        )
        return memories
    except Exception as e:
        await log_error(f"Error retrieving memory context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.post("/memory/load", response_model=List[Dict[str, Any]])
async def load_memory_endpoint(query_data: MemoryQuery):
    """
    Loads memory entries based on a specific query (e.g., for search).
    """
    if not memory_service:
        await log_error("MemoryService not initialized when /api/memory/load was called.")
        raise HTTPException(status_code=503, detail="Memory service not available.")
    try:
        # The MemoryService's load_memory method already handles query structure
        memories = await memory_service.load_memory(query=query_data.query)
        return memories
    except Exception as e:
        await log_error(f"Error loading memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


# --- Include the API router in the main app ---
app.include_router(api_router)

# --- Main block to run the FastAPI app ---
if __name__ == "__main__":
    import uvicorn
    # To run this server, you would execute:
    # uvicorn Coddy.backend.main:app --host 0.0.0.0 --port 8000 --reload
    # The --reload flag is useful for development as it restarts the server on code changes.
    print("Starting Coddy Backend API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

