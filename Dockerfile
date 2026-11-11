# Production-optimized Dockerfile without editable install
# Uses Debian slim with clean dependency installation

FROM python:3.13-slim

# Install essential runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./
RUN mkdir -p src && touch src/__init__.py
COPY src/_version.py ./src/_version.py

# Install uv and sync dependencies from lock file into .venv
# --no-install-project: install deps only, project source comes from filesystem COPY later
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
RUN uv sync --frozen --no-dev --no-install-project && \
    rm -rf /root/.cache/uv

# Configure .venv as active Python environment
# uv sync creates .venv by default (no --system flag in current uv 0.11.x)
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user for security
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -m -s /bin/sh appuser

# Create necessary directories and set permissions before switching user
RUN mkdir -p logs && \
    chown -R appuser:appuser /app

# Copy real source code with ownership suitable for the non-root runtime
COPY --chown=appuser:appuser src/ ./src/

# Switch to non-root user
USER appuser

# Environment defaults for FastMCP HTTP
ENV SERVER_MODE=http-auth \
    HOST=0.0.0.0 \
    PORT=8000 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Expose the application's port
EXPOSE 8000

# Healthcheck: use the dedicated health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=2 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["python", "-m", "src.server"]
