import asyncio
import json
import hashlib
import logging
from typing import Any, Optional, Dict, Callable
from functools import wraps
from datetime import datetime, timedelta
import time
from app.config import settings

logger = logging.getLogger(__name__)

class InMemoryCache:
    """
    Simple in-memory cache with TTL support
    """
    def __init__(self):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        """
        async with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if entry['expires'] > time.time():
                    return entry['value']
                else:
                    # Remove expired entry
                    del self.cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set value in cache with TTL
        """
        async with self.lock:
            self.cache[key] = {
                'value': value,
                'expires': time.time() + ttl,
                'created': time.time()
            }
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from cache
        """
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """
        Clear all cache entries
        """
        async with self.lock:
            self.cache.clear()
    
    async def cleanup_expired(self) -> None:
        """
        Remove expired entries
        """
        async with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry['expires'] <= current_time
            ]
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        """
        return {
            'total_entries': len(self.cache),
            'memory_usage': self._estimate_memory_usage(),
            'oldest_entry': self._get_oldest_entry_age(),
            'newest_entry': self._get_newest_entry_age()
        }
    
    def _estimate_memory_usage(self) -> int:
        """
        Estimate memory usage of cache
        """
        try:
            return len(json.dumps(self.cache).encode('utf-8'))
        except:
            return 0
    
    def _get_oldest_entry_age(self) -> Optional[float]:
        """
        Get age of oldest entry in seconds
        """
        if not self.cache:
            return None
        
        oldest_created = min(entry['created'] for entry in self.cache.values())
        return time.time() - oldest_created
    
    def _get_newest_entry_age(self) -> Optional[float]:
        """
        Get age of newest entry in seconds
        """
        if not self.cache:
            return None
        
        newest_created = max(entry['created'] for entry in self.cache.values())
        return time.time() - newest_created

class RedisCache:
    """
    Redis-based cache (placeholder - would need redis client)
    """
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self.redis_client = None
        # Note: In production, you'd initialize Redis client here
        logger.warning("Redis cache not implemented - using in-memory cache")
        self.fallback_cache = InMemoryCache()
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from Redis cache
        """
        try:
            # In production, implement Redis get
            return await self.fallback_cache.get(key)
        except Exception as e:
            logger.error(f"Redis cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """
        Set value in Redis cache
        """
        try:
            # In production, implement Redis set
            await self.fallback_cache.set(key, value, ttl)
        except Exception as e:
            logger.error(f"Redis cache set error: {e}")
    
    async def delete(self, key: str) -> bool:
        """
        Delete value from Redis cache
        """
        try:
            # In production, implement Redis delete
            return await self.fallback_cache.delete(key)
        except Exception as e:
            logger.error(f"Redis cache delete error: {e}")
            return False

# Global cache instance
cache = InMemoryCache()

def generate_cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from function arguments
    """
    key_data = {
        'args': args,
        'kwargs': kwargs
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()

def cached(ttl: int = None, key_prefix: str = ""):
    """
    Decorator for caching function results
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_result
            
            # Execute function
            logger.debug(f"Cache miss for {func.__name__}")
            result = await func(*args, **kwargs)
            
            # Cache result
            cache_ttl = ttl or settings.cache_ttl_seconds
            await cache.set(cache_key, result, cache_ttl)
            
            return result
        
        return wrapper
    return decorator

class CacheManager:
    """
    Cache manager with different caching strategies
    """
    def __init__(self):
        self.cache = cache
        self.hit_count = 0
        self.miss_count = 0
        self.error_count = 0
    
    async def get_or_set(self, key: str, func: Callable, ttl: int = None) -> Any:
        """
        Get value from cache or set it using provided function
        """
        try:
            # Try cache first
            result = await self.cache.get(key)
            if result is not None:
                self.hit_count += 1
                return result
            
            # Execute function
            self.miss_count += 1
            result = await func()
            
            # Cache result
            cache_ttl = ttl or settings.cache_ttl_seconds
            await self.cache.set(key, result, cache_ttl)
            
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Cache operation error: {e}")
            # Return function result without caching
            return await func()
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern
        """
        # This is a simplified implementation
        # In production, use Redis pattern matching
        count = 0
        for key in list(self.cache.cache.keys()):
            if pattern in key:
                await self.cache.delete(key)
                count += 1
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        """
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'error_count': self.error_count,
            'hit_rate': hit_rate,
            'cache_stats': self.cache.get_stats()
        }
    
    def reset_stats(self) -> None:
        """
        Reset cache statistics
        """
        self.hit_count = 0
        self.miss_count = 0
        self.error_count = 0

# Global cache manager
cache_manager = CacheManager()

class CacheWarmup:
    """
    Cache warmup utility
    """
    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self.warmup_tasks = []
    
    def add_warmup_task(self, key: str, func: Callable, ttl: int = None):
        """
        Add warmup task
        """
        self.warmup_tasks.append({
            'key': key,
            'func': func,
            'ttl': ttl
        })
    
    async def run_warmup(self):
        """
        Run all warmup tasks
        """
        logger.info(f"Starting cache warmup with {len(self.warmup_tasks)} tasks")
        
        for task in self.warmup_tasks:
            try:
                await self.cache_manager.get_or_set(
                    task['key'],
                    task['func'],
                    task['ttl']
                )
                logger.debug(f"Warmed up cache for {task['key']}")
            except Exception as e:
                logger.error(f"Cache warmup failed for {task['key']}: {e}")
        
        logger.info("Cache warmup completed")

# Background task for cache cleanup
async def cache_cleanup_task():
    """
    Background task to clean up expired cache entries
    """
    while True:
        try:
            await cache.cleanup_expired()
            await asyncio.sleep(300)  # Clean every 5 minutes
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            await asyncio.sleep(60)  # Retry after 1 minute

# Cache decorators for specific use cases
def cache_search_results(ttl: int = 1800):  # 30 minutes
    """
    Cache search results
    """
    return cached(ttl=ttl, key_prefix="search")

def cache_supplier_data(ttl: int = 3600):  # 1 hour
    """
    Cache supplier data
    """
    return cached(ttl=ttl, key_prefix="supplier")

def cache_market_data(ttl: int = 7200):  # 2 hours
    """
    Cache market intelligence data
    """
    return cached(ttl=ttl, key_prefix="market")

def cache_llm_responses(ttl: int = 86400):  # 24 hours
    """
    Cache LLM responses
    """
    return cached(ttl=ttl, key_prefix="llm")