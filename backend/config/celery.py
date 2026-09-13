import os

from celery import Celery
from celery.signals import worker_process_init

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("cocotte")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@worker_process_init.connect
def _close_inherited_db_connections(**kwargs):
    # The prefork pool forks worker children from a parent process that may already
    # hold an open DB connection; libpq's connection state isn't fork-safe, so a child
    # reusing it can crash with a SIGSEGV instead of a catchable exception.
    from django.db import connections

    connections.close_all()
