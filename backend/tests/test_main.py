"""Test main application"""
import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.db.database import Database

@pytest.fixture
def test_client(test_database):
    """Create a test client"""
    return TestClient(app)

def test_root(test_client):
    """Test root endpoint"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "Welcome to ImLaw API",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

def test_health_check(test_client):
    """Test health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"} 