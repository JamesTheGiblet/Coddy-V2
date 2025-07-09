# c:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\backend\api\routers\automation.py
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any

from Coddy.backend.api.models.automation import GenerateChangelogRequest, GenerateTodoStubsRequest
from Coddy.core.changelog_generator import ChangelogGenerator
from Coddy.core.stub_auto_generator import StubAutoGenerator

router = APIRouter()

@router.post("/generate_changelog", response_model=Dict[str, Any])
async def generate_changelog_endpoint(request: Request, payload: GenerateChangelogRequest):
    try:
        changelog_generator: ChangelogGenerator = request.app.state.services["changelog_generator"]
        
        # Assuming a default repo_url for now, this could be part of the user profile or config
        repo_url = "https://github.com/youruser/yourrepo" 

        changelog_content = await changelog_generator.generate_changelog(
            output_file=payload.output_file,
            user_profile=payload.user_profile,
            repo_url=repo_url
        )
        
        return {"message": f"Changelog generated and saved to {payload.output_file}", "changelog_content": changelog_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate changelog: {str(e)}")

@router.post("/generate_todo_stubs", response_model=Dict[str, Any])
async def generate_todo_stubs_endpoint(request: Request, payload: GenerateTodoStubsRequest):
    try:
        stub_generator: StubAutoGenerator = request.app.state.services["stub_auto_generator"]
        
        stubs_content = await stub_generator.generate_todo_stubs(
            scan_path=payload.scan_path,
            output_file=payload.output_file,
            user_profile=payload.user_profile
        )
        
        return {"message": f"TODO stubs generated and saved to {payload.output_file}", "stubs_content": stubs_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate TODO stubs: {str(e)}")