"""
Revolution X - Caching System
Redis-based caching with fallback to in-memory
"""
import json
import pickle
import hashlib
from typing import Any, Optional, Union, Callable
from functools import wraps
from datetime import timedelta
import asyncio

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings
from app.core.logging import logger


class CacheManager:
    """Advanced caching manager with Redis and local fallback."""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.local_cache: dict = {}
        self.local_ttl: dict = {}
        self._lock = asyncio.Lock()
        self._connected = False
    
    async def connect(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            await self.redis_client.ping()
            self._connected = True
            logger.info("✅ Redis cache connected")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable, using in-memory cache: {e}")
            self._connected = False
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        try:
            if self._connected:
                data = await self.redis_client.get(key)
                if data:
                    return pickle.loads(data)
            
            # Fallback to local cache
            async with self._lock:
                if key in self.local_cache:
                    if asyncio.get_event_loop().time() < self.local_ttl.get(key, 0):
                        return self.local_cache[key]
                    else:
                        del self.local_cache[key]
                        del self.local_ttl[key]
            
            return default
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return default
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False
    ) -> bool:
        """Set value in cache."""
        try:
            serialized = pickle.dumps(value)
            
            if self._connected:
                if nx:
                    return await self.redis_client.setnx(key, serialized)
                await self.redis_client.setex(key, ttl or 300, serialized)
                return True
            
            # Fallback to local cache
            async with self._lock:
                self.local_cache[key] = value
                self.local_ttl[key] = asyncio.get_event_loop().time() + (ttl or 300)
            return True
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if self._connected:
                await self.redis_client.delete(key)
            
            async with self._lock:
                self.local_cache.pop(key, None)
                self.local_ttl.pop(key, None)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        try:
            if self._connected:
                keys = await self.redis_client.keys(pattern)
                if keys:
                    return await self.redis_client.delete(*keys)
            
            # Local cache clear
            async with self._lock:
                keys_to_delete = [k for k in self.local_cache if pattern in k]
                for k in keys_to_delete:
                    del self.local_cache[k]
                    del self.local_ttl[k]
                return len(keys_to_delete)
                
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return 0
    
    async def get_or_set(
        self,
        key: str,
        factory: Callable,
        ttl: Optional[int] = None
    ) -> Any:
        """Get from cache or compute and store."""
        value = await self.get(key)
        if value is not None:
            return value
        
        value = await factory() if asyncio.iscoroutinefunction(factory) else factory()
        await self.set(key, value, ttl)
        return value
    
    def cached(self, ttl: int = 300, key_prefix: str = ""):
        """Decorator for caching function results."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                cache_key = self._generate_key(
                    key_prefix or func.__name__,
                    *args,
                    **kwargs
                )
                
                cached_value = await self.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                result = await func(*args, **kwargs)
                await self.set(cache_key, result, ttl)
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # For sync functions, use simple key
                cache_key = f"{key_prefix or func.__name__}:{str(args)}"
                
                # Check local cache only for sync
                if cache_key in self.local_cache:
                    return self.local_cache[cache_key]
                
                result = func(*args, **kwargs)
                asyncio.create_task(self.set(cache_key, result, ttl))
                return result
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomic increment operation."""
        if self._connected:
            return await self.redis_client.incrby(key, amount)
        
        # Local implementation (not atomic)
        async with self._lock:
            current = self.local_cache.get(key, 0)
            self.local_cache[key] = current + amount
            return current + amount
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key."""
        if self._connected:
            return await self.redis_client.expire(key, seconds)
        
        async with self._lock:
            if key in self.local_cache:
                self.local_ttl[key] = asyncio.get_event_loop().time() + seconds
                return True
        return False


# Global cache instance
cache = CacheManager()


# Specific cache helpers for trading data
class MarketDataCache:
    """Specialized cache for market data."""
    
    TICK_TTL = 1  # 1 second for ticks
    CANDLE_TTL = 60  # 1 minute for candles
    ANALYSIS_TTL = 300  # 5 minutes for analysis
    
    @staticmethod
    async def get_tick(symbol: str) -> Optional[dict]:
        """Get cached tick data."""
        key = f"tick:{symbol}"
        return await cache.get(key)
    
    @staticmethod
    async def set_tick(symbol: str, data: dict):
        """Cache tick data."""
        key = f"tick:{symbol}"
        await cache.set(key, data, ttl=MarketDataCache.TICK_TTL)
    
    @staticmethod
    async def get_candles(symbol: str, timeframe: str, limit: int = 100) -> Optional[list]:
        """Get cached candles."""
        key = f"candles:{symbol}:{timeframe}:{limit}"
        return await cache.get(key)
    
    @staticmethod
    async def set_candles(symbol: str, timeframe: str, data: list, limit: int = 100):
        """Cache candle data."""
        key = f"candles:{symbol}:{timeframe}:{limit}"
        await cache.set(key, data, ttl=MarketDataCache.CANDLE_TTL)
    
    @staticmethod
    async def get_analysis(symbol: str, timeframe: str) -> Optional[dict]:
        """Get cached analysis."""
        key = f"analysis:{symbol}:{timeframe}"
        return await cache.get(key)
    
    @staticmethod
    async def set_analysis(symbol: str, timeframe: str, data: dict):
        """Cache analysis results."""
        key = f"analysis:{symbol}:{timeframe}"
        await cache.set(key, data, ttl=MarketDataCache.ANALYSIS_TTL)
    
    @staticmethod
    async def invalidate_symbol(symbol: str):
        """Invalidate all cache for symbol."""
        patterns = [f"tick:{symbol}*", f"candles:{symbol}*", f"analysis:{symbol}*"]
        for pattern in patterns:
            await cache.clear_pattern(pattern)


class UserCache:
    """Specialized cache for user data."""
    
    SESSION_TTL = 3600  # 1 hour
    PROFILE_TTL = 600  # 10 minutes
    
    @staticmethod
    async def get_session(user_id: int) -> Optional[dict]:
        """Get cached user session."""
        key = f"session:{user_id}"
        return await cache.get(key)
    
    @staticmethod
    async def set_session(user_id: int, data: dict):
        """Cache user session."""
        key = f"session:{user_id}"
        await cache.set(key, data, ttl=UserCache.SESSION_TTL)
    
    @staticmethod
    async def get_profile(user_id: int) -> Optional[dict]:
        """Get cached user profile."""
        key = f"profile:{user_id}"
        return await cache.get(key)
    
    @staticmethod
    async def set_profile(user_id: int, data: dict):
        """Cache user profile."""
        key = f"profile:{user_id}"
        await cache.set(key, data, ttl=UserCache.PROFILE_TTL)
    
    @staticmethod
    async def invalidate_user(user_id: int):
        """Invalidate all user cache."""
        patterns = [f"session:{user_id}*", f"profile:{user_id}*"]
        for pattern in patterns:
            await cache.clear_pattern(pattern)
