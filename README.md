<p align="center">
  <img src="frontend/public/pwa-512.png" width="110" alt="Cocotte logo">
</p>

<h1 align="center">Cocotte</h1>

<p align="center">
  An open-source recipe manager and weekly meal planner that puts nutrition and
  <strong>carbon footprint</strong> right next to every recipe.
</p>

<p align="center">
  <a href="https://github.com/jacquesfize/testrecetteapp/actions/workflows/ci.yml"><img src="https://github.com/jacquesfize/testrecetteapp/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white" alt="Vue 3">
  <img src="https://img.shields.io/badge/Django-5-092E20?logo=django&logoColor=white" alt="Django 5">
</p>

## What is Cocotte?

Cocotte lets you store recipes (written by hand or imported from a URL), search them by ingredient, season, diet or cooking time, and plan them over a week — for yourself or for a household. Each recipe carries its nutritional values and its estimated CO2 impact, and the
weekly planner rolls both up so you can see, at a glance, what a week of meals costs your body and the planet.

#### 💫 Main features

- **Recipe management** — manual entry or import from a URL (image fetched automatically when the source page has one), recipe image/video/source link, PDF export.
- **Recipe versioning** — fork a recipe into a variation (e.g. "gluten-free", "spicier") that stays linked to the original.
- **Search & filters** — by ingredient, season, diet, total time; shareable/bookmarkable filtered URLs; a homepage with themed  shortcuts (seasonal produce, vegan, ready in 30 minutes).
- **Weekly meal planning** — a week grid with per-day and weekly totals for nutrition and carbon footprint, exportable as a single PDF (the week plus every recipe in it).
- **Nutrition tracking** — per-serving macronutrients plus iron, B12, calcium, omega-3 and zinc, with deficiency alerts tuned to your diet type and activity level.
- **Carbon footprint** — every ingredient carries a kg CO2e/kg estimate; recipes and the weekly plan show the cumulative impact.
- **Shopping lists** — generated from your planned meals, ingredients aggregated and scaled to servings.
- **Cooklang-style step links** — reference an ingredient from a recipe step (`@ingredient`) with autocomplete, plus inline cooking timers (`~{10%minutes}`).
- **Accounts & admin** — email-based login, password reset by email, full data export, account deletion, and a staff-only user administration page.
- **Bilingual PWA** — French/English UI, installable, mobile-first, with offline reading and offline shopping-list check-off.

## 🌍 Why this project?

Cocotte is built as a free, open-source alternative focused on
**planning**, not browsing — storing your own recipes (or someone else's household), organizing them into a week, and generating the shopping list that comes out of it.

An important reason is environmental. Diet is one of the largest levers an individual has on their carbon footprint, and that impact is almost never visible at the point where the decision is actually made — while picking what to cook. Cocotte surfaces the carbon footprint of every ingredient and recipe next to its nutrition facts, so a dietary shift (e.g. eating less meat and dairy) is something you can see and track over a week, not an abstract statistic. The season filter pushes the same idea further: cooking with vegetables that are actually in season usually means less energy-intensive production and transport. This environmental dimension is a core design goal of the app, not an add-on.

## 🚀 Get started

Docker Compose is the fastest way to get a full stack (Postgres + backend + frontend) running.

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- Frontend: `http://localhost:5173/`
- API: `http://localhost:8000/api/`
- Django admin: `http://localhost:8000/admin/`

The first time you start the stack, the database is empty — **you must run migrations, create an
admin account, and seed reference data before the app is usable** (nutrient thresholds and the
carbon-footprint ingredient library in particular are what make nutrition/carbon tracking work at
all):

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py seed_nutrient_requirements
docker compose exec backend python manage.py seed_common_ingredients
docker compose exec backend python manage.py seed_thematic_pages
```

All three seed commands are idempotent — safe to re-run any time without duplicating data.

### 🔒 Production deployment

`docker-compose.prod.yml` builds production images (backend served by Gunicorn, frontend built
to static files) behind a Caddy reverse proxy that automatically obtains and renews an HTTPS
certificate (Let's Encrypt). It needs a server with Docker + Docker Compose, a domain whose DNS
(A/AAAA) already points at that server, and ports 80/443 open.

```bash
cp .env.prod.example .env.prod
# edit .env.prod — see the Configuration section below

docker compose -f docker-compose.prod.yml --env-file .env.prod up --build -d

# migrations run automatically on container start; still create the first admin account and seed data:
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python manage.py createsuperuser
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python manage.py seed_nutrient_requirements
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python manage.py seed_common_ingredients
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python manage.py seed_thematic_pages
```

Uploaded images/PDFs (`media/`), static files (`staticfiles/`) and Caddy's certificates
(`caddy_data`) live in named Docker volumes, so they survive a repeated
`docker compose up --build`. `POSTGRES_PASSWORD` and the password embedded in `DATABASE_URL` must
stay identical.

## 🧑‍🍳 How to use it

**Create a recipe.** Either write one by hand (title, servings, prep/cook time, steps,
ingredients) or paste a URL from a supported recipe site — Cocotte scrapes the title, ingredients,
steps and picture automatically, so you can review and adjust before saving. From an existing
recipe you can also create a **version**: a fork (e.g. a gluten-free or spicier variant) that
stays linked to the original so all variations stay discoverable together.

**Add ingredients.** While typing a recipe step, `@ingredient` opens an autocomplete over the
whole ingredient database, not just what's already in the recipe — picking one adds it to the
recipe automatically. If nothing matches, "+ Create" opens a small form (name, category, default
unit, nutrition, carbon footprint) that can pre-fill itself from Open Food Facts and Agribalyse
lookups, so you don't have to hunt down nutrition values by hand.

**Search.** The recipe list filters by ingredient, season, diet and total time, and the current
filters live in the URL — so a filtered view is a link you can bookmark or share. The homepage
also surfaces a few themed shortcuts (seasonal produce, vegan, ready in 30 minutes) that are just
pre-set filters, editable from the Django admin without touching any code.

**Plan your week & shop.** Add recipes to the weekly planner grid, scale servings per meal, and
generate a shopping list from the whole week in one click — ingredients are aggregated and scaled
automatically across every recipe you planned.

**Export PDFs.** Any recipe page has a "Download as PDF" button; the weekly planner has a
"Download the week's PDF" button that bundles the week grid with the full detail of every recipe
in it — handy to print and take to a vegan association, a store, or just the kitchen.

## ⚙️ Configuration

Environment variables read by the backend (`backend/.env` in dev, `.env.prod` for the Docker
production stack — see `backend/.env.example` and `.env.prod.example`):

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | `change-me-in-production` | Django's cryptographic secret key. Always set a long random value outside of local dev. |
| `DEBUG` | `False` | Django debug mode. `.env.example` sets it to `True` for local development. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hostnames the backend will serve. |
| `DATABASE_URL` | `postgres://postgres:postgres@localhost:5432/cocotte` | Postgres connection string (`postgres://user:password@host:port/dbname`). |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated origins allowed to call the API from a browser (the frontend's origin). |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | Django email backend. The console backend prints password-reset emails to the backend logs instead of sending them — fine for dev, must be changed for production. |
| `EMAIL_HOST` | `localhost` | SMTP server host (only used with the SMTP backend). |
| `EMAIL_PORT` | `25` | SMTP server port. |
| `EMAIL_HOST_USER` | *(empty)* | SMTP username. |
| `EMAIL_HOST_PASSWORD` | *(empty)* | SMTP password. |
| `EMAIL_USE_TLS` | `False` | Whether to use TLS for the SMTP connection. |
| `DEFAULT_FROM_EMAIL` | `Cocotte <noreply@cocotte.app>` | "From" address for outgoing emails (password reset, etc.). |
| `FRONTEND_URL` | `http://localhost:5173` | Base URL used to build links sent by email (e.g. the password-reset link). Must point at the public frontend URL in production. |

Production-only variables (`config/settings/prod.py`, `docker-compose.prod.yml`):

| Variable | Default | Description |
|---|---|---|
| `DOMAIN` | *(required)* | Public domain name Caddy requests an HTTPS certificate for and serves the app on. |
| `ACME_EMAIL` | *(required)* | Contact email used for the Let's Encrypt account. |
| `CSRF_TRUSTED_ORIGINS` | *(empty)* | Comma-separated origins allowed to pass Django's CSRF check (your public HTTPS domain). |
| `SECURE_SSL_REDIRECT` | `True` | Redirect all HTTP requests to HTTPS. |
| `SECURE_HSTS_SECONDS` | `604800` (1 week) | How long browsers should remember to only reach the site over HTTPS (HSTS). |
| `POSTGRES_PASSWORD` | *(required)* | Password for the Postgres container's `postgres` user — must match the password embedded in `DATABASE_URL`. |

## 🛠️ Dev mode (without Docker)

### 🐍 Backend

Uses [uv](https://docs.astral.sh/uv/) for dependency management (`pyproject.toml` + `uv.lock`,
no `requirements.txt`):

```bash
cd backend
uv sync --group dev
cp .env.example .env   # point DATABASE_URL at your local Postgres
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py seed_nutrient_requirements
uv run python manage.py seed_common_ingredients
uv run python manage.py seed_thematic_pages
uv run python manage.py runserver
```

Tests and linting:

```bash
uv run pytest                    # full suite
uv run pytest --cov=apps         # with coverage
uv run ruff check .              # lint
```

### 💻 Frontend

Needs the backend running on `:8000` (Vite proxies `/api` there — see `vite.config.js`):

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173/`.

```bash
npm run test:unit                # Vitest
npx playwright install           # once
npm run test:e2e                 # Playwright — needs backend AND frontend already running
npm run build                    # production build
```

## 🙏 Acknowledgments

Cocotte's code, including most of this README, was written with the assistance of AI coding tools (Claude Code) — reviewed and directed by a human, but you should read it with that in mind.

Nutrition and carbon-footprint data come from:

- [Open Food Facts](https://world.openfoodfacts.org/) — packaged-product nutrition facts, used to
  suggest macronutrients when creating an ingredient.
- [Agribalyse](https://agribalyse.ademe.fr/) (ADEME/INRAE) — life-cycle environmental impact data
  for food products, used for carbon-footprint suggestions and as the main source for the seeded
  ingredient library.
- [Poore & Nemecek (2018)](https://www.science.org/doi/10.1126/science.aaq0216), via
  [Our World in Data](https://ourworldindata.org/environmental-impacts-of-food) — used as a
  secondary reference for category-level carbon footprint averages in the seeded ingredient
  library.

These are category-level averages, not lab measurements or a certified carbon audit — production method (meat/dairy vs. plant-based, in particular) dominates a food's carbon footprint far more than transport distance.

Recipe import is powered by [recipe-scrapers](https://github.com/hhursev/recipe-scrapers), and
PDF export by [WeasyPrint](https://weasyprint.org/).
