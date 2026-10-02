# GDPR compliance

Cocotte gives an instance the tools to comply with the GDPR (RGPD). As the administrator you are
the **data controller**: the software helps, but some obligations are yours alone.

> [!NOTE]
> This page is a practical checklist, not legal advice. Have your texts validated for your
> situation (a personal instance for friends is not the same as a public one).

## What Cocotte already does

| Requirement | How |
|---|---|
| Access and portability (art. 15, 20) | **Export my data** on the **My account** page (ZIP of JSON files). |
| Rectification (art. 16) | Users edit their profile, diet and allergies. |
| Erasure (art. 17) | **Delete my account** removes the account, planner and lists, and its recipes, unless the user chooses to keep their public recipes under an anonymous author. |
| Explicit consent for health data (art. 9) | Required checkbox at sign-up; date and policy version stored; can be withdrawn from **My account** (this erases diet, activity level and allergies). |
| Information (art. 13) | **Legal notice** and **Privacy policy** pages, linked in the footer and on the sign-up form. |
| Storage limitation (art. 5) | `purge_inactive_users`, see [below](#inactive-accounts). |
| Minimisation / no tracking | No analytics, advertising or third-party scripts; only strictly necessary browser storage (login tokens, language, appearance, offline cache), so no cookie banner is needed. |

## Fill in the legal pages

Set these variables (see [Configuration](configuration.md#privacy-and-gdpr)) and restart the
backend:

```ini
LEGAL_PUBLISHER_NAME=Association Cocotte
LEGAL_PUBLISHER_ADDRESS=1 rue des Fourneaux, 75000 Paris
LEGAL_CONTACT_EMAIL=contact@cocotte.example.org
LEGAL_HOST_NAME=Example Hosting
LEGAL_HOST_ADDRESS=2 avenue du Cloud, 59000 Lille
PRIVACY_CONTACT_EMAIL=privacy@cocotte.example.org
```

The pages are `/legal` and `/privacy` on your domain. The policy text is generic and shipped
with the app (French and English); only the identities and the retention period come from your
configuration. If you change how you process data, bump `PRIVACY_POLICY_VERSION`: it is stored with
each consent.

## Inactive accounts

`purge_inactive_users` applies the retention period:

1. Accounts with no login for `INACTIVE_ACCOUNT_RETENTION_DAYS − INACTIVE_ACCOUNT_WARNING_DAYS`
   days receive one warning email (an account that was never used counts from its sign-up date).
2. If the user has not logged in `INACTIVE_ACCOUNT_WARNING_DAYS` days after the warning, and the
   retention period is over, the account and all its data are deleted.

Staff and superuser accounts are never touched. A user who logs in after the warning is safe.
With `INACTIVE_ACCOUNT_RETENTION_DAYS=0` the command does nothing. Emails need a working
[SMTP configuration](configuration.md#email-smtp).

Preview first, then schedule it daily:

By default the purge deletes the users' recipes with them. Add `--keep-recipes` to keep their
public recipes under the anonymous author instead (see
[Account deletion](#account-deletion-and-anonymous-recipes)).

/// tab | Docker

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python manage.py purge_inactive_users --dry-run
```

Daily cron entry on the host:

```cron
15 3 * * * cd /opt/cocotte && docker compose -f docker-compose.prod.yml --env-file .env.prod exec -T backend python manage.py purge_inactive_users
```

///

/// tab | Classic

```bash
cd /opt/cocotte/app/backend
sudo -u cocotte env DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python manage.py purge_inactive_users --dry-run
```

Daily cron entry:

```cron
15 3 * * * cd /opt/cocotte/app/backend && sudo -u cocotte env DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python manage.py purge_inactive_users
```

///

> [!NOTE]
> Users who already had an account before this feature count from their last login (or sign-up
> date). They have no recorded consent: **My account** invites them to give it.

## Account deletion and anonymous recipes

Deleting an account (by the user in **My account**, or by staff in [Users](users.md)) can keep
the account's **public** recipes: they are reassigned to a shared, inactive account named
"Utilisateur supprimé" (`deleted-user@cocotte.invalid`) that cannot log in and is never purged.
Private recipes, planner entries, shopping lists and ratings are always deleted, and comments
left by the user lose their display name.

> [!NOTE]
> The anonymisation covers the author. Free-text fields the user typed themselves, such as an
> image credit or the recipe text, are kept as is; remove them by hand if a request asks for it.

## Data export

**Export my data** contains `profil.json` (including consent date and policy version and last
login), `recettes.json`, `agenda.json`, `listes_de_courses.json`, `partages_agenda.json`
(agendas shared by or with the user), `commentaires.json` and `notes.json`.

## What remains your responsibility

- **Hosting**: prefer a provider in the EU and sign a data processing agreement with it.
- **Backups**: they hold deleted accounts until they expire. Keep them for a bounded time and state
  it in your policy (see [Maintenance](maintenance.md#back-up-and-restore)).
- **Requests by email**: answer access or erasure requests sent to `PRIVACY_CONTACT_EMAIL` within one
  month. Staff can delete or deactivate accounts in [Users](users.md).
- **Registry of processing activities** (art. 30) and, depending on your scale, a DPO or an impact
  assessment.
- **Data breaches**: notify the CNIL (or your authority) within 72 hours when personal data is
  compromised.
