# App de gestion de recettes

Application de gestion de recettes : recherche par ingrédients/saison/régime/temps, tirage
d'une recette au hasard, planification dans un agenda, génération de listes de courses, import
manuel ou depuis une URL. Backend Django/DRF, frontend Vue 3 — interface traduite (FR/EN) et
responsive (mobile-first, navigation par barre d'onglets en bas d'écran).

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
- `frontend/src/i18n/` : configuration vue-i18n + fichiers de traduction (`locales/fr.json`, `locales/en.json`).

## Internationalisation

L'interface est traduite via [vue-i18n](https://vue-i18n.intlify.dev/). Le sélecteur de langue est
dans la barre de navigation ; le choix est mémorisé dans `localStorage`. Pour ajouter une langue :
créer `frontend/src/i18n/locales/<code>.json` (copier `fr.json` comme base), l'enregistrer dans
`frontend/src/i18n/index.js` (`messages` et `SUPPORTED_LOCALES`).

## Responsive

L'interface est pensée mobile-first (layout en `flex-wrap`, aucune largeur fixe supérieure à un
écran de téléphone, cibles tactiles ≥ 40px). Sous 600px, la navigation passe d'une barre de liens
en haut à une barre d'onglets fixée en bas d'écran (Recettes / Au hasard / Agenda / Courses), le
compte (langue, déconnexion) restant accessible via le bouton rond en haut à droite sur toutes les
tailles d'écran. Testé sur viewport 390×844 (iPhone 12) sans débordement horizontal — voir
`frontend/tests/e2e/i18n-and-responsive.spec.js`.

## Design

Palette chaude (rouge-orangé) et composants inspirés du design iOS récent / d'applications comme
Alan : cartes blanches à coins très arrondis et ombre douce, boutons en pilule, champs de saisie
remplis sans bordure visible. Les tokens de couleur/rayon/ombre sont centralisés dans
`frontend/src/assets/base.css` (`--color-primary`, `--shadow-card`, etc.).
