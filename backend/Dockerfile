# Production Dockerfile for Tech4Future-Global Management System V13
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

WORKDIR /app

# Install runtime dependencies (libpq for PostgreSQL, curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Create dedicated non-root application user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Copy application code, static assets, and configurations
COPY . /app

# Create staticfiles and media directories and set permissions
RUN mkdir -p /app/backend/staticfiles /app/backend/media && \
    chown -R appuser:appuser /app && \
    chmod +x /app/backend/entrypoint.sh

WORKDIR /app/backend
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD curl -f http://localhost:8000/api/v1/system/health || exit 1

ENTRYPOINT ["/app/backend/entrypoint.sh"]
