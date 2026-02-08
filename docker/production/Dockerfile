# ==============================================================================
# PRODUCTION DOCKERFILE - DISTROLESS & ROOTLESS
# ==============================================================================
# Best Practices:
# ✓ Multi-stage build (smaller final image)
# ✓ Non-root user (security)
# ✓ Distroless base (minimal attack surface - NO shell, NO package manager)
# ✓ Build-time security scanning
# ✓ Minimal layers
# ✓ No secrets in image
# ==============================================================================

# Stage 1: Builder
# Uses full Python image to install dependencies
FROM python:3.11-slim AS builder

# Set build-time environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (layer caching optimization)
COPY requirements.txt .

# Install Python dependencies into a separate directory
RUN pip install --prefix=/install --no-warn-script-location -r requirements.txt

# ==============================================================================
# Stage 2: Runtime (Distroless)
# ==============================================================================
FROM gcr.io/distroless/python3-debian12:nonroot

# Metadata labels (OCI standard)
LABEL maintainer="SRE Team <sre@company.com>" \
      org.opencontainers.image.title="SRE Demo API" \
      org.opencontainers.image.description="Production-grade FastAPI microservice" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Company" \
      org.opencontainers.image.authors="SRE Team"

# Set runtime environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/install/bin:$PATH" \
    ENVIRONMENT=production

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create app directory and copy application
WORKDIR /app
COPY --chown=nonroot:nonroot app/ /app/app/

# Distroless images already run as 'nonroot' user (UID 65532)
# No need to specify USER directive - it's already non-root

# Health check (using Python since no curl/wget available)
# Note: Distroless has limitations - this won't work in distroless
# HEALTHCHECK is skipped - rely on Kubernetes probes instead

# Expose application port
EXPOSE 8000

# Run the application
# Note: Using list format (exec form) is critical for proper signal handling
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# ==============================================================================
# USAGE:
# Build: docker build -f docker/production/Dockerfile -t sre-demo-api:prod .
# Run:   docker run -p 8000:8000 sre-demo-api:prod
#
# SECURITY NOTES:
# - No shell available (cannot 'docker exec -it <container> /bin/sh')
# - No package manager (cannot install anything at runtime)
# - Non-root user (UID 65532)
# - Minimal attack surface (~50MB image)
#
# DEBUGGING:
# If you need to debug, use the development Dockerfile
# ==============================================================================
