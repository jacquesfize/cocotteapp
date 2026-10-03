# Configuration

Cocotte is configured entirely through environment variables. This page lists every variable the
application reads, with its default and its effect, and then covers the settings that need the
most care in production: email, public URLs, HTTPS, CORS/CSRF and the secret key.

## Where the variables live

| Setup | File | How it is read |
|---|---|---|
| Docker (both modes) | `.env.prod` at the repository root (template: `.env.prod.example`) | Passed to the `db`, `backend` and `frontend` containers through `env_file`, and used by `--env-file` for variables in the compose files (`PROXY_NETWORK_NAME`). |
| Classic | `backend/.env` (template: `backend/.env.example`) | Loaded by Django at startup (`config/settings/base.py`). Variables already set in the process environment take precedence over the file. |
| Development | `backend/.env` | Same as Classic. See [Development environment](../developer/dev-environment.md). |

Settings are split into `backend/config/settings/base.py` (shared), `dev.py` and `prod.py`. The
module is selected by `DJANGO_SETTINGS_MODULE`:

| Entry point | Default settings module |
|---|---|
| Production Docker image | `config.settings.prod` (set in `backend/Dockerfile`) |
| Gunicorn / `config.wsgi` | `config.settings.prod` |
| `manage.py` | `config.settings.dev` |

> [!IMPORTANT]
> In a Classic deployment, set `DJANGO_SETTINGS_MODULE=config.settings.prod` in the systemd
> unit and on every `manage.py` command line (see [Production deployment](deployment.md)). It cannot be set in `backend/.env`, which is
> only read once the settings module has been chosen.

After changing a variable, restart the backend so that Django reads it again:

/// tab | Docker

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

`up -d` recreates the containers whose configuration changed. If you use the shared-proxy mode,
add `-f docker-compose.prod.proxy.yml` after `-f docker-compose.prod.yml`.

///

/// tab | Classic

```bash
sudo systemctl restart cocotte
```

///

## Django and database

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | `change-me-in-production` | Django's cryptographic key. It signs login tokens (JWT), admin sessions and password-reset links. **Must** be set to a long random value in production (see [Generate a secret key](#generate-a-secret-key)). |
| `DEBUG` | `False` | Django debug mode. `backend/.env.example` sets it to `True` for development. **Ignored in production**: `config/settings/prod.py` always forces `DEBUG = False`. |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names Django accepts in the `Host` header. Set it to your public domain, e.g. `cocotte.example.org`. Requests for any other host get a `400 Bad Request`. |
| `DATABASE_URL` | `postgres://postgres:postgres@localhost:5432/cocotte` | PostgreSQL connection string, `postgres://user:password@host:port/dbname`. In Docker the host is `db`, the user `postgres` and the database `cocotte`. URL-encode special characters in the password (for example `@` becomes `%40`). |
| `POSTGRES_PASSWORD` | *(none, required in Docker)* | Read by the `db` container only: password of its `postgres` user. Must be identical to the password in `DATABASE_URL`. Only applied when the database volume is first initialised. |
| `DJANGO_SETTINGS_MODULE` | see [above](#where-the-variables-live) | Settings module. Use `config.settings.prod` in production. |

## Public URLs, CORS and CSRF

| Variable | Default | Description |
|---|---|---|
| `FRONTEND_URL` | `http://localhost:5173` | Public base URL of the app, without a trailing slash. Used to build the link in password-reset emails. |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated origins allowed to call the API from a browser on another origin. |
| `CSRF_TRUSTED_ORIGINS` | *(empty)* in production | Comma-separated origins trusted by Django's CSRF protection, including the scheme (`https://cocotte.example.org`). Read by `prod.py` only; in development it is always set to `FRONTEND_URL`. |

### Why `FRONTEND_URL` matters

When someone requests a password reset, the backend emails a link of the form
`{FRONTEND_URL}/reset-password/<uid>/<token>`. If `FRONTEND_URL` still has its development value,
users receive a link to `http://localhost:5173/...`, which does not work for them. Set it to your
public HTTPS URL, for example `https://cocotte.example.org`.

### CORS and CSRF in practice

In every supported deployment, the SPA and the API are served from the **same origin** (the web
server reverse-proxies `/api/`), so browsers never make cross-origin API calls. Still set both
variables to your public origin:

- `CORS_ALLOWED_ORIGINS=https://cocotte.example.org` keeps the default `http://localhost:5173`
  out of production.
- `CSRF_TRUSTED_ORIGINS=https://cocotte.example.org` is used by the Django admin forms (login,
  edits) at `/django-admin/`. If you get a "CSRF verification failed" error when logging in to
  the Django admin, check this value and that your proxy forwards the original `Host` header and
  `X-Forwarded-Proto`.

The public domain must be consistent across `DOMAIN` (standalone Docker), your host proxy
configuration, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` and
`FRONTEND_URL`. Several domains can be listed, comma-separated, in the three list variables.

## Email (SMTP)

Cocotte sends one kind of email: the password-reset link (its text is in French, whatever the
user's interface language). By default it uses Django's console
backend, which prints emails to the backend logs instead of sending them.

| Variable | Default | Description |
|---|---|---|
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | Set to `django.core.mail.backends.smtp.EmailBackend` in production. |
| `EMAIL_HOST` | `localhost` | SMTP server host name. |
| `EMAIL_PORT` | `25` | SMTP server port. |
| `EMAIL_HOST_USER` | *(empty)* | SMTP user name. |
| `EMAIL_HOST_PASSWORD` | *(empty)* | SMTP password. |
| `EMAIL_USE_TLS` | `False` | Use STARTTLS on the SMTP connection. |
| `DEFAULT_FROM_EMAIL` | `Cocotte <noreply@cocotte.app>` | Sender address of outgoing emails. Also sent, as a contact, in the `User-Agent` of requests to Open Food Facts and Agribalyse. |

> [!WARNING]
> Until `EMAIL_BACKEND` is set to the SMTP backend, password-reset emails are **never sent**: they
> only appear in the backend logs.

> [!NOTE]
> Only STARTTLS (`EMAIL_USE_TLS`, usually port 587) is configurable. Implicit TLS on port 465
> (`EMAIL_USE_SSL` in Django) is not read from the environment, so use your provider's STARTTLS
> port.

### Generic SMTP server with STARTTLS

```ini
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.org
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@cocotte.example.org
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Cocotte <noreply@cocotte.example.org>
```

Most hosted providers (your domain registrar's mailboxes, Brevo, Mailgun, Postmark, Amazon SES,
and so on) work with this pattern: use the SMTP host, port 587, and the SMTP credentials they
give you. Use a sender address on a domain the provider is allowed to send for (SPF/DKIM),
otherwise emails are likely to land in spam.

### Local relay on the host (Classic)

If the server already runs a local mail relay (Postfix, OpenSMTPD...) that accepts unauthenticated
mail from `localhost`:

```ini
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=localhost
EMAIL_PORT=25
DEFAULT_FROM_EMAIL=Cocotte <noreply@cocotte.example.org>
```

### Test the configuration

Send a test email from the backend:

/// tab | Docker

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod exec backend python manage.py sendtestemail you@example.org
```

///

/// tab | Classic

```bash
cd /opt/cocotte/app/backend
sudo -u cocotte env DJANGO_SETTINGS_MODULE=config.settings.prod .venv/bin/python manage.py sendtestemail you@example.org
```

///

An error here (authentication, TLS, connection refused) is the same error a password-reset request
would hit. If the SMTP server is unreachable when a user requests a reset, the request fails with
a server error.

## Privacy and GDPR

These variables feed the **Legal notice** and **Privacy policy** pages and the inactive-account
purge. See [GDPR compliance](gdpr.md) for the full checklist.

| Variable | Default | Description |
|---|---|---|
| `LEGAL_PUBLISHER_NAME` | *(empty)* | Name of the person or organisation running the instance (legal notice). |
| `LEGAL_PUBLISHER_ADDRESS` | *(empty)* | Postal address of the publisher. |
| `LEGAL_CONTACT_EMAIL` | *(empty)* | Contact email shown in the legal notice. |
| `LEGAL_HOST_NAME` | *(empty)* | Name of the hosting provider. |
| `LEGAL_HOST_ADDRESS` | *(empty)* | Address of the hosting provider. |
| `PRIVACY_CONTACT_EMAIL` | `LEGAL_CONTACT_EMAIL` | Address (or DPO) users write to in order to exercise their rights. |
| `PRIVACY_POLICY_VERSION` | `1` | Stored with each user's consent. Increase it when the policy changes significantly. |
| `INACTIVE_ACCOUNT_RETENTION_DAYS` | `730` | Accounts with no login for this many days are deleted by `purge_inactive_users`. `0` disables the purge. |
| `INACTIVE_ACCOUNT_WARNING_DAYS` | `30` | How many days before deletion the warning email is sent. |

Fields left empty appear as "Not provided by the instance administrator." on the public pages.

## Planning and nutrition features

These toggles enable features that are **off by default** for every user of the instance (they
are not a per-user preference): restart the backend after changing them, same as any other
setting on this page.

| Variable | Default | Description |
|---|---|---|
| `PLANNING_SNACK_ENABLED` | `False` | Shows the **Snack** row in the weekly planner grid when `True`. Meals already planned as a snack (from before the setting was changed, or via the API) keep working either way; this only controls whether the planner *offers* the slot. |
| `NUTRITION_ALERTS_ENABLED` | `False` | Shows the **Nutritional intake** button in the weekly planner, and the "Possibly insufficient intake this week" deficiency alerts inside its dialog, when `True`. When `False` (the default), the button itself is hidden and the nutrition summary endpoint always returns an empty list of deficiencies; the carbon-footprint total is unaffected. |

## HTTPS and security

These settings live in `config/settings/prod.py` and only apply in production.

| Variable | Default | Description |
|---|---|---|
| `SECURE_SSL_REDIRECT` | `True` | Redirect plain-HTTP requests to HTTPS. Leave it on; the web server also redirects. |
| `SECURE_HSTS_SECONDS` | `604800` (one week) | Value of the `Strict-Transport-Security` header: how long browsers must refuse to reach the site over plain HTTP. |

Fixed settings (not configurable through the environment):

- `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` are on: cookies are only sent over HTTPS.
- `SECURE_PROXY_SSL_HEADER` is `X-Forwarded-Proto: https`: Django trusts this header, set by the
  reverse proxy, to know that the original request was HTTPS. The proxy in front of Gunicorn
  **must** set it, otherwise every request is redirected in a loop.
- HSTS is sent without `includeSubDomains` and without `preload`.

> [!CAUTION]
> Once browsers have seen the HSTS header, they refuse plain HTTP on your domain for
> `SECURE_HSTS_SECONDS`. The one-week default limits the damage if HTTPS breaks. Increase it
> (for example to `31536000`, one year) only once HTTPS has been working reliably.

## Docker-only variables

These are read by the compose files and the bundled Caddy, not by Django.

| Variable | Default | Mode | Description |
|---|---|---|---|
| `DOMAIN` | *(none, required)* | Standalone | Public domain served by the bundled Caddy (`deploy/Caddyfile.standalone`), which requests a Let's Encrypt certificate for it. |
| `ACME_EMAIL` | *(none, required)* | Standalone | Contact email given to Let's Encrypt (expiry and renewal notices). |
| `PROXY_NETWORK_NAME` | `proxy` | Shared proxy | Name of the existing external Docker network the host Caddy is attached to (`docker-compose.prod.proxy.yml`). |

`DOMAIN` and `ACME_EMAIL` are unused in the shared-proxy mode, and `PROXY_NETWORK_NAME` is
unused in standalone mode.

## Generate a secret key

Use a long value made of URL-safe characters:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(50))"
```

Paste the result as `DJANGO_SECRET_KEY` in `.env.prod` or `backend/.env`.

> [!TIP]
> Avoid keys containing `$`, `#`, quotes or spaces (Django's own `get_random_secret_key()` can
> produce `$` and `#`). Docker Compose may try to interpolate `$` in env files, and `#` can be
> read as the start of a comment.

Changing the key later logs everyone out; see
[Rotate the secret key](maintenance.md#rotate-the-secret-key).

## Settings that are not configurable

Some behaviour is fixed in `config/settings/base.py` and would require a code change:

| Setting | Value |
|---|---|
| Access token lifetime | 1 hour (refreshed automatically by the app) |
| Refresh token lifetime | 7 days: users must log in again after a week without using the app |
| Anonymous comment rate limit | 10 comments per hour per client |
| API page size | 20 items |
| Server language and time zone | `fr-fr`, `Europe/Paris` (used by the Django admin and emails; the app's own UI language is chosen by each user) |
| Static and media URLs | `/static/` and `/media/`, stored in `backend/staticfiles/` and `backend/media/` (`/app/staticfiles` and `/app/media` in the Docker image) |
