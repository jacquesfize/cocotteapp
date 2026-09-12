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

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
cp .env.example .env  # adapter DATABASE_URL à votre Postgres local
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Tests

```bash
cd backend
pytest
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
