# Testing

Cocotte has three layers of automated tests, all run by CI on every push and pull request:

| Layer | Tool | Location | Needs |
|---|---|---|---|
| Backend unit + API tests | pytest, pytest-django, factory-boy | `backend/apps/*/tests/` | PostgreSQL |
| Frontend unit tests | Vitest, @vue/test-utils, jsdom | `frontend/tests/unit/` | nothing |
| End-to-end tests | Playwright (Chromium) | `frontend/tests/e2e/` | running backend + frontend + database |

Plus static checks: `ruff` for Python and `vue-tsc` for TypeScript.

## Backend

### Running the tests

/// tab | Docker

```bash
docker compose exec backend uv run pytest                                  # everything
docker compose exec backend uv run pytest apps/shopping                    # one app
docker compose exec backend uv run pytest apps/shopping/tests/test_api.py  # one file
docker compose exec backend uv run pytest apps/shopping/tests/test_api.py::test_name  # one test
docker compose exec backend uv run pytest -k allergen                      # by keyword
docker compose exec backend uv run pytest --cov=apps                       # with coverage
```

///

/// tab | Classic

```bash
cd backend
uv run pytest                                  # everything
uv run pytest apps/shopping                    # one app
uv run pytest apps/shopping/tests/test_api.py  # one file
uv run pytest apps/shopping/tests/test_api.py::test_name  # one test
uv run pytest -k allergen                      # by keyword
uv run pytest --cov=apps                       # with coverage (as in CI)
uv run pytest --cov=apps --cov-report=html     # browsable report in htmlcov/
```

///

The pytest configuration lives in `backend/pyproject.toml`:

- `DJANGO_SETTINGS_MODULE = "config.settings.dev"`: tests use the same settings as the dev
  server, so they need the PostgreSQL database from `DATABASE_URL` to be reachable (Django
  creates a separate `test_<name>` database, it never touches your dev data).
- `addopts = "--reuse-db"`: the test database is kept between runs to save time. **After adding
  or changing migrations, run once with `--create-db`** to rebuild it.

> [!NOTE]
> Tests need a real PostgreSQL, not SQLite: the models use `ArrayField`, and ingredient search
> relies on the `unaccent` and `pg_trgm` extensions.

### Writing backend tests

- Put tests in the app's `tests/` package, in files named `test_*.py`, as plain functions marked
  with `@pytest.mark.django_db`.
- Build data with the **factories** rather than `Model.objects.create(...)` with every field:
  `UserFactory` (`accounts`), `IngredientFactory` (`ingredients`), `RecipeFactory`,
  `RecipeIngredientFactory`, `RecipeCommentFactory` (`recipes`), `MealPlanEntryFactory`,
  `PlanningShareFactory` (`planning`). Override only the fields the test cares about.
- For API tests, use DRF's `APIClient` and `force_authenticate`:

  ```python
  import pytest
  from rest_framework.test import APIClient

  from apps.accounts.factories import UserFactory
  from apps.recipes.factories import RecipeFactory


  @pytest.mark.django_db
  def test_author_can_delete_own_recipe():
      user = UserFactory()
      recipe = RecipeFactory(author=user)
      client = APIClient()
      client.force_authenticate(user)

      response = client.delete(f"/api/recipes/{recipe.id}/")

      assert response.status_code == 204
  ```

- Test business logic in `services.py` directly (see `shopping/tests/test_services.py`,
  `nutrition/tests/test_services.py`), and keep API tests for permissions, validation and
  response shape.
- Mock external HTTP calls (recipe scraping, Open Food Facts, Agribalyse): tests must not hit the
  network. See `importer/tests/` and `ingredients/tests/test_services.py` for examples.
- Emails sent during a test land in `django.core.mail.outbox` (see the password-reset tests in
  `accounts/tests/test_api.py`).

### Lint

```bash
cd backend
uv run ruff check .            # what CI runs
uv run ruff check . --fix      # apply safe automatic fixes
```

Ruff is configured in `pyproject.toml` (line length 110, Python 3.11 target).

## Frontend unit tests and typecheck

/// tab | Docker

```bash
docker compose exec frontend npm run test:unit
docker compose exec frontend npx vitest run tests/unit/authStore.test.ts   # one file
docker compose exec frontend npm run typecheck
```

///

/// tab | Classic

```bash
cd frontend
npm run test:unit                              # vitest run, all tests/unit/**/*.test.ts
npx vitest run tests/unit/authStore.test.ts    # one file
npx vitest tests/unit/RecipeCard.test.ts       # watch mode while developing
npm run typecheck                              # vue-tsc -b --noEmit
```

///

- Unit tests run in jsdom (configured in the `test` section of `vite.config.ts`) and cover
  components, views (with the API modules mocked), the auth store, utilities (Cooklang parsing,
  dates, formatting, theme) and the offline queue (with `fake-indexeddb`).
- `npm run typecheck` runs `vue-tsc` over the whole project, including tests. `npm run build`
  runs it too, so a type error also breaks the production build.

## End-to-end tests (Playwright)

The e2e suite drives a real Chromium against the **real** stack: the Vite dev server on `:5173`
(`baseURL` in `playwright.config.ts`) proxying to Django on `:8000`, with PostgreSQL behind it.
Nothing is mocked.

### Running them

1. Start the full stack (see [Development environment](dev-environment.md)) and make sure the
   database is migrated. Seed data is recommended.
2. Create a staff account for the test clean-up, once:

    ```bash
    DJANGO_SUPERUSER_USERNAME=e2e-admin DJANGO_SUPERUSER_EMAIL=e2e-admin@example.com \
    DJANGO_SUPERUSER_PASSWORD=e2e-admin-password \
    uv run python manage.py createsuperuser --noinput
    ```

3. Run the tests **from the host** (also with the Docker setup, since both ports are published):

    ```bash
    cd frontend
    npx playwright install chromium     # once
    export E2E_ADMIN_EMAIL=e2e-admin@example.com E2E_ADMIN_PASSWORD=e2e-admin-password
    npm run test:e2e                                      # all specs
    npx playwright test tests/e2e/golden-path.spec.ts     # one file
    npx playwright test --ui                              # interactive UI mode
    npx playwright show-report                            # last HTML report
    ```

Tests run serially (`workers: 1`). Set `PLAYWRIGHT_CHROMIUM_PATH` to use an already-installed
Chromium instead of the one Playwright downloads.

### The database is never reset

The e2e tests share your development database and never wipe it. To stay repeatable, every spec
imports `test` and `expect` from `tests/e2e/fixtures.ts` instead of `@playwright/test`:

```ts
import { expect, test } from './fixtures'
```

That module defines an **automatic `cleanup` fixture** that watches the browser's successful
`POST` responses during the test and, once it ends, deletes what was created:

- **Accounts** registered through `/api/auth/register/` are deleted with
  `DELETE /api/auth/me/`, which cascades to their recipes, planner, shopping lists and shares.
  Passwords changed or reset during the test are tracked too, so the fixture can still log in.
- **Ingredients** created on the fly (`POST /api/ingredients/`) survive their creator's account
  deletion and can only be deleted by staff, so the fixture logs in with
  `E2E_ADMIN_EMAIL` / `E2E_ADMIN_PASSWORD`. Without these variables it prints a warning and
  leaves the ingredients in the database. Seeded ingredients are never touched.

When writing a new spec:

- create a **fresh user per test** (register through the UI or the API) instead of relying on
  existing accounts;
- give created data unique names (e.g. with `Date.now()`), since the database already contains
  data from your own usage;
- if the test creates a new kind of data that doesn't cascade from the user, extend
  `fixtures.ts` to clean it up;
- prefer accessible locators (`getByRole`, `getByLabel`) over CSS selectors. They double as
  accessibility checks.

## Continuous integration

`.github/workflows/ci.yml` runs on every push (all branches) and pull request, with three
parallel jobs:

| Job | Steps |
|---|---|
| `backend-tests` | PostgreSQL 16 service → `uv sync --frozen --group dev` → `uv run ruff check .` → `uv run pytest --cov=apps` |
| `frontend-tests` | Node 22 → `npm ci` → `npm run typecheck` → `npm run test:unit` |
| `e2e-tests` | PostgreSQL 16 → backend deps → `migrate` → `createsuperuser --noinput` (`e2e-admin@example.com`) → `runserver` → `npm ci` → `playwright install --with-deps chromium` → `npm run dev` → wait for `/api/health/` and `:5173` → `npx playwright test` with `E2E_ADMIN_EMAIL`/`E2E_ADMIN_PASSWORD` |

In CI, Playwright retries a failing test twice (`retries: process.env.CI ? 2 : 0`), and the
HTML report is uploaded as the `playwright-report` artifact when the job fails. Download it from
the workflow run page to inspect traces.

A separate workflow, `.github/workflows/docs.yml`, builds the documentation with
`mkdocs build --strict` when documentation files change; see
[Writing documentation](documentation.md).
