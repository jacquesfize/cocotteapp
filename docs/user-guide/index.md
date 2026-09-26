# The interface

This page is a tour of Cocotte's interface: the top bar, the account menu, the language and
theme buttons and the mobile tab bar. It also explains what you can do without an account and
what needs one.

> [!NOTE]
> Button labels in this guide are quoted in **English**. Cocotte starts in French, so switch the
> language first (see [Language and theme](#language-and-theme)) if you want the labels to match.

## The top bar

![The buttons on the right of the top bar (dice, language flag, dark mode, account) with the account menu open, showing My account, the Administration section and Log out](../assets/screenshots/navbar-account-menu.png)

From left to right:

| Element | What it does |
|---|---|
| **Cocotte** logo | Back to the home page. |
| **Home** | The home page: latest recipes, your week, thematic shortcuts, seasonal recipes. See [Browsing recipes](browsing-recipes.md#the-home-page). |
| **Recipes** | The full recipe list with search and filters. |
| **Planner** | Your meal planner. *Logged-in users only.* See [Meal planning](planning.md). |
| **Shopping** | Your shopping lists. *Logged-in users only.* See [Shopping lists](shopping-lists.md). |
| Dice button (**Surprise me**) | Opens a random recipe. See [Random recipe](browsing-recipes.md#random-recipe). |
| Flag button | Language selector (Français / English). |
| Moon / sun button | Switches between light and dark mode. |
| Person button | Logged out: opens the login page. Logged in: opens the account menu. |

## The account menu

When you are logged in, the person button opens a menu with:

- your **username** at the top,
- **My account**: your profile, allergies, appearance, password, data export, agenda sharing and
  account deletion. See [Your account](account.md).
- **Administration** (staff accounts only): **Admin** (user management), **Thematic pages** and
  **Ingredients**. These pages are described in the [Admin guide](../admin-guide/users.md).
- **Log out**.

Click outside the menu or press Escape to close it.

## Language and theme

### Change the language

1. Click the **flag** button in the top bar.
2. Choose **Français** or **English**. A check mark shows the current language.

The whole interface switches immediately. Your choice is saved in the browser, so it applies
on this device only, whether or not you are logged in.

> [!NOTE]
> The language setting translates the interface. Recipe content stays in the language it was
> written in. Ingredient names from the built-in library are in French.

### Dark mode

Click the **moon** button to switch to dark mode, and the **sun** button to switch back. On
your first visit, Cocotte follows your operating system's light/dark setting. Once you click
the button, your choice is saved on this device.

![The home page in dark mode](../assets/screenshots/dark-mode-home.png)

You can also change the **accent colour** of the app in **My account** → **Appearance**. See
[Your account](account.md#appearance-accent-colour).

## On a phone

On narrow screens (up to 600 px wide), the text links and the dice button move out of the top
bar into a **tab bar at the bottom of the screen**:

- **Home**, **Recipes** and **Surprise me** for everyone,
- **Planner** and **Shopping** when you are logged in.

The top bar keeps the logo, the language, theme and account buttons.

![Cocotte on a phone, with the bottom tab bar](../assets/screenshots/mobile-home.png)

> [!TIP]
> Cocotte can be installed like an app on your phone's home screen. See
> [Install & offline](offline-and-install.md).

## Visitors vs. logged-in users

You can use part of Cocotte without an account. The login page has a
**Browse recipes without an account** link for that.

| Action | Visitor | Logged in |
|---|:---:|:---:|
| Browse the home page, recipe list, filters and random recipe | ✅ | ✅ |
| Read a recipe, its nutrition facts and carbon footprint | ✅ | ✅ |
| Download a recipe as PDF | ✅ | ✅ |
| Read and post comments (visitors must enter a name) | ✅ | ✅ |
| Create, import, edit and delete your own recipes | — | ✅ |
| Create a variant of a recipe | — | ✅ |
| Add a recipe to the planner, use the planner | — | ✅ |
| Shopping lists | — | ✅ |
| Allergen filtering and warnings based on your profile | — | ✅ |

If you open a page that needs an account, such as `/planning`, Cocotte sends you to the login
page. After you log in, you land back on the page you asked for.

> [!NOTE]
> Some imported recipes only show their title, picture, source link, allergens and carbon
> footprint to other people. Only the person who imported them and admins see the full
> description, ingredients and steps. See
> [Recipes with restricted content](browsing-recipes.md#recipes-with-restricted-content).

## Where to go next

- [Your account](account.md): sign up, log in and set up your profile and allergies.
- [Browsing recipes](browsing-recipes.md): find and read recipes.
- [Creating recipes](creating-recipes.md): add your own.
- [Meal planning](planning.md) and [Shopping lists](shopping-lists.md): plan the week and shop.
