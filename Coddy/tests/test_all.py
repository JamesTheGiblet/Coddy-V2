# Coddy/tests/test_all.py
import pytest
import os
import sys
import traceback # Import the traceback module

# Add the 'Coddy' root directory to the Python path
# This allows imports like 'from core.my_module import ...' to work during testing
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def run_all_tests():
    """
    Discovers and runs all tests in the 'tests' directory using pytest.
    Returns the pytest exit code.
    Implements robust error handling for graceful crash recovery with traceback logging.
    """
    print("\n🚀 Running all Coddy tests...")
    exit_code = 1 # Default to a non-zero exit code (failure)

    try:
        # Run pytest, capturing output.
        # The current directory '.' ensures pytest searches for tests from the current directory (Coddy/tests)
        exit_code = pytest.main([os.path.dirname(__file__)])
        
        if exit_code == 0:
            print("\n✅ All Coddy tests passed successfully!")
        else:
            print(f"\n❌ Some Coddy tests failed. Pytest exit code: {exit_code}")
    except pytest.ExitGroup as e:
        # pytest.ExitGroup is raised when pytest exits, possibly with errors.
        # The exit code is usually available in e.code
        exit_code = e.returncode if hasattr(e, 'returncode') else 1
        print(f"\n❌ pytest encountered an issue during execution (ExitGroup). Exit code: {exit_code}")
        print("Detailed traceback (if available):")
        traceback.print_exc() # Print full traceback
    except Exception as e:
        # Catch any other unexpected exceptions during the test run
        print(f"\n❌ An unexpected error occurred while running tests: {e}")
        print("Detailed traceback:")
        traceback.print_exc() # Print full traceback
        exit_code = 1 # Ensure a failure exit code

    return exit_code

if __name__ == "__main__":
    # Ensure pytest is installed
    try:
        import pytest
    except ImportError:
        print("pytest is not installed. Please install it using: pip install pytest")
        sys.exit(1)

    # Run the tests
    # Added a try-except block here for the top-level execution as well
    try:
        exit_code = run_all_tests()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\nFATAL ERROR: An unhandled exception occurred during test execution: {e}")
        traceback.print_exc()
        sys.exit(1) # Exit with an error code
