"""
Revolution X - Performance Optimization
Database query optimization, connection pooling, and async operations
"""
import asyncio
import time
from contextlib import asynccontextmanager
from typing import Optional, List, Any, Callable
from functools import wraps
import threading

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
import asyncpg

from app.core.config import settings
from app.core.logging import logger
from app.db.base import Base


class DatabaseOptimizer:
    """Database performance optimization."""
    
    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        self._query_stats = {}
        self._stats_lock = threading.Lock()
    
    def create_optimized_engine(self):
        """Create optimized async database engine."""
        self.engine = create_async_engine(
            settings.ASYNC_DATABASE_URL,
            echo=settings.DB_ECHO,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_timeout=30,
            connect_args={
                "command_timeout": 60,
                "server_settings": {
                    "jit": "off",  # Disable JIT for short queries
                    "application_name": "revolution_x"
                }
            }
        )
        
        self.async_session_maker = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False
        )
        
        logger.info("✅ Optimized database engine created")
        return self.engine
    
    @asynccontextmanager
    async def get_session(self):
        """Get optimized database session."""
        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()
    
    def log_query_time(self, query_name: str, duration: float):
        """Log query execution time for monitoring."""
        with self._stats_lock:
            if query_name not in self._query_stats:
                self._query_stats[query_name] = {
                    "count": 0,
                    "total_time": 0,
                    "avg_time": 0,
                    "max_time": 0
                }
            
            stats = self._query_stats[query_name]
            stats["count"] += 1
            stats["total_time"] += duration
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["max_time"] = max(stats["max_time"], duration)
            
            # Alert on slow queries
            if duration > 1.0:  # 1 second threshold
                logger.warning(f"🐌 Slow query detected: {query_name} took {duration:.2f}s")
    
    def get_slow_queries(self, threshold: float = 0.5) -> List[dict]:
        """Get list of slow queries."""
        with self._stats_lock:
            return [
                {
                    "query": name,
                    "avg_time": stats["avg_time"],
                    "max_time": stats["max_time"],
                    "count": stats["count"]
                }
                for name, stats in self._query_stats.items()
                if stats["avg_time"] > threshold
            ]


class QueryOptimizer:
    """SQL query optimization utilities."""
    
    @staticmethod
    def add_indexes():
        """Recommended database indexes for performance."""
        indexes = [
            # User tables
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            
            # Trading tables
            "CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)",
            "CREATE INDEX IF NOT EXISTS idx_trades_created_at ON trades(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_trades_user_symbol ON trades(user_id, symbol)",
            
            # Positions tables
            "CREATE INDEX IF NOT EXISTS idx_positions_user_id ON positions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_positions_status ON positions(status)",
            
            # Market data
            "CREATE INDEX IF NOT EXISTS idx_candles_symbol_timeframe ON candles(symbol, timeframe, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_candles_timestamp ON candles(timestamp)",
            
            # AI predictions
            "CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON predictions(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at)",
            
            # Notifications
            "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id, read)",
        ]
        return indexes
    
    @staticmethod
    async def analyze_table(session, table_name: str):
        """Run ANALYZE on table for query planner."""
        await session.execute(f"ANALYZE {table_name}")
    
    @staticmethod
    async def vacuum_table(session, table_name: str):
        """Run VACUUM on table (requires exclusive lock)."""
        await session.execute(f"VACUUM ANALYZE {table_name}")


class AsyncBatchProcessor:
    """Batch processing for high-throughput operations."""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 1.0):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._buffer = []
        self._lock = asyncio.Lock()
        self._flush_task = None
    
    async def start(self):
        """Start background flush task."""
        self._flush_task = asyncio.create_task(self._periodic_flush())
    
    async def stop(self):
        """Stop and flush remaining items."""
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        await self.flush()
    
    async def add(self, item: Any):
        """Add item to batch."""
        async with self._lock:
            self._buffer.append(item)
            
            if len(self._buffer) >= self.batch_size:
                await self.flush()
    
    async def flush(self):
        """Flush buffer to database."""
        async with self._lock:
            if not self._buffer:
                return
            
            batch = self._buffer[:]
            self._buffer = []
        
        # Process batch
        try:
            await self._process_batch(batch)
        except Exception as e:
            logger.error(f"Batch processing error: {e}")
            # Re-add to buffer for retry
            async with self._lock:
                self._buffer = batch + self._buffer
    
    async def _periodic_flush(self):
        """Periodic flush based on time."""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self.flush()
    
    async def _process_batch(self, batch: List[Any]):
        """Override this method to process batch."""
        raise NotImplementedError


class ConnectionPoolMonitor:
    """Monitor database connection pool health."""
    
    def __init__(self, engine):
        self.engine = engine
        self._check_interval = 30
    
    async def start_monitoring(self):
        """Start pool monitoring."""
        while True:
            await self._check_pool_health()
            await asyncio.sleep(self._check_interval)
    
    async def _check_pool_health(self):
        """Check connection pool statistics."""
        pool = self.engine.pool
        stats = {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow()
        }
        
        # Alert if pool is exhausted
        if stats["checked_out"] / stats["size"] > 0.8:
            logger.warning(f"⚠️ Connection pool near exhaustion: {stats}")
        
        return stats


def measure_time(func: Callable) -> Callable:
    """Decorator to measure function execution time."""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return await func(*args, **kwargs)
        finally:
            duration = time.perf_counter() - start
            if duration > 0.1:  # Log if > 100ms
                logger.debug(f"⏱️ {func.__name__} took {duration:.3f}s")
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            duration = time.perf_counter() - start
            if duration > 0.1:
                logger.debug(f"⏱️ {func.__name__} took {duration:.3f}s")
    
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


class MemoryOptimizer:
    """Memory usage optimization."""
    
    @staticmethod
    def optimize_dataframe(df, categorical_threshold: int = 50):
        """Optimize pandas DataFrame memory usage."""
        import pandas as pd
        
        for col in df.columns:
            col_type = df[col].dtype
            
            if col_type != object:
                c_min = df[col].min()
                c_max = df[col].max()
                
                if str(col_type)[:3] == 'int':
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                
                else:
                    if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
                        df[col] = df[col].astype(np.float16)
                    elif c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
                        df[col] = df[col].astype(np.float32)
            
            else:
                if df[col].nunique() < categorical_threshold:
                    df[col] = df[col].astype('category')
        
        return df


# Global instances
db_optimizer = DatabaseOptimizer()
query_optimizer = QueryOptimizer()
