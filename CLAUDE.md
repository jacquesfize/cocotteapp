# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Cocotte: a recipe-management app (recipe search/filters, weekly meal planning with nutrition
tracking, shopping-list generation, recipe import from a URL or manual/Cooklang entry, PDF export,
account management, admin). Django/DRF backend, Vue 3 frontend, French/English UI, PWA with
limited offline support. See `docs/` (published with GitHub Pages) for full user, admin and contributor documentation
(nutrition rules, pagination, i18n, PWA/offline behavior, deployment, etc.) — this file focuses on
commands and architecture rather than duplicating it.

## Commands

### Backend (`backend/`, uses `uv`, not pip/requirements.txt)

```bash
cd backend
uv sync --group dev                          # install deps
cp .env.example .env                         # set DATABASE_URL for your local Postgres
uv run python manage.py migrate
uv run python manage.py runserver

uv run pytest                                # full test suite
uv run pytest apps/shopping/tests/test_api.py       # single file
uv run pytest apps/shopping/tests/test_api.py::test_name  # single test
uv run pytest --cov=apps                     # with coverage (used in CI)
uv run ruff check .                          # lint (used in CI)
```

Tests use `pytest-django` with `--reuse-db` (see `pyproject.toml`); `DJANGO_SETTINGS_MODULE` is
`config.settings.dev` for both running the dev server and running tests. Model factories live in
each app's `factories.py` (factory-boy).

Seed commands (idempotent, run after the first migration):

```bash
uv run python manage.py seed_nutrient_requirements   # reference nutrient thresholds
uv run python manage.py seed_common_ingredients       # ingredient library with real nutrition data
uv run python manage.py seed_thematic_pages           # homepage thematic shortcuts
```

### Frontend (`frontend/`)

```bash
cd frontend
npm install
npm run dev                    # Vite dev server on :5173, proxies /api to :8000

npm run test:unit              # Vitest, all files under tests/unit/
npx vitest run tests/unit/authStore.test.js   # single file
npm run test:e2e               # Playwright — requires backend AND frontend already running
npx playwright test tests/e2e/golden-path.spec.js   # single e2e file

npm run build                  # production build (also runs vite-plugin-pwa's generateSW)
```

The frontend needs the Django backend running on `:8000` (see `server.proxy` in
`vite.config.js`) for both dev and e2e tests — e2e tests are not mocked, they hit a real backend
and Postgres.

### Docker (full stack)

```bash
cp backend/.env.example backend/.env
docker compose up --build      # backend :8000, frontend :5173
```

`docker-compose.prod.yml` is the production stack (`db`, `backend` on Gunicorn, `frontend`) and
is **standalone by default**: `frontend` runs Caddy (not nginx) as its `prod` target, so the same
container serves the built static SPA, reverse-proxies `/api` and `/django-admin` to `backend`, *and*
terminates TLS — it publishes `80`/`443` directly and obtains/renews its own Let's Encrypt
certificate for `DOMAIN`/`ACME_EMAIL`, using `deploy/Caddyfile.standalone` (bind-mounted, not
baked into the image, so it's editable without a rebuild). Use this mode when the app is the
only thing on the server.

The `docker-compose.prod.proxy.yml` overlay switches `frontend` to sit behind a *shared*,
host-level Caddy instead (one per server, its own stack, handling Let's Encrypt for every app on
the box): it swaps in `deploy/Caddyfile.proxy` (plain HTTP, no TLS — it always assumes whatever
sits in front of it, standalone or host Caddy, has already terminated TLS), drops the published
ports, and joins an external Docker network (name set by `PROXY_NETWORK_NAME`, default `proxy`)
on which the host Caddy also sits, reaching this stack as `cocotte-frontend`. Use this mode when
several apps share one host Caddy. See `docs/admin-guide/deployment.md` for the exact commands
and required `.env.prod` variables per mode.

## Architecture

### Backend: one Django app per domain, consistent internal shape

`backend/apps/{accounts,ingredients,recipes,nutrition,planning,shopping,importer}/` each
generally contain `models.py`, `serializers.py`, `views.py`, `urls.py`, `filters.py`,
`factories.py` (test factories), and `tests/`. Business logic that doesn't belong on a model or
in a view/serializer lives in a `services.py` (e.g. `shopping/services.py` aggregates recipe
ingredients scaled by `entry.servings / recipe.servings` into a `ShoppingList`;
`nutrition/services.py` computes per-serving nutrition and weekly deficiency alerts by diet/
activity level). All app URLs are mounted under `/api/` in `config/urls.py`; auth token endpoints
(`/api/auth/token/`, `/api/auth/token/refresh/`) are wired directly there via SimpleJWT views
rather than through `apps.accounts.urls`.

Key cross-app relationships: `Recipe` (`recipes`) has `RecipeIngredient` rows pointing at
`Ingredient` (`ingredients`, which carries nutrition values + seasonality); `MealPlanEntry`
(`planning`) references a `Recipe` for a given date/meal/servings; `ShoppingList` (`shopping`) is
built from a set of `MealPlanEntry` and aggregates their ingredients. `User` (`accounts`) extends
`AbstractUser` with `USERNAME_FIELD = "email"` (login is by email; `username` is kept only as a
display identifier and is still required at registration) plus `diet_type`/`activity_level`,
which drive the nutrition-deficiency thresholds.

Recipe import has two independent paths: `apps.importer` scrapes a given URL (via
`recipe_scrapers`, synchronously in the request/response cycle, and also fetches the source's
og:image when available) into a normal `Recipe`; `apps/recipes/cooklang.py` is a self-contained parser for a small subset of
the Cooklang markup language (`@ingredient`, multi-word names joined with an underscore, e.g.
`huile_olive`) with its own tests — nothing currently sets `SourceType.COOKLANG` or calls this
parser, so treat it as dormant rather than wired into any view. The frontend independently
reimplements the same `@mention` regex client-side
(`frontend/src/utils/cooklangMentions.ts`) to let a recipe step reference one of the recipe's own
ingredients (autocomplete while typing `@` in `CooklangStepInput.vue`, a highlighted link back to
the ingredient in `RecipeSummary.vue`) — the two parsers are independent, not sharing code, and
only the frontend one is actually exercised by the app today.

PDF export (recipe or full week) uses WeasyPrint rendering server-side HTML templates
(`apps/recipes/templates/pdf/recipe.html`, `apps/planning/templates/pdf/week.html`), not a
client-side PDF library.

Settings are split `config/settings/{base,dev,prod}.py`, driven by env vars via `django-environ`
(`DATABASE_URL`, `DJANGO_SECRET_KEY`, `EMAIL_*`, `FRONTEND_URL` — the last is used to build
password-reset links). `EMAIL_BACKEND` defaults to the console backend in dev.

### Frontend: views own their data fetching, Pinia only holds auth

`frontend/src/views/` are route-level components that fetch their own data in `onMounted`/
`watch` via `frontend/src/api/*` (one module per backend resource, all built on the shared axios
instance in `api/client.js`, which attaches the JWT bearer token and transparently retries once
on a 401 after refreshing it via `authStore.refreshAccessToken()`). The only Pinia store is
`stores/auth.js` (tokens + current user) — there's no global store for recipes/planning/shopping
data.

Routing (`src/router/index.js`) uses two route-meta flags checked in a single global
`beforeEach`: `meta.public` (skip the auth redirect) and `meta.requiresStaff` (client-side hint
only — the API itself enforces staff-only access; the guard just avoids flashing a page before
redirecting).

List views that can grow unbounded (recipes, shopping lists) share `components/Pagination.vue`
and keep both filters and the current page number in the URL query string (so filtered/paginated
views are shareable/bookmarkable) — see `RecipeListView.vue` for the pattern (`filters`/`page`
refs synced from `route.query`, `router.replace` after each fetch).

Offline support (`src/offline/db.js`, `src/offline/sync.js`) is deliberately narrow: Workbox
(configured in `vite.config.js`, active under both `vite dev` and production build) caches GET
responses for read-only offline access; the *only* offline write path is marking a shopping-list
item as owned, via an optimistic UI update + an IndexedDB queue replayed on the `online` event.
Don't extend this pattern to other mutations without re-reading `docs/user-guide/offline-and-install.md` — offline editing of recipes/planning was deliberately scoped out (no conflict
resolution for a single-user app).

i18n (`src/i18n/`) uses vue-i18n with `locales/fr.json`/`locales/en.json` kept in lockstep — when
adding a user-facing string, add the key to both files.

## Documentation

User, admin and contributor docs live in `docs/` (MkDocs Material, nav in `mkdocs.yml`), are
published to GitHub Pages by `.github/workflows/docs.yml`, and must stay readable in GitHub's
file browser. **Every new feature or fix must update the documentation when it changes
something a user, admin or contributor sees or does** — in the same PR, not later:

- the matching page(s) in `docs/user-guide/`, `docs/admin-guide/`, `docs/getting-started/` or
  `docs/developer/` (new UI labels quoted exactly as in `locales/en.json`; new env vars in
  `admin-guide/configuration.md`; new management commands in `getting-started/first-run.md` and
  `admin-guide/deployment.md`);
- an entry under `## [Unreleased]` in `CHANGELOG.md` for any user-visible change;
- regenerated screenshots, but **only the ones showing the feature you actually changed**, never
  speculatively. From `frontend/`, against the already-running, seeded dev stack:

  ```bash
  E2E_ADMIN_EMAIL=e2e-admin@example.com E2E_ADMIN_PASSWORD=e2e-admin-password \
    SHOTS=recipe-list,recipe-list-filters npm run docs:screenshots
  ```

  `SHOTS` (comma-separated screenshot names, no `.png`) is the key lever: the full
  `tests/docs/screenshots.spec.ts` scenario always runs end to end regardless, but only the
  listed files are written/compressed — everything else in `docs/assets/screenshots/` is left
  untouched, so there's nothing to filter out of `git status` afterward and no needless Git LFS
  churn. Map your change to screenshot names by grepping `shotPage`/`shotElement`/`shotAround`
  calls in `screenshots.spec.ts` and checking which view/component renders that screen (e.g.
  `RecipeCard.vue` → `recipe-list` via `RecipeListView.vue`/`HomeView.vue`); when a component is
  shared, check every page that renders it, not just the one you were looking at.
  `E2E_ADMIN_EMAIL`/`E2E_ADMIN_PASSWORD` log into the admin screenshots and are needed for
  clean-up even when your change isn't admin-related — the dev stack already has this account
  seeded with the credentials above. Omitting `SHOTS` regenerates every PNG instead (only do
  this when you're unsure of the blast radius); in that case `git status
  docs/assets/screenshots/` and stage only the files whose feature you touched — small rendering
  noise (fonts, anti-aliasing) can flag unrelated images as changed even though nothing about
  them actually did. See "When to regenerate" in `docs/developer/documentation.md`.

Authoring conventions (see `docs/developer/documentation.md`): relative `.md` links, GitHub
alerts (`> [!NOTE]`) for callouts, `/// tab | Docker` / `/// tab | Classic` blocks for command
variants. Check with `uvx --with-requirements docs/requirements.txt mkdocs build --strict`.
