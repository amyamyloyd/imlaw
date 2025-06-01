import pytest
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from middleware.rate_limiter import RateLimiter
import time
import asyncio

@pytest.fixture
def rate_limiter():
    """Create a RateLimiter instance for testing"""
    limiter = RateLimiter(
        redis_url="redis://localhost:6379",
        default_limit=5,
        default_window=10  # 10 seconds for testing
    )
    # Clear Redis after each test
    yield limiter
    limiter.redis.flushdb()

@pytest.fixture
def test_app(rate_limiter):
    """Create a test FastAPI app with rate limiting"""
    app = FastAPI()
    
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        await rate_limiter.check_rate_limit(request)
        response = await call_next(request)
        await rate_limiter.add_rate_limit_headers(request, response)
        return response
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/test-custom-limit")
    async def test_custom_endpoint():
        return {"message": "success"}
    
    return app

@pytest.fixture
def client(test_app):
    """Create a test client"""
    return TestClient(test_app)

def test_basic_rate_limiting(client):
    """Test basic rate limiting functionality"""
    # Make requests up to the limit
    for _ in range(5):
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-RateLimit-Remaining" in response.headers
    
    # Next request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert "Too many requests" in response.json()["detail"]

def test_rate_limit_window(client):
    """Test rate limit window expiration"""
    # Make requests up to the limit
    for _ in range(5):
        response = client.get("/test")
        assert response.status_code == 200
    
    # Wait for window to expire
    time.sleep(10)
    
    # Should be able to make requests again
    response = client.get("/test")
    assert response.status_code == 200

def test_different_clients(client):
    """Test rate limiting for different clients"""
    # Make requests from first client
    for _ in range(5):
        response = client.get(
            "/test",
            headers={"X-API-Key": "client1"}
        )
        assert response.status_code == 200
    
    # First client should be rate limited
    response = client.get(
        "/test",
        headers={"X-API-Key": "client1"}
    )
    assert response.status_code == 429
    
    # Second client should still be able to make requests
    response = client.get(
        "/test",
        headers={"X-API-Key": "client2"}
    )
    assert response.status_code == 200

def test_endpoint_specific_limits(client, rate_limiter):
    """Test endpoint-specific rate limits"""
    # Override limit for specific endpoint
    rate_limiter.endpoint_limits["test-custom-limit"] = (2, 10)  # 2 requests per 10 seconds
    
    # Make requests up to custom limit
    for _ in range(2):
        response = client.get("/test-custom-limit")
        assert response.status_code == 200
    
    # Next request should be rate limited
    response = client.get("/test-custom-limit")
    assert response.status_code == 429

def test_rate_limit_headers(client):
    """Test rate limit headers"""
    response = client.get("/test")
    assert response.status_code == 200
    
    # Check headers
    headers = response.headers
    assert "X-RateLimit-Remaining" in headers
    assert "X-RateLimit-Reset" in headers
    
    # Verify remaining count decrements
    remaining = int(headers["X-RateLimit-Remaining"])
    next_response = client.get("/test")
    next_remaining = int(next_response.headers["X-RateLimit-Remaining"])
    assert next_remaining == remaining - 1

def test_forwarded_ip(client):
    """Test rate limiting with X-Forwarded-For header"""
    # Make requests with forwarded IP
    for _ in range(5):
        response = client.get(
            "/test",
            headers={"X-Forwarded-For": "10.0.0.1"}
        )
        assert response.status_code == 200
    
    # Should be rate limited
    response = client.get(
        "/test",
        headers={"X-Forwarded-For": "10.0.0.1"}
    )
    assert response.status_code == 429
    
    # Different forwarded IP should work
    response = client.get(
        "/test",
        headers={"X-Forwarded-For": "10.0.0.2"}
    )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_redis_failure_handling(rate_limiter):
    """Test handling of Redis connection failures"""
    # Create a request with invalid Redis connection
    rate_limiter.redis = None
    
    # Create a mock request
    request = Request(scope={
        'type': 'http',
        'method': 'GET',
        'path': '/test',
        'headers': [],
        'client': ('127.0.0.1', 1234)
    })
    
    # Should not raise an exception
    await rate_limiter.check_rate_limit(request)
    
    # Request should be allowed
    assert not hasattr(request.state, 'rate_limit_remaining') 