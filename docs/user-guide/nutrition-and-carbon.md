# Nutrition & carbon

Cocotte shows nutrition facts and a carbon footprint for every recipe, adds them up in the
planner, and flags possible nutrient shortfalls. This page explains where the numbers come from,
how they are computed, and what their limits are.

> [!IMPORTANT]
> All figures are **estimates** meant to help you compare recipes and spot obvious gaps. They
> are **not medical or dietary advice** and **not a certified carbon audit**. Talk to a health
> professional for personal nutrition needs.

## Where the data comes from

Everything is computed from the **ingredients**. Each ingredient in the library stores:

- nutrition values **per 100 g** (or 100 ml): calories, protein, carbs, fat, fiber, iron,
  vitamin B12, calcium, omega-3 and zinc,
- a **carbon footprint** in kg CO₂e per kg (or litre) of product,
- its **months of peak season**, if any,
- its **allergens**, and whether they have been checked.

The values come from two places:

| Source | Used for |
|---|---|
| The built-in library (`seed_common_ingredients`) | Nutrition rounded from common food composition tables (Ciqual/USDA). Carbon footprint from [Agribalyse](https://agribalyse.ademe.fr/) (ADEME/INRAE) and [Poore & Nemecek (2018)](https://www.science.org/doi/10.1126/science.aaq0216) via [Our World in Data](https://ourworldindata.org/environmental-impacts-of-food). |
| **Suggest values** when a user creates an ingredient | Macronutrients (calories, protein, carbs, fat, fiber) from [Open Food Facts](https://world.openfoodfacts.org/). Carbon footprint from Agribalyse's "climate change" indicator. See [Create a missing ingredient](creating-recipes.md#create-a-missing-ingredient). |

These are category-level averages, not lab measurements or values for a specific producer.
For a food's carbon footprint, the production method (meat and dairy versus plant-based, in
particular) matters far more than transport distance.

> [!WARNING]
> Ingredients created on the fly without values count as zero. The same goes for ingredients
> created automatically by a [Cooklang import](creating-recipes.md#paste-a-cooklang-recipe). A
> recipe that uses them will look lighter and lower-carbon than it really is. Admins can
> complete them in the [Ingredient library](../admin-guide/ingredients.md).

## How per-serving nutrition is computed

For each ingredient line of a recipe:

1. The quantity is converted to grams:

    | Unit | Counted as |
    |---|---|
    | g, ml | 1 g |
    | kg, l | 1,000 g |
    | piece | 100 g |
    | tbsp | 15 g |
    | tsp | 5 g |
    | pinch | 1 g |

2. The grams are multiplied by the ingredient's values per 100 g.
3. All lines are added up for the whole recipe, then divided by the recipe's **servings**.

The recipe page's **Nutrition facts** card shows the result **per serving**: calories, protein,
carbs, fat, iron, vitamin B12, calcium, omega-3 and zinc.

> [!NOTE]
> Liquids are counted with the density of water (1 ml = 1 g), and a *piece* is always 100 g,
> whether it's an egg, a lemon or a pumpkin. For accurate figures, enter quantities in grams
> where you can.

## Carbon footprint

The carbon footprint of a recipe is the sum over its ingredients of:

*quantity in grams × ingredient's kg CO₂e per kg ÷ 1,000*

using the same unit conversion as above. The result is in **kg CO₂e** (kilograms of CO₂
equivalent, which includes other greenhouse gases).

Where you see it:

- the recipe page: **Carbon footprint (per serving)** in the **Nutrition facts** card,
- the recipe list: a leaf badge on each recipe,
- the planner: **This week's carbon footprint** in **Nutritional intake**. It's the total of the
  displayed period, with each meal scaled to its planned servings.

### Carbon levels

The **Carbon impact per serving** filter of the recipe list sorts recipes into three levels
based on their footprint **per serving**:

| Level | Per serving |
|---|---|
| **Low** | 0.5 kg CO₂e or less |
| **Medium** | more than 0.5, up to 1.5 kg CO₂e |
| **High** | more than 1.5 kg CO₂e |

The leaf badge on recipe cards uses the same three colours: green, amber and red.

For comparison, a plant-based main dish is usually in the low band, while a portion of beef
easily reaches the high band.

## Weekly deficiency alerts

> [!NOTE]
> This feature is **off by default** and must be turned on by the instance administrator (see
> [Configuration](../admin-guide/configuration.md#planning-and-nutrition-features)). If it's
> off, the planner's nutritional intake summary never lists any deficiency and the home page's
> badge never appears, regardless of what's planned.

The planner's **Nutritional intake** dialog (and the badge on the home page's **This week**
strip) warns you when your planned meals may not cover some nutrients.

### How it works

1. Cocotte adds up the nutrients of every meal in the displayed period, each scaled by
   *planned servings ÷ recipe servings*.
2. It divides the total by the **number of days in the period**: 7 for a week, or the number of
   days of the month in month view. Days with nothing planned still count.
3. It compares this **daily average** with the daily minimums for your **diet** and **activity
   level** (set in [Your account](account.md#profile)).
4. Each nutrient below its minimum is listed as *average / minimum*.

### The daily minimums

Six nutrients are checked. Calories, carbs, fat and fiber are shown on recipes but not checked.

| Nutrient | Omnivore | Vegetarian | Vegan |
|---|---|---|---|
| Protein | 50 / 65 / 100 g | 50 / 65 / 100 g | 50 / 65 / 100 g |
| Iron | 10 mg (12 mg athlete) | 14 mg (16.8 mg athlete) | 18 mg (21.6 mg athlete) |
| Zinc | 10 mg (12 mg athlete) | 13 mg (15.6 mg athlete) | 13 mg (15.6 mg athlete) |
| Vitamin B12 | 2.4 µg | 2.4 µg | 2.4 µg |
| Calcium | 950 mg | 950 mg | 950 mg |
| Omega-3 | 1.1 g | 1.1 g | 1.1 g |

Protein depends on the activity level: **Sedentary** 50 g, **Moderate** 65 g, **Athlete**
100 g. Iron and zinc are higher for vegetarian and vegan diets, because the body absorbs them
less well from plants. They are also multiplied by 1.2 for athletes.

These thresholds are deliberately simplified. They are loaded by the `seed_nutrient_requirements`
command. If you see no alerts at all, ask your administrator to check that it was run (see
[First run](../getting-started/first-run.md#3-load-the-reference-data)).

> [!TIP]
> Vitamin B12 is almost absent from unfortified plant foods. On a vegan diet, a B12 alert is
> expected unless you plan fortified foods: it's a reminder, not an error.

### Reading the alerts sensibly

- The summary only knows what is **in the planner**. Unplanned breakfasts, snacks and drinks
  aren't counted, so a partly planned week will almost always show alerts.
- Iron, B12, calcium, omega-3 and zinc are only as good as the ingredient data. Ingredients
  created with **Suggest values** have **no** micronutrients unless someone typed them in.
- For a shared agenda, the thresholds of the agenda's **owner** are used.

## Seasonality

Each ingredient can list its months of peak season. An ingredient with no months ticked is
considered **available all year** (most dry goods, dairy, oils and spices in the library).

A recipe is **in season** when **none** of its ingredients is out of season in the current
month. This is used by:

- the **In-season ingredients only** filter of the recipe list and the random recipe,
- the **In season now** section of the home page,
- the *Produits de saison* thematic page.

Cooking with produce that is in season usually means less energy-intensive production and
transport.

## Allergen data

Allergens are attached to **ingredients**. A recipe's allergens are those of its ingredients.
Cocotte knows the 14 allergens that must be declared in the EU plus lactose: gluten, milk,
lactose, eggs, peanuts, tree nuts, soy, fish, crustaceans, molluscs, celery, mustard, sesame,
sulphites and lupin.

Each ingredient also has a **"reviewed"** flag, which says that someone has checked its
allergens:

- Library ingredients are all reviewed. An ingredient with no allergen listed has been checked
  and contains none.
- Ingredients created by users are reviewed only if they have at least one allergen ticked, or
  if the creator ticked **I checked: this ingredient contains none of the listed allergens**.
  Ingredients created by a Cooklang import are never reviewed.

When at least one ingredient of a recipe is **not reviewed**, the recipe shows *Allergens not
verified for some ingredients*. The absence of a badge then proves nothing.

> [!WARNING]
> The **Hide recipes containing my allergens** filter only hides recipes with a **known**
> allergen. Recipes with unverified ingredients are **not** hidden. Processed products
> (stock cubes, sauces, charcuterie…) vary between brands. Allergen information in Cocotte is
> indicative: **always check product labels**.

## Credits

- [Open Food Facts](https://world.openfoodfacts.org/): packaged-product nutrition facts, used to
  suggest macronutrients when creating an ingredient.
- [Agribalyse](https://agribalyse.ademe.fr/) (ADEME/INRAE): life-cycle environmental impact data
  for food products, used for carbon-footprint suggestions and for the seeded ingredient
  library.
- [Poore & Nemecek (2018)](https://www.science.org/doi/10.1126/science.aaq0216), via
  [Our World in Data](https://ourworldindata.org/environmental-impacts-of-food): secondary
  reference for category-level carbon footprint averages in the seeded library.
