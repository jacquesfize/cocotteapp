from django.db import models
from django.db.models import Q
from django.utils import timezone


class AnnouncementQuerySet(models.QuerySet):
    def active(self):
        """Annonces activées dont la fenêtre de dates (facultative) contient l'instant présent."""
        now = timezone.now()
        return self.filter(is_active=True).filter(
            Q(starts_at__isnull=True) | Q(starts_at__lte=now),
            Q(ends_at__isnull=True) | Q(ends_at__gt=now),
        )


class Announcement(models.Model):
    """Message affiché en bandeau en haut du site (maintenance, nouveauté...). Géré dans le
    Django admin ; le texte est saisi en français et en anglais (repli sur l'autre langue)."""

    class Level(models.TextChoices):
        INFO = "info", "Information"
        WARNING = "warning", "Avertissement"
        CRITICAL = "critical", "Critique (maintenance)"

    level = models.CharField(max_length=10, choices=Level.choices, default=Level.INFO)
    title_fr = models.CharField("titre (FR)", max_length=120, blank=True)
    title_en = models.CharField("titre (EN)", max_length=120, blank=True)
    message_fr = models.TextField("message (FR)", blank=True)
    message_en = models.TextField("message (EN)", blank=True)
    link_url = models.CharField(
        "lien", max_length=500, blank=True, help_text="URL complète ou chemin du site (ex. /blog)."
    )
    link_label_fr = models.CharField("libellé du lien (FR)", max_length=60, blank=True)
    link_label_en = models.CharField("libellé du lien (EN)", max_length=60, blank=True)
    dismissible = models.BooleanField(
        "peut être fermée", default=True, help_text="Décochée : le bandeau reste affiché (ex. maintenance)."
    )
    is_active = models.BooleanField("activée", default=True)
    starts_at = models.DateTimeField("début", null=True, blank=True, help_text="Vide : visible tout de suite.")
    ends_at = models.DateTimeField("fin", null=True, blank=True, help_text="Vide : visible sans limite.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = AnnouncementQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title_fr or self.title_en or self.message_fr or self.message_en
