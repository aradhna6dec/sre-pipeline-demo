# ==============================================================================
# STANDARD DOCKERFILE - SECURITY HARDENED (with debug capabilities)
# ==============================================================================
# Best Practices:
# ✓ Multi-stage build
# ✓ Non-root user (custom UID/GID)
# ✓ Minimal base image (slim)
# ✓ Security scanning ready
# ✓ Health checks
# ✓ Shell available for debugging (trade-off: slightly larger attack surface)
# ==============================================================================

# Stage 1: Builder
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

# ==============================================================================
# Stage 2: Runtime
# ==============================================================================
FROM python:3.11-slim

# Install runtime dependencies and security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    tini \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create non-root user and group
# Using explicit UID/GID for consistency across environments
RUN groupadd -g 1001 appuser && \
    useradd -r -u 1001 -g appuser -s /sbin/nologin -c "Application user" appuser

# Copy installed packages
COPY --from=builder /install /usr/local

# Create app directory with proper permissions
WORKDIR /app
COPY --chown=appuser:appuser app/ /app/app/

# Switch to non-root user
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=production

# Metadata
LABEL maintainer="SRE Team" \
      version="1.0.0" \
      description="SRE Demo API - Standard Build"

# Health check (can use curl since it's available)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Expose port
EXPOSE 8000

# Use tini as init system (proper signal handling, zombie reaping)
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ==============================================================================
# USAGE:
# Build: docker build -f docker/standard/Dockerfile -t sre-demo-api:standard .
# Run:   docker run -p 8000:8000 sre-demo-api:standard
# Debug: docker exec -it <container> /bin/bash
#
# SECURITY NOTES:
# - Runs as non-root user (UID 1001)
# - Minimal base image (slim variant)
# - Security updates applied
# - Shell available for debugging
# - Tini for proper init
#
# IMAGE SIZE: ~200MB (vs ~50MB for distroless)
# ==============================================================================
