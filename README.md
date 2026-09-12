# App de gestion de recettes

Application de gestion de recettes : recherche par ingrédients/saison/régime/temps,
planification dans un agenda, génération de listes de courses, import manuel ou depuis une URL.
Backend Django/DRF, frontend Vue 3.

## Lancer en local (Docker)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- API : `http://localhost:8000/api/`, admin : `http://localhost:8000/admin/`
- Frontend : `http://localhost:5173/`

## Backend — lancer en local (sans Docker)

Le projet utilise [uv](https://docs.astral.sh/uv/) pour la gestion des dépendances Python
(`pyproject.toml` + `uv.lock`, pas de `requirements.txt`).

```bash
cd backend
uv sync --group dev
cp .env.example .env  # adapter DATABASE_URL à votre Postgres local
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Tests :

```bash
cd backend
uv run pytest
```

## Frontend — lancer en local (sans Docker)

Le frontend consomme l'API DRF via un proxy Vite (`/api` → `http://localhost:8000`), donc le
backend doit tourner en parallèle.

```bash
cd frontend
npm install
npm run dev
```

Ouvrir `http://localhost:5173/`.

Tests unitaires (Vitest) :

```bash
cd frontend
npm run test:unit
```

Tests end-to-end (Playwright) — nécessite le backend ET le frontend démarrés :

```bash
cd frontend
npx playwright install  # une seule fois
npm run test:e2e
```

## Structure

- `backend/config/` : settings Django (base/dev/prod), urls, Celery.
- `backend/apps/accounts/` : utilisateurs (régime alimentaire, niveau d'activité), auth JWT.
- `backend/apps/ingredients/` : ingrédients, valeurs nutritionnelles, saisonnalité.
- `backend/apps/recipes/` : recettes, ingrédients de recette, étapes, tags, parseur Cooklang.
- `backend/apps/nutrition/` : calcul des apports nutritionnels et détection de carences.
- `backend/apps/planning/` : agenda / planning de repas.
- `backend/apps/shopping/` : génération et export de listes de courses.
- `backend/apps/importer/` : import de recettes depuis une URL (tâche Celery).
- `frontend/src/api/` : client axios + modules par ressource.
- `frontend/src/stores/` : store Pinia (authentification, tokens JWT).
- `frontend/src/views/` : pages (connexion, recettes, agenda, listes de courses).
- `frontend/src/components/` : `IngredientPicker`/`RecipePicker` (recherche + création à la volée).
