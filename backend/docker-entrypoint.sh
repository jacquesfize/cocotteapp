#!/bin/sh
set -e

# Migrations + fichiers statiques : uniquement avant de démarrer le serveur web, pas avant
# les workers Celery (qui démarrent en parallèle et n'en ont pas besoin).
if [ "$1" = "gunicorn" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
fi

exec "$@"
