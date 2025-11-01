# AI-PAL Production Dockerfile
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create data directories
RUN mkdir -p /app/data /app/logs

# Copy requirements files
COPY requirements.txt setup.py README.md ./

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -e .

# Copy application code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create non-root user
RUN useradd -m -u 1000 aipal && \
    chown -R aipal:aipal /app

# Switch to non-root user
USER aipal

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "ai_pal.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
