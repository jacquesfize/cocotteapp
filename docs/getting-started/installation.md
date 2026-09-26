# Installation

This page shows how to run Cocotte on your own computer so you can try it or use it at home.
There are two ways to do it:

- **Docker** (recommended): one command starts PostgreSQL, the Django backend and the Vue
  frontend. You don't need Python, Node or PostgreSQL on your machine.
- **Classic**: you install the backend with `uv`, the frontend with `npm` and use a local
  PostgreSQL server. Use this if you already have these tools or don't want Docker.

> [!IMPORTANT]
> This page covers a **local** setup. It uses Django's development server and Vite's dev server,
> which are not meant for the internet. To host Cocotte on a server with HTTPS, follow
> [Production deployment](../admin-guide/deployment.md) instead.

Both options end with the same URLs:

| What | URL |
|---|---|
| The app | `http://localhost:5173/` |
| The API | `http://localhost:8000/api/` |
| Django admin | `http://localhost:8000/django-admin/` |

## Prerequisites

/// tab | Docker

- [Docker](https://docs.docker.com/get-docker/) with the Docker Compose plugin (`docker compose`).
- Git, to clone the repository.
- Free ports `5173` (frontend), `8000` (backend) and `5432` (PostgreSQL) on your machine.

///

/// tab | Classic

- **Python 3.11 or newer**.
- [**uv**](https://docs.astral.sh/uv/getting-started/installation/), the Python package manager
  the backend uses. There is no `requirements.txt`: dependencies live in `pyproject.toml` and
  `uv.lock`.
- **Node.js 22** and npm, for the frontend.
- **PostgreSQL** (the Docker setup uses version 16) with the `unaccent` and `pg_trgm`
  extensions available. They ship with the standard PostgreSQL packages. The migrations create
  them, so the database user needs permission to create extensions. The default `postgres`
  superuser works.
- **WeasyPrint system libraries**, used to render recipe and week PDFs: Pango, HarfBuzz,
  fontconfig and GLib, plus at least one font.
    - Debian/Ubuntu:

        ```bash
        sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfontconfig1 \
          libglib2.0-0 shared-mime-info fonts-liberation
        ```

    - macOS (Homebrew): `brew install pango`
    - Other systems: see
      [WeasyPrint's installation guide](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html).
- Git, to clone the repository.

///

## Get the code

```bash
git clone https://github.com/jacquesfize/cocotteapp.git cocotte
cd cocotte
```

## Configure and start

/// tab | Docker

1. Create the backend configuration file from the example:

    ```bash
    cp backend/.env.example backend/.env
    ```

    The defaults already point at the `db` container (`DATABASE_URL=postgres://postgres:postgres@db:5432/cocotte`),
    so you don't need to edit anything to get started.

2. Build and start the stack:

    ```bash
    docker compose up --build
    ```

    This starts three containers: `db` (PostgreSQL 16), `backend` (`manage.py runserver` on
    port 8000) and `frontend` (the Vite dev server on port 5173). Your code is mounted into the
    containers, so edits apply immediately.

3. Leave this terminal running. Open a second terminal for the commands in
   [First run](first-run.md).

Useful commands afterwards:

```bash
docker compose logs -f backend   # follow the logs (or "frontend", "db")
docker compose down              # stop the stack, keep the database
docker compose down -v           # stop the stack and DELETE the database
```

> [!NOTE]
> Re-run `docker compose up --build` only when dependencies change (`pyproject.toml`/`uv.lock` or
> `package.json`/`package-lock.json`).

///

/// tab | Classic

1. Create a PostgreSQL database for Cocotte, for example:

    ```bash
    createdb -U postgres cocotte
    ```

2. Install the backend dependencies and create its configuration file:

    ```bash
    cd backend
    uv sync --group dev
    cp .env.example .env
    ```

3. Edit `backend/.env` and point `DATABASE_URL` at **your** PostgreSQL server. The example file
   targets the Docker host name `db`, which doesn't exist outside Docker:

    ```dotenv
    DATABASE_URL=postgres://postgres:postgres@localhost:5432/cocotte
    ```

    The other defaults (`DEBUG=True`, `FRONTEND_URL=http://localhost:5173`, and emails printed to
    the console) are fine for local use. See [Configuration](../admin-guide/configuration.md) for
    every variable.

4. Prepare the database as described in [First run](first-run.md), then start the backend:

    ```bash
    uv run python manage.py runserver
    ```

5. In a second terminal, install and start the frontend:

    ```bash
    cd frontend
    npm install
    npm run dev
    ```

    The Vite dev server listens on port 5173 and forwards `/api`, `/django-admin`, `/static` and
    `/media` to the backend on port 8000. The backend must be running for the app to work.

///

## Check that it works

Open `http://localhost:5173/`. You should see the Cocotte home page. Until you complete
[First run](first-run.md), it shows no recipes and the database tables may not exist yet, so
some pages will fail to load.

> [!TIP]
> The interface starts in **French**. To switch to English, click the flag button in the top
> bar and choose **English**. See [The interface](../user-guide/index.md#language-and-theme).

## Next step

Continue with [First run](first-run.md) to create the database tables, your admin account and
the reference data.
