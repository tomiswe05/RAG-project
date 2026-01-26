# =============================================================================
# Dockerfile for RAG React Backend
# =============================================================================
# This creates a container for the FastAPI backend.
# ChromaDB runs as a separate container (see docker-compose.yml)

# -----------------------------------------------------------------------------
# Base Image
# -----------------------------------------------------------------------------
# python:3.12-slim is a minimal Python image (~150MB vs ~1GB for full)
# "slim" removes docs, man pages, and other extras we don't need
FROM python:3.12-slim

# -----------------------------------------------------------------------------
# Environment Variables
# -----------------------------------------------------------------------------
# PYTHONDONTWRITEBYTECODE=1 → Don't create .pyc files (smaller image)
# PYTHONUNBUFFERED=1 → Print logs immediately (important for Docker)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Pip settings
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# -----------------------------------------------------------------------------
# Working Directory
# -----------------------------------------------------------------------------
# All commands after this run from /app
# This is where our code will live inside the container
WORKDIR /app

# -----------------------------------------------------------------------------
# System Dependencies
# -----------------------------------------------------------------------------
# Some Python packages need C libraries to compile:
# - build-essential: gcc compiler
# - libpq-dev: PostgreSQL client library (for psycopg2)
#
# We clean up apt cache to keep image small
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# Python Dependencies
# -----------------------------------------------------------------------------
# COPY requirements first, then install
# Docker caches each layer - if requirements.txt hasn't changed,
# Docker reuses the cached layer (much faster rebuilds!)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Application Code
# -----------------------------------------------------------------------------
# Copy everything from local directory to /app in container
# .dockerignore excludes files we don't want (venv, .git, etc.)
COPY . .

# -----------------------------------------------------------------------------
# Port
# -----------------------------------------------------------------------------
# EXPOSE documents which port the app uses
# It doesn't actually publish the port - that's done in docker-compose
EXPOSE 8000

# -----------------------------------------------------------------------------
# Health Check
# -----------------------------------------------------------------------------
# Docker periodically runs this to check if container is healthy
# Used by Docker Compose, ECS, Kubernetes for orchestration
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# -----------------------------------------------------------------------------
# Startup Command
# -----------------------------------------------------------------------------
# This runs when the container starts
# Using exec form (JSON array) for proper signal handling
# --host 0.0.0.0 allows connections from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
