# Coddy/backend/main.py
import asyncio
import os
import sys
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, Field

try:
    from ..core.memory_service import MemoryService
    from ..core.utility_functions import read_file, write_file, list_files
    from ..core.logging_utility import log_info, log_warning, log_error, log_debug
    from ..core.vibe_mode import VibeModeEngine
    from ..core.code_generator import CodeGenerator
    from ..core.task_decomposition_engine import TaskDecompositionEngine
    from ..core.git_analyzer import GitAnalyzer
except ImportError as e:
    print(f"FATAL ERROR: Could not import core modules required for FastAPI backend: {e}", file=sys.stderr)
    sys.exit(1)

# --- Pydantic Models ---
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

class DecomposeRequest(BaseModel):
    instruction: str

class CodeGenerationRequest(BaseModel):
    prompt: str
    context: Optional[str] = Field(None, description="Optional context to provide to the code generator.")

class GitAnalysisRequest(BaseModel):
    repo_path: str = Field(".", description="Path to the git repository.")

class GitStatusResponse(BaseModel):
    branch: str
    uncommitted_files: List[str]
    untracked_files: List[str]
    log: List[Dict[str, Any]]

# --- Lifespan Management (Modern Approach) ---
services = {}
DEFAULT_USER_ID = "api_user"
DEFAULT_SESSION_ID = "api_session_default"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes core services when the FastAPI application starts."""
    await log_info("Coddy Backend API: Initializing core services...")
    try:
        services["memory_service"] = MemoryService(session_id=DEFAULT_SESSION_ID, user_id=DEFAULT_USER_ID, is_backend_core=True)
        services["vibe_engine"] = VibeModeEngine(services["memory_service"], user_id=DEFAULT_USER_ID)
        services["code_generator"] = CodeGenerator()
        services["task_decomposition_engine"] = TaskDecompositionEngine()
        services["git_analyzer"] = GitAnalyzer()

        await services["code_generator"].initialize()
        await log_info("Coddy Backend API: Core services initialized successfully.")
        yield
    except Exception as e:
        await log_error(f"Coddy Backend API: Failed to initialize core services: {e}", exc_info=True)
        raise
    finally:
        await log_info("Coddy Backend API: Shutting down...")
        services.clear()

# --- App Initialization ---
app = FastAPI(
    title="Coddy Unified API",
    description="Unified API for Coddy, managing file operations, memory, and autonomous agent tasks.",
    version="2.1.0",
    lifespan=lifespan,
)

# --- API Routers ---
api_router = APIRouter(prefix="/api")

# --- Endpoints ---
@api_router.get("/roadmap", response_model=Dict[str, str], tags=["Roadmap"])
async def get_roadmap_endpoint():
    try:
        roadmap_content = await read_file("roadmap.md")
        return {"content": roadmap_content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Roadmap file not found.")
    except Exception as e:
        await log_error(f"Error fetching roadmap: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.get("/files/list", response_model=ListItem, tags=["File Operations"])
async def list_files_endpoint(path: str = "."):
    try:
        items = await list_files(path)
        return {"items": items}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Directory not found: {path}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await log_error(f"Error listing files for path '{path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.get("/files/read", response_model=FileContent, tags=["File Operations"])
async def read_file_endpoint(path: str):
    try:
        content = await read_file(path)
        return {"path": path, "content": content}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await log_error(f"Error reading file '{path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.post("/files/write", response_model=MessageResponse, tags=["File Operations"])
async def write_file_endpoint(file_data: FileContent):
    try:
        await write_file(file_data.path, file_data.content)
        return {"message": f"Successfully wrote to {file_data.path}"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await log_error(f"Error writing to file '{file_data.path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.post("/memory/store", response_model=MessageResponse, tags=["Memory Operations"])
async def store_memory_endpoint(memory_entry: MemoryEntry):
    memory_service = services.get("memory_service")
    if not memory_service:
        await log_error("MemoryService not initialized when /api/memory/store was called.")
        raise HTTPException(status_code=503, detail="Memory service not available.")
    try:
        await memory_service.store_memory(
            content=memory_entry.content,
            tags=memory_entry.tags
        )
        return {"message": "Memory stored successfully."}
    except Exception as e:
        await log_error(f"Error storing memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.post("/memory/retrieve_context", response_model=List[Dict[str, Any]], tags=["Memory Operations"])
async def retrieve_memory_context_endpoint(query_data: MemoryQuery):
    memory_service = services.get("memory_service")
    if not memory_service:
        await log_error("MemoryService not initialized when /api/memory/retrieve_context was called.")
        raise HTTPException(status_code=503, detail="Memory service not available.")
    try:
        query_params = query_data.query.copy()
        if "user_id" not in query_params:
            query_params["user_id"] = DEFAULT_USER_ID

        memories = await memory_service.retrieve_context(
            num_recent=query_data.num_recent,
            query=query_params
        )
        return memories
    except Exception as e:
        await log_error(f"Error retrieving memory context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.post("/memory/load", response_model=List[Dict[str, Any]], tags=["Memory Operations"])
async def load_memory_endpoint(query_data: MemoryQuery):
    memory_service = services.get("memory_service")
    if not memory_service:
        await log_error("MemoryService not initialized when /api/memory/load was called.")
        raise HTTPException(status_code=503, detail="Memory service not available.")
    try:
        memories = await memory_service.load_memory(query=query_data.query)
        return memories
    except Exception as e:
        await log_error(f"Error loading memory: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.post("/tasks/decompose", response_model=List[str], tags=["Agent Operations"])
async def decompose_task_endpoint(request: DecomposeRequest):
    engine = services.get("task_decomposition_engine")
    if not engine:
        raise HTTPException(status_code=503, detail="Task Decomposition Engine not available.")
    try:
        subtasks = await engine.decompose(request.instruction)
        if not subtasks or (len(subtasks) == 1 and "Error:" in subtasks[0]):
             raise HTTPException(status_code=400, detail=f"Could not decompose task: {subtasks[0] if subtasks else 'Unknown issue'}")
        return subtasks
    except Exception as e:
        await log_error(f"Error during task decomposition: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during decomposition: {e}")

@api_router.post("/code/generate", response_model=Dict[str, str], tags=["Agent Operations"])
async def generate_code_endpoint(request: CodeGenerationRequest):
    generator = services.get("code_generator")
    if not generator:
        raise HTTPException(status_code=503, detail="Code Generator not available.")
    try:
        generated_code = await generator.generate_code(
            prompt=request.prompt,
            context=request.context # Removed user_id=DEFAULT_USER_ID
        )
        return {"code": generated_code}
    except Exception as e:
        await log_error(f"Error generating code: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during code generation: {e}")

app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    print("Starting Coddy Backend API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
