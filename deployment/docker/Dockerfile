# Claude Multiagent PM Framework - Docker Container
# CLAUDE_MULTIAGENT_PM_ROOT Support (M01-043)
# =====================================

# Use Python 3.11 slim as base image
FROM python:3.11-slim as base

# Set build arguments
ARG CLAUDE_PM_VERSION=3.0.0
ARG BUILD_DATE
ARG VCS_REF

# Set labels
LABEL org.opencontainers.image.title="Claude Multiagent PM Framework"
LABEL org.opencontainers.image.description="AI-driven Project Management Framework with Multi-Agent Orchestration"
LABEL org.opencontainers.image.version="${CLAUDE_PM_VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
LABEL org.opencontainers.image.vendor="Claude Multiagent PM"
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV CLAUDE_PM_VERSION=${CLAUDE_PM_VERSION}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    make \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create application user and group
RUN groupadd -r claude-multiagent-pm && useradd -r -g claude-multiagent-pm claude-multiagent-pm

# Create application directories
ENV CLAUDE_MULTIAGENT_PM_ROOT=/app/claude-multiagent-pm
ENV CLAUDE_MULTIAGENT_PM_DATA_PATH=/app/data
ENV CLAUDE_MULTIAGENT_PM_LOGS_PATH=/app/logs
ENV CLAUDE_MULTIAGENT_PM_CONFIG_PATH=/app/config

# Legacy support for backward compatibility
ENV CLAUDE_PM_ROOT=${CLAUDE_MULTIAGENT_PM_ROOT}

RUN mkdir -p ${CLAUDE_MULTIAGENT_PM_ROOT} ${CLAUDE_MULTIAGENT_PM_DATA_PATH} ${CLAUDE_MULTIAGENT_PM_LOGS_PATH} ${CLAUDE_MULTIAGENT_PM_CONFIG_PATH} \
    && chown -R claude-multiagent-pm:claude-multiagent-pm /app

# Set working directory
WORKDIR ${CLAUDE_MULTIAGENT_PM_ROOT}

# =======================
# Development Stage
# =======================
FROM base as development

# Install development dependencies
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements/ ./requirements/
RUN pip install --no-cache-dir -r requirements/dev.txt

# Copy source code
COPY . .

# Install in development mode
RUN pip install -e .

# Change ownership
RUN chown -R claude-multiagent-pm:claude-multiagent-pm /app

# Switch to non-root user
USER claude-multiagent-pm

# Expose ports
EXPOSE 8001 7001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "from claude_pm.core.config import Config; config = Config(); print('healthy')" || exit 1

# Development command
CMD ["python", "-m", "claude_pm.cli", "service", "start"]

# =======================
# Production Stage
# =======================
FROM base as production

# Copy requirements first
COPY requirements/ ./requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy source code
COPY . .

# Install in production mode
RUN pip install .

# Remove unnecessary files
RUN rm -rf \
    requirements/ \
    tests/ \
    .git/ \
    .pytest_cache/ \
    *.md \
    .gitignore

# Change ownership
RUN chown -R claude-multiagent-pm:claude-multiagent-pm /app

# Switch to non-root user
USER claude-multiagent-pm

# Expose ports
EXPOSE 8001 7001

# Health check
HEALTHCHECK --interval=60s --timeout=15s --start-period=120s --retries=5 \
    CMD python -c "from claude_pm.core.config import Config; config = Config(); print('healthy')" || exit 1

# Production command
CMD ["python", "-m", "claude_pm.cli", "service", "start"]

# =======================
# Testing Stage
# =======================
FROM development as testing

# Install test dependencies
RUN pip install --no-cache-dir pytest pytest-cov pytest-asyncio

# Copy test files
COPY tests/ ./tests/

# Run tests
RUN python -m pytest tests/ -v --cov=claude_pm --cov-report=term-missing

# Test command
CMD ["python", "-m", "pytest", "tests/", "-v"]

# =======================
# Build Stage Selection
# =======================
FROM ${BUILD_TARGET:-production} as final

# Final stage configuration
ENV ENVIRONMENT=docker
ENV CLAUDE_PM_CONTAINER=true

# Create volume mount points
VOLUME ["${CLAUDE_PM_DATA_PATH}", "${CLAUDE_PM_LOGS_PATH}", "${CLAUDE_PM_CONFIG_PATH}"]

# Set final working directory
WORKDIR ${CLAUDE_PM_ROOT}

# Container startup script
COPY deployment/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]