FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# libpq-dev/gcc : psycopg ; les autres libs : rendu PDF des recettes/agendas (WeasyPrint,
# qui s'appuie sur Pango/HarfBuzz/fontconfig depuis la version 53, plus besoin de Cairo).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfontconfig1 libglib2.0-0 \
    shared-mime-info fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

# --- Image de développement : dépendances de dev incluses, code monté en volume, runserver.
FROM base AS dev
RUN uv sync --frozen --no-install-project --group dev
COPY . .
RUN uv sync --frozen --group dev
ENV PATH="/app/.venv/bin:$PATH"

# --- Image de production : uniquement les dépendances nécessaires + gunicorn.
FROM base AS prod
RUN uv sync --frozen --no-install-project --no-group dev --extra prod
COPY . .
RUN uv sync --frozen --no-group dev --extra prod
ENV PATH="/app/.venv/bin:$PATH"
ENV DJANGO_SETTINGS_MODULE=config.settings.prod

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--access-logfile", "-", "--error-logfile", "-"]
