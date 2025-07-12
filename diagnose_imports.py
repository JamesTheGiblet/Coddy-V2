# C:\Users\gilbe\Documents\GitHub\Coddy_V2\diagnose_imports.py

import os
import sys

print("--- Diagnostics Start ---")
print(f"Current Working Directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")
print("-" * 30)

try:
    print("Attempting to import Coddy.core.logging_utility...")
    from Coddy.core.logging_utility import log_debug, log_error, log_info
    print("SUCCESS: Successfully imported Coddy.core.logging_utility!")
    # Try calling a function to ensure it's fully loaded
    async def run_log_test():
        await log_info("Test log from diagnose_imports.py")
    import asyncio
    asyncio.run(run_log_test())
    print("SUCCESS: Test logging function executed.")

except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
    print("This indicates Python still cannot find 'logging_utility' within the 'Coddy.core' package.")
except Exception as e:
    print(f"FAILURE: An unexpected error occurred during logging_utility import: {e}")

print("-" * 30)

try:
    print("Attempting to import Coddy.backend.main...")
    import Coddy.backend.main
    print("SUCCESS: Successfully imported Coddy.backend.main!")
except ImportError as e:
    print(f"FAILURE: ImportError: {e}")
    print("This indicates a problem with the overall 'Coddy.backend.main' package or its dependencies.")
except Exception as e:
    print(f"FAILURE: An unexpected error occurred during Coddy.backend.main import: {e}")

print("--- Diagnostics End ---")