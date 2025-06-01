from typing import Optional, Any
import json
from redis import Redis
from datetime import timedelta
import logging

class CacheService:
    """Service for caching frequently accessed data using Redis"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.logger = logging.getLogger(__name__)
        
        # Default cache expiration times
        self.FORM_METADATA_TTL = timedelta(hours=1)
        self.FORM_LIST_TTL = timedelta(minutes=5)
        self.FIELD_DEFS_TTL = timedelta(hours=2)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        try:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            self.logger.warning(f"Cache get failed for key {key}: {str(e)}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> bool:
        """Set a value in cache with optional TTL"""
        try:
            serialized = json.dumps(value)
            return self.redis.set(
                key,
                serialized,
                ex=int(ttl.total_seconds()) if ttl else None
            )
        except Exception as e:
            self.logger.warning(f"Cache set failed for key {key}: {str(e)}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete a value from cache"""
        try:
            return bool(self.redis.delete(key))
        except Exception as e:
            self.logger.warning(f"Cache delete failed for key {key}: {str(e)}")
            return False
    
    async def clear_form_cache(self, form_id: str) -> None:
        """Clear all cached data related to a specific form"""
        try:
            keys = [
                f"form:metadata:{form_id}",
                f"form:fields:{form_id}",
                "form:list"  # Clear the forms list cache as well
            ]
            self.redis.delete(*keys)
        except Exception as e:
            self.logger.warning(f"Failed to clear form cache for {form_id}: {str(e)}")
    
    def generate_key(self, prefix: str, *parts: str) -> str:
        """Generate a cache key from parts"""
        return ":".join([prefix, *parts]) 