from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Supprime les comptes sans connexion depuis INACTIVE_ACCOUNT_RETENTION_DAYS jours, après "
        "un e-mail de préavis envoyé INACTIVE_ACCOUNT_WARNING_DAYS jours avant (RGPD : durée de "
        "conservation). À planifier chaque jour (cron). Les comptes staff ne sont jamais touchés."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Affiche sans envoyer ni supprimer.")

    def handle(self, *args, dry_run=False, **options):
        retention = settings.INACTIVE_ACCOUNT_RETENTION_DAYS
        if retention <= 0:
            self.stdout.write("INACTIVE_ACCOUNT_RETENTION_DAYS vaut 0 : purge désactivée.")
            return
        warning = min(settings.INACTIVE_ACCOUNT_WARNING_DAYS, retention)
        now = timezone.now()

        candidates = User.objects.filter(is_staff=False, is_superuser=False, is_active=True)

        to_delete, to_warn = [], []
        for user in candidates.filter(
            Q(last_login__lt=now - timedelta(days=retention - warning))
            | Q(last_login__isnull=True, date_joined__lt=now - timedelta(days=retention - warning))
        ):
            # Repère d'activité : dernière connexion, ou inscription si jamais connecté.
            activity = user.last_login or user.date_joined
            warned = user.inactivity_warned_at and user.inactivity_warned_at > activity
            if not warned:
                to_warn.append(user)
            elif (
                activity < now - timedelta(days=retention)
                and user.inactivity_warned_at <= now - timedelta(days=warning)
            ):
                to_delete.append(user)

        for user in to_warn:
            self.stdout.write(f"Préavis : {user.email}")
            if not dry_run:
                self._send_warning(user, warning)
                user.inactivity_warned_at = now
                user.save(update_fields=["inactivity_warned_at"])
        for user in to_delete:
            self.stdout.write(f"Suppression : {user.email}")
            if not dry_run:
                user.delete()

        suffix = " (simulation)" if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(f"{len(to_warn)} préavis, {len(to_delete)} suppression(s){suffix}.")
        )

    def _send_warning(self, user, warning_days):
        send_mail(
            "Cocotte — votre compte sera bientôt supprimé",
            f"Bonjour {user.username},\n\n"
            f"Vous ne vous êtes pas connecté à Cocotte depuis longtemps. Conformément à notre "
            f"politique de conservation des données, votre compte et vos données (recettes, "
            f"agenda, listes de courses) seront supprimés dans {warning_days} jours.\n\n"
            f"Pour le conserver, il suffit de vous connecter : {settings.FRONTEND_URL}/login\n",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
