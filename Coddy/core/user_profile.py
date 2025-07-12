# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\core\user_profile.py

import json
from pathlib import Path
from typing import Optional, Any, Dict, List
from datetime import datetime

from pydantic import BaseModel

from Coddy.models.user_profile_model import UserProfileModel, Feedback
from Coddy.core.memory_service import MemoryService
from Coddy.core.logging_utility import log_info, log_warning, log_error

class UserProfile:
    """
    Manages loading, saving, and updating the user's profile using MemoryService
    for asynchronous MongoDB persistence.
    """

    def __init__(self, session_id: str, user_id: str, memory_service: Optional[MemoryService] = None):
        """
        Initializes the UserProfile with a session ID and user ID.
        If a MemoryService instance is provided, it will be used for persistence;
        otherwise, a new one is created.
        """
        self.session_id = session_id
        self.user_id = user_id
        self.memory_service = memory_service or MemoryService(session_id=session_id, user_id=user_id)
        self.profile: Optional[UserProfileModel] = None # Profile will be loaded asynchronously

    async def initialize(self):
        """
        Asynchronously loads the user profile upon initialization.
        This method should be called after creating a UserProfile instance.
        """
        self.profile = await self._load_profile()
        await log_info(f"UserProfile initialized for user: {self.user_id}")

    async def _load_profile(self) -> UserProfileModel:
        """
        Loads the user profile from the persistent store (MongoDB via MemoryService).
        If no profile is found, a new default profile is created and saved.
        """
        try:
            # Query for the user profile document using its unique type and user_id
            query = {"type": "user_profile", "user_id": self.user_id}
            # Load all memories matching the query. We expect at most one user profile.
            profiles_data: List[Dict[str, Any]] = await self.memory_service.load_memory(query=query)

            if profiles_data:
                # Assuming the most recent or first one found is the correct profile
                profile_data = profiles_data[0].get("content", {})
                await log_info(f"Loaded existing user profile for {self.user_id}.")
                return UserProfileModel(**profile_data)
            else:
                await log_info(f"No existing user profile found for {self.user_id}. Creating default.")
                return await self._create_default_profile()
        except Exception as e:
            await log_error(f"Failed to load user profile for {self.user_id}: {e}", exc_info=True)
            # Fallback to creating a default profile if loading fails
            return await self._create_default_profile()

    async def _create_default_profile(self) -> UserProfileModel:
        """
        Creates a new default profile and saves it to the persistent store.
        """
        default_profile = UserProfileModel(username=self.user_id) # Use user_id as default username
        await self.save_profile(default_profile)
        await log_info(f"Created and saved default user profile for {self.user_id}.")
        return default_profile

    async def save_profile(self, profile: Optional[UserProfileModel] = None):
        """
        Saves the current user profile (or a provided profile) to the persistent store.
        The profile is stored with a specific 'type' and 'user_id' for easy retrieval.
        """
        profile_to_save = profile or self.profile
        if not profile_to_save:
            await log_warning("Attempted to save an uninitialized profile.")
            return

        try:
            # Store the profile model as a dictionary, adding a 'type' tag for identification
            content_to_store = profile_to_save.model_dump()
            content_to_store["type"] = "user_profile" # Tag to identify this memory as a user profile
            
            # The MemoryService store_memory method already adds session_id, user_id, and timestamp
            await self.memory_service.store_memory(
                content=content_to_store,
                tags=["user_profile", self.user_id]
            )
            await log_info(f"User profile for {self.user_id} saved successfully.")
        except Exception as e:
            await log_error(f"Failed to save user profile for {self.user_id}: {e}", exc_info=True)
            raise # Re-raise to indicate a critical persistence error

    async def set(self, key: str, value: Any):
        """
        Sets a specific attribute in the user profile and saves the updated profile.
        Supports dot notation for nested fields (e.g., 'coding_style_preferences.indentation').
        """
        if not self.profile:
            await log_warning("UserProfile not initialized. Cannot set attribute.")
            return

        try:
            # Handle nested attributes using a simple traversal
            parts = key.split('.')
            current_obj = self.profile
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    if hasattr(current_obj, part):
                        setattr(current_obj, part, value)
                        await log_info(f"Set profile attribute '{key}' to '{value}'.")
                    else:
                        await log_warning(f"Profile has no attribute '{key}'. Cannot set.")
                        return # Do not raise, just log and exit
                else:
                    if hasattr(current_obj, part):
                        current_obj = getattr(current_obj, part)
                        if not isinstance(current_obj, (dict, BaseModel)):
                            await log_warning(f"Cannot set nested attribute. '{part}' is not a dictionary or Pydantic model.")
                            return
                    else:
                        await log_warning(f"Profile has no nested attribute '{part}' in path '{key}'. Cannot set.")
                        return

            await self.save_profile()
        except Exception as e:
            await log_error(f"Error setting profile attribute '{key}': {e}", exc_info=True)
            raise

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieves a specific attribute from the user profile.
        Supports dot notation for nested fields (e.g., 'coding_style_preferences.indentation').
        """
        if not self.profile:
            await log_warning("UserProfile not initialized. Cannot get attribute.")
            return default

        try:
            parts = key.split('.')
            current_obj = self.profile
            for i, part in enumerate(parts):
                if hasattr(current_obj, part):
                    current_obj = getattr(current_obj, part)
                else:
                    await log_warning(f"Profile has no attribute '{key}'. Returning default.")
                    return default
            return current_obj
        except Exception as e:
            await log_error(f"Error getting profile attribute '{key}': {e}", exc_info=True)
            return default


    async def add_feedback(self, rating: int, comment: Optional[str] = None, context_id: Optional[str] = None):
        """
        Adds a feedback entry to the profile's feedback log and saves the updated profile.
        Automatically uses the last_interaction_summary's context_id if available and not provided.
        """
        if not self.profile:
            await log_warning("UserProfile not initialized. Cannot add feedback.")
            return

        # Use context_id from last_interaction_summary if not explicitly provided
        if context_id is None and self.profile.last_interaction_summary:
            context_id = self.profile.last_interaction_summary.get("context_id")

        feedback_entry = Feedback(
            timestamp=datetime.utcnow().isoformat(),
            rating=rating,
            comment=comment,
            context_id=context_id
        )
        self.profile.feedback_log.append(feedback_entry)
        await log_info(f"Added feedback (rating: {rating}) for user {self.user_id}.")
        await self.save_profile()

    async def update_last_interaction_summary(self, summary: Dict[str, Any]):
        """
        Updates the last_interaction_summary in the user profile.
        This is crucial for providing context for subsequent feedback.
        """
        if not self.profile:
            await log_warning("UserProfile not initialized. Cannot update last interaction summary.")
            return
        self.profile.last_interaction_summary = summary
        await log_info(f"Updated last interaction summary for user {self.user_id}.")
        await self.save_profile()

    async def clear_profile(self):
        """
        Resets the user's profile to its default state and saves it.
        """
        self.profile = await self._create_default_profile()
        await log_info(f"User profile for {self.user_id} cleared to default.")

    async def close(self):
        """
        Closes the underlying MemoryService client.
        """
        await self.memory_service.close()
        await log_info("UserProfile MemoryService client closed.")


# Example usage (for testing purposes, typically called from main application flow)
async def main_test_user_profile():
    print("\n--- Testing UserProfile with MemoryService ---")
    
    test_session_id = "test_user_profile_session"
    test_user_id = "test_user_001"

    # Initialize UserProfile
    user_profile_manager = UserProfile(session_id=test_session_id, user_id=test_user_id)
    await user_profile_manager.initialize() # Call initialize to load profile

    print(f"\nInitial Profile for {test_user_id}:")
    print(user_profile_manager.profile.model_dump_json(indent=2))

    # Test setting preferences
    print("\nSetting coding style preference: indentation...")
    await user_profile_manager.set("coding_style_preferences.indentation", 4)
    await user_profile_manager.set("coding_style_preferences.tabs_or_spaces", "spaces")
    await user_profile_manager.set("preferred_languages", ["Python", "JavaScript"])

    print("\nProfile after setting preferences:")
    print(user_profile_manager.profile.model_dump_json(indent=2))

    # Test adding feedback
    print("\nAdding feedback...")
    await user_profile_manager.add_feedback(rating=5, comment="Great code generation!", context_id="gen_code_123")
    await user_profile_manager.update_last_interaction_summary({"type": "idea_synth", "content": "A new idea", "context_id": "idea_456"})
    await user_profile_manager.add_feedback(rating=4, comment="Helpful idea.", context_id="idea_456") # Context ID from last_interaction_summary

    print("\nProfile after adding feedback:")
    print(user_profile_manager.profile.model_dump_json(indent=2))

    # Test retrieving a specific preference
    indentation = await user_profile_manager.get("coding_style_preferences.indentation")
    print(f"\nRetrieved indentation preference: {indentation}")
    
    non_existent = await user_profile_manager.get("non_existent_field", "default_value")
    print(f"Retrieved non-existent field (with default): {non_existent}")

    # Simulate loading the profile again to check persistence
    print("\nSimulating re-loading profile...")
    reloaded_profile_manager = UserProfile(session_id=test_session_id, user_id=test_user_id)
    await reloaded_profile_manager.initialize()
    print("\nProfile after re-load:")
    print(reloaded_profile_manager.profile.model_dump_json(indent=2))

    # Test clearing profile
    print("\nClearing profile...")
    await user_profile_manager.clear_profile()
    print("\nProfile after clear:")
    print(user_profile_manager.profile.model_dump_json(indent=2))

    # Simulate loading after clear
    print("\nSimulating re-loading profile after clear...")
    reloaded_profile_manager_after_clear = UserProfile(session_id=test_session_id, user_id=test_user_id)
    await reloaded_profile_manager_after_clear.initialize()
    print("\nProfile after re-load (should be default):")
    print(reloaded_profile_manager_after_clear.profile.model_dump_json(indent=2))


    await user_profile_manager.close()
    await reloaded_profile_manager.close()
    await reloaded_profile_manager_after_clear.close()
    print("\n--- End of UserProfile Tests ---")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_test_user_profile())
