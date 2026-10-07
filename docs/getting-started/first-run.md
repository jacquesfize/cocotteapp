# First run

A fresh Cocotte install has an empty database. Before the app is usable, you need to:

1. create the database tables (migrations),
2. create an administrator account,
3. load the reference data (nutrient thresholds, the ingredient library with allergens, and
   the home page shortcuts).

You only do this once. The seed commands are **idempotent**: running them again updates the
data without creating duplicates.

> [!NOTE]
> The **Docker** commands below are for the local development stack (`docker-compose.yml`),
> started as shown in [Installation](installation.md). They run in a second terminal while
> `docker compose up` keeps running. The production stack is covered in
> [Production deployment](../admin-guide/deployment.md).

## 1. Create the database tables

/// tab | Docker

```bash
docker compose exec backend python manage.py migrate
```

///

/// tab | Classic

```bash
cd backend
uv run python manage.py migrate
```

///

> [!NOTE]
> On the development Docker stack, migrations do **not** run automatically: you have to run
> this command yourself, and again after pulling code that adds new migrations. Only the
> production image runs them on start-up.

## 2. Create an administrator account

/// tab | Docker

```bash
docker compose exec backend python manage.py createsuperuser
```

///

/// tab | Classic

```bash
uv run python manage.py createsuperuser
```

///

The command asks for an **email** (this is what you log in with), a **username** (the name
shown in the app) and a password. This account is a *staff* account. It can open the
**Administration** section of the account menu and Django admin at
`http://localhost:8000/django-admin/`. See [Users](../admin-guide/users.md).

## 3. Load the reference data

Run these commands in this order:

/// tab | Docker

```bash
docker compose exec backend python manage.py seed_allergens
docker compose exec backend python manage.py seed_common_ingredients
docker compose exec backend python manage.py seed_cookware
docker compose exec backend python manage.py seed_nutrient_requirements
docker compose exec backend python manage.py seed_thematic_pages
```

///

/// tab | Classic

```bash
uv run python manage.py seed_allergens
uv run python manage.py seed_common_ingredients
uv run python manage.py seed_cookware
uv run python manage.py seed_nutrient_requirements
uv run python manage.py seed_thematic_pages
```

///

| Command | What it loads | Without it… |
|---|---|---|
| `seed_allergens` | The reference list of allergens: the 14 EU allergens plus lactose. | The **Allergies and intolerances** section of the profile and the allergen checkboxes of the ingredient form are empty. |
| `seed_common_ingredients` | A library of common ingredients with nutrition values (per 100 g), carbon footprint (kg CO₂e/kg), seasonality, English names and **checked allergens**. | You would have to create every ingredient by hand, and recipes would show no nutrition or carbon data. |
| `seed_cookware` | About 60 common cookware items (oven, air fryer, pans, dishes, tools) with their English names, emojis and photos downloaded from Wikimedia Commons (needs Internet access; `--skip-images` to skip them). | The cookware picker of the recipe form and the **Cookware** filter start empty; users create items as they go. |
| `seed_nutrient_requirements` | Daily minimums for protein, iron, vitamin B12, calcium, omega-3 and zinc, for every diet type and activity level. | The planner never shows nutrition alerts. |
| `seed_thematic_pages` | Three home page shortcuts: *Produits de saison* (in season), *Spécial végan* and *Prêt en 30 minutes* (30 minutes of prep or less), with their images. | The **Explore** section of the home page stays empty. |

> [!TIP]
> Running a public instance? Fill in the `LEGAL_*` variables and schedule `purge_inactive_users` and `purge_audit_logs`:
> see [GDPR compliance](../admin-guide/gdpr.md).

> [!NOTE]
> `seed_common_ingredients` needs the allergen list to tag ingredients. It runs `seed_allergens`
> itself first, so nothing breaks if you skip that step. Running `seed_allergens` explicitly
> keeps the order clear, and it's also how you get the allergen list alone if you'd rather build
> your own ingredient library from scratch.

> [!TIP]
> Running `seed_common_ingredients` again later is safe. It updates the library entries,
> including ingredients created by users with the same name (case-insensitive match), and
> leaves your other ingredients alone. See [Ingredient library](../admin-guide/ingredients.md).

## 4. Log in

1. Open `http://localhost:5173/`.
2. Click the person icon at the top right. The login page opens.
3. Enter the **email** and **password** of the account you just created, then click
   **Log in** (*Se connecter*).

![The login page, with the Log in / Sign up tabs next to a cover photo](../assets/screenshots/login.png)

After logging in you are taken to the recipe list. It is empty for now: see
[Creating recipes](../user-guide/creating-recipes.md) to add your first one.

## 5. Switch the language

The interface starts in French. To change it:

1. Click the **flag** button in the top bar, between the dice and the moon/sun button.
2. Choose **English** (or **Français** to go back).

This choice is saved in your browser, so you only do it once per device. The same top bar has
the dark mode toggle. See [The interface](../user-guide/index.md#language-and-theme).

## 6. Create more accounts

Anyone who opens the app can create their own account:

1. Click the person icon, then the **Sign up** tab (*Inscription*).
2. Fill in the username, email, password, diet and activity level.
3. Click **Create my account**.

See [Your account](../user-guide/account.md#create-an-account) for details. To give another
person admin rights, see [Users](../admin-guide/users.md).

> [!IMPORTANT]
> In a local setup, password-reset emails are **not sent**. They are printed in the backend
> logs (`docker compose logs -f backend` or the `runserver` terminal). To send real emails,
> configure SMTP as described in [Configuration](../admin-guide/configuration.md).
