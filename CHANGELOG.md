# Changelog

All notable changes to Cocotte are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
will follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) once releases start.
No version has been released yet: everything below lives under **Unreleased** and describes the
current state of the `main` branch.

## [Unreleased]

### Added

- **Documentation website**: user, administrator and contributor documentation built with MkDocs
  Material, published to [GitHub Pages](https://jacquesfize.github.io/cocotteapp/), with
  generated screenshots, this changelog and a contributing guide.
- **Recipes**: create and edit recipes by hand (title, description, servings, prep/cook time,
  diet, grouped ingredients with quantities and units, ordered steps, tags); only the author can
  edit or delete a recipe.
- **Recipe media**: photo upload or external image URL, embedded YouTube video
  (privacy-enhanced `youtube-nocookie` player) and source link.
- **PDF export** of a single recipe, and of a whole planned week (week grid followed by every
  recipe in it), rendered server-side with WeasyPrint.
- **Import from a URL**: scrapes the page with `recipe-scrapers` (fetching its `og:image` when
  the scraper finds no picture), parses each ingredient line, matches it against the ingredient
  library (including translated names, so English recipes map onto French ingredients), and
  pre-fills the recipe form for review before anything is saved
  ([#18](https://github.com/jacquesfize/cocotteapp/pull/18)).
- **Cooklang paste mode**: create a recipe by pasting Cooklang markup, parsed server-side through
  `POST /api/recipes/import-cooklang/`, then reviewed in the edit form
  ([#14](https://github.com/jacquesfize/cocotteapp/pull/14)).
- **YouTube recipe importer**: a Claude Code subagent and helper scripts that turn a YouTube
  cooking video's transcript into Cooklang recipes and create them through the API, with the
  video thumbnail as the image ([#22](https://github.com/jacquesfize/cocotteapp/pull/22)).
- **Ingredient mentions in steps**: `@ingredient` references in a step become links to the
  ingredient list ([#6](https://github.com/jacquesfize/cocotteapp/pull/6)), with
  autocomplete over the whole ingredient library and on-the-fly ingredient creation
  ([#8](https://github.com/jacquesfize/cocotteapp/pull/8)).
- **Step timers**: Cooklang durations (`~{10%minutes}`) render as countdown buttons with
  pause/resume/reset, a chime and a browser notification when time is up
  ([#11](https://github.com/jacquesfize/cocotteapp/pull/11)).
- **Recipe versions**: fork any recipe into a labelled variation (e.g. "gluten-free") that stays
  linked to the original ([#13](https://github.com/jacquesfize/cocotteapp/pull/13)).
- **Comments**: anyone can comment on a recipe without an account (rate-limited); the recipe
  author or staff can hide abusive comments
  ([#12](https://github.com/jacquesfize/cocotteapp/pull/12)).
- **Random recipe** page, honouring the same filters as the search, with a direct "add to
  planner" form.
- **Search and filters**: by ingredient, season, diet, preparation/cooking time and carbon
  footprint level, kept in the URL so filtered views can be bookmarked and shared, with
  pagination on recipe and shopping lists
  ([#21](https://github.com/jacquesfize/cocotteapp/pull/21)).
- **Home page** with thematic shortcuts, a seasonal-recipe carousel, the current week at a glance
  and quick actions.
- **Thematic pages** (e.g. "Seasonal produce", "Vegan", "Ready in 30 minutes"): pre-set recipe
  filters stored in the database, seeded by `seed_thematic_pages`, manageable from a staff page
  ([#16](https://github.com/jacquesfize/cocotteapp/pull/16)) and illustrated with an image
  ([#25](https://github.com/jacquesfize/cocotteapp/pull/25)).
- **Weekly meal planner**: Monday-to-Sunday grid, per-meal servings, week navigation.
- **Planner sharing**: share your planner with another user, read-only or read-write
  ([#15](https://github.com/jacquesfize/cocotteapp/pull/15)).
- **Calendar export**: download the week as an `.ics` file or subscribe to a private,
  regenerable calendar feed ([#21](https://github.com/jacquesfize/cocotteapp/pull/21)).
- **Shopping lists** generated from the planned week, ingredients aggregated and scaled to
  servings, with "already owned" check-off and plain-text export.
- **Nutrition tracking**: per-serving macronutrients plus iron, vitamin B12, calcium, omega-3 and
  zinc, with weekly deficiency alerts tuned to the user's diet and activity level (reference
  thresholds seeded by `seed_nutrient_requirements`).
- **Carbon footprint**: every ingredient carries a kg CO2e/kg estimate; recipes and the weekly
  plan show the cumulative impact ([#10](https://github.com/jacquesfize/cocotteapp/pull/10)).
- **Ingredient library** seeded by `seed_common_ingredients` with realistic nutrition, carbon and
  seasonality data, expanded to about 170 ingredients
  ([#19](https://github.com/jacquesfize/cocotteapp/pull/19)).
- **Ingredient data suggestions** from Open Food Facts (nutrition) and Agribalyse (carbon
  footprint) when creating an ingredient
  ([#18](https://github.com/jacquesfize/cocotteapp/pull/18)).
- **Fuzzy, accent-insensitive ingredient search** (PostgreSQL `unaccent` + trigram) and a staff
  page to manage the ingredient library
  ([#21](https://github.com/jacquesfize/cocotteapp/pull/21)).
- **Allergies and intolerances**: the 14 EU allergens plus lactose, declared in the profile;
  recipes show their allergens (derived from ingredients, unverified ingredients flagged), the
  recipe list hides matching recipes by default and the planner warns when one is scheduled
  ([#26](https://github.com/jacquesfize/cocotteapp/pull/26)).
- **Copyright protection for imported recipes**: recipes imported from a URL or a video only
  show their title, source, allergens and carbon footprint publicly unless the importer opts in;
  external images are credited to their source domain
  ([#27](https://github.com/jacquesfize/cocotteapp/pull/27)).
- **Accounts**: registration, email-based login with JWT, password reset by email, account page
  (profile, diet, activity level, password change), full personal data export (ZIP) and account
  deletion.
- **Recipe library export/import** as a ZIP archive (staff can export the whole instance)
  ([#24](https://github.com/jacquesfize/cocotteapp/pull/24)).
- **User administration** page for staff: search, activate/deactivate, grant/revoke staff,
  delete accounts.
- **French/English interface** with a language switcher remembered across visits.
- **Light/dark theme** toggle and accent colour picker
  ([#23](https://github.com/jacquesfize/cocotteapp/pull/23)).
- **Installable PWA** with offline reading of recipes, planner and shopping lists, and offline
  shopping-list check-off replayed when the connection comes back
  ([#2](https://github.com/jacquesfize/cocotteapp/pull/2)).
- **Production deployment** with Docker Compose: Gunicorn backend, Caddy serving the SPA with
  automatic HTTPS, a health-check endpoint, and an overlay to run behind a shared host-level
  Caddy ([#21](https://github.com/jacquesfize/cocotteapp/pull/21)).
- **Bundled SMTP relay**: optional send-only Postfix service (`mail` Compose profile) for
  password-reset emails, with an auto-generated DKIM key, direct delivery or forwarding through
  an SMTP provider, usable in both standalone and shared-proxy modes.
- **Continuous integration**: backend lint and tests, frontend typecheck and unit tests, and a
  Playwright end-to-end job ([#9](https://github.com/jacquesfize/cocotteapp/pull/9)) that
  cleans up the data it creates ([#26](https://github.com/jacquesfize/cocotteapp/pull/26)).

### Changed

- Login and signup are merged into a single split-screen page with tabs, password visibility
  toggle and a "browse without an account" link; logged-out visitors get a login icon button and
  the language picker becomes a flag button available to everyone
  ([#30](https://github.com/jacquesfize/cocotteapp/pull/30)).
- Ingredient quantities are displayed without useless decimals (integer-only units rounded up),
  and unit labels agree with the quantity ("2 pieces", "2 pincées")
  ([#29](https://github.com/jacquesfize/cocotteapp/pull/29)).
- Recipe list rows show diet, total time, servings, carbon footprint, privacy, author, variant
  and tags, with edit/delete buttons for the owner and an "imported by" byline
  ([#28](https://github.com/jacquesfize/cocotteapp/pull/28)).
- Login uses the email address instead of the username (the username remains the public display
  name).
- The home page, recipe list, recipe pages and random recipe are browsable without an account;
  planner, shopping lists and editing still require one.
- Staff members can edit or delete any recipe
  ([#27](https://github.com/jacquesfize/cocotteapp/pull/27)).
- Importing from a URL no longer creates the recipe or its ingredients immediately: it pre-fills
  the form for review ([#18](https://github.com/jacquesfize/cocotteapp/pull/18)).
- The "Import from URL" form is folded behind an "Import" button
  ([#5](https://github.com/jacquesfize/cocotteapp/pull/5)).
- The Django admin moved from `/admin/` to `/django-admin/`
  ([#21](https://github.com/jacquesfize/cocotteapp/pull/21)).
- Visual redesign: warm palette, rounded cards, pill buttons, bottom tab bar on mobile, account
  popover, self-hosted Inter font and Lucide icons on buttons.
- The app is named **Cocotte**, with its own logo and icons.
- The frontend is written in TypeScript, with a `typecheck` step in CI
  ([#4](https://github.com/jacquesfize/cocotteapp/pull/4)).
- Python dependencies are managed with `uv` (`pyproject.toml` + `uv.lock`).

### Fixed

- A PDF export could reveal the full content of a copyright-restricted recipe
  ([#27](https://github.com/jacquesfize/cocotteapp/pull/27)).
- The random recipe page crashed on a copyright-restricted recipe
  ([#28](https://github.com/jacquesfize/cocotteapp/pull/28)).
- The first ingredient appeared empty when editing an existing recipe
  ([#7](https://github.com/jacquesfize/cocotteapp/pull/7)).
- Step timers displayed sub-minute, non-whole-minute and over-an-hour durations incorrectly
  ([#11](https://github.com/jacquesfize/cocotteapp/pull/11)).
- PDF generation failed on macOS because WeasyPrint could not find its native libraries
  ([#17](https://github.com/jacquesfize/cocotteapp/pull/17)).
- Creating two ingredients whose names differ only by case ("Tomate"/"tomate") raised a
  database error.
- The logged-in user's name disappeared from the navigation after a page reload.
- Form labels were not associated with their fields, hurting accessibility.

### Removed

- Celery and Redis: URL import runs synchronously and no background worker is needed any more.
- The separate `requirements/*.txt` files, replaced by `pyproject.toml` and `uv.lock`.

[Unreleased]: https://github.com/jacquesfize/cocotteapp/commits/main
