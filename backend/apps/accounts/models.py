from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class DietType(models.TextChoices):
    # Valeur stockée historique "omnivore" conservée ; affichée « Flexitarien ».
    OMNIVORE = "omnivore", "Flexitarien"
    VEGETARIAN = "vegetarian", "Végétarien"
    VEGAN = "vegan", "Végan"


class ActivityLevel(models.TextChoices):
    SEDENTARY = "sedentary", "Sédentaire"
    MODERATE = "moderate", "Modéré"
    ATHLETE = "athlete", "Sportif"


class AllergySeverity(models.TextChoices):
    ALLERGY = "allergy", "Allergie"
    INTOLERANCE = "intolerance", "Intolérance"


class User(AbstractUser):
    email = models.EmailField("email address", unique=True)

    # On se connecte avec l'email plutôt que le nom d'utilisateur ; ce dernier reste un
    # identifiant affiché (auteur d'une recette, etc.) mais n'est plus utilisé pour l'auth.
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    diet_type = models.CharField(max_length=20, choices=DietType.choices, default=DietType.OMNIVORE)
    activity_level = models.CharField(
        max_length=20, choices=ActivityLevel.choices, default=ActivityLevel.MODERATE
    )

    # RGPD art. 9 : allergies, intolérances et régime peuvent révéler des données de santé ou des
    # convictions ; on conserve la preuve du consentement explicite (date + version du texte).
    health_data_consent_at = models.DateTimeField(null=True, blank=True)
    health_data_consent_version = models.CharField(max_length=20, blank=True)

    # Date du dernier e-mail de préavis avant suppression pour inactivité (cf. purge_inactive_users).
    inactivity_warned_at = models.DateTimeField(null=True, blank=True)

    allergens = models.ManyToManyField(
        "ingredients.Allergen", through="UserAllergen", related_name="users", blank=True
    )

    def __str__(self):
        return self.username

    def grant_health_data_consent(self):
        self.health_data_consent_at = timezone.now()
        self.health_data_consent_version = settings.PRIVACY_POLICY_VERSION
        self.save(update_fields=["health_data_consent_at", "health_data_consent_version"])

    def withdraw_health_data_consent(self):
        """Retire le consentement et efface les données concernées (allergies, régime, activité)."""
        self.allergen_links.all().delete()
        self.diet_type = DietType.OMNIVORE
        self.activity_level = ActivityLevel.MODERATE
        self.health_data_consent_at = None
        self.health_data_consent_version = ""
        self.save(
            update_fields=[
                "diet_type",
                "activity_level",
                "health_data_consent_at",
                "health_data_consent_version",
            ]
        )

    def allergen_slugs(self, severity=None):
        rows = self.allergen_links.all()
        if severity:
            rows = rows.filter(severity=severity)
        return list(rows.values_list("allergen__slug", flat=True))


class UserAllergen(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="allergen_links")
    allergen = models.ForeignKey("ingredients.Allergen", on_delete=models.CASCADE)
    severity = models.CharField(
        max_length=20, choices=AllergySeverity.choices, default=AllergySeverity.ALLERGY
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "allergen"], name="unique_user_allergen")
        ]


class AuditLog(models.Model):
    """Trace d'une action de modération faite par un compte staff
    (modification/suppression d'une recette, d'un article, d'un compte, fusion de doublons,
    masquage d'un commentaire...). Les libellés sont figés à l'écriture : la ligne reste lisible
    quand l'objet ou l'acteur est supprimé."""

    class Action(models.TextChoices):
        UPDATE = "update", "Modification"
        DELETE = "delete", "Suppression"
        MERGE = "merge", "Fusion"
        HIDE_COMMENT = "hide_comment", "Commentaire masqué"
        UNHIDE_COMMENT = "unhide_comment", "Commentaire réaffiché"

    actor = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_logs"
    )
    actor_label = models.CharField(max_length=254)
    action = models.CharField(max_length=20, choices=Action.choices)
    target_type = models.CharField(max_length=100)
    target_id = models.CharField(max_length=50, blank=True)
    target_label = models.CharField(max_length=255, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.actor_label} — {self.action} — {self.target_type} {self.target_label}"
