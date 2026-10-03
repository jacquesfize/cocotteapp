# Development environment

This page gets you from a fresh clone to a running Cocotte stack you can hack on: a Django/DRF
API on `:8000`, the Vue 3 dev server on `:5173`, and a PostgreSQL database with reference data.

You can run everything in **Docker** (quickest, nothing to install but Docker) or **natively**
("Classic"), which gives faster test runs and better IDE integration. Most commands on this page
come in both flavours: pick the tab that matches your setup.

> [!TIP]
> Just want to *use* Cocotte rather than develop it? See
> [Installation](../getting-started/installation.md) instead.

## Prerequisites

| | Docker | Classic |
|---|---|---|
| Git + [Git LFS](https://git-lfs.com/) | required | required |
| Docker with Docker Compose | required | optional (handy for PostgreSQL only) |
| Python | – | 3.11 or newer |
| [uv](https://docs.astral.sh/uv/) | – | required (no `pip`/`requirements.txt`) |
| Node.js | – | 22 (same as CI and the frontend image) |
| PostgreSQL | – | 16, with the `unaccent` and `pg_trgm` extensions available |
| WeasyPrint system libraries | – | Pango, HarfBuzz, fontconfig (for PDF export) |

Install Git LFS **before** cloning, otherwise the documentation images come down as small text
pointer files:

```bash
git lfs install                     # once per machine
git clone https://github.com/<you>/cocotteapp.git
cd cocotteapp
```

### Native libraries for WeasyPrint (Classic only)

PDF export uses [WeasyPrint](https://weasyprint.org/), which needs a few system libraries. The
backend image installs them in `backend/Dockerfile`; do the same on your machine:

- **Debian/Ubuntu**:

  ```bash
  sudo apt install libpq-dev gcc libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b \
    libfontconfig1 libglib2.0-0 shared-mime-info fonts-liberation
  ```

- **macOS** (Homebrew): `brew install pango`. The settings module
  (`config/settings/base.py`) automatically points `DYLD_FALLBACK_LIBRARY_PATH` at
  `/opt/homebrew/lib` and `/usr/local/lib`, because `uv run` strips `DYLD_*` variables on macOS.

Everything except PDF export works without these libraries.

## 1. Configure the backend

The backend reads its configuration from `backend/.env` (loaded by `django-environ`). Start from
the example file:

```bash
cp backend/.env.example backend/.env
```

/// tab | Docker

The defaults work as is: `DATABASE_URL` points at the `db` service of `docker-compose.yml`.

///

/// tab | Classic

Edit `backend/.env` and point `DATABASE_URL` at your local PostgreSQL (the example uses the
Docker hostname `db`):

```dotenv
DATABASE_URL=postgres://postgres:postgres@localhost:5432/cocotte
```

Create the database first (`createdb cocotte`, or run just the database container with
`docker compose up -d db`, which publishes port 5432 on the host).

///

> [!IMPORTANT]
> Migration `ingredients.0004_search_extensions` runs `CREATE EXTENSION unaccent` and
> `CREATE EXTENSION pg_trgm` (used for fuzzy ingredient search). The database role in
> `DATABASE_URL` must be allowed to create extensions (a superuser, as with the default
> `postgres` user), or a superuser must create both extensions beforehand.

Every variable is documented in [Configuration](../admin-guide/configuration.md). In development
you usually only touch `DATABASE_URL`. Emails (password reset) are printed to the backend console
by default.

## 2. Install dependencies and start the stack

/// tab | Docker

```bash
docker compose up --build
```

This starts three services from `docker-compose.yml` (the **dev** compose file, distinct from
`docker-compose.prod.yml`):

- `db`: PostgreSQL 16, data kept in the `postgres_data` volume, published on `:5432`;
- `backend`: `manage.py runserver` on `:8000`, with `./backend` bind-mounted into the container;
- `frontend`: the Vite dev server on `:5173`, with `./frontend` bind-mounted, proxying the API to
  `http://backend:8000` (`VITE_API_PROXY_TARGET`).

Code edits apply immediately (Django autoreload, Vite hot module replacement). Rebuild with
`docker compose up --build` only after changing dependencies (`pyproject.toml`/`uv.lock` or
`package.json`/`package-lock.json`).

///

/// tab | Classic

Backend, in one terminal:

```bash
cd backend
uv sync --group dev          # creates backend/.venv with runtime + dev dependencies
uv run python manage.py runserver
```

Frontend, in another terminal:

```bash
cd frontend
npm install
npm run dev                  # Vite on http://localhost:5173
```

///

## 3. Initialise the database

A fresh database is empty. Apply the migrations, create an administrator, then load the
reference data: without it, nutrition and carbon tracking have nothing to compute with.

/// tab | Docker

```bash
docker compose exec backend uv run python manage.py migrate
docker compose exec backend uv run python manage.py createsuperuser
docker compose exec backend uv run python manage.py seed_allergens
docker compose exec backend uv run python manage.py seed_common_ingredients
docker compose exec backend uv run python manage.py seed_nutrient_requirements
docker compose exec backend uv run python manage.py seed_thematic_pages
```

///

/// tab | Classic

```bash
cd backend
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py seed_allergens
uv run python manage.py seed_common_ingredients
uv run python manage.py seed_nutrient_requirements
uv run python manage.py seed_thematic_pages
```

///

What each seed command does:

| Command | App | Loads |
|---|---|---|
| `seed_allergens` | `ingredients` | The 14 EU allergens plus lactose (`Allergen` table). |
| `seed_common_ingredients` | `ingredients` | About 170 common ingredients with nutrition values, carbon footprint, seasonality, translations and allergen tags. Runs `seed_allergens` itself first. |
| `seed_nutrient_requirements` | `nutrition` | Daily reference thresholds per diet type and activity level, used for deficiency alerts. |
| `seed_thematic_pages` | `recipes` | The three default home-page thematic pages, with their bundled images. |

All four commands are **idempotent**: re-running them updates existing rows instead of creating
duplicates, and `seed_common_ingredients` enriches an ingredient that was already created by hand
(case-insensitive match) rather than duplicating it. The only ordering constraint is that
ingredients need allergens, which `seed_common_ingredients` handles by calling `seed_allergens`
itself; `seed_allergens` is listed separately so the allergen table can be refreshed on its own.

`createsuperuser` asks for the **email** (the login field), a username (public display name) and
a password. For scripts and CI, use the non-interactive form:

```bash
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_EMAIL=admin@example.com \
DJANGO_SUPERUSER_PASSWORD=admin-password \
uv run python manage.py createsuperuser --noinput
```

## 4. Open the app

| URL | What |
|---|---|
| <http://localhost:5173/> | The Vue app (use this one) |
| <http://localhost:8000/api/> | The DRF API (browsable) |
| <http://localhost:8000/api/health/> | Health check (`{"status": "ok"}`) |
| <http://localhost:5173/django-admin/> | Django admin, through the Vite proxy |

### The Vite proxy

The frontend always calls the API with relative URLs (`/api/...`). In development, Vite forwards
`/api`, `/django-admin`, `/static` and `/media` to the backend (`server.proxy` in
`frontend/vite.config.ts`), exactly like Caddy does in production. The target is
`http://localhost:8000`, or `VITE_API_PROXY_TARGET` when set (the Docker setup uses
`http://backend:8000`). So:

- no CORS configuration is needed in development;
- the backend must be running for the frontend to do anything useful;
- `config/settings/dev.py` trusts `FRONTEND_URL` for CSRF so the Django admin works through the
  proxy on `:5173`.

> [!NOTE]
> The PWA service worker is also active under `npm run dev` (so offline behaviour can be tested
> without a production build). If the app behaves oddly after switching branches, clear the site
> data in your browser's developer tools (*Application → Storage → Clear site data*).

## Everyday commands

/// tab | Docker

```bash
# Backend
docker compose exec backend uv run pytest                     # full test suite
docker compose exec backend uv run pytest apps/shopping       # one app
docker compose exec backend uv run ruff check .               # lint
docker compose exec backend uv run python manage.py makemigrations
docker compose exec backend uv run python manage.py shell

# Frontend
docker compose exec frontend npm run test:unit
docker compose exec frontend npm run typecheck

# Stack
docker compose logs -f backend      # or frontend, db
docker compose restart backend
docker compose down                 # stop, keep the database
```

Playwright end-to-end tests run from the host, not inside the containers: see
[Testing](testing.md).

///

/// tab | Classic

```bash
# Backend (from backend/)
uv run pytest                              # full test suite
uv run pytest apps/shopping                # one app
uv run ruff check .                        # lint
uv run python manage.py makemigrations
uv run python manage.py shell

# Frontend (from frontend/)
npm run test:unit
npm run typecheck
npm run build                              # vue-tsc + production build
```

///

After pulling changes, re-run `migrate` (new migrations) and, when dependencies changed,
`uv sync --group dev` / `npm install` (Classic) or `docker compose up --build` (Docker).

## Resetting the database

The seed commands make a reset cheap. To start over from an empty database:

/// tab | Docker

```bash
docker compose down -v       # removes the postgres_data volume
docker compose up -d
# then repeat step 3 (migrate, createsuperuser, seeds)
```

///

/// tab | Classic

```bash
dropdb cocotte && createdb cocotte
cd backend && uv run python manage.py migrate
# then createsuperuser and the seed commands (step 3)
```

///

Uploaded images are stored under `backend/media/`; delete that folder too for a completely clean
slate.

> [!NOTE]
> The pytest suite uses its own `test_cocotte` database, kept between runs (`--reuse-db`). After
> changing models or migrations, run `uv run pytest --create-db` once to rebuild it.

## IDE tips

- **Python interpreter**: point your editor at `backend/.venv/bin/python` (created by
  `uv sync`). Set the working directory to `backend/` and `DJANGO_SETTINGS_MODULE` to
  `config.settings.dev` for run configurations.
- **Ruff**: install the Ruff extension; it picks up the `[tool.ruff]` section of
  `backend/pyproject.toml` (line length 110).
- **Vue/TypeScript**: use the official Vue extension (Volar) so the editor sees the same types as
  `vue-tsc`.
- **i18n**: the i18n Ally extension (VS Code) shows translations inline from
  `frontend/src/i18n/locales/`.

## Optional: YouTube recipe importer

The repository ships a [Claude Code](https://claude.com/claude-code) subagent,
`.claude/agents/youtube-recipe-importer.md`, that turns a YouTube cooking video into Cocotte
recipes. It relies on two self-contained scripts in `scripts/youtube_recipes/` (run with
`uv run --script`, dependencies declared inline):

- `fetch_transcript.py <url>` prints the video's transcript as JSON;
- `post_cooklang.py recipe.cook --title "…" [--servings N] [--video-url URL] [--dry-run]` logs in
  and creates the recipe through `POST /api/recipes/import-cooklang/`, using the video thumbnail
  as the image.

The agent writes one Cooklang file per recipe found in the transcript, reusing existing
ingredient names, then posts each file. Set the credentials of the account that will own the
recipes in the environment:

```bash
export COCOTTE_EMAIL=you@example.com COCOTTE_PASSWORD=...
export COCOTTE_API=http://localhost:8000/api    # default
```

Recipes created this way carry a source/video URL, so their description and steps stay
restricted to their owner and staff until the owner rewrites them and makes them public from the
edit screen.

## Next steps

- [Architecture](architecture.md): how the code is organised.
- [Testing](testing.md): running and writing tests.
- [How to contribute](contributing.md): the pull-request workflow.
