# Changelog

All notable changes to Cocotte are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project
follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### ✨ Added

- **Flat theme**: in **My account > Appearance**, the new **Shape** setting (**Rounded** or **Flat**)
  removes every rounded corner from the interface. Like the accent colour, it is stored on this
  device.
- **Moderation log**: actions staff take (edit or delete a recipe, blog
  post, ingredient, cookware or account, merge duplicates, hide a comment) are recorded and
  listed, read-only, in the Django admin under **Audit logs**. Lines are kept 365 days
  (`AUDIT_LOG_RETENTION_DAYS`, purged by the new `purge_audit_logs` command) and a deleted staff
  account's email is erased from them.
  The **Privacy policy** page now describes the log and its retention period.
- **Ingredient sections**: ingredients are now listed in bordered sections (*Dough*, *Filling*...)
  that you create with **Add a section** and name yourself, the first one included. Each
  ingredient is added or edited in a window opened by the **Add an ingredient** button of its
  section, and listed compactly (quantity, unit, name). The same ingredient can be used in several
  sections with a different quantity each, which the shopping list, nutrition and carbon
  estimates add up. The recipe page and PDF exports show a heading per section, and mentions in
  steps no longer clash when an ingredient appears twice.
- **Ingredient alternatives**: an ingredient can carry alternatives (vegan, vegetarian,
  gluten-free, lactose-free, *If you don't have it*, or a smaller quantity of the same
  ingredient), each with its own quantity and an optional note, added from the ingredient's window
  with **Add an alternative**. On the recipe page, a pill next to the ingredient unfolds the
  options; choosing one replaces the ingredient on that line until you leave the recipe. The
  choice is shared with cook mode, where you can also make it from the ingredients panel; the
  steps then name the alternative and the quantity popover says what it replaces. Alternatives are not counted in the shopping list, the planner or
  the nutrition and carbon estimates. They are copied by versions and included in recipe
  archives.
- **Announcements**: a banner at the top of every page, for a maintenance, an update or any
  message to your users. Admins create it in the Django admin (**Announcements**) with a level
  (information, warning, critical), a French and English text, an optional link and an optional
  display period. Readers can close it unless the admin made it permanent; an edited
  announcement is shown again. Setting `TEST_INSTANCE=True` also shows a permanent "test instance,
  your data may be deleted at any time" banner.
- **My tags**: personal tags to sort recipes your own way (*🎂 Birthdays*, *To try*...), each
  with a name, an optional emoji and a color. Put them on any recipe from its new **My tags**
  card, or create one on the go by typing its name; before creating it, Cocotte shows your
  similar existing tags (accents, plurals, typos) so you can reuse one. Only you see your tags.
  Manage them (rename, emoji, color, delete) on the new **My tags** page in the account menu,
  filter the recipe list and the random recipe with the new **My tags** filter, and see them as
  colored pills on recipe cards. Your tags are included in **Export my data**.
- **Cookware**: a recipe can list the cookware it needs (oven, frying pan, air fryer...), shown on
  the recipe page, in cook mode (where step mentions stand out with a 🍳) and in the PDF, so you know before starting whether you have it.
  Pick it in the new **Cookware** card of the recipe form, or create a missing item on the go by
  typing its name. In steps, type `#` (or use the **Cookware** button) to mention one, as in
  Cooklang: the mention links to the cookware list. Pasted Cooklang `#cookware` is now matched
  with the library instead of being dropped.
- **Cookware** filter on the recipe list and the random recipe: shows recipes using at least one
  of the chosen items (e.g. the oven or the air fryer).
- Staff **Administration** > **Cookware** page to rename, translate, set an emoji and a photo, and
  delete cookware (a photo needs its license and credit, as for recipes), and a `seed_cookware`
  command loading about 60 common items, most with a photo downloaded from Wikimedia Commons
  (public domain or CC BY / CC BY-SA, saved with its credit).
- Click a cookware item on the recipe page or in cook mode to see its photo with its credit. Recipe exports now include cookware.
- A **Page not found** page for unknown addresses, with links back to the home page and the
  recipes, instead of silently showing the recipe list.
- Each page now has its own browser tab title (for example *Recipes · Cocotte*, or the recipe's
  title on its page).
- **Unverified** ingredients and cookware: an item you create from the recipe form (or that a
  Cooklang or archive import creates for you) is marked **Unverified** until an administrator
  reviews it. Until then, and as long as no other user's recipe or shopping list uses it, you can
  fix it (**Edit**) or delete it yourself from the recipe form. Administrators get an
  **Unverified** filter on the **Ingredients** and **Cookware** pages, a **Verify** button, and
  **Merge into…** to fold a duplicate into the item to keep (its recipes and shopping lists move
  to that item).

### 🐛 Fixed

- **Admins can edit and delete any recipe** from the recipe page and the recipe list: the
  **Edit** and **Delete** actions were only shown to the recipe's author, although the API
  already allowed staff.
- **Sign-up** now shows why a field is refused (email already used or invalid, username taken, password rejected) under that field. For the password, the rules (8 characters minimum, not
  too common, not only digits) show under the field, and the reason appears there when the
  password is rejected, instead of a generic error.

### 🔄 Changed

- **Paste Cooklang** no longer creates the recipe straight away: **Import** now opens the
  **Manual entry** form filled in with what was read from the text (title, description,
  servings, times, source, ingredients and steps), so you can correct it before clicking
  **Save**. Ingredients that match nothing in the library are no longer created automatically:
  they show a **Not found** badge until you pick or create one. A missing title no longer
  blocks the import; type it in the form.
- Home page: **Plan for later** and the **+** buttons of the **This week** card no longer send you
  to the planner. **Plan for later** opens a dialog to pick the date and meal for that recipe, and
  a **+** button opens the **Add a meal** dialog for that day and meal, right on the home page.
- The **Omnivore** diet is now called **Flexitarian**. Since a flexitarian eats everything, the
  diet filter no longer offers it as a separate choice: **All (flexitarian)** covers it, and old
  links filtering on it now show every recipe.
- Imported recipes and copyright: importing a recipe from a URL no longer copies the website's
  photo. Their ingredients and times are now public for everyone (they're facts, not covered by
  copyright); only the description and steps stay restricted. The box to make the whole recipe
  public now reads **I rewrote the steps in my own words and the images used respect copyright:
  make the whole recipe public**, shows a
  copyright reminder when ticked, and right after an import refuses to save while a step is still
  the imported text.
- Planner redesign: the week view now shows one day at a time, picked from a row of day buttons,
  on both computers and phones. Meals appear as cards with the recipe photo, and each meal row has
  an icon. The month view shows meal icons, up to three recipes per day with a **+N more** link,
  and dots on phones. The PDF download and calendar export are grouped in a single **Export**
  menu, and the footer shows how many meals are planned in the displayed period.
- The **Add a meal** dialog lists matching recipes as you type, offers **Surprise me** to pick a
  random recipe, and starts the servings at the recipe's own number of servings.
- Recipe list: 10 recipes per page by default instead of 20.
- Random recipe redesign: the page now opens on a big dice to roll. The drawn recipe is shown as
  a large card (photo on top, details below) with a smaller dice underneath to roll again. The
  page no longer shows the full ingredients and steps, nor the **Add to planner** form: click the
  recipe to open its page. Its filters are now the same as the recipe list's (search,
  ingredients, maximum times and carbon impact are new there).
- Nutrition alerts only appear once at least half the days of the displayed period have a planned
  meal (4 days for a week); before that, the planner explains how many more days to plan instead
  of listing alerts for an almost empty week.
- Recipe form: errors are shown under the field concerned (for example the title), which is
  highlighted and scrolled into view. **Save** and **Cancel** stay visible in a bar at the bottom
  of the screen on long forms.
- Step `@ingredient` suggestions can be picked with the arrow keys and **Enter** (**Shift+Enter**
  still adds a new line), and the "not in the ingredient list" warning waits until you've finished
  typing the mention.
- Account page: without health-data consent, the diet, activity level and allergy fields are
  locked, with the consent button right next to them; the API also refuses those fields without
  consent. Deleting the account asks for confirmation in a dialog (**Delete permanently**).
- Sign-up: the health-data consent is now optional and reads as one short line, **Personalise my
  recipes using my diet, activity level and allergies**, with the details under **Why?**. Without
  it, the account is created without diet, activity level or allergies (the **Diet** and
  **Activity level** fields only appear once the box is ticked), and you can consent later from
  **My account**.
- Logged-in users no longer have to type a name to comment: the form shows **Posting as** and
  their username.
- Numbers (nutrition values, carbon footprint) follow the interface language's format
  (`0,6 kg CO₂e` in French), and missing times or carbon data are no longer shown as zero.
- Photo credits on recipe cards and home tiles sit behind a small camera button showing the full
  credit, instead of a truncated line or a label covering the card text.
- Anonymous home page: the sign-up invitation (**Create an account**) now sits under the hero's
  buttons, and the side cards are sized to their content.
- The **Add to planner** form on a recipe page starts at today's date, and the **Cook mode**
  button keeps its label on phones.
- Imported recipes: the copyright notice shown to visitors is now a calm information block, and
  the padlock on recipe cards explains itself in a tooltip.
- Recipe list: when no recipe matches, a **Reset filters** button clears every filter; the
  filters' reset button no longer looks disabled when there is something to reset.
- Shopping lists: the empty state offers **Open the planner**, where lists are generated from.
- Admin users table: the **Active** / **Staff** toggles look like buttons, and the "This is you" note
  no longer overflows its column.

### ✨ Added

- Recipe form: **Suggest a free image** searches for freely licensed pictures (CC BY, CC BY-SA,
  public domain, via Openverse) and fills in the image and its credit when you pick one.
- Planner: drag a meal to another meal row or onto another day's button to move it, and hold
  **Alt** while dropping to copy it. This also works between days in the month view.
- Planner: removing a meal shows an **Undo** message for a few seconds.
- Recipe list: a **Recipes per page** selector below the list shows 10, 20 or 50 recipes per
  page. The choice is kept in the page address and remembered in the browser.
- **Blog**: a new **Blog** section (top bar and phone tab bar) where any logged-in user can
  **Write a post**, with an optional cover image, using a rich-text editor (headings, lists,
  quotes, links, uploaded pictures) and embed Cocotte recipes in the text as clickable cards, with
  the **Recipe** button or **Ctrl+Alt+R** (**⌘ ⌥ R** on a Mac). Everyone can read posts and comment
  on them; the author can turn comments off with **Allow comments**. Before publishing, the form recalls the rules (no
  discriminatory or hateful language, texts and images must respect copyright) and asks to
  confirm them. The blog list has **Search** and **Author** filters, laid out like the recipe
  list's, and **Edit** / **Delete** buttons on your own posts. The home page shows the **Latest
  blog posts**. Blog posts and comments are included in **Export my data** and deleted with the
  account.

### 🐛 Fixed

- Recipe and week PDFs no longer show raw Cooklang markup in steps (`@Beurre`, `#Four`,
  `~{20%minutes}`): ingredients are printed in bold, cookware is underlined and timers are
  highlighted, as on the recipe page.
- In production (Docker, standalone or behind a shared proxy), `/django-admin` without a trailing
  slash now opens the Django admin instead of falling back to the app's recipe list.
- Recipe cards showed the whole recipe's carbon footprint labelled "/ serving"; they now show the
  footprint per serving, matching the recipe page and the carbon impact filter.
- The account page no longer shows an empty username and email after reloading the page.
- A step mention that doesn't match a recipe ingredient (such as `@len`) is now shown as typed
  on the recipe page and in cook mode, instead of losing its `@`.

## [0.2.0] "Lasagna" 🍝 - 2026-10-03

### ✨ Added

- Recipe list: active filters now also show as removable pills next to the **Filters** button
  (one pill per selected ingredient/allergen), so you can clear a single filter without opening
  the filters panel.
- Recipe list: the **Exclude allergens** filter lets you choose individual allergens to hide,
  instead of the all-or-nothing "Hide recipes containing my allergens" checkbox. Your own
  allergies and intolerances are still selected by default, and **Add my allergies and
  intolerances** puts them back after removing some.
- The **Random recipe** page's filters (diet, in-season ingredients, and a new allergen
  exclusion filter) are now hidden by default behind a filter toggle button next to **Another
  one**, with a badge showing how many are active. The new allergen filter is pre-filled from
  the signed-in user's own allergies/intolerances, like the main recipe list already does.
- Shopping-list export now offers a **Share** option (using the device's share sheet) on devices
  that support the Web Share API, so a list can be sent directly into a notes or to-do app (Apple
  Notes, Google Keep, Reminders, Todoist, etc.) instead of only downloading a `.txt` file. On
  browsers without the Web Share API (most desktop browsers besides Windows/Safari), the button
  now copies the list to the clipboard instead, ready to paste into any app; downloading a `.txt`
  file remains the last-resort fallback.
- Two new instance-level settings, both off by default: `PLANNING_SNACK_ENABLED` shows or hides
  the **Snack** meal slot in the weekly planner, and `NUTRITION_ALERTS_ENABLED` shows or hides
  the nutrient-deficiency alerts in the planner's nutritional intake summary. See the admin
  guide's Configuration page.
- The seeded ingredient library now includes "Tomates concassées" (canned crushed tomatoes), which the
  documentation demo data relies on.
- GDPR tooling for instance administrators: explicit consent to the processing of health-related
  data (diet, activity level, allergies) is now required at sign-up and can be withdrawn or given
  again from **My account**; withdrawing it erases that data.
- **Legal notice** and **Privacy policy** pages (linked in the footer and on the sign-up form),
  filled from the new `LEGAL_*`, `PRIVACY_CONTACT_EMAIL` and `PRIVACY_POLICY_VERSION` settings.
- When deleting their account, users can now keep their public recipes under an anonymous author
  ("Utilisateur supprimé") instead of deleting them; staff can do the same through the API and
  `purge_inactive_users --keep-recipes`.
- **Export my data** now also contains the agenda shares, the user's comments and ratings, and the
  consent date and policy version.
- `purge_inactive_users` management command (with `--dry-run`): emails then deletes accounts with
  no login for `INACTIVE_ACCOUNT_RETENTION_DAYS` days (default 730; staff accounts are never
  touched). See the new "GDPR compliance" page of the admin guide.
- The app version is now shown discreetly at the bottom of the **My account** page.
- Recipe cover images and individual recipe steps can now carry an image license and credit (CC
  BY, CC BY-SA, public domain, personal photo, used with permission, or not specified) — required
  for a new or changed image, shown as attribution wherever the image appears, and never
  retroactively required for images that already existed.
- Each recipe step can optionally have its own photo, added via an "Add an image" button and
  viewable by tapping a small photo icon next to the step (on the recipe page and in cook mode).

### 🔄 Changed

- The weekly planner's **Nutritional intake** button is now hidden entirely when
  `NUTRITION_ALERTS_ENABLED` is off (the default), instead of only hiding the deficiency list
  inside its dialog.
- **Paste Cooklang** now understands full Cooklang files, such as those downloaded from
  recipes.cooklang.org: metadata (title, servings, prep/cook times, source link, description),
  multi-word ingredient names, fractions (`1/2`, `½`), preparation notes (`@café{30%g}(moulu)`),
  sections (used to group ingredients) and notes (added to the description). Title and servings
  are now optional in the form when the file's metadata provides them. Pasted ingredients are
  matched against the library like a URL import (by translation and close spelling too), and
  `cl`/`dl`/`mg` quantities are converted. Parsing now relies on the `cooklang-py` library.
- Recipe list redesign: on a computer the filters now sit in a column on the left of the list
  (always visible) and recipes are shown two per row; on a phone the **Filters** button opens the
  panel above the list instead of a bottom sheet. Ingredients are picked from a searchable
  multi-select shown as pills, the diet is a list of radio buttons, max prep/cook times are
  sliders, carbon impact is a colour-coded slider (green / orange / red), and the in-season
  checkbox is now an **In season** leaf toggle. The **New recipe** and **Import** buttons are
  merged into a single **New recipe** menu (**Create manually** / **Import from a URL**).
- The "pièce" (piece) unit now accepts decimal quantities on a recipe (e.g. 0.5 for half a
  camembert); shopping lists still round up to a whole piece when aggregating.
- Cook mode's button now uses a chef's hat icon instead of a generic expand icon, and reaching the
  last step and pressing "next" now exits cook mode instead of doing nothing.
- Images imported from a URL are credited as "Not specified" with a note citing the source,
  editable before saving.
- Adding a recipe to a planner slot now opens in a dialog instead of an inline form squeezed into
  the calendar cell, which also fixes the recipe-search dropdown being clipped in narrow agenda
  cells.
- The planner's calendar grid now has a white background, and page titles across the app now show
  a small icon next to them for quicker visual scanning.
- Form fields now have a white background with a subtle colored border and less rounded corners.
- Shopping-list items are now grouped under a heading per ingredient category (vegetable, fruit,
  dairy, etc.) instead of a single flat list, and a ticked item can now be unticked again by
  clicking its checkbox a second time (previously it was stuck checked once ticked — generating a
  new list from the planner was the only way to undo a mistaken tick).
- Shopping lists got a visual refresh: each category heading now has an icon, a progress summary
  ("x/y bought") with a progress bar sits above the list, each category shows its own "done/total"
  count, and quantities are shown as a small pill badge for easier scanning. The **Shopping**
  overview page got the same treatment (an icon, date and progress bar per list, on a clickable
  card), and the list detail page now has a "Back to my lists" link.
- On the homepage, "New recipe" and "Import" are now a single "New recipe" button that opens a
  menu offering "Create manually" or "Import from a URL", and the "Browse recipes" button was
  removed since the main navigation already links to the recipe list.
- In cook mode, a step's photo now fills most of the available height instead of a small fixed-size
  crop, with the instruction text anchored to a band at the bottom (around 20% of the height by
  default, growing to fit longer instructions instead of ever clipping them).
- The homepage got a visual refresh. The latest-recipes carousel is replaced by a "today's pick"
  hero: the most recent recipe in a large photo card (with a decorative stack of cards behind
  it), its diet/time/servings, a **View recipe** and a **Plan for later** button. It auto-advances
  through your 5 latest recipes, with dots below to jump to one directly (on mobile, the title and
  CTAs sit over the photo instead of above it); the "New recipe" quick action now sits at the top
  of that same hero instead of floating in its own row above an unrelated section, and is now
  styled as a card matching the **Latest shopping list** button next to it (an icon over a label)
  instead of a stretched pill. That **Latest shopping list** card (showing its bought/total
  progress) sits in its own box next to, rather than inside, the "This week" card, which floats
  over the hero's bottom edge and lists Today/Tomorrow side by side: each meal slot (Breakfast,
  Lunch, Dinner, Snack) is the same size, either a photo tile (recipe picture, meal, title) when
  planned or a **+** button to add one when empty, instead of one plain text line or a single
  "Plan a meal" prompt per day. Further down, **Explore** and **In season now** are now two
  matching cards side by side instead of two plain headed sections stacked vertically, with larger
  Explore photo avatars (a row of round photo avatars instead of square tiles, so a page without
  its own photo shows its icon on a plain accent-tinted circle instead of a flat saturated-color
  card) to fill the roomier card.
- The weekly/monthly planner now tints today's column (week view) or day cell (month view) so
  it's easy to spot, and the "Today" button that jumps back to the current period (shown once
  you've navigated away) got a reset icon and a visible border so it reads as a button rather
  than a label.
- In cook mode, clicking a highlighted ingredient name now shows its quantity in a small popover
  anchored next to it instead of a full modal dialog; on a mouse, the popover also appears just by
  hovering over the name.

### 🐛 Fixed

- Recipe list: a long recipe title no longer runs under the owner's actions (**⋮**) menu button —
  the title now clamps to two lines (hover to see the full title) and the button no longer
  overlaps the text.
- On a phone, the page footer no longer gets hidden behind the bottom tab bar.
- Form validation errors (recipe details, ingredients, planner entries) are now shown consistently
  via inline messages instead of relying on the browser's native validation bubbles, which could be
  invisible or badly positioned on mobile.
- Fixed autocomplete dropdowns reopening after selecting a suggestion (noticeable on the recipe
  picker used when adding a recipe to the planner, and on the ingredient-mention autocomplete in
  recipe step text), which made it look like the first click didn't register and required
  clicking the suggestion a second time.

## [0.1.0] "Tiramisu" 🍰 - 2026-09-27

### ✨ Added

- **Cook mode**: a full-screen, swipeable view of a recipe's steps (one step per screen, with
  Previous/Next buttons, a swipe gesture on touch devices, or the arrow keys, animated with a
  directional slide transition), designed for reading a recipe on a phone while cooking. The
  ingredient list stays one tap away in a toggleable panel that closes on an outside click or
  Escape, and tapping a highlighted ingredient in a step opens its quantity in a small popup
  instead of jumping away from the step. A timer started from a step is automatically pinned to a
  dock at the bottom of the screen with its own controls, so it keeps counting down and stays
  visible and controllable even after swiping to another step; several timers running at once
  each get their own row. A discreet link to the recipe's YouTube video (when there is one) sits
  next to the step counter.
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
- **Anonymous star ratings**: rate any recipe 1-5 stars without an account and without giving a
  name — separate from comments. An anonymous vote is deduplicated by a salted hash of the
  voter's IP (never stored in the clear) so re-voting updates their own rating instead of padding
  the average; a signed-in vote is tied to the account instead. Rate-limited like comments.
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
- **Continuous integration**: backend lint and tests, frontend typecheck and unit tests, and a
  Playwright end-to-end job ([#9](https://github.com/jacquesfize/cocotteapp/pull/9)) that
  cleans up the data it creates ([#26](https://github.com/jacquesfize/cocotteapp/pull/26)).

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

- Celery and Redis: URL import runs synchronously and no background worker is needed any more.
- The separate `requirements/*.txt` files, replaced by `pyproject.toml` and `uv.lock`.

[Unreleased]: https://github.com/jacquesfize/cocotteapp/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/jacquesfize/cocotteapp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jacquesfize/cocotteapp/releases/tag/v0.1.0
