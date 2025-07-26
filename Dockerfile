# Multi-stage Dockerfile for YouTube EV Lead Generation Platform
# Based on Python 3.11 with uv package manager

# Base stage for shared dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency files and README
COPY pyproject.toml uv.lock README.md ./

# Development stage
FROM base as development

# Install dependencies with uv
RUN uv sync --dev

# Copy source code
COPY . .

# Create virtual environment symlink for compatibility
RUN ln -s /root/.cache/uv/venv /app/.venv

# Expose port
EXPOSE 8501

# Default command for development
CMD ["uv", "run", "streamlit", "run", "dashboard/streamlit_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]

# Production stage
FROM base as production

# Install only production dependencies
RUN uv sync --no-dev

# Copy source code
COPY . .

# Create virtual environment symlink for compatibility
RUN ln -s /root/.cache/uv/venv /app/.venv

# Create necessary directories
RUN mkdir -p /app/data /app/reports /app/visualizations /app/logs

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command for production (original dashboard)
CMD ["uv", "run", "streamlit", "run", "dashboard/streamlit_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]

# For enhanced dashboard, use:
# CMD ["uv", "run", "streamlit", "run", "dashboard/enhanced_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"] 