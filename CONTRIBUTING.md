# Contributing to Cocotte

Thanks for your interest in Cocotte! Whether you report a bug, fix a typo, translate a string or
build a whole feature, your help is welcome. This guide explains how to get set up, what the
project expects from a pull request, and how to get it merged smoothly.

The full contributor documentation lives on the
[documentation site](https://jacquesfize.github.io/cocotteapp/developer/contributing/); this
file is its entry point.

## Ways to contribute

- **Report a bug or suggest a feature**: open an
  [issue](https://github.com/jacquesfize/cocotteapp/issues/new/choose). For a bug, the issue
  template asks for the steps to reproduce it and the desired behavior; also mention your
  browser/OS (or `docker compose logs` output for a backend error).
- **Fix a bug or build a feature**: open a pull request. For anything bigger than a small fix,
  open an issue first so we can agree on the approach before you spend time on it.
- **Translate**: the interface is available in French and English. Improving wording, fixing a
  translation or adding a new language is a great first contribution, see the
  [translation guide](https://jacquesfize.github.io/cocotteapp/developer/i18n/).
- **Improve the documentation**: every page has an "edit" button; see
  [Writing documentation](https://jacquesfize.github.io/cocotteapp/developer/documentation/).

## Prerequisites

- **Git** and **Git LFS**. Documentation images (`docs/assets/**/*.png`, `.jpg`, ...) are stored
  with Git LFS, as declared in
  [`.gitattributes`](https://github.com/jacquesfize/cocotteapp/blob/main/.gitattributes).
  Run this once per machine, **before cloning**:

  ```bash
  git lfs install
  ```

  If you cloned without LFS, the images are small text "pointer" files instead of pictures; fix
  it with `git lfs install && git lfs pull`.
- **Either Docker** (with Docker Compose), the quickest route,
- **or a native toolchain**: Python 3.11+ with [uv](https://docs.astral.sh/uv/), Node.js 22,
  PostgreSQL 16 and the WeasyPrint system libraries (Pango, HarfBuzz, fontconfig).

The [development environment guide](https://jacquesfize.github.io/cocotteapp/developer/dev-environment/)
walks through both setups, the seed commands and everyday commands.

## Workflow

1. **Fork** the repository and clone your fork (with Git LFS installed).
2. **Create a branch** from an up-to-date `main`, named after the kind of change:

   | Prefix | Use for | Example |
   |---|---|---|
   | `feat/` | a new user-visible feature | `feat/auth-split-page` |
   | `fix/` | a bug fix | `fix/ingredient-picker-edit-mode` |
   | `docs/` | documentation only | `docs/user-documentation` |
   | `chore/` | tooling, refactoring, dependencies | `chore/update-thematic-pages-ux` |
   | `test/` | tests only | `test/e2e-cleanup` |

3. **Set up** your environment and **make your change**, with tests.
4. **Run the checks** below locally.
5. **Update the changelog and the docs** if the change is user-visible.
6. **Push** and open a pull request against `main`, filling in the
   [pull request template](#opening-the-pull-request).

## Checks run by CI

Every push and pull request runs the
[CI workflow](https://github.com/jacquesfize/cocotteapp/blob/main/.github/workflows/ci.yml)
(three jobs), plus the
[Docs workflow](https://github.com/jacquesfize/cocotteapp/blob/main/.github/workflows/docs.yml)
when documentation files change. Run the same commands locally before pushing:

```bash
# Backend (lint + tests with coverage), needs a running PostgreSQL
cd backend
uv run ruff check .
uv run pytest --cov=apps

# Frontend (typecheck + unit tests)
cd frontend
npm run typecheck
npm run test:unit

# End-to-end tests: backend on :8000 and frontend on :5173 must already be running
cd frontend
npx playwright install chromium        # once
E2E_ADMIN_EMAIL=e2e-admin@example.com E2E_ADMIN_PASSWORD=e2e-admin-password npm run test:e2e

# Documentation (only if you touched docs/, mkdocs.yml, CHANGELOG.md or CONTRIBUTING.md)
uvx --with-requirements docs/requirements.txt mkdocs build --strict
```

The end-to-end tests run against a real backend and database, which are **never reset**: a
Playwright fixture deletes what each test creates. Deleting on-the-fly ingredients needs a staff
account, passed through `E2E_ADMIN_EMAIL` / `E2E_ADMIN_PASSWORD` (create one with
`createsuperuser`). See the
[testing guide](https://jacquesfize.github.io/cocotteapp/developer/testing/) for details.

## Code conventions

The [architecture page](https://jacquesfize.github.io/cocotteapp/developer/architecture/)
explains the design in depth. The essentials:

**Backend (Django/DRF, `backend/apps/`)**

- One Django app per domain (`accounts`, `ingredients`, `recipes`, `nutrition`, `planning`,
  `shopping`, `importer`), each with the same shape: `models.py`, `serializers.py`, `views.py`,
  `urls.py`, `filters.py`, `factories.py` and `tests/`.
- Business logic that belongs neither on a model nor in a view/serializer goes into the app's
  `services.py` (e.g. `shopping/services.py`, `nutrition/services.py`).
- Tests use pytest-django and factory-boy: build test data with the app's `factories.py` rather
  than creating model instances by hand.
- Lint with `ruff` (line length 110). Management commands that seed data must stay idempotent.

**Frontend (Vue 3 + TypeScript, `frontend/src/`)**

- Route-level views fetch their own data (`onMounted`/`watch`) through the modules in `src/api/`,
  which all use the shared axios client in `src/api/client.ts`.
- Pinia holds **only** authentication (`stores/auth.ts`). Don't add a global store for recipes,
  planning or shopping data.
- Every user-facing string goes through vue-i18n: add each new key to **both**
  `src/i18n/locales/fr.json` and `src/i18n/locales/en.json`, in the same place.
- Unbounded lists use `components/Pagination.vue` and keep filters and page number in the URL
  query string (see `RecipeListView.vue`).
- Code must pass `npm run typecheck` (`vue-tsc`): no implicit `any`.

> [!WARNING]
> Offline support is deliberately narrow: GET responses are cached for reading, and the **only**
> offline write is checking off a shopping-list item. Don't extend offline writes to other
> mutations without discussing it in an issue first: offline editing of recipes and planning was
> scoped out on purpose (there is no conflict resolution).

## Commit messages

Use short, imperative, [Conventional Commits](https://www.conventionalcommits.org/)-style
subjects, as in the recent history:

```text
feat: add image support to thematic pages
fix: gate PDF export behind recipe content-restriction check
chore: remove celery and redis since it is not used anymore
test: add ingredient creation button interaction and dialog verification
docs: document the development environment
```

Common types are `feat`, `fix`, `chore`, `test`, `docs`, `ci` and `copy` (wording changes). An
optional scope is fine (`feat(auth): ...`). Use the body to explain *why* when it isn't obvious.
English is preferred for new commits.

## Changelog

Every pull request with a **user-visible** change (feature, behaviour change, bug fix, removal)
adds a line to the `## [Unreleased]` section of
[`CHANGELOG.md`](https://github.com/jacquesfize/cocotteapp/blob/main/CHANGELOG.md), under
`Added`, `Changed`, `Fixed` or `Removed`, following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Describe the change from the user's
point of view, in one line, and link the pull request. Pure refactoring, test or CI changes don't
need an entry.

## Documentation and screenshots

If your change affects what users, administrators or contributors see or do, update the matching
page under [`docs/`](https://github.com/jacquesfize/cocotteapp/tree/main/docs) in the same
pull request. If it changes the UI shown in a screenshot, run `npm run docs:screenshots` (against
a running, seeded stack), then commit only the PNGs that cover the feature you changed — not the
whole suite, even though the command regenerates every screenshot. They are stored in Git LFS.
The [documentation guide](https://jacquesfize.github.io/cocotteapp/developer/documentation/)
explains how.

## Opening the pull request

GitHub pre-fills every new pull request with the
[pull request template](https://github.com/jacquesfize/cocotteapp/blob/main/.github/pull_request_template.md).
Please fill it in rather than deleting it:

- **Summary**: what the pull request changes and why, with a link to the related issue if there
  is one (`Fixes #123`).
- **Screenshots**: before/after screenshots or a short clip for UI changes; delete the section
  otherwise.
- **AI assistance**: whether AI wrote the code, and if so, your confirmation that you understand
  it, the starting prompt and optionally the model (see
  [AI-assisted contributions](#ai-assisted-contributions)).

Then tick the template's checklist:

- [ ] Tests added or updated (`uv run pytest`, `npm run test:unit`, e2e if relevant)
- [ ] `uv run ruff check .` and `npm run typecheck` pass
- [ ] New UI strings added to both `fr.json` and `en.json`
- [ ] `CHANGELOG.md` updated under `[Unreleased]` (user-visible changes)
- [ ] Docs updated in `docs/`, and if its UI changed, only the screenshots covering the feature
      this PR changed committed (not the whole suite)

If you're instead reporting a bug or requesting a feature, open an
[issue](https://github.com/jacquesfize/cocotteapp/issues/new/choose) — its template asks for the
bug description, steps to reproduce, and desired behavior.

Before asking for a review, also make sure that:

- the branch is up to date with `main` and has a descriptive name (`feat/…`, `fix/…`, ...);
- new migrations are included and seed commands stay idempotent;
- `mkdocs build --strict` passes if you touched the documentation.

## AI-assisted contributions

AI-assisted pull requests are welcome: Cocotte itself was largely written with AI coding tools
(see the README's acknowledgments), so this is about **transparency, not prohibition**. Just
disclose it in the template's **AI assistance** section:

- whether the code was written with AI: *No*, *Partly* or *Mostly or entirely*;
- if it was, tick the box confirming that you understand all the code and can explain, justify
  and discuss it with the maintainers;
- paste the starting prompt you used;
- optionally, name the model (and tool).

You remain responsible for everything in your pull request, whoever or whatever typed it. Expect
review questions about why the code works the way it does. A pull request whose author can't
explain or discuss its code may be closed.

## Conduct

Be kind and constructive in issues and reviews: everyone here is volunteering their time.
