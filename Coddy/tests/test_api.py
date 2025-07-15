# C:\Users\gilbe\Documents\GitHub\Coddy_V2\Coddy\tests\test_api.py

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

# The 'app' object from your FastAPI application
from backend.main import app

client = TestClient(app)

def test_read_root():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Coddy API is running. Visit /docs for API documentation."}

def test_get_roadmap_success():
    """Test the /api/roadmap endpoint for a successful response."""
    # We can mock the RoadmapManager to avoid actual file I/O
    with patch('api.main.roadmap_manager.get_roadmap_content', return_value="# Roadmap Title") as mock_get_content:
        response = client.get("/api/roadmap")
        assert response.status_code == 200
        assert response.json() == {"content": "# Roadmap Title"}
        mock_get_content.assert_called_once()

def test_get_roadmap_not_found():
    """Test the /api/roadmap endpoint when the file is not found."""
    with patch('api.main.roadmap_manager.get_roadmap_content', side_effect=FileNotFoundError("File not found")) as mock_get_content:
        response = client.get("/api/roadmap")
        assert response.status_code == 404
        assert response.json() == {"detail": "File not found"}
        mock_get_content.assert_called_once()

def test_list_files_success():
    """Test the /api/files/list endpoint for a successful response."""
    with patch('api.main.list_files', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = ["file1.txt", "dir1/"]
        response = client.get("/api/files/list", params={"path": "some/dir"})
        assert response.status_code == 200
        assert response.json() == {"items": ["file1.txt", "dir1/"]}
        mock_list.assert_awaited_once_with("some/dir")

def test_list_files_not_found():
    """Test the /api/files/list endpoint when the directory is not found."""
    with patch('api.main.list_files', new_callable=AsyncMock) as mock_list:
        mock_list.side_effect = FileNotFoundError("Dir not found")
        response = client.get("/api/files/list", params={"path": "nonexistent/dir"})
        assert response.status_code == 404
        assert response.json() == {"detail": "Directory not found: nonexistent/dir"}

def test_list_files_invalid_path():
    """Test the /api/files/list endpoint with an invalid path."""
    with patch('api.main.list_files', new_callable=AsyncMock) as mock_list:
        mock_list.side_effect = ValueError("Path is outside the project root")
        response = client.get("/api/files/list", params={"path": "../etc/passwd"})
        assert response.status_code == 400
        assert response.json() == {"detail": "Path is outside the project root"}

def test_read_file_success():
    """Test the /api/files/read endpoint for a successful response."""
    with patch('api.main.read_file', new_callable=AsyncMock) as mock_read:
        mock_read.return_value = "file content"
        response = client.get("/api/files/read", params={"path": "file.txt"})
        assert response.status_code == 200
        assert response.json() == {"content": "file content"}
        mock_read.assert_awaited_once_with("file.txt")

def test_read_file_not_found():
    """Test the /api/files/read endpoint when the file is not found."""
    with patch('api.main.read_file', new_callable=AsyncMock) as mock_read:
        mock_read.side_effect = FileNotFoundError("File not found")
        response = client.get("/api/files/read", params={"path": "nonexistent.txt"})
        assert response.status_code == 404
        assert response.json() == {"detail": "File not found: nonexistent.txt"}

def test_write_file_success():
    """Test the /api/files/write endpoint for a successful response."""
    with patch('api.main.write_file', new_callable=AsyncMock) as mock_write:
        request_body = {"path": "new_file.txt", "content": "new content"}
        response = client.post("/api/files/write", json=request_body)
        assert response.status_code == 200
        assert response.json() == {"message": "Successfully wrote to new_file.txt"}
        mock_write.assert_awaited_once_with("new_file.txt", "new content")