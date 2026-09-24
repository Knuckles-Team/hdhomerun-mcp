# syntax=docker/dockerfile:1
# One slim multi-stage image (build in a builder, ship only /usr/local — no
# dev-tools/source): the MCP server. The agent-runtime (A2A) build target was
# retired with hdhomerun_mcp/agent_server.py (EH-481 policy: agent_server.py +
# its console script are retired fleet-wide) -- this connector now ships only
# the MCP server.
#
#   docker build --target mcp -t hdhomerun-mcp:1.1.0 .
# See agent-packages/CLAUDE.md "Connector recipe" for the tag contract.
FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS builder-base
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_SYSTEM_PYTHON=1 \
    UV_HTTP_TIMEOUT=3600
# A few transitive deps ship no manylinux wheel and build from sdist, needing a C++
# toolchain. Install it in the builder only — final stages copy just /usr/local.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Slim MCP-only dependency closure.
FROM builder-base AS builder-mcp
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --upgrade --break-system-packages --prerelease=allow hdhomerun-mcp[mcp]>=1.1.0

FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6 AS runtime-base
ARG HOST=0.0.0.0
ARG PORT=8000
ARG TRANSPORT="stdio"
ARG AUTH_TYPE="none"
ENV HOST=${HOST} \
    PORT=${PORT} \
    TRANSPORT=${TRANSPORT} \
    AUTH_TYPE=${AUTH_TYPE} \
    PYTHONUNBUFFERED=1 \
    PATH="/root/.local/bin:/usr/local/bin:${PATH}" \
    UV_HTTP_TIMEOUT=3600 \
    UV_SYSTEM_PYTHON=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# MCP server image (the only image this connector ships).
FROM runtime-base AS mcp
COPY --from=builder-mcp /usr/local /usr/local
CMD ["hdhomerun-mcp"]
