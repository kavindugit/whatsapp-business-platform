# backend/Dockerfile
# Multi-stage build: development (hot-reload) and production targets.

# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # uv settings
    UV_SYSTEM_PYTHON=1 \
    UV_NO_CACHE=1

WORKDIR /app

# Install uv
RUN pip install --no-cache-dir uv==0.5.1

# Copy dependency manifests
COPY pyproject.toml ./

# ── Development target ────────────────────────────────────────────────────────
FROM base AS development

# Install all dependencies including dev extras
RUN uv pip install -e ".[dev]"

# Copy application source (mounted as volume in compose for hot-reload)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Production target ─────────────────────────────────────────────────────────
FROM base AS production

# Install production dependencies only
RUN uv pip install -e "."

COPY . .

EXPOSE 8000

# Production: run with multiple workers; no reload
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
