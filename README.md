# App de gestion de recettes

Backend Django/DRF pour la gestion de recettes : recherche par ingrédients/saison/régime/temps,
planification dans un agenda, génération de listes de courses, import manuel ou depuis une URL.

## Lancer en local (Docker)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

L'API est disponible sur `http://localhost:8000/api/`, l'admin sur `http://localhost:8000/admin/`.

## Lancer en local (sans Docker)

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

## Tests

```bash
cd backend
uv run pytest
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
