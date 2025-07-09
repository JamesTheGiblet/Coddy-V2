# c:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\backend\api\models\automation.py
from pydantic import BaseModel
from typing import Optional, Dict, Any

class GenerateChangelogRequest(BaseModel):
    output_file: str
    user_profile: Optional[Dict[str, Any]] = None

class GenerateTodoStubsRequest(BaseModel):
    scan_path: str
    output_file: str
    user_profile: Optional[Dict[str, Any]] = None