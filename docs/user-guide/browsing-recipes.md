# Browsing recipes

This page shows how to find recipes and read them: the home page, the recipe list and its
filters, the random recipe, and the recipe page with its timers, nutrition facts, PDF download,
variants and comments. You don't need an account for any of this.

## The home page

Click **Home** (or the Cocotte logo) to open the home page.

![The home page of a logged-in user](../assets/screenshots/home.png)

From top to bottom:

**Quick actions**
:   Logged-in users get a **New recipe** button that opens a small menu with two choices:
    **Create manually** (the blank recipe form) or **Import from a URL** (see
    [Creating recipes](creating-recipes.md#import-a-recipe-from-a-url)). Visitors get **Sign up**
    instead. The recipe list itself is always reachable from **Recipes** in the main navigation,
    so there's no separate "browse recipes" button here.

**Today's pick**
:   One of your 5 most recent recipes, with its picture, diet, total time and servings. It
    auto-advances every few seconds; the dots below it jump straight to one and pause the
    auto-advance while you're looking. **View recipe** opens it; **Plan for later** opens the
    planner.

**This week** *(logged-in users only)*
:   A photo tile per planned meal for **Today** and **Tomorrow** — the recipe's picture, its meal
    (Breakfast, Lunch, …) and its title; click one to open the recipe. An empty day shows a
    **Plan a meal** prompt that opens the planner. On the left, **Latest shopping list** opens
    your most recent shopping list and shows its bought/total progress; a red badge such as
    *2 nutrition alerts* appears next to the heading when the next seven days of your planner
    fall short of your daily minimums (opens the planner).

**Explore**
:   Thematic shortcuts chosen by the administrators, for example *Produits de saison*,
    *Spécial végan* or *Prêt en 30 minutes*. Each one opens the recipe list with filters already
    applied. See [Thematic pages](../admin-guide/thematic-pages.md).

**In season now**
:   Up to four recipes made only of ingredients that are in season this month. The **+** button
    opens the full list with the in-season filter on.

![The home page for a visitor, with the Sign up button](../assets/screenshots/home-public.png)

## The recipe list

Click **Recipes** to see all recipes, newest first, 20 per page.

![The recipe list](../assets/screenshots/recipe-list.png)

Each row shows the recipe's picture, title, diet, total time (hover it to see prep and cook
time separately), servings, a leaf badge with its carbon footprint, and up to three tags. It can
also show:

- the variant name (for example *Gluten-free*), if the recipe is a [variant](#versions-and-variants),
- *imported by …* for recipes imported from a website, or *by …* for other people's recipes,
- a padlock next to the title when the recipe's [content is restricted](#recipes-with-restricted-content),
- badges for **your** allergens, if the recipe contains any.

On your own recipes, a pencil button (**Edit**) and a bin button (**Delete**) appear on the
right. Delete asks for confirmation first.

### Filter the list

Click **Filters** to open the filter panel. A number on the button shows how many filters are
active.

![The filter panel open over the recipe list](../assets/screenshots/recipe-list-filters.png)

| Filter | How it works |
|---|---|
| **Search** | Looks for your text in the recipe title and description. |
| **Diet** | **All**, **Omnivore**, **Vegetarian** or **Vegan**. |
| **Ingredients (comma-separated)** | For example `tomato, onion`. Shows recipes that contain **all** the listed ingredients. Each name must match an ingredient's full name, but case and accents don't matter (`creme fraiche` finds *Crème fraîche*). The English names of library ingredients work too. |
| **Max prep time (min)** | Prep time at most this many minutes. |
| **Max cook time (min)** | Cook time at most this many minutes. |
| **Carbon impact per serving** | **Any**, **Low (≤ 0.5 kg CO₂e)**, **Medium (0.5 to 1.5 kg CO₂e)** or **High (> 1.5 kg CO₂e)**. See [Nutrition & carbon](nutrition-and-carbon.md#carbon-levels). |
| **In-season ingredients only** | Hides recipes that use any ingredient that is out of season this month. Ingredients without a season are considered available all year. |
| **Hide recipes containing my allergens** | Only shown when your profile has allergies or intolerances. **Ticked by default**. See [Allergies and intolerances](account.md#allergies-and-intolerances). |

The list updates as you type. **Show results** closes the panel, and **Reset** clears every
filter.

> [!TIP]
> In a recipe page, clicking an ingredient name opens the recipe list filtered on that
> ingredient. It's a quick way to find other recipes that use it.

### Share or bookmark a filtered list

The active filters and the page number are part of the page address, for example:

```text
/recipes?diet_type=vegan&in_season=true&carbon_level=low&page=2
```

Copy the address to share the exact same view, or bookmark it. The **Explore** shortcuts on the
home page work the same way.

### Pages

When there are more than 20 results, use the arrows at the bottom of the list (**Previous
page** / **Next page**) to move between pages. *Page X of Y* shows where you are.

## Random recipe

Can't decide what to cook? Click the **dice** button in the top bar (or **Surprise me** in the
mobile tab bar).

![The Random recipe page](../assets/screenshots/random-recipe.png)

The **Random recipe** page shows a random recipe with its ingredients and steps. You can:

- narrow the draw with **Diet** and **In-season ingredients only**. A new recipe is drawn as
  soon as you change them.
- click **Another one** for a new draw,
- click the recipe title to open its full page,
- if you're logged in, add it straight to your planner with the **Add to planner** form.

If no recipe matches, you see *No recipe matches these criteria.*

## The recipe page

Click a recipe anywhere in the app to open its page.

![A recipe page](../assets/screenshots/recipe-detail.png)

### Summary

At the top you find the title, then *by …* or *imported by …* when relevant, then chips for the
**diet**, **servings**, **prep** and **cook** time.

Below that, the recipe's allergens are shown as badges, with your own allergies and
intolerances highlighted. *Allergens not verified for some ingredients* appears when at least
one ingredient hasn't had its allergens checked.

Then comes the picture, with a **Source** button on it when the recipe comes from a website,
and the YouTube video if there is one. A credit line is shown under the picture — the author and
license (see [Image credit and license](creating-recipes.md#image-credit-and-license)) when
they're set, an *image via …* domain for an older picture that predates that feature and never
got one, or *Credit not specified* when there's truly no credit information at all.

### Ingredients and steps

The **Ingredients** card lists quantities and units. Ingredients may be grouped under
sub-headings. Click an ingredient name to see other recipes that use it.

In the **Steps** card:

- **highlighted ingredient names** are links to the ingredient in the list (handy on a phone),
- **timer buttons** (for example ⏱ *10 min* or ⏱ *rest · 1 h*) start a countdown,
- a small **photo icon** at the end of a step's text means that step has its own picture — click
  it to view it (with its credit) in a dialog.

![The Ingredients and Steps cards: ingredient names highlighted in the steps, and 5 min and 50 min timer buttons](../assets/screenshots/recipe-detail-steps.png)

### Cook mode

If the recipe has steps, a prominent **Cook mode** button appears above the diet/servings/time
badges (next to a small **Download as PDF** icon). It opens a full-screen, one-step-at-a-time
view, with an animated slide as you move between steps, meant for following along on a phone
while cooking:

![Cook mode showing one step, with highlighted ingredient names](../assets/screenshots/mobile-cookmode-step.png)

- Move between steps with the **‹** / **›** buttons on the sides, a swipe left/right on a touch
  screen, the dots at the bottom, or the ← / → arrow keys. On the last step, the **›** button
  turns into a checkmark — pressing it (or swiping/pressing → again) exits cook mode instead of
  doing nothing.
- A step with its own photo (see [Add a photo to a step](creating-recipes.md#add-a-photo-to-a-step))
  shows it filling most of the screen, with the instruction text in a band at the bottom that
  grows taller for longer instructions.
- The **ingredients** button (top right) slides up a panel with every ingredient and its
  quantity, without leaving the step you're on. It closes on the same button, on **Escape**, or
  by tapping outside it.
- Tapping a highlighted ingredient name in a step opens its quantity in a small popup, closable
  the same ways.
- If the recipe has a YouTube video, a small play icon next to the step counter opens it in a
  new tab.
- Starting a timer in a step pins it to a dock at the bottom of the screen with its own
  pause/resume and reset buttons. It keeps counting down, and stays in the dock, even after you
  move to another step — so a "rest 10 min" timer from step 2 is still visible and controllable
  while you're reading step 5. Several timers running at once each get their own row in the dock.
- Close cook mode with the **✕** button or the **Escape** key.

![A running timer, shown both inline in the step and pinned to the dock at the bottom](../assets/screenshots/mobile-cookmode-timer-dock.png)

![The ingredients panel open over a step, with a dimmed backdrop behind it](../assets/screenshots/mobile-cookmode-ingredients.png)

### Use a step timer

1. Click the timer button in the step. The countdown starts.
2. Use **Pause** / **Resume** and **Reset** as needed.
3. When time is up, the button shows **Done!** and a short chime plays.

The first time you start a timer, your browser asks whether Cocotte may show **notifications**.
If you allow it, you also get a *Timer done!* notification when the time is up, even if you are
in another tab. You can run several timers at once.

> [!NOTE]
> Timers only run while the recipe page stays open. If you leave the page or close the tab, the
> timer stops.

### Nutrition facts and carbon footprint

The **Nutrition facts** card shows values **per serving**: calories, protein, carbs, fat, iron,
vitamin B12, calcium, omega-3 and zinc, and the **Carbon footprint (per serving)** in kg CO₂e.

![The Nutrition facts card of a recipe](../assets/screenshots/recipe-detail-nutrition.png)

These are estimates computed from the ingredients. See
[Nutrition & carbon](nutrition-and-carbon.md) to learn how.

### Download as PDF

Click **Download as PDF**, next to the summary chips, to get a printable PDF of the recipe. On
small screens the button shows only a download icon.

### Add to the planner

Logged-in users see an **Add to planner** card below the recipe:

1. Pick a **Date**.
2. Choose the **Meal**: **Breakfast**, **Lunch**, **Dinner** (default) or **Snack**.
3. Set the number of **Servings**. It starts at the recipe's servings.
4. Click **Add**.

*Added to the planner.* confirms it. If the recipe contains one of your allergens, a warning is
shown under the form. See [Meal planning](planning.md) for more.

![The Add to planner card](../assets/screenshots/recipe-add-to-planning.png)

### The actions menu

When you're logged in, a **⋮** button (**Actions**) at the top right of the recipe opens a
menu:

- **Edit** and **Delete**: on your own recipes only. Delete asks for confirmation.
- **Create a variant**: see below.

![The recipe actions menu](../assets/screenshots/recipe-actions-menu.png)

## Versions and variants

A **variant** is your own copy of a recipe, such as a gluten-free or spicier version. It stays
linked to the original.

To create one:

1. Open the recipe, then **⋮** → **Create a variant**.
2. Type a **variant name**, for example *Gluten-free*.
3. Click **Confirm** (or **Cancel**).

![The variant name field under the recipe title](../assets/screenshots/recipe-fork-dialog.png)

Cocotte copies the recipe (ingredients, steps, servings, times, diet and tags) into a new
recipe that belongs to you, titled *Original title (Variant name)*. It then opens the edit
form so you can make your changes. The picture, video and source link are not copied.

Every version of a recipe then lists the others under **Other versions of this recipe**, with
their variant name (or **Original**) and author:

![The Other versions of this recipe section](../assets/screenshots/recipe-versions.png)

> [!NOTE]
> You can make a variant of anyone's recipe, except recipes whose content is restricted (see
> below). Only the person who imported those can make variants of them.

## Recipes with restricted content

Recipes imported from a website, or with a **source link**, may be protected by copyright. By
default, only the following is public for them: the title, picture or video, **Source** link,
allergens and carbon footprint. The **description, ingredients and steps are only visible to the
person who added the recipe and to admins**. Other people see a notice with a padlock instead.

The author can make the full content public if they own the rights or have permission. See
[Creating recipes](creating-recipes.md#publicly-licensed-content).

For other people, a restricted recipe:

- shows a padlock in the recipe list,
- can't be downloaded as PDF or used for a variant,
- can still be added to the planner and to shopping lists.

## Ratings

Next to every recipe's title, click a star (1 to 5) to rate it. Ratings are fully anonymous — no
name or account is needed, and it's completely separate from comments below. Clicking a star
again later updates your own rating instead of adding a new one, and the average shown to
everyone always reflects one vote per person. To limit abuse, you can rate at most about 30
recipes per hour.

## Comments

At the bottom of every recipe, the **Comments** card shows the comments, newest first.

![The comments section of a recipe](../assets/screenshots/recipe-comments.png)

To post a comment, under **Leave a comment**:

1. Enter your **Name**. Visitors must enter one. If you're logged in and leave it empty, your
   username is used.
2. Type your **Comment** (up to 2,000 characters).
3. Click **Post**.

You don't need an account to comment. To limit spam, visitors can post at most about 10
comments per hour.

### Hide a comment

The recipe's author and admins see a **Hide** button under each comment. A hidden comment
disappears for everyone else and stays visible to them with a *(hidden)* mark. Click **Unhide**
to show it again. See [Moderation](../admin-guide/moderation.md).
