# Stage 1 — frontend build
FROM node:22-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG VITE_FELLOW_API_KEY
ENV VITE_FELLOW_API_KEY=${VITE_FELLOW_API_KEY}
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

RUN useradd --create-home appuser
USER appuser
WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=frontend-build /app/frontend/dist /app/frontend/dist
ENV PATH="/app/.venv/bin:$PATH"
ENV BREW_FRONTEND_DIST=/app/frontend/dist

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "brew.main:app", "--host", "0.0.0.0", "--port", "8000"]
