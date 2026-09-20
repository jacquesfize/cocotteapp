#!/bin/sh
set -e

# Migrations + fichiers statiques : uniquement avant de démarrer le serveur web.
if [ "$1" = "gunicorn" ]; then
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
fi

exec "$@"
