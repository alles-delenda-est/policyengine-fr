# syntax=docker/dockerfile:1

FROM node:22-alpine AS ui-builder
WORKDIR /build/ui
COPY ui/package.json ui/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY ui/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STUDIO_UI_DIST=/app/ui/dist \
    PORT=8080 \
    WEB_CONCURRENCY=2 \
    GUNICORN_THREADS=4

RUN groupadd --system app && useradd --system --gid app --home-dir /app --create-home app
WORKDIR /app

COPY pyproject.toml README.md /tmp/src/
COPY policyengine_fr /tmp/src/policyengine_fr
RUN pip install --no-cache-dir /tmp/src "gunicorn>=22,<24" && rm -rf /tmp/src

COPY --from=ui-builder --chown=app:app /build/ui/dist /app/ui/dist

USER app
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8080') + '/api/health', timeout=3).read()"

CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8080} --workers ${WEB_CONCURRENCY:-2} --threads ${GUNICORN_THREADS:-4} --worker-class gthread --preload --timeout 30 --graceful-timeout 15 --access-logfile - --error-logfile - policyengine_fr.studio:application"]
