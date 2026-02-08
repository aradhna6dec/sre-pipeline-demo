# ==============================================================================
# DEVELOPMENT DOCKERFILE - Full Tooling & Hot Reload
# ==============================================================================
# Features:
# ✓ Full Python image with all tools
# ✓ Development dependencies
# ✓ Hot reload for code changes
# ✓ Debugging tools (ipdb, py-spy)
# ✓ Running as root for convenience (NOT for production!)
# ==============================================================================

FROM python:3.11

# Install system dependencies and debugging tools
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    git \
    htop \
    net-tools \
    procps \
    strace \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies (including dev tools)
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    ipdb \
    ipython \
    py-spy \
    debugpy \
    pytest-watch

# Environment variables for development
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=development \
    DEBUG=true \
    LOG_FORMAT=text

# Copy application (will be overridden by volume mount)
COPY app/ /app/app/

# Expose ports
EXPOSE 8000
EXPOSE 5678

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Development server with auto-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--log-level", "debug"]

# ==============================================================================
# USAGE:
# Build: docker build -f docker/development/Dockerfile -t sre-demo-api:dev .
# Run:   docker run -p 8000:8000 -v $(pwd)/app:/app/app sre-demo-api:dev
#
# Hot Reload: Mount the app directory as volume
# Debugging:  Attach debugger to port 5678
#
# SECURITY WARNING:
# ⚠️  DO NOT USE IN PRODUCTION
# - Running as root
# - Debug tools installed
# - Auto-reload enabled (performance impact)
# ==============================================================================
