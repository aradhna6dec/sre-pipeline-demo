"""
Prometheus Metrics
Following Google SRE's "Four Golden Signals":
1. Latency - http_request_duration_seconds
2. Traffic - http_requests_total
3. Errors - http_requests_total (by status code)
4. Saturation - process_* metrics (CPU, memory)
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from app.core.config import settings


class Metrics:
    """Centralized metrics registry"""
    
    def __init__(self):
        # Application info
        self.app_info = Info(
            "app_info",
            "Application information"
        )
        self.app_info.info({
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
            "name": settings.APP_NAME
        })
        
        # HTTP Request Metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests",
            ["method", "endpoint", "status"]
        )
        
        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency",
            ["method", "endpoint", "status"],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0)
        )
        
        self.http_requests_in_progress = Gauge(
            "http_requests_in_progress",
            "HTTP requests currently being processed",
            ["method", "endpoint"]
        )
        
        # Business Metrics (examples)
        self.items_processed_total = Counter(
            "items_processed_total",
            "Total items processed",
            ["operation", "status"]
        )
        
        self.cache_hits_total = Counter(
            "cache_hits_total",
            "Total cache hits",
            ["cache_name"]
        )
        
        self.cache_misses_total = Counter(
            "cache_misses_total",
            "Total cache misses",
            ["cache_name"]
        )
        
        # Database Metrics (for future use)
        self.db_connections_total = Gauge(
            "db_connections_total",
            "Current database connections",
            ["pool"]
        )
        
        self.db_query_duration_seconds = Histogram(
            "db_query_duration_seconds",
            "Database query duration",
            ["query_type"],
            buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)
        )
        
        # Error Tracking
        self.errors_total = Counter(
            "errors_total",
            "Total errors by type",
            ["error_type", "severity"]
        )
        
        # Resource Usage
        self.active_workers = Gauge(
            "active_workers",
            "Number of active workers"
        )


# Global metrics instance
metrics = Metrics()
