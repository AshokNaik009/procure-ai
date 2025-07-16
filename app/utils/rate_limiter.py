import time
import asyncio
from typing import Dict, Optional
from collections import defaultdict, deque
from functools import wraps
import logging
from fastapi import HTTPException, Request
from app.config import settings

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed based on rate limiting
        """
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        request_times = self.requests[key]
        while request_times and request_times[0] < window_start:
            request_times.popleft()
        
        # Check if limit exceeded
        if len(request_times) >= self.max_requests:
            return False
        
        # Add current request
        request_times.append(now)
        return True
    
    def get_reset_time(self, key: str) -> Optional[float]:
        """
        Get time until rate limit resets
        """
        if key not in self.requests or not self.requests[key]:
            return None
        
        oldest_request = self.requests[key][0]
        reset_time = oldest_request + self.window_seconds
        return max(0, reset_time - time.time())

# Global rate limiter instance
rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60
)

def rate_limit(max_requests: int = None, window_seconds: int = 60):
    """
    Decorator for rate limiting endpoints
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                # If no request object found, proceed without rate limiting
                return await func(*args, **kwargs)
            
            # Create rate limiter for this endpoint
            limiter = RateLimiter(
                max_requests=max_requests or settings.rate_limit_per_minute,
                window_seconds=window_seconds
            )
            
            # Use IP address as key
            client_ip = request.client.host if request.client else "unknown"
            key = f"{client_ip}:{request.url.path}"
            
            if not limiter.is_allowed(key):
                reset_time = limiter.get_reset_time(key)
                logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
                
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "retry_after": reset_time,
                        "limit": max_requests or settings.rate_limit_per_minute,
                        "window": window_seconds
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

class TokenBucket:
    """
    Token bucket implementation for API rate limiting
    """
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> bool:
        """
        Consume tokens from bucket
        """
        async with self.lock:
            now = time.time()
            
            # Add tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            # Check if enough tokens available
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    async def get_wait_time(self, tokens: int = 1) -> float:
        """
        Get time to wait until tokens are available
        """
        async with self.lock:
            if self.tokens >= tokens:
                return 0.0
            
            needed_tokens = tokens - self.tokens
            return needed_tokens / self.refill_rate

class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts limits based on load
    """
    def __init__(self, base_limit: int = 10, max_limit: int = 100):
        self.base_limit = base_limit
        self.max_limit = max_limit
        self.current_limit = base_limit
        self.success_count = 0
        self.error_count = 0
        self.last_adjustment = time.time()
        self.adjustment_interval = 60  # Adjust every minute
    
    def adjust_limit(self):
        """
        Adjust rate limit based on success/error ratio
        """
        now = time.time()
        if now - self.last_adjustment < self.adjustment_interval:
            return
        
        total_requests = self.success_count + self.error_count
        if total_requests == 0:
            return
        
        error_rate = self.error_count / total_requests
        
        # Decrease limit if error rate is high
        if error_rate > 0.1:  # More than 10% errors
            self.current_limit = max(self.base_limit, self.current_limit * 0.8)
        # Increase limit if error rate is low
        elif error_rate < 0.05:  # Less than 5% errors
            self.current_limit = min(self.max_limit, self.current_limit * 1.2)
        
        # Reset counters
        self.success_count = 0
        self.error_count = 0
        self.last_adjustment = now
        
        logger.info(f"Adjusted rate limit to {self.current_limit}")
    
    def record_success(self):
        """Record successful request"""
        self.success_count += 1
        self.adjust_limit()
    
    def record_error(self):
        """Record failed request"""
        self.error_count += 1
        self.adjust_limit()

# Global adaptive rate limiter
adaptive_limiter = AdaptiveRateLimiter()

def get_client_identifier(request: Request) -> str:
    """
    Get unique identifier for client (IP + User-Agent)
    """
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")
    return f"{client_ip}:{hash(user_agent)}"

async def check_rate_limit(request: Request, endpoint: str) -> bool:
    """
    Check if request should be rate limited
    """
    client_id = get_client_identifier(request)
    key = f"{client_id}:{endpoint}"
    
    return rate_limiter.is_allowed(key)

class RateLimitMiddleware:
    """
    Middleware for global rate limiting
    """
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            await self.app(scope, receive, send)
            return
        
        # Check rate limit
        if not await check_rate_limit(request, request.url.path):
            response = {
                "type": "http.response.start",
                "status": 429,
                "headers": [[b"content-type", b"application/json"]],
            }
            await send(response)
            
            body = {
                "type": "http.response.body",
                "body": b'{"error": "Rate limit exceeded", "status": 429}',
            }
            await send(body)
            return
        
        await self.app(scope, receive, send)