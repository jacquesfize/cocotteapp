# Creating recipes

You need to be logged in to add recipes. There are three ways to create one:

| Method | Best for | Where |
|---|---|---|
| **Manual entry** | Your own recipes | **Recipes** → **New recipe**, or **New recipe** on the home page |
| **Import from a URL** | A recipe from a cooking website | **Recipes** → **Import**, or **Import** on the home page |
| **Paste Cooklang** | A recipe already written in [Cooklang](https://cooklang.org/) markup | **New recipe** → **Paste Cooklang** tab |

Whichever you choose, you end up in the same recipe form, where you can check and fix everything
before or after saving.

## Write a recipe by hand

1. Click **Recipes** in the top bar, then **New recipe**.
2. Make sure the **Manual entry** tab is selected.
3. Fill in the cards described below.
4. Click **Save**. The recipe page opens.

![The New recipe form](../assets/screenshots/recipe-form.png)

### General information

| Field | Notes |
|---|---|
| **Title** | Required. |
| **Description** | Optional. A few words to introduce the dish. |
| **Servings** | Required, at least 1 (default 4). Quantities in the planner and shopping lists are scaled from this number. |
| **Prep time (min)** | Required (default 10). |
| **Cook time (min)** | Required (default 20). |
| **Diet** | **Omnivore**, **Vegetarian** or **Vegan**. Used by the diet filter. |

> [!NOTE]
> Cocotte doesn't guess the diet from the ingredients. Choose it yourself so that the diet
> filters and thematic pages show the recipe in the right place.

### Ingredients

Each row has three fields:

- **Ingredient**: start typing and pick an ingredient from the suggestions. You can use the
  arrow keys and Enter. The search ignores case and accents, tolerates typos and also finds
  ingredients by their English name.
- **Quantity**: a number. With the **piece** unit, only whole numbers are allowed (switching to
  *piece* rounds the quantity).
- **Unit**: **g**, **kg**, **ml**, **l**, **piece**, **tbsp**, **tsp** or **pinch**.

Click **Add an ingredient** for another row, and the bin button to remove a row.

Every row must have an ingredient picked from the list. Otherwise saving fails with *Select an
ingredient for each row (or remove the row).*

> [!TIP]
> Units affect the nutrition and carbon estimates: Cocotte converts 1 piece to 100 g, 1 tbsp to
> 15 g, 1 tsp to 5 g and 1 pinch to 1 g, and treats 1 ml as 1 g. When you can, prefer grams for
> accurate figures. See [Nutrition & carbon](nutrition-and-carbon.md#how-per-serving-nutrition-is-computed).

### Create a missing ingredient

If the ingredient you need doesn't exist yet, the suggestion list ends with
**+ Create "your text"**. Click it to open the **New ingredient** form:

![The New ingredient form with the Suggest values button](../assets/screenshots/ingredient-create-modal.png)

1. Check the **Name** (pre-filled with what you typed). Optionally add an **English name**.
2. Click **Suggest values** to look the ingredient up online:
    - **Open Food Facts** provides calories, protein, carbs, fat and fiber per 100 g,
    - **Agribalyse** (ADEME) provides the carbon footprint in kg CO₂e per kg.

    If something is found, you see *Suggested values applied — review before creating the
    ingredient.* Otherwise: *No suggestion found for this ingredient.* Suggestions are based on
    the first search result, so always check them.
3. Pick a **Category** and a **Default unit**.
4. Under **Seasonality**, tick the months when it is in season. Leave all months unticked if it
   is available all year.
5. Fill in or correct the **Nutrition facts (per 100 g / 100 ml)**. Iron, vitamin B12, calcium,
   omega-3 and zinc are never suggested: enter them yourself if you know them.
6. Check the **Carbon footprint (kg CO2e / kg)**.
7. Under **Allergens**, tick the allergens it contains. If it contains none, tick **I checked:
   this ingredient contains none of the listed allergens**. Otherwise recipes using it will say
   *Allergens not verified for some ingredients*.
8. Click **Create ingredient**. It's added to the shared library and selected in your row.

> [!IMPORTANT]
> Ingredients are shared by everyone on the instance. Once created, only admins can edit or
> delete them (see [Ingredient library](../admin-guide/ingredients.md)). Take a moment to get
> the name and values right.

### Steps

Each step is a text box. Click **Add a step** to add one, and the bin button to remove one.
Empty steps are ignored when saving.

The two buttons next to each step insert special markup:

| Button | Inserts | Result on the recipe page |
|---|---|---|
| **Ingredient** | `@` and opens the ingredient suggestions | A highlighted link to the ingredient in the list |
| **Duration** | `~{10%minutes}` with `10` selected, ready to overwrite | A timer button |

#### Link an ingredient with `@`

Type `@` followed by the start of an ingredient's name, for example `@oign`. A list of
matching ingredients from the whole library appears:

- Pick one: Cocotte writes it as a mention (for example `@oignon`). **If the ingredient isn't in
  the recipe yet, it's added to the ingredient list automatically** with its default unit. Don't
  forget to fill in its quantity.
- If nothing fits, **+ Create "…"** opens the [New ingredient](#create-a-missing-ingredient)
  form.

![Typing @ in a step opens the ingredient suggestions](../assets/screenshots/recipe-form-mention.png)

Rules of the syntax:

- A mention ends at the first space. **Multi-word names use underscores** instead of spaces:
  `@huile_olive` refers to *huile olive*, and `@creme_fraiche` to *creme fraiche*. Cocotte
  inserts the underscores for you when you pick a suggestion.
- The name must match the ingredient's name in the list (case doesn't matter). Otherwise a
  warning appears under the step: *"name" isn't in the ingredient list above.* The step still
  saves, but the mention won't be a link.
- You can add a quantity in braces, as in Cooklang: `@huile_olive{2%tbsp}`. In manual entry the
  braces are accepted and hidden on the recipe page, but **quantities come from the Ingredients
  card**, not from the step.

Example:

```text
Faire revenir l'@oignon dans l'@huile_olive, puis ajouter les @tomates.
```

#### Add a timer with `~`

Write a duration as `~{quantity%unit}`, for example:

```text
Laisser mijoter ~{20%minutes}, puis laisser reposer ~repos{1%heure}.
```

- The unit can be seconds (`s`, `sec`, `seconds`, `secondes`…), minutes (`m`, `min`,
  `minutes`…) or hours (`h`, `hr`, `hours`, `heure`, `heures`…), in French or English.
- Decimals work with a dot or a comma (`~{1,5%h}`).
- An optional name before the braces (`~repos{…}`) is shown on the timer button. Use
  underscores for several words.
- If the unit isn't recognised, the text is shown as-is, without a timer button.

See [Use a step timer](browsing-recipes.md#use-a-step-timer) for how timers work when cooking.

### Media & source

| Field | Notes |
|---|---|
| **Image URL** | Link to a picture on the web. |
| **Or upload a file** | Upload a picture from your device. An uploaded file is shown instead of the image URL. |
| **Source (link to the original recipe)** | Where the recipe comes from. Shown as a **Source** button on the recipe page. |
| **Video (YouTube link)** | A YouTube link, for example `https://www.youtube.com/watch?v=…`. The video is embedded on the recipe page. |

#### Publicly licensed content

As soon as a **Source** is filled in, a **Make this recipe's content public** checkbox
appears.

By default, a recipe with a source only shows its title, picture, source link, allergens and
carbon footprint to other people. Its **description, ingredients and steps stay visible only to
you and to admins**, out of respect for the original author's copyright. See
[Recipes with restricted content](browsing-recipes.md#recipes-with-restricted-content).

Tick the box only if you own the rights to this content, or have explicit permission to share
it. Then everyone can see the full recipe.

## Import a recipe from a URL

Cocotte can read recipes from many cooking websites (the ones supported by
[recipe-scrapers](https://github.com/hhursev/recipe-scrapers)).

1. On the **Recipes** page, click **Import**. On the home page, **Import** opens the same form
   in a dialog.
2. Paste the recipe's address in **Import from a URL**.
3. Click **Import** and wait a few seconds.

![The Import from a URL dialog opened from the home page, with a recipe address pasted in](../assets/screenshots/recipe-import-url.png)

Cocotte reads the page and opens the **New recipe** form pre-filled with:

- the title, servings and cook time,
- the picture (from the recipe data, or the page's preview image),
- the source link,
- the steps,
- the ingredients, each **matched with the ingredient library** when possible, in French or
  English.

**Nothing is saved yet.** Review the form:

1. Look for rows with a **Not found** badge, followed by the original line from the website (for
   example *Not found — « 2 gousses d'ail »*). No ingredient could be matched for those rows.
   Pick the right one in the **Ingredient** field, or create it with **+ Create**. You can also
   remove the row.
2. Check the quantities and units. Unusual formats may be misread.
3. Fill in what import doesn't provide: description, **prep time**, **diet**.
4. Click **Save**.

If the page can't be read, you see *Couldn't fetch this recipe. Check the URL and try again.*

> [!NOTE]
> Imported recipes keep the source link, so their content is
> [restricted](browsing-recipes.md#recipes-with-restricted-content) by default. Other people
> see *imported by* followed by your name.

## Paste a Cooklang recipe

[Cooklang](https://cooklang.org/) is a simple markup for recipes. Cocotte understands a subset of
it.

1. Click **New recipe**, then the **Paste Cooklang** tab.
2. Enter the **Title** and **Servings**.
3. Paste your text in **Cooklang text**.
4. Click **Import**.

![The Paste Cooklang tab](../assets/screenshots/recipe-form-cooklang.png)

The syntax Cocotte understands:

| Syntax | Meaning |
|---|---|
| `@name` | An ingredient (one word). |
| `@huile_olive{2%tbsp}` | An ingredient with a quantity and unit. Use underscores for multi-word names. |
| `@oignon{1}` | A quantity without unit. |
| `~{10%minutes}`, `~repos{1%heure}` | A timer. |
| `#poele` | Cookware. It's shown as plain text in the step. |
| A line starting with `--` | A comment, ignored. |
| Each other non-empty line | One step. |

Example:

```text
Faire revenir l'@oignon{1%pièce} dans l'@huile_olive{2%cs} pendant ~{5%minutes}.
Ajouter les @tomates{400%g} et laisser mijoter ~{20%minutes}.
-- Astuce : on peut ajouter du basilic à la fin.
```

What happens on import:

- The recipe is **created immediately**, and its edit form opens so you can check it.
- Units are mapped to Cocotte's units. French and English abbreviations work: `g`, `kg`, `ml`,
  `l`, `cs`/`c.à.s`/`tbsp`, `cc`/`c.à.c`/`tsp`, `pincée`/`pinch`, `pièce`/`piece`… A missing or
  unknown unit becomes **piece**. A quantity that isn't a plain number (`1/2`, `2-3`,
  `quelques`) becomes **1**.
- Each ingredient is looked up by exact name (case-insensitive). **If it doesn't exist, it's
  created with no nutrition, carbon or allergen data.** Ask an admin to complete it, or pick an
  existing ingredient in the edit form instead.
- Mentioning the same ingredient again without a quantity doesn't create a duplicate row.
- Prep time, cook time and diet keep their default values (10 min, 20 min, Omnivore). Adjust
  them in the edit form.

## Edit or delete a recipe

You can edit and delete **your own** recipes:

- **Edit**: open the recipe and choose **⋮** → **Edit**, or click the pencil button on its row in
  the recipe list. The same form opens, titled **Edit recipe**. Make your changes and click
  **Save**.
- **Delete**: open the recipe and choose **⋮** → **Delete**, or click the bin button on its row.
  Confirm the prompt.

> [!WARNING]
> Deleting a recipe also removes it from every planner it was scheduled in, including other
> people's. Existing variants are kept but no longer linked to it.

To make your own version of someone else's recipe, create a
[variant](browsing-recipes.md#versions-and-variants) instead.
