# Announcements

An announcement is a banner shown at the top of every page, just under the navigation bar, to
everyone who opens the site, logged in or not. Use it for a planned maintenance, a new feature, or
to warn that the instance is only for testing.

Announcements are managed in the [Django admin](django-admin.md), under **Announcements** >
**Announcements** (*Annonces*).

## Levels

| Level | Use it for | Look |
|---|---|---|
| **Information** | A new feature, an update | Accent colour, ✨ icon |
| **Avertissement** (warning) | Something to be aware of | Amber, 🧪 icon |
| **Critique (maintenance)** (critical) | A maintenance or an outage | Red, 🔧 icon, announced as an alert to screen readers |

When several announcements are active, the most severe is shown first.

## Create an announcement

1. Go to `/django-admin/`, then **Announcements** > **Add announcement**.
2. Pick a **level**.
3. Write the **title** and **message** in French and in English. Both are optional, but fill at
   least one: when the reader's language is empty, the other one is shown. Keep the message to one
   or two sentences.
4. Optionally add a **link** (a full URL, or a site path such as `/blog`) with its label.
5. Optionally set a **start** and an **end** date: the banner appears and disappears on its own.
   Leave them empty to show it right away and without end.
6. **Save**.

Uncheck **Activée** (*is active*) to hide an announcement without deleting it.

## Dismissal

By default a reader can close the banner with the **×** button, and it stays closed on that
browser. If you edit the announcement afterwards, it is shown again, since it is no longer the
same message. Uncheck **Peut être fermée** (*dismissible*) for a message that must stay visible,
such as a maintenance.

## Test instance banner

To warn that an instance is for testing and that its data may be deleted at any time, set
`TEST_INSTANCE=True` in the environment (see [Configuration](configuration.md#test-instance-banner)) and
restart the backend. The banner *Test instance. Your data may be deleted at any time.* is then
shown on every page, in the reader's language, and cannot be closed. It needs no announcement in
the Django admin and is shown below the admin-created ones.
