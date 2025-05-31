from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_root():
    """Test the health check endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "imlaw-api"} 