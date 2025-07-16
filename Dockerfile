# Multi-stage build for production-ready Procurement Intelligence System
FROM python:3.11-slim as builder

# Set build arguments
ARG BUILD_DATE
ARG VERSION=1.0.0
ARG VCS_REF

# Add metadata
LABEL maintainer="Procurement Intelligence Team" \
      version="${VERSION}" \
      build-date="${BUILD_DATE}" \
      vcs-ref="${VCS_REF}" \
      description="AI-powered procurement intelligence platform"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    ENVIRONMENT=production

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create app directory
WORKDIR /app

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Ensure proper permissions
RUN chown -R appuser:appuser /app && \
    chmod -R 755 /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Development stage
FROM production as development

# Switch back to root for development dependencies
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install additional development packages
RUN pip install pytest pytest-asyncio pytest-cov black flake8 mypy

# Set environment for development
ENV ENVIRONMENT=development

# Switch back to appuser
USER appuser

# Override command for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Testing stage
FROM development as testing

# Copy test requirements
COPY requirements-test.txt .

# Install test dependencies
RUN pip install -r requirements-test.txt

# Copy test files
COPY --chown=appuser:appuser tests/ tests/

# Run tests
RUN python -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Build stage for CI/CD
FROM builder as ci

# Copy source code
COPY . .

# Run linting and type checking
RUN pip install black flake8 mypy && \
    black --check app/ && \
    flake8 app/ && \
    mypy app/

# Security scanning stage
FROM production as security

# Install security scanning tools
USER root
RUN pip install safety bandit

# Run security scans
RUN safety check && \
    bandit -r app/ -f json -o security-report.json

# Switch back to appuser
USER appuser

# Production-ready stage with optimizations
FROM production as optimized

# Enable Python optimizations
ENV PYTHONOPTIMIZE=1

# Use gunicorn for production
RUN pip install gunicorn[gevent]

# Copy gunicorn configuration
COPY --chown=appuser:appuser gunicorn.conf.py .

# Override command for production
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app.main:app"]