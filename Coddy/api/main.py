# C:\Users\gilbe\Documents\GitHub\Coddy V2\Coddy\api\main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..core.roadmap_manager import RoadmapManager
from ..core.utility_functions import list_files, read_file, write_file
from ..core.task_decomposition_engine import TaskDecompositionEngine

# --- Pydantic Models ---
class FileWriteRequest(BaseModel):
    path: str
    content: str

class DecomposeRequest(BaseModel):
    instruction: str

# --- Lifespan Management ---
services = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    print("Coddy API starting up...")
    # You can initialize resources here, like database connections.
    services["task_decomposition_engine"] = TaskDecompositionEngine()
    yield
    # Clean up resources on shutdown.
    services.clear()
    print("Coddy API shutting down...")

# --- App Initialization ---
app = FastAPI(
    title="Coddy API",
    description="Backend services for the Coddy AI Dev Companion.",
    version="2.0.0",
    lifespan=lifespan,
)

# --- Middleware ---
# Allow all origins for now, for easy dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
# Group file-related endpoints for better organization
file_router = APIRouter(
    prefix="/api/files",
    tags=["File Operations"],
)

task_router = APIRouter(
    prefix="/api/tasks",
    tags=["Task Operations"],
)

# --- Dependencies and Services ---
roadmap_manager = RoadmapManager()

# --- API Endpoints ---
@app.get("/api/roadmap", tags=["Roadmap"])
async def get_roadmap():
    """Retrieves the content of the project's roadmap.md file."""
    try:
        content = roadmap_manager.get_roadmap_content()
        return {"content": content}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@file_router.get("/list")
async def list_directory_contents(path: str = "."):
    """Lists files and directories at a given path."""
    try:
        items = await list_files(path)
        return {"items": items}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
    except ValueError as e:  # For safe_path validation
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@file_router.get("/read")
async def read_file_contents(path: str):
    """Reads the content of a file at a given path."""
    try:
        content = await read_file(path)
        return {"content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {path}")
    except ValueError as e:  # For safe_path validation
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@file_router.post("/write")
async def write_file_contents(request: FileWriteRequest):
    """Writes content to a file at a given path."""
    try:
        await write_file(request.path, request.content)
        return {"message": f"Successfully wrote to {request.path}"}
    except ValueError as e:  # For safe_path validation
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@task_router.post("/decompose", response_model=list[str])
async def decompose_task(request: DecomposeRequest):
    """Decomposes a high-level instruction into a series of subtasks."""
    try:
        engine = services.get("task_decomposition_engine")
        if not engine:
            raise HTTPException(status_code=503, detail="Task Decomposition Engine not available.")
        
        subtasks = await engine.decompose(request.instruction)
        
        if not subtasks or (len(subtasks) == 1 and "Error:" in subtasks[0]):
             raise HTTPException(status_code=400, detail=f"Could not decompose task: {subtasks[0] if subtasks else 'Unknown issue'}")

        return subtasks
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during decomposition: {e}")

# Include the router in the main app
app.include_router(file_router)
app.include_router(task_router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Coddy API is running. Visit /docs for API documentation."}