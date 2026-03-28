# Adapted from backend/Dockerfile
# Also see https://docs.astral.sh/uv/guides/integration/docker/

# ---
# Stage 1: build the application in the `/app` directory.
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}astral/uv:python3.14-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Omit development dependencies
ENV UV_NO_DEV=1

# Disable Python downloads - use the system interpreter across both images
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Copy root workspace files from workspace context (the repo root)
COPY --from=workspace pyproject.toml uv.lock /app/

# Copy mcp packages from mcp context
COPY --from=mcp mcp-lms /app/mcp/mcp-lms

# Copy nanobot project files (from the primary context which is ./nanobot)
COPY pyproject.toml /app/nanobot/pyproject.toml
COPY . /app/nanobot

# Sync dependencies (no dev deps, install nanobot package)
RUN --mount=type=cache,target=/root/.cache/uv \
    cd /app/nanobot && uv sync --frozen --no-dev

# ---
# Stage 2: use a final image without uv
# ---

ARG REGISTRY_PREFIX_DOCKER_HUB
FROM ${REGISTRY_PREFIX_DOCKER_HUB}python:3.14.2-slim-bookworm

# Set environment variables for Python and application
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Make sure we use UTF-8 encoding
ENV LANG=C.UTF-8

# Setup a non-root user
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# Copy the application from the builder
COPY --from=builder --chown=nonroot:nonroot /app /app

# Create writable directory for nanobot workspace
RUN mkdir -p /app/nanobot/workspace && chown -R nonroot:nonroot /app/nanobot

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Use `/app/nanobot` as the working directory
WORKDIR /app/nanobot

# Use the non-root user to run our application
USER nonroot

# Run the nanobot gateway via entrypoint
ENTRYPOINT ["python", "/app/nanobot/entrypoint.py"]
