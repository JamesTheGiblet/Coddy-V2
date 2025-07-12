# test_import.py
import sys
import os

print(f"Current Working Directory: {os.getcwd()}")
print(f"sys.path: {sys.path}")

try:
    from Coddy.logging_utility import log_debug, log_error, log_info
    print("Successfully imported logging_utility!")
except ImportError as e:
    print(f"ImportError encountered: {e}")
    print("This means Python still can't find the module.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("\nAttempting to import backend.main directly:")
try:
    import Coddy.backend.main
    print("Successfully imported Coddy.backend.main!")
except ImportError as e:
    print(f"ImportError on Coddy.backend.main: {e}")
    print("This indicates a problem with the overall package structure recognition.")
except Exception as e:
    print(f"An unexpected error occurred importing Coddy.backend.main: {e}")