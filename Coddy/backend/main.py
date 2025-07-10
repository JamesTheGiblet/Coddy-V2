# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\backend\main.py

import asyncio
import os
import sys
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from the .env file located one level up from backend
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

# --- Path Setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

try:
    from core.memory_service import MemoryService
    from core.utility_functions import read_file, write_file, list_files
    from core.logging_utility import log_info, log_warning, log_error, log_debug
    from core.vibe_mode import VibeModeEngine
    from core.code_generator import CodeGenerator
    from core.task_decomposition_engine import TaskDecompositionEngine
    from core.git_analyzer import GitAnalyzer
    from core.user_profile import UserProfile
    from core.changelog_generator import ChangelogGenerator
    from core.stub_auto_generator import StubAutoGenerator
    from core.llm_provider import get_llm_provider

except ImportError as e:
    print(f"FATAL ERROR: Could not import core modules required for FastAPI backend: {e}", file=sys.stderr)
    sys.exit(1)

# Import Routers
from backend.api.routers import automation
from backend.services import services

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
    user_profile: Optional[Dict[str, Any]] = Field(None, description="User's personalization profile.")

class CodeGenerationRequest(BaseModel):
    prompt: str
    context: Optional[Dict[str, Any]] = Field(None, description="Optional context to provide to the code generator.")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="User's personalization profile.")

class RefactorCodeRequest(BaseModel):
    file_path: str
    original_code: str
    instructions: str
    user_profile: Optional[Dict[str, Any]] = Field(None, description="User's personalization profile.")

class RefactorCodeResponse(BaseModel):
    refactored_code: str

class UserProfileData(BaseModel):
    profile_data: Dict[str, Any]

class FeedbackRequest(BaseModel):
    rating: int
    comment: Optional[str] = None
    context_id: Optional[str] = None

class GitAnalysisRequest(BaseModel):
    repo_path: str = Field(".", description="Path to the git repository.")

class GitStatusResponse(BaseModel):
    branch: str
    uncommitted_files: List[str]
    untracked_files: List[str]
    log: List[Dict[str, Any]]


# --- Lifespan Management (Modern Approach) ---
DEFAULT_USER_ID = "api_user"
DEFAULT_SESSION_ID = "api_session_default"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes core services when the FastAPI application starts."""
    LLM_MODEL_NAME = "gemini-1.5-flash-latest"
    LLM_PROVIDER_TYPE = "gemini"

    await log_info("Coddy Backend API: Initializing core services...")
    try:
        services = {}
        services["memory_service"] = MemoryService(session_id=DEFAULT_SESSION_ID, user_id=DEFAULT_USER_ID, is_backend_core=True)
        
        services["user_profile_manager"] = UserProfile(
            session_id=DEFAULT_SESSION_ID, 
            user_id=DEFAULT_USER_ID,
            memory_service=services["memory_service"]
        )
        await services["user_profile_manager"].initialize()

        services["llm_provider"] = get_llm_provider(
            provider_name=LLM_PROVIDER_TYPE,
            config={"model": LLM_MODEL_NAME}
        )
        await log_info("LLMProvider initialized.")


        services["vibe_engine"] = VibeModeEngine(services["memory_service"], user_id=DEFAULT_USER_ID)
        await services["vibe_engine"].initialize()

        # MODIFIED: Pass llm_provider directly, removed model_name
        services["code_generator"] = CodeGenerator(
            llm_provider=services["llm_provider"], # Pass the centralized LLMProvider
            memory_service=services["memory_service"],
            vibe_engine=services["vibe_engine"],
            user_profile_manager=services["user_profile_manager"]
        )
        await services["code_generator"].initialize()

        # MODIFIED: Pass llm_provider directly, removed model_name
        services["task_decomposition_engine"] = TaskDecompositionEngine(
            llm_provider=services["llm_provider"] # Pass the centralized LLMProvider
        )
        
        services["git_analyzer"] = GitAnalyzer()

        services["changelog_generator"] = ChangelogGenerator(
            llm_provider=services["llm_provider"],
            memory_service=services["memory_service"],
            git_analyzer=services["git_analyzer"],
            user_profile_manager=services["user_profile_manager"]
        )
        services["stub_auto_generator"] = StubAutoGenerator(
            memory_service=services["memory_service"],
            code_generator=services["code_generator"],
            user_profile_manager=services["user_profile_manager"]
        )

        await log_info("Coddy Backend API: Core services initialized successfully.")
        yield
    except Exception as e:
        await log_error(f"Coddy Backend API: Failed to initialize core services: {e}", exc_info=True)
        raise
    finally:
        await log_info("Coddy Backend API: Shutting down...")
        memory_service = services.get("memory_service")
        if memory_service:
            await memory_service.close()
        user_profile_manager = services.get("user_profile_manager")
        if user_profile_manager:
            await user_profile_manager.close()
        services.clear()

# --- App Initialization ---
app = FastAPI(
    title="Coddy Unified API",
    description="Unified API for Coddy, managing file operations, memory, and autonomous agent tasks.",
    version="2.1.0",
    lifespan=lifespan,
)

# Include the new automation router
app.include_router(automation.router, prefix="/api/automation", tags=["Automation"])

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
        # Pass user_profile to the decompose method
        subtasks = await engine.decompose(request.instruction, user_profile=request.user_profile)
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
        # Pass user_profile to the generate_code method
        generated_code = await generator.generate_code(
            prompt=request.prompt,
            context=request.context,
            user_profile=request.user_profile
        )
        return {"code": generated_code}
    except Exception as e:
        await log_error(f"Error generating code: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during code generation: {e}")

@api_router.post("/code/refactor", response_model=RefactorCodeResponse, tags=["Agent Operations"])
async def refactor_code_endpoint(request: RefactorCodeRequest):
    generator = services.get("code_generator")
    if not generator:
        raise HTTPException(status_code=503, detail="Code Generator not available.")
    try:
        # The generate_code_fix method can be repurposed for general refactoring
        refactored_code = await generator.generate_code_fix(
            file_path=request.file_path,
            context={
                "original_code": request.original_code,
                "problem_description": request.instructions
            },
            user_profile=request.user_profile
        )
        return {"refactored_code": refactored_code}
    except Exception as e:
        await log_error(f"Error refactoring code for '{request.file_path}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during refactoring: {e}")

@api_router.get("/profile", response_model=Dict[str, Any], tags=["Personalization"])
async def get_user_profile_endpoint():
    user_profile_manager = services.get("user_profile_manager")
    if not user_profile_manager or not user_profile_manager.profile:
        raise HTTPException(status_code=503, detail="User Profile service not available or not loaded.")
    try:
        # Return the profile data as a dictionary
        return user_profile_manager.profile.model_dump()
    except Exception as e:
        await log_error(f"Error getting user profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.post("/profile/set", response_model=MessageResponse, tags=["Personalization"])
async def set_user_profile_endpoint(request: UserProfileData):
    user_profile_manager = services.get("user_profile_manager")
    if not user_profile_manager:
        raise HTTPException(status_code=503, detail="User Profile service not available.")
    try:
        # Iterate through the provided profile_data and set each key-value pair
        for key, value in request.profile_data.items():
            await user_profile_manager.set(key, value)
        return {"message": "User profile updated successfully."}
    except AttributeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid profile attribute: {e}")
    except Exception as e:
        await log_error(f"Error setting user profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.post("/profile/clear", response_model=MessageResponse, tags=["Personalization"])
async def clear_user_profile_endpoint():
    user_profile_manager = services.get("user_profile_manager")
    if not user_profile_manager:
        raise HTTPException(status_code=503, detail="User Profile service not available.")
    try:
        await user_profile_manager.clear_profile()
        return {"message": "User profile cleared to default."}
    except Exception as e:
        await log_error(f"Error clearing user profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@api_router.post("/feedback/add", response_model=MessageResponse, tags=["Personalization"])
async def add_feedback_endpoint(request: FeedbackRequest):
    user_profile_manager = services.get("user_profile_manager")
    if not user_profile_manager:
        raise HTTPException(status_code=503, detail="User Profile service not available.")
    try:
        await user_profile_manager.add_feedback(
            rating=request.rating,
            comment=request.comment,
            context_id=request.context_id
        )
        return {"message": "Feedback submitted successfully."}
    except Exception as e:
        await log_error(f"Error adding feedback: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    print("Starting Coddy Backend API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
