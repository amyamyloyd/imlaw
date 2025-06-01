from fastapi import Request, HTTPException
from redis import Redis
import time
from datetime import timedelta
import logging
from typing import Optional

class RateLimiter:
    """Rate limiting middleware using Redis"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        default_limit: int = 100,
        default_window: int = 3600  # 1 hour in seconds
    ):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.default_limit = default_limit
        self.default_window = default_window
        self.logger = logging.getLogger(__name__)
        
        # Endpoint-specific rate limits
        self.endpoint_limits = {
            "extract_metadata": (20, 3600),  # 20 requests per hour
            "list_forms": (1000, 3600),      # 1000 requests per hour
            "get_form_metadata": (500, 3600), # 500 requests per hour
            "get_form_fields": (500, 3600)    # 500 requests per hour
        }
    
    async def check_rate_limit(
        self,
        request: Request,
        endpoint: Optional[str] = None
    ) -> None:
        """Check if request is within rate limits"""
        try:
            # Get client identifier (IP address or API key)
            client_id = self._get_client_id(request)
            
            # Get endpoint-specific limits or defaults
            limit, window = self.endpoint_limits.get(
                endpoint,
                (self.default_limit, self.default_window)
            )
            
            # Generate Redis key
            key = f"ratelimit:{client_id}:{endpoint or 'default'}"
            
            # Get current count and timestamp
            current_time = int(time.time())
            window_start = current_time - window
            
            # Clean old requests
            self.redis.zremrangebyscore(key, 0, window_start)
            
            # Count requests in current window
            request_count = self.redis.zcard(key)
            
            if request_count >= limit:
                raise HTTPException(
                    status_code=429,
                    detail="Too many requests. Please try again later."
                )
            
            # Add current request
            self.redis.zadd(key, {str(current_time): current_time})
            
            # Set expiration on the key
            self.redis.expire(key, window)
            
            # Add rate limit headers
            remaining = limit - request_count - 1
            reset_time = current_time + window
            
            request.state.rate_limit_remaining = remaining
            request.state.rate_limit_reset = reset_time
            
        except HTTPException:
            raise
        except Exception as e:
            self.logger.error(f"Rate limiting failed: {str(e)}")
            # Allow request on rate limiting failure
            return None
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request"""
        # Try to get API key from header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key}"
        
        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        return request.client.host
    
    async def add_rate_limit_headers(self, request: Request, response: Response):
        """Add rate limit headers to response"""
        if hasattr(request.state, "rate_limit_remaining"):
            response.headers["X-RateLimit-Remaining"] = str(
                request.state.rate_limit_remaining
            )
        if hasattr(request.state, "rate_limit_reset"):
            response.headers["X-RateLimit-Reset"] = str(
                request.state.rate_limit_reset
            ) 