"""
Revolution X - Rate Limiting Middleware
Advanced rate limiting with Redis backend
"""
import time
from typing import Optional, Callable
from functools import wraps
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import redis

from app.core.config import settings
from app.core.logging import logger


class RateLimiter:
    """Advanced rate limiter with sliding window."""
    
    def __init__(self):
        self.redis_client = None
        self._local_cache = {}
    
    def connect(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=1,  # Separate DB for rate limiting
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
        except Exception as e:
            logger.error(f"Redis connection failed for rate limiting: {e}")
    
    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate rate limit key."""
        return f"rate_limit:{identifier}:{endpoint}"
    
    def _get_identifier(self, request: Request) -> str:
        """Get client identifier (IP or user ID)."""
        # Check for forwarded IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fall back to direct IP
        return request.client.host
    
    def is_allowed(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window: int
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed.
        Returns (allowed, headers).
        """
        key = self._get_key(identifier, endpoint)
        now = time.time()
        window_start = now - window
        
        try:
            if self.redis_client:
                # Use Redis sorted set for sliding window
                pipe = self.redis_client.pipeline()
                
                # Remove old entries
                pipe.zremrangebyscore(key, 0, window_start)
                
                # Count current entries
                pipe.zcard(key)
                
                # Add current request
                pipe.zadd(key, {str(now): now})
                
                # Set expiry
                pipe.expire(key, window)
                
                results = pipe.execute()
                current_count = results[1]
                
            else:
                # Fallback to local cache
                if key not in self._local_cache:
                    self._local_cache[key] = []
                
                # Clean old entries
                self._local_cache[key] = [
                    ts for ts in self._local_cache[key]
                    if ts > window_start
                ]
                
                current_count = len(self._local_cache[key])
                self._local_cache[key].append(now)
            
            allowed = current_count < max_requests
            remaining = max(0, max_requests - current_count - 1)
            reset_time = int(now + window)
            
            headers = {
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(reset_time),
                "X-RateLimit-Window": str(window)
            }
            
            return allowed, headers
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open in case of error
            return True, {}
    
    def limit(
        self,
        requests: int = 100,
        window: int = 60,
        key_func: Optional[Callable] = None
    ):
        """Decorator for rate limiting."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(request: Request, *args, **kwargs):
                identifier = key_func(request) if key_func else self._get_identifier(request)
                allowed, headers = self.is_allowed(identifier, func.__name__, requests, window)
                
                if not allowed:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded",
                        headers={
                            **headers,
                            "Retry-After": str(window)
                        }
                    )
                
                response = await func(request, *args, **kwargs)
                
                # Add rate limit headers to response
                if hasattr(response, 'headers'):
                    response.headers.update(headers)
                
                return response
            
            return async_wrapper
        return decorator


# Specific rate limit configurations
RATE_LIMITS = {
    # Authentication endpoints - strict
    "auth_login": {"requests": 5, "window": 300},      # 5 per 5 minutes
    "auth_register": {"requests": 3, "window": 3600},   # 3 per hour
    "auth_refresh": {"requests": 10, "window": 60},     # 10 per minute
    
    # Trading endpoints - moderate
    "place_trade": {"requests": 30, "window": 60},      # 30 per minute
    "modify_trade": {"requests": 60, "window": 60},     # 60 per minute
    
    # API endpoints - generous
    "market_data": {"requests": 1000, "window": 60},    # 1000 per minute
    "ai_predict": {"requests": 100, "window": 60},      # 100 per minute
    
    # WebSocket connections
    "ws_connect": {"requests": 10, "window": 60},       # 10 per minute
}


class RateLimitMiddleware:
    """FastAPI middleware for rate limiting."""
    
    def __init__(self, app):
        self.app = app
        self.limiter = RateLimiter()
        self.limiter.connect()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive)
        
        # Determine rate limit based on path
        path = request.url.path
        
        if "/auth/login" in path:
            config = RATE_LIMITS["auth_login"]
        elif "/auth/register" in path:
            config = RATE_LIMITS["auth_register"]
        elif "/trading/trades" in path and request.method == "POST":
            config = RATE_LIMITS["place_trade"]
        elif "/ai/predict" in path:
            config = RATE_LIMITS["ai_predict"]
        else:
            await self.app(scope, receive, send)
            return
        
        identifier = self.limiter._get_identifier(request)
        allowed, headers = self.limiter.is_allowed(
            identifier,
            path,
            config["requests"],
            config["window"]
        )
        
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"},
                headers=headers
            )
            await response(scope, receive, send)
            return
        
        # Add headers to response
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = message.get("headers", [])
                for name, value in headers.items():
                    headers.append([name.encode(), value.encode()])
                message["headers"] = headers
            await send(message)
        
        await self.app(scope, receive, send_with_headers)


# Brute force protection
class BruteForceProtection:
    """Protection against brute force attacks."""
    
    def __init__(self):
        self.failed_attempts = {}
        self.blocked_ips = {}
    
    def record_failure(self, identifier: str):
        """Record failed login attempt."""
        now = time.time()
        
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []
        
        self.failed_attempts[identifier].append(now)
        
        # Clean old attempts (older than 1 hour)
        self.failed_attempts[identifier] = [
            ts for ts in self.failed_attempts[identifier]
            if now - ts < 3600
        ]
        
        # Check if should block
        if len(self.failed_attempts[identifier]) >= 5:
            self.blocked_ips[identifier] = now + 3600  # Block for 1 hour
            logger.warning(f"🚫 Brute force protection: Blocked {identifier}")
    
    def record_success(self, identifier: str):
        """Clear failed attempts on success."""
        self.failed_attempts.pop(identifier, None)
    
    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is blocked."""
        if identifier in self.blocked_ips:
            if time.time() < self.blocked_ips[identifier]:
                return True
            else:
                del self.blocked_ips[identifier]
        return False
    
    def get_block_time_remaining(self, identifier: str) -> int:
        """Get remaining block time in seconds."""
        if identifier in self.blocked_ips:
            remaining = int(self.blocked_ips[identifier] - time.time())
            return max(0, remaining)
        return 0


brute_force_protection = BruteForceProtection()
