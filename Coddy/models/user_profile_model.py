# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\models\user_profile_model.py

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class Feedback(BaseModel):
    timestamp: str
    rating: int
    comment: Optional[str] = None
    context_id: Optional[str] = None # Unique ID of the interaction being rated

class UserProfileModel(BaseModel):
    username: str = "default_user"
    llm_provider_config: Dict[str, Any] = Field(default_factory=dict)
    idea_synth_persona: str = "default"
    idea_synth_creativity: float = 0.7
    feedback_log: List[Feedback] = Field(default_factory=list)
    coding_style_preferences: Dict[str, Any] = Field(default_factory=dict)
    # --- New fields for enhanced personalization ---
    preferred_languages: List[str] = Field(default_factory=list)
    common_patterns: Dict[str, Any] = Field(default_factory=dict)
    last_interaction_summary: Optional[Dict[str, Any]] = None # To store a summary of the last AI output for feedback context