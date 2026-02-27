"""
Revolution X - Structured Logging Configuration
ELK-compatible JSON logging with rotation
"""
import json
import logging
import logging.handlers
import sys
from datetime import datetime
from typing import Any, Dict
import traceback
from pythonjsonlogger import jsonlogger
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]):
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        
        # Add source location
        log_record["source"] = {
            "file": record.filename,
            "line": record.lineno,
            "function": record.funcName
        }
        
        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            log_record["correlation_id"] = record.correlation_id
        
        # Add user context if available
        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id
        
        # Format exception info
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "stacktrace": traceback.format_exception(*record.exc_info)
            }


def setup_logging():
    """Configure structured logging."""
    
    # Sentry integration
    if getattr(settings, "SENTRY_DSN", None):
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=[sentry_logging],
            environment=settings.ENVIRONMENT,
            release=settings.APP_VERSION,
            traces_sample_rate=0.1
        )
    
    # Create formatter
    formatter = CustomJsonFormatter(
        "%(timestamp)s %(level)s %(name)s %(message)s"
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename="logs/revolutionx.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # Error file handler
    error_handler = logging.handlers.RotatingFileHandler(
        filename="logs/error.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=10,
        encoding="utf-8"
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    root_logger.handlers = []
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("websockets").setLevel(logging.WARNING)
    
    return root_logger


class ContextualLogger:
    """Logger with context support."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.context = {}
    
    def bind(self, **kwargs):
        """Bind context to logger."""
        self.context.update(kwargs)
        return self
    
    def _log(self, level: int, message: str, extra: Dict = None):
        """Log with context."""
        extra = extra or {}
        extra.update(self.context)
        
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, extra={**self.context, **kwargs})


# Audit logging for security events
class AuditLogger:
    """Specialized logger for audit events."""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        
        # Separate audit log file
        handler = logging.handlers.RotatingFileHandler(
            filename="logs/audit.log",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=20,
            encoding="utf-8"
        )
        handler.setFormatter(CustomJsonFormatter())
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_auth_event(self, event_type: str, user_id: int, details: Dict):
        """Log authentication event."""
        self.logger.info(
            "Authentication event",
            extra={
                "event_type": event_type,
                "user_id": user_id,
                "details": details,
                "category": "auth"
            }
        )
    
    def log_trade_event(self, event_type: str, user_id: int, trade_details: Dict):
        """Log trading event."""
        self.logger.info(
            "Trading event",
            extra={
                "event_type": event_type,
                "user_id": user_id,
                "trade": trade_details,
                "category": "trading"
            }
        )
    
    def log_admin_event(self, event_type: str, admin_id: int, target_id: int, details: Dict):
        """Log administrative action."""
        self.logger.info(
            "Admin event",
            extra={
                "event_type": event_type,
                "admin_id": admin_id,
                "target_id": target_id,
                "details": details,
                "category": "admin"
            }
        )
    
    def log_security_event(self, event_type: str, severity: str, details: Dict):
        """Log security-related event."""
        self.logger.warning(
            "Security event",
            extra={
                "event_type": event_type,
                "severity": severity,
                "details": details,
                "category": "security"
            }
        )


# Performance logging
class PerformanceLogger:
    """Log performance metrics."""
    
    def __init__(self):
        self.logger = logging.getLogger("performance")
    
    def log_db_query(self, query: str, duration: float, rows: int):
        """Log database query performance."""
        if duration > 1.0:  # Slow query threshold
            self.logger.warning(
                "Slow database query",
                extra={
                    "query": query[:200],
                    "duration_ms": duration * 1000,
                    "rows_returned": rows,
                    "type": "db_query"
                }
            )
    
    def log_api_call(self, endpoint: str, method: str, duration: float, status_code: int):
        """Log API call performance."""
        self.logger.info(
            "API call",
            extra={
                "endpoint": endpoint,
                "method": method,
                "duration_ms": duration * 1000,
                "status_code": status_code,
                "type": "api_call"
            }
        )
    
    def log_ai_prediction(self, model: str, symbol: str, duration: float):
        """Log AI prediction performance."""
        self.logger.info(
            "AI prediction",
            extra={
                "model": model,
                "symbol": symbol,
                "duration_ms": duration * 1000,
                "type": "ai_prediction"
            }
        )


# Global instances
audit_logger = AuditLogger()
performance_logger = PerformanceLogger()


def get_logger(name: str) -> ContextualLogger:
    """Get contextual logger."""
    return ContextualLogger(logging.getLogger(name))
