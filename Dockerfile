# Stage 1 — frontend build
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_FELLOW_API_KEY
ARG VITE_BASE_PATH=/
ARG VITE_API_BASE=/api
ENV VITE_FELLOW_API_KEY=${VITE_FELLOW_API_KEY}
ENV VITE_BASE_PATH=${VITE_BASE_PATH}
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build

# Stage 2 — Python builder
FROM python:3.13-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ src/
RUN uv sync --frozen --no-dev --no-editable

# Stage 3 — runtime
FROM python:3.13-slim

# tmux + Node 22 + Anthropic Claude Code CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    tmux ca-certificates curl \
 && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
 && apt-get install -y --no-install-recommends nodejs \
 && npm install -g @anthropic-ai/claude-code \
 && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home appuser
USER appuser
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist

# Workspace dir for the in-container claude session. The skills/brew/ tree
# from the repo root is copied in alongside so it appears as a project skill.
COPY brew-workspace/ /app/brew-workspace/
COPY skills/brew/ /app/brew-workspace/.claude/skills/brew/

ENV PATH="/app/.venv/bin:$PATH"
ENV BREW_FRONTEND_DIST=/app/frontend/dist
ENV HOME=/home/appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "brew.main:app", "--host", "0.0.0.0", "--port", "8000"]
