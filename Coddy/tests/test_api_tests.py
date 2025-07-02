# tests/api_tests.py
import httpx
import pytest

API_BASE_URL = "http://127.0.0.1:8000" # Ensure your FastAPI server is running

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

# ... similar tests for list, write, and other error scenarios