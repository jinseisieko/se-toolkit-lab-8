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

# Copy all workspace packages to their expected paths
COPY --from=mcp mcp-lms /app/mcp/mcp-lms
COPY --from=workspace mcp/mcp-obs /app/mcp/mcp-obs
COPY --from=workspace nanobot-websocket-channel /app/nanobot-websocket-channel

# Copy nanobot project files (from the primary context which is ./nanobot)
COPY pyproject.toml /app/nanobot/pyproject.toml
COPY . /app/nanobot

# Copy config.json explicitly (it's gitignored but needed for runtime)
COPY config.json /app/nanobot/config.json

# Sync dependencies from root workspace
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --package nanobot

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

# Setup a non-root user matching host UID/GID for bind mounts
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd --system --gid ${APP_GID} appgroup && \
    useradd --system --gid ${APP_GID} --uid ${APP_UID} --create-home appuser

# Copy the application from the builder
COPY --from=builder --chown=appgroup:appgroup /app /app

# Copy config.json explicitly (it's gitignored but needed for runtime)
COPY config.json /app/nanobot/config.json

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# Use `/app/nanobot` as the working directory
WORKDIR /app/nanobot

# Use the app user to run our application
USER ${APP_UID}:${APP_GID}

# Run the nanobot gateway via entrypoint
ENTRYPOINT ["python", "/app/nanobot/entrypoint.py"]
