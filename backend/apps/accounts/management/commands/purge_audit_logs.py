from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.accounts.models import AuditLog


class Command(BaseCommand):
    help = (
        "Supprime les lignes du journal de modération plus anciennes que AUDIT_LOG_RETENTION_DAYS "
        "(RGPD : durée de conservation). À planifier chaque jour (cron)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Compte sans supprimer.")

    def handle(self, *args, dry_run=False, **options):
        retention = settings.AUDIT_LOG_RETENTION_DAYS
        if retention <= 0:
            self.stdout.write("AUDIT_LOG_RETENTION_DAYS vaut 0 : purge désactivée.")
            return
        old = AuditLog.objects.filter(created_at__lt=timezone.now() - timedelta(days=retention))
        count = old.count()
        if not dry_run:
            old.delete()
        suffix = " (simulation)" if dry_run else ""
        self.stdout.write(self.style.SUCCESS(f"{count} ligne(s) du journal supprimée(s){suffix}."))
