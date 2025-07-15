# tests/api_tests.py
import httpx
import pytest
import os # NEW: Import os for file operations in tests

# NEW: Import API_BASE_URL from the centralized config
from Coddy.core.config import API_BASE_URL

# API_BASE_URL = "http://127.0.0.1:8000" # REMOVED: No longer hardcoded here

# Define a temporary directory for file operation tests
TEST_FILES_DIR = "test_api_files"

@pytest.fixture(scope="module", autouse=True)
def setup_test_files_dir():
    """Fixture to create and clean up a temporary directory for file tests."""
    if not os.path.exists(TEST_FILES_DIR):
        os.makedirs(TEST_FILES_DIR)
    yield
    # Clean up after all tests in the module
    if os.path.exists(TEST_FILES_DIR):
        import shutil
        shutil.rmtree(TEST_FILES_DIR)

@pytest.mark.asyncio
async def test_get_roadmap_success():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/roadmap")
        assert response.status_code == 200
        assert "content" in response.json()
        assert isinstance(response.json()["content"], str)

@pytest.mark.asyncio
async def test_read_file_not_found():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/files/read", params={"path": "non_existent_file_12345.txt"})
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "File not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_files_success():
    """Test successful listing of files in a directory."""
    # Create a dummy file in the test directory
    dummy_file_path = os.path.join(TEST_FILES_DIR, "dummy.txt")
    with open(dummy_file_path, "w") as f:
        f.write("test content")

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/files/list", params={"path": TEST_FILES_DIR})
        assert response.status_code == 200
        assert "items" in response.json()
        assert "dummy.txt" in response.json()["items"]

@pytest.mark.asyncio
async def test_list_files_not_found():
    """Test listing a non-existent directory."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/api/files/list", params={"path": "non_existent_dir_12345"})
        assert response.status_code == 404
        assert "detail" in response.json()
        assert "Directory not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_write_file_success():
    """Test successful writing to a file."""
    test_file = os.path.join(TEST_FILES_DIR, "write_test.txt")
    content_to_write = "Hello from test!"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/files/write",
            json={"path": test_file, "content": content_to_write}
        )
        assert response.status_code == 200
        assert "message" in response.json()
        assert f"Successfully wrote to {test_file}" in response.json()["message"]
    
    # Verify content was written
    with open(test_file, "r") as f:
        assert f.read() == content_to_write

@pytest.mark.asyncio
async def test_write_file_invalid_path():
    """Test writing to an invalid path (e.g., outside project root)."""
    invalid_path = "../../../evil.txt" # Attempt to write outside project
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/files/write",
            json={"path": invalid_path, "content": "malicious content"}
        )
        assert response.status_code == 400
        assert "detail" in response.json()
        assert "Path is outside the project root" in response.json()["detail"]

@pytest.mark.asyncio
async def test_store_memory_success():
    """Test successful storage of a memory fragment."""
    memory_data = {
        "content": {"type": "test_event", "data": "test_data"},
        "tags": ["test", "memory"],
        "session_id": "test_session_123",
        "user_id": "test_user_456"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/memory/store",
            json=memory_data
        )
        assert response.status_code == 200 # FastAPI returns 200 for success, not 201 by default for this endpoint
        assert "message" in response.json()
        assert "Memory stored successfully." == response.json()["message"]

@pytest.mark.asyncio
async def test_store_memory_missing_content():
    """Test storing memory with missing content."""
    invalid_memory_data = {
        "tags": ["test", "invalid"],
        "session_id": "test_session_123",
        "user_id": "test_user_456"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/memory/store",
            json=invalid_memory_data
        )
        assert response.status_code == 422 # Pydantic validation error
        assert "detail" in response.json()
        # The error message from Pydantic will be more detailed, check for a key part
        assert "field required" in str(response.json()["detail"]).lower()