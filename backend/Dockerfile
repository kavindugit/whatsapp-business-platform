# backend/Dockerfile
# Multi-stage build: development (hot-reload) and production targets.
#
# Network note: --trusted-host flags are required on networks with SSL inspection
# (corporate proxies, some ISPs). They allow pip to reach PyPI without certificate
# chain verification errors. Remove in production on clean networks.

# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# Prevent Python from writing .pyc files; enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# pip trusted-host configuration for SSL-intercepted networks
ENV PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org pypi.python.org" \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Upgrade pip itself first (avoids old pip SSL bugs)
RUN pip install --upgrade pip

# Copy dependency manifests
COPY pyproject.toml ./

# ── Development target ────────────────────────────────────────────────────────
FROM base AS development

# Install all dependencies including dev extras
# Uses pip directly (no uv) for maximum compatibility
RUN pip install -e ".[dev]"

# Copy application source (mounted as volume in compose for hot-reload)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Production target ─────────────────────────────────────────────────────────
FROM base AS production

# Install production dependencies only
RUN pip install -e "."

COPY . .

EXPOSE 8000

# Production: 2 workers; no reload
CMD ["uvicorn", "app.main:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
