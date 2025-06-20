# Stage 1: Builder
FROM python:3.11-slim AS builder

# Install build tools, including the GCC C compiler, and uv
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
RUN pip install uv

# Create a virtual environment in a standard location
ENV VENV_PATH=/opt/venv
RUN python3 -m venv $VENV_PATH

# Set the PATH to include the venv's bin directory for subsequent RUN commands
ENV PATH="$VENV_PATH/bin:$PATH"

# Copy project files
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./

# Install dependencies into the virtual environment
# Using --system is a misnomer here; with an active venv, it installs into that venv.
# This is a robust way to ensure all packages land in the venv.
RUN uv sync --frozen --no-dev

# Stage 2: Production
FROM python:3.11-slim AS production

# Create a non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
WORKDIR /app
COPY --chown=appuser:appuser . .

# Set the user
USER appuser

# Set PATH so that the 'streamlit' command is found
ENV PATH="/opt/venv/bin:$PATH"

# Expose the Streamlit port
EXPOSE 8501

# Health check to ensure the app is running
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Command to run the Streamlit application
CMD ["streamlit", "run", "dashboard/streamlit_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
