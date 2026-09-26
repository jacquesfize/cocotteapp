# Ingredient library

Every recipe ingredient in Cocotte points to a shared **ingredient** record. That record carries
the data behind the app's key features: nutrition values, carbon footprint, seasonality and
allergens. Keeping the library accurate is therefore the most useful curation task for a staff
member.

This page explains the staff **Ingredients** page, every field of the ingredient form, the
**Suggest values** pre-fill, deletion rules and the seeded data.

## Who can do what

| Action | Who |
|---|---|
| Create an ingredient | Any logged-in user, from the recipe form when an ingredient is missing (see [Creating recipes](../user-guide/creating-recipes.md)), and staff from the **Ingredients** page. Recipe imports can also create ingredients automatically. |
| Edit an ingredient | Staff only |
| Delete an ingredient | Staff only, and only when no recipe or shopping list uses it |

Because anyone can create ingredients, and imports create them with minimal data, it is worth
reviewing recently added ingredients from time to time: they often have zero nutrition values,
no carbon footprint and unreviewed allergens.

## Open the Ingredients page

Open the account menu (person icon, top right) and choose **Administration** > **Ingredients**,
or go to `/admin/ingredients`.

![The staff Ingredients page](../assets/screenshots/admin-ingredients.png)

The table shows each ingredient's **Name**, **Category** and **Season** (the abbreviated
peak-season months, or **All year**), with an **Edit** button and a delete button (bin icon). The
list is paginated, 20 ingredients per page.

The **Search** field (placeholder "French or English name...") matches the ingredient name and
its English name. The search ignores case and accents, and tolerates small typos. The search and
page number are kept in the URL.

## Create or edit an ingredient

1. Click **New ingredient** to create one, or **Edit** on a row to modify it. The form opens as
   a dialog (**New ingredient** or **Edit ingredient**).
2. Fill in the fields described below. Optionally click **Suggest values** to pre-fill nutrition
   and carbon data.
3. Click **Create ingredient** (new) or **Save** (edit). **Cancel**, the close button or the
   `Esc` key closes the form without saving.

![The ingredient form](../assets/screenshots/admin-ingredient-modal.png)

### Identity

| Field | Description |
|---|---|
| **Name** | The ingredient's name, as displayed everywhere in the app. It must be unique. By convention the library uses French names (the seeded data does). |
| **English name** | Optional English name. It is used by the ingredient search (so English speakers can find "garlic" as well as "ail") and to match ingredients when importing recipes written in English. Other translations stored on an ingredient (the seeded data also includes German and Spanish names) are kept when you save. |
| **Category** | One of **Vegetable**, **Fruit**, **Legume**, **Grain**, **Nut / seed**, **Dairy**, **Meat / fish**, **Egg**, **Fat**, **Condiment / spice**, **Other**. |
| **Default unit** | The unit pre-selected when the ingredient is added to a recipe: **g**, **kg**, **ml**, **l**, **piece**, **tbsp**, **tsp** or **pinch**. |

### Seasonality

Tick the months when the ingredient is in **peak season**. Leave every month unticked for an
ingredient available all year (pasta, oil, spices...).

The "in season" recipe filter and the seasonal homepage shortcut keep only recipes whose
ingredients are **all** in season in the current month; an all-year ingredient never excludes a
recipe.

### Nutrition facts

All values are **per 100 g** (or per 100 ml for liquids):

| Field | Unit |
|---|---|
| **Calories** | kcal |
| **Protein** | g |
| **Carbs** | g |
| **Fat** | g |
| **Fiber** | g |
| **Iron** | mg |
| **Vitamin B12** | µg |
| **Calcium** | mg |
| **Omega-3** | g |
| **Zinc** | mg |

These values feed the per-serving nutrition of each recipe and the weekly deficiency alerts of
the planner (see [Nutrition & carbon](../user-guide/nutrition-and-carbon.md)).

To compute them, recipe quantities are converted to grams with fixed factors: 1 ml = 1 g,
1 **l** = 1 **kg** = 1000 g, 1 **tbsp** = 15 g, 1 **tsp** = 5 g, 1 **pinch** = 1 g, and 1
**piece** = 100 g. The piece conversion is a rough average; for ingredients usually counted
(eggs, onions...), per-100 g values remain the reference.

### Carbon footprint

**Carbon footprint (kg CO2e / kg)**: the estimated greenhouse-gas emissions of producing one
kilogram (or litre) of the product, in kilograms of CO2 equivalent, from a life-cycle assessment.
This is an order of magnitude, not a measurement. The seeded values come from Agribalyse
(ADEME/INRAE) and Poore & Nemecek (2018).

It is converted with the same unit factors as nutrition to give each recipe's footprint, the
per-serving carbon level shown on recipe cards, and the planner's weekly total.

### Allergens

The **Allergens** section lists the reference allergens: the 14 allergens of EU regulation
1169/2011 (**Gluten**, **Milk**, **Eggs**, **Peanuts**, **Tree nuts**, **Soy**, **Fish**,
**Crustaceans**, **Molluscs**, **Celery**, **Mustard**, **Sesame**, **Sulphites**, **Lupin**)
plus **Lactose**. Tick the ones the ingredient contains.

Below the list, the checkbox **I checked: this ingredient contains none of the listed
allergens** records that the allergens were **reviewed**:

- Ticking at least one allergen automatically marks the ingredient as reviewed (the checkbox is
  then locked).
- For an ingredient without any allergen, tick the checkbox yourself once you have verified it.
  "No allergen ticked" alone means **unknown**, not "allergen-free".

**What users see.** A recipe's allergens are derived from its ingredients. Recipes containing
at least one unreviewed ingredient show **Allergens not verified for some ingredients** next to
their allergen badges. Filters that hide recipes matching a user's allergies only exclude
recipes whose ingredients have that allergen *ticked*: a recipe with unreviewed ingredients is
flagged, never silently treated as safe, but it is not hidden either.

Ingredients created on the fly by users or by recipe imports start unreviewed unless their
creator ticks the box. Reviewing them is the best way to make allergy warnings reliable.

> [!NOTE]
> The allergen list is loaded with the reference data (`seed_allergens`, which
> `seed_common_ingredients` runs automatically). If the **Allergens** section of the form is
> empty, the reference data has not been loaded; see
> [Production deployment](deployment.md#create-the-first-administrator-and-load-reference-data).

## Pre-fill with Suggest values

Next to **Name**, the **Suggest values** button looks the name up in two public databases and
fills the form with what it finds:

| Source | What it provides | How it is queried |
|---|---|---|
| [Open Food Facts](https://world.openfoodfacts.org/) | **Calories**, **Protein**, **Carbs**, **Fat**, **Fiber** (per 100 g) | Search API (`world.openfoodfacts.org/api/v2/search`), first matching product |
| [Agribalyse 3.1](https://agribalyse.ademe.fr/) (ADEME open data) | **Carbon footprint (kg CO2e / kg)**, from the "climate change" indicator | ADEME data API (`data.ademe.fr`, dataset `agribalyse-31-synthese`), first matching line |

Micronutrients (iron, B12, calcium, omega-3, zinc) are never suggested: their units are too
inconsistent in Open Food Facts to be imported safely.

After a click, the form shows either "Suggested values applied — review before creating the
ingredient." or "No suggestion found for this ingredient.". Suggested values **overwrite** the
corresponding fields of the form, and nothing is saved until you click **Create ingredient** or
**Save**.

> [!TIP]
> Both lookups take only the first result, which can be a processed product rather than the raw
> ingredient (Open Food Facts is a database of packaged products). Agribalyse is indexed by French
> product names, so French names give better carbon matches. Always check the values before
> saving.

The lookups are made by the backend, with a 5-second timeout each, so the server needs outgoing
HTTPS access to `world.openfoodfacts.org` and `data.ademe.fr`. If either service is unreachable,
the button simply finds nothing.

## Delete an ingredient

Click the bin icon on the ingredient's row and confirm ("Permanently delete ingredient "…"?").

An ingredient that is still used cannot be deleted: the database protects ingredients referenced
by a recipe or by a shopping-list item. The page then shows "Cannot delete "…": it is used by
recipes or shopping lists. Remove it from them first."

To get rid of a duplicate or misspelled ingredient that is in use:

1. Make sure the correct ingredient exists.
2. Edit each recipe that uses the wrong one and replace it with the correct one. You can find
   those recipes in the Django admin (**Recipes** > **Recipes**, open a recipe to see its
   ingredient lines), or by filtering the recipe list by that ingredient.
3. Shopping lists are snapshots: delete old lists that still contain it, or wait until their
   owners do.
4. Delete the unused ingredient.

## Seeded data

`seed_common_ingredients` loads about 170 common ingredients with realistic nutrition values,
carbon footprint, seasonality, English/German/Spanish names and reviewed allergens. It is run
once at installation (see [Production deployment](deployment.md#create-the-first-administrator-and-load-reference-data)).

Running it again updates the seeded ingredients in place, matching them by name regardless of
case, which also enriches an ingredient that a user had already created under the same name.

> [!WARNING]
> Re-running `seed_common_ingredients` overwrites your edits to seeded ingredients (nutrition,
> carbon, season, category, unit, translations and allergens). See
> [Re-run the seed commands](maintenance.md#re-run-the-seed-commands).

You can also browse and filter the library in the [Django admin](django-admin.md#ingredients),
which offers filters on category, allergens and review status. The review-status filter is a
quick way to list every ingredient whose allergens still need checking.
