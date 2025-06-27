# models/user_profile_model.py
from pydantic import BaseModel
from datetime import date

class UserProfileModel(BaseModel):
    """A Pydantic model for a user profile."""
    username: str
    full_name: str
    age: int
    is_active: bool
    join_date: date