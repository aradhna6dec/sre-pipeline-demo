"""
Production-Ready FastAPI Application
Senior SRE Best Practices:
- Structured logging with correlation IDs
- Prometheus metrics
- Health checks (liveness/readiness)
- Graceful shutdown
- OpenTelemetry tracing
"""

import asyncio
import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentation
from prometheus_client import (CONTENT_TYPE_LATEST, Counter, Gauge, Histogram,
                               generate_latest)

from app.api.routes import api_router
from app.core.config import settings
from app.core.logging_config import get_logger, setup_logging
from app.core.metrics import metrics

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# Application state
app_state = {
    "ready": False,
    "start_time": time.time(),
    "request_count": 0,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown"""
    # Startup
    logger.info(
        "Starting application",
        extra={
            "app_name": settings.APP_NAME,
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT,
        },
    )

    # Simulate initialization (DB connections, cache warmup, etc.)
    await asyncio.sleep(0.5)
    app_state["ready"] = True
    logger.info("Application ready to serve traffic")

    yield

    # Shutdown
    logger.info("Initiating graceful shutdown")
    app_state["ready"] = False
    # Give time for in-flight requests to complete
    await asyncio.sleep(2)
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Production-grade microservice with full observability",
    lifespan=lifespan,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to all requests for tracing"""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id

    # Track request
    metrics.http_requests_total.labels(
        method=request.method, endpoint=request.url.path
    ).inc()

    # Time the request
    start_time = time.time()

    try:
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time
        metrics.http_request_duration_seconds.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
        ).observe(duration)

        response.headers["X-Correlation-ID"] = correlation_id

        logger.info(
            "Request completed",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
            },
        )

        return response

    except Exception as e:
        logger.error(
            "Request failed",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
            },
            exc_info=True,
        )
        metrics.http_requests_total.labels(
            method=request.method, endpoint=request.url.path
        ).inc()
        raise


# Health check endpoints (Kubernetes probes)
@app.get("/health/live", tags=["health"], status_code=status.HTTP_200_OK)
async def liveness_probe() -> Dict[str, str]:
    """
    Liveness probe - indicates if the application is running
    Kubernetes will restart the pod if this fails
    """
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def readiness_probe() -> Response:
    """
    Readiness probe - indicates if the application can serve traffic
    Kubernetes will remove pod from service if this fails
    """
    if app_state["ready"]:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ready",
                "uptime_seconds": round(time.time() - app_state["start_time"], 2),
            },
        )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"status": "not_ready"}
    )


@app.get("/health/startup", tags=["health"])
async def startup_probe() -> Response:
    """
    Startup probe - indicates if the application has started
    Used for slow-starting applications
    """
    if app_state["ready"]:
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"status": "started"}
        )
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"status": "starting"}
    )


@app.get("/metrics", tags=["observability"])
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/", tags=["root"])
async def root() -> Dict[str, Any]:
    """Root endpoint with service information"""
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "operational",
        "uptime_seconds": round(time.time() - app_state["start_time"], 2),
    }


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# OpenTelemetry instrumentation
FastAPIInstrumentation.instrument_app(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True,
        # Production settings
        workers=4 if settings.ENVIRONMENT == "production" else 1,
        loop="uvloop",  # High-performance event loop
        http="httptools",  # High-performance HTTP parser
    )
