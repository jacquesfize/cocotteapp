<p align="center">
  <img src="frontend/public/pwa-512.png" width="110" alt="Cocotte logo">
</p>

<h1 align="center">Cocotte</h1>

<p align="center">
  An open-source recipe manager and weekly meal planner that puts nutrition and
  <strong>carbon footprint</strong> right next to every recipe.
</p>

<p align="center">
  <a href="https://github.com/jacquesfize/cocotteapp/actions/workflows/ci.yml"><img src="https://github.com/jacquesfize/cocotteapp/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <img src="https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/Vue-3-4FC08D?logo=vue.js&logoColor=white" alt="Vue 3">
  <img src="https://img.shields.io/badge/Django-5-092E20?logo=django&logoColor=white" alt="Django 5">
  <a href="https://jacquesfize.github.io/cocotteapp/"><img src="https://img.shields.io/badge/docs-online-FF6A3D?logo=materialformkdocs&logoColor=white" alt="Documentation"></a>
</p>

> 📖 **Documentation:** the full user, administrator and contributor guide lives at
> **[jacquesfize.github.io/cocotteapp](https://jacquesfize.github.io/cocotteapp/)**
> (sources in [`docs/`](docs/)).

## What is Cocotte?

Cocotte lets you store recipes (written by hand or imported from a URL), search them by ingredient, season, diet or cooking time, and plan them over a week — for yourself or for a household. Each recipe carries its nutritional values and its estimated CO2 impact, and the
weekly planner rolls both up so you can see, at a glance, what a week of meals costs your body and the planet.

#### 💫 Main features

- **Recipe management** — manual entry or import from a URL (image fetched automatically when the source page has one), recipe image/video/source link, PDF export.
- **Recipe versioning** — fork a recipe into a variation (e.g. "gluten-free", "spicier") that stays linked to the original.
- **Search & filters** — by ingredient, season, diet, total time; shareable/bookmarkable filtered URLs; a homepage with themed  shortcuts (seasonal produce, vegan, ready in 30 minutes).
- **Weekly meal planning** — a week grid with per-day and weekly totals for nutrition and carbon footprint, exportable as a single PDF (the week plus every recipe in it).
- **Allergies & intolerances** — declare them in your profile (the 14 EU allergens plus lactose, each tagged as *allergy* or *intolerance*); recipes show their allergens, the list hides matching recipes by default, and the planner warns when you schedule one. Allergens come from the ingredients; an ingredient without verified allergen data is flagged as such (never silently treated as safe). Indicative only — always check product labels.
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

## 🚀 Quick start

The fastest way to try Cocotte is Docker Compose (Postgres + backend + frontend):

```bash
cp backend/.env.example backend/.env
docker compose up --build

# in a second terminal, the first time only
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py seed_allergens
docker compose exec backend python manage.py seed_common_ingredients
docker compose exec backend python manage.py seed_nutrient_requirements
docker compose exec backend python manage.py seed_thematic_pages
```

Then open <http://localhost:5173/>. Installing without Docker (uv + npm + local Postgres) is
covered in the [installation guide](https://jacquesfize.github.io/cocotteapp/getting-started/installation/).

## 📖 Documentation

| I want to… | Read |
|---|---|
| Install Cocotte and load its reference data | [Getting started](https://jacquesfize.github.io/cocotteapp/getting-started/installation/) |
| Learn how to use the app (recipes, planning, shopping, offline…) | [User guide](https://jacquesfize.github.io/cocotteapp/user-guide/) |
| Deploy to production (Docker standalone, behind a shared proxy, or classic) | [Production deployment](https://jacquesfize.github.io/cocotteapp/admin-guide/deployment/) |
| Look up an environment variable | [Configuration](https://jacquesfize.github.io/cocotteapp/admin-guide/configuration/) |
| Update, back up or monitor an instance | [Maintenance](https://jacquesfize.github.io/cocotteapp/admin-guide/maintenance/) |
| Set up a dev environment, run the tests, understand the architecture | [Contributing](https://jacquesfize.github.io/cocotteapp/developer/dev-environment/) |

The documentation sources live in [`docs/`](docs/) and are readable directly on GitHub.

## 🙏 Acknowledgments

Cocotte's code, including most of this README, was written with the assistance of AI coding tools (Claude Code) — reviewed and directed by a human, but you should read it with that in mind.

Nutrition and carbon-footprint data come from:

- [Open Food Facts](https://world.openfoodfacts.org/) — packaged-product nutrition facts, used to
  suggest macronutrients when creating an ingredient.
- [Ciqual](https://ciqual.anses.fr/) (ANSES) and USDA food composition tables — rounded nutrition
  values of the seeded ingredient library.
- [Agribalyse](https://agribalyse.ademe.fr/) (ADEME/INRAE) — life-cycle environmental impact data
  for food products, used for carbon-footprint suggestions and as the main source for the carbon
  values of the seeded ingredient library.
- [Poore & Nemecek (2018)](https://www.science.org/doi/10.1126/science.aaq0216), via
  [Our World in Data](https://ourworldindata.org/environmental-impacts-of-food) — used as a
  secondary reference for category-level carbon footprint averages in the seeded ingredient
  library.

These are category-level averages, not lab measurements or a certified carbon audit — production method (meat/dairy vs. plant-based, in particular) dominates a food's carbon footprint far more than transport distance.

Recipe import is powered by [recipe-scrapers](https://github.com/hhursev/recipe-scrapers), and
PDF export by [WeasyPrint](https://weasyprint.org/).

## 🤝 Contributing

Contributions are welcome! Read [CONTRIBUTING.md](CONTRIBUTING.md) to get started, and see
[CHANGELOG.md](CHANGELOG.md) for what has changed.
