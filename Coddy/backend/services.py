# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\backend\services.py

"""
Global service registry for the Coddy backend.

This module provides a centralized dictionary `services` to hold instances of
core services, making them accessible across different parts of the application
without causing circular imports.
"""
from typing import Dict, Any

services: Dict[str, Any] = {}