"""
Revolution X - Prometheus Metrics
Application performance monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry
from prometheus_client.exposition import generate_latest
from fastapi import Request, Response
import time
from typing import Callable

from app.core.config import settings


# Create registry
registry = CollectorRegistry()

# Application info
app_info = Info(
    "revolutionx_app",
    "Application information",
    registry=registry
)
app_info.info({
    "version": settings.APP_VERSION,
    "environment": settings.ENVIRONMENT,
    "name": "Revolution X"
})

# HTTP metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=registry
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
    registry=registry
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
    registry=registry
)

# Active connections
active_connections = Gauge(
    "active_connections",
    "Number of active connections",
    registry=registry
)

# Database metrics
db_connections_active = Gauge(
    "db_connections_active",
    "Active database connections",
    registry=registry
)

db_connections_idle = Gauge(
    "db_connections_idle",
    "Idle database connections",
    registry=registry
)

db_query_duration_seconds = Histogram(
    "db_query_duration_seconds",
    "Database query duration",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry
)

# Trading metrics
trades_executed_total = Counter(
    "trades_executed_total",
    "Total trades executed",
    ["symbol", "side", "strategy"],
    registry=registry
)

trade_volume_total = Counter(
    "trade_volume_total",
    "Total trading volume",
    ["symbol"],
    registry=registry
)

trade_pnl = Gauge(
    "trade_pnl",
    "Trade profit/loss",
    ["symbol", "trade_id"],
    registry=registry
)

open_positions = Gauge(
    "open_positions",
    "Number of open positions",
    ["symbol"],
    registry=registry
)

# AI metrics
ai_predictions_total = Counter(
    "ai_predictions_total",
    "Total AI predictions made",
    ["model", "symbol"],
    registry=registry
)

ai_prediction_accuracy = Gauge(
    "ai_prediction_accuracy",
    "AI model accuracy",
    ["model"],
    registry=registry
)

ai_prediction_latency_seconds = Histogram(
    "ai_prediction_latency_seconds",
    "AI prediction latency",
    ["model"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
    registry=registry
)

# Risk metrics
risk_exposure = Gauge(
    "risk_exposure",
    "Current risk exposure",
    ["type"],
    registry=registry
)

margin_level = Gauge(
    "margin_level",
    "Current margin level",
    registry=registry
)

drawdown_percentage = Gauge(
    "drawdown_percentage",
    "Current drawdown percentage",
    registry=registry
)

# System metrics
memory_usage_bytes = Gauge(
    "memory_usage_bytes",
    "Memory usage in bytes",
    ["type"],
    registry=registry
)

cpu_usage_percent = Gauge(
    "cpu_usage_percent",
    "CPU usage percentage",
    registry=registry
)

disk_usage_bytes = Gauge(
    "disk_usage_bytes",
    ["path"],
    registry=registry
)

# Business metrics
active_users = Gauge(
    "active_users",
    "Number of active users",
    registry=registry
)

user_sessions_total = Counter(
    "user_sessions_total",
    "Total user sessions",
    registry=registry
)

# WebSocket metrics
websocket_connections_active = Gauge(
    "websocket_connections_active",
    "Active WebSocket connections",
    registry=registry
)

websocket_messages_total = Counter(
    "websocket_messages_total",
    "Total WebSocket messages",
    ["direction"],
    registry=registry
)


class MetricsMiddleware:
    """Middleware to collect HTTP metrics."""
    
    async def __call__(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        # Track active connections
        active_connections.inc()
        
        try:
            response = await call_next(request)
            
            # Record metrics
            duration = time.time() - start_time
            status_code = response.status_code
            method = request.method
            endpoint = request.url.path
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            # Request/response sizes
            if request.headers.get("content-length"):
                http_request_size_bytes.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(int(request.headers["content-length"]))
            
            if response.headers.get("content-length"):
                http_response_size_bytes.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(int(response.headers["content-length"]))
            
            return response
            
        finally:
            active_connections.dec()


class TradingMetrics:
    """Helper class for trading metrics."""
    
    @staticmethod
    def record_trade(symbol: str, side: str, strategy: str, volume: float):
        """Record trade execution."""
        trades_executed_total.labels(
            symbol=symbol,
            side=side,
            strategy=strategy
        ).inc()
        
        trade_volume_total.labels(symbol=symbol).inc(volume)
    
    @staticmethod
    def update_position_count(symbol: str, count: int):
        """Update open positions gauge."""
        open_positions.labels(symbol=symbol).set(count)
    
    @staticmethod
    def record_pnl(symbol: str, trade_id: str, pnl: float):
        """Record trade P&L."""
        trade_pnl.labels(symbol=symbol, trade_id=trade_id).set(pnl)
    
    @staticmethod
    def update_margin_level(level: float):
        """Update margin level."""
        margin_level.set(level)
    
    @staticmethod
    def update_drawdown(drawdown: float):
        """Update drawdown percentage."""
        drawdown_percentage.set(drawdown)


class AIMetrics:
    """Helper class for AI metrics."""
    
    @staticmethod
    def record_prediction(model: str, symbol: str, latency: float):
        """Record AI prediction."""
        ai_predictions_total.labels(model=model, symbol=symbol).inc()
        ai_prediction_latency_seconds.labels(model=model).observe(latency)
    
    @staticmethod
    def update_accuracy(model: str, accuracy: float):
        """Update model accuracy."""
        ai_prediction_accuracy.labels(model=model).set(accuracy)


def get_metrics() -> bytes:
    """Generate latest metrics for Prometheus scraping."""
    return generate_latest(registry)


async def metrics_endpoint():
    """FastAPI endpoint for metrics."""
    from fastapi import Response
    return Response(
        content=get_metrics(),
        media_type="text/plain"
    )
