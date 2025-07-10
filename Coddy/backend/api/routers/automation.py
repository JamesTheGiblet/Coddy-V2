# c:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\backend\api\routers\automation.py

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional

# Use absolute imports from the project root for clarity and consistency
from backend.api.models.automation import GenerateChangelogRequest, GenerateTodoStubsRequest
from core.changelog_generator import ChangelogGenerator
from core.stub_auto_generator import StubAutoGenerator
from backend.services import services

router = APIRouter()

@router.post("/generate_changelog", response_model=Dict[str, Any])
async def generate_changelog_endpoint(payload: GenerateChangelogRequest):
    """
    Generates a changelog from Git history and saves it to a file.
    """
    changelog_generator: Optional[ChangelogGenerator] = services.get("changelog_generator")
    if not changelog_generator:
        raise HTTPException(status_code=503, detail="Changelog Generator service not available.")

    try:
        # Assuming a default repo_url for now, this could be part of the user profile or config
        repo_url = "https://github.com/youruser/yourrepo" 

        changelog_content = await changelog_generator.generate_changelog(
            output_file=payload.output_file,
            user_profile=payload.user_profile,
            repo_url=repo_url
        )

        return {"message": f"Changelog generated and saved to {payload.output_file}", "changelog_content": changelog_content}
    except Exception as e:
        # Consider logging the exception here for better debugging
        raise HTTPException(status_code=500, detail=f"Failed to generate changelog: {str(e)}")

@router.post("/generate_todo_stubs", response_model=Dict[str, Any])
async def generate_todo_stubs_endpoint(payload: GenerateTodoStubsRequest):
    """
    Scans a directory for TODO comments and generates a markdown file with stubs.
    """
    stub_generator: Optional[StubAutoGenerator] = services.get("stub_auto_generator")
    if not stub_generator:
        raise HTTPException(status_code=503, detail="Stub Auto-Generator service not available.")

    try:
        stubs_content = await stub_generator.generate_todo_stubs(
            scan_path=payload.scan_path,
            output_file=payload.output_file,
            user_profile=payload.user_profile
        )
        
        return {"message": f"TODO stubs generated and saved to {payload.output_file}", "stubs_content": stubs_content}
    except Exception as e:
        # Consider logging the exception here for better debugging
        raise HTTPException(status_code=500, detail=f"Failed to generate TODO stubs: {str(e)}")