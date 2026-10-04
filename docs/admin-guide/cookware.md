# Cookware library

Recipes can list the **cookware** they need (oven, frying pan, air fryer...). Like ingredients,
cookware items are shared records: every recipe points to the same **Four** or **Wok**, which is
what makes the **Cookware** filter of the recipe list work.

## Who can do what

| Action | Who |
|---|---|
| Create cookware | Any logged-in user, from the recipe form (see [Creating recipes](../user-guide/creating-recipes.md#cookware)), and staff from the **Cookware** page. Importing a Cooklang recipe through the API (`POST /api/recipes/import-cooklang/`) also creates the `#cookware` it doesn't find. |
| Rename or delete cookware | Staff, at any time. Its creator too, while it is **unverified** and no other user's recipe uses it (see [Unverified cookware](#unverified-cookware)). |
| Change the photo, verify or merge cookware | Staff only |

Since anyone can create cookware, check the list from time to time for duplicates or typos
(*Poele* next to *Poêle*, *four* next to *Four*). A name must be unique, ignoring case.

## Unverified cookware

Cookware created by a user who is not staff starts **unverified**, and records who created it.
This includes cookware created while importing a Cooklang recipe or a recipe archive: the
importing user is recorded as its creator. Items created by staff, loaded by `seed_cookware`, or that existed before this feature are
**verified**.

While an item is unverified, its creator can rename or delete it themselves, as long as only
their own recipes use it. It becomes **locked** for them, and only staff can change it, as soon
as a staff member verifies it or another user's recipe uses it.

To review new items, turn on the **Unverified** filter of the **Cookware** page: it lists the
items still waiting for a review, with the name of the user who created each one. Fix the name if
needed, then click **Verify**; for a duplicate, use **Merge into…** (see below).

## Open the Cookware page

Open the account menu (person icon, top right) and choose **Administration** > **Cookware**, or
go to `/admin/cookware`.

The table shows each item's photo (or its emoji when it has no photo), **Name** and **English
name**, with an **Edit** button and a delete button (bin icon). The **Search** field (placeholder "French or English name...") filters the
list as you type.

## Create or edit cookware

1. Click **New cookware**, or **Edit** on a row. A dialog opens (**New cookware** or **Edit
   cookware**).
2. Fill in **Name** (by convention in French, like the seeded data) and, optionally, **English
   name**. The English name is used by the search and to match the `#cookware` of a Cooklang
   recipe written in English. Other translations stored on an item are kept when you save.
3. Optionally set an **Emoji** (only when one actually depicts the object, such as 🍳 for a
   frying pan) and a **Photo** (pick a file; **Remove the photo** deletes the current one). The
   photo is shown on the recipe page and in cook mode; without one, the emoji is used.
   A new photo needs its **Image license**, with the same rules as a recipe photo (see
   [Image credit and license](../user-guide/creating-recipes.md#image-credit-and-license)): for
   **CC BY** and **CC BY-SA**, the **Author** and **Source URL** are required. The credit is shown
   with the photo when a reader clicks the cookware item.
4. Click **Save**. A name that already exists shows *This cookware already exists.*

## Delete cookware

Click the bin icon and confirm. **The item is removed from every recipe that uses it**; the
recipes themselves are not affected otherwise (a `#mention` of it in a step becomes plain text).
To get rid of a duplicate, merge it instead.

## Merge a duplicate

The merge button (branch icon, tooltip **Merge into…**, next to the bin) replaces a duplicate
(the item on whose row you click) by the correct item you
pick, then deletes the duplicate and its photo: every recipe that used the duplicate now uses the
chosen item, and translations missing from the chosen item are copied from the duplicate (its own
ones are kept when both have one). Recipe steps that mention the duplicate by name (`#poele`) are
not rewritten. Merging cannot be undone.

## Seeded cookware

`seed_cookware` loads about 60 common items (appliances such as **Four** or **Friteuse à air**,
pans and dishes, preparation tools), each with its English name, an emoji when one exists, and,
for most of them, a photo.

The photos are **downloaded from Wikimedia Commons when the command runs** (nothing is bundled
with the code), so the server needs Internet access; the first run takes one or two minutes, one
photo per second to respect Wikimedia's rate limits. They are either in the public domain or under
CC BY / CC BY-SA, and each one is saved with its credit (author, Commons page, license), shown to
readers with the photo. The list of files and credits lives in `PHOTOS` in
`backend/apps/recipes/management/commands/seed_cookware.py`.

A photo that can't be downloaded (no network, file removed from Commons...) doesn't stop the
command: the item is created without it, and a *Photo non téléchargée* line names it; run the
command again later to fetch it. On a server without Internet access, pass `--skip-images` to
load the list without any photo.

Re-running it is safe: it creates the missing items, sets their English name, and fills in the
emoji and photo **only when they are empty** (only missing photos are downloaded), so an emoji or
photo you chose is never replaced. It never deletes or renames anything. See
[First run](../getting-started/first-run.md#3-load-the-reference-data).
