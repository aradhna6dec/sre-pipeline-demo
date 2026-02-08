"""
Structured Logging Configuration
Outputs JSON for easy parsing by Loki/ELK
"""

import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
        }
        
        # Add extra fields if present
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id
        
        # Add any extra attributes from the log call
        for key, value in record.__dict__.items():
            if key not in [
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "message", "pathname", "process", "processName",
                "relativeCreated", "thread", "threadName", "exc_info",
                "exc_text", "stack_info"
            ]:
                log_data[key] = value
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Human-readable text formatter for local development"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as readable text"""
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        correlation_id = getattr(record, "correlation_id", "N/A")
        
        base_msg = f"[{timestamp}] [{record.levelname}] [{correlation_id}] {record.name}: {record.getMessage()}"
        
        if record.exc_info:
            base_msg += "\n" + self.formatException(record.exc_info)
        
        return base_msg


def setup_logging():
    """Configure application logging"""
    
    # Determine formatter
    if settings.LOG_FORMAT == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Add stdout handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)
