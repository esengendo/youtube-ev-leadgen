# Stage 1: Builder
FROM python:3.11-slim AS builder

# Install build tools and uv
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install uv

# Copy project files
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./

# Install dependencies using UV (creates .venv automatically)
RUN uv sync --frozen --no-dev

# Stage 2: Production
FROM python:3.11-slim AS production

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install UV in production stage for running scripts
RUN pip install uv

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the application code
WORKDIR /app
COPY --chown=appuser:appuser . .

# Set the user
USER appuser

# Set PATH so that the virtual environment is found
ENV PATH="/app/.venv/bin:$PATH"

# Expose the Streamlit port
EXPOSE 8501

# Health check to ensure the app is running
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Command to run the Streamlit application
CMD ["python", "-m", "streamlit", "run", "dashboard/streamlit_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
