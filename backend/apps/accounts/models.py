from django.contrib.auth.models import AbstractUser
from django.db import models


class DietType(models.TextChoices):
    OMNIVORE = "omnivore", "Omnivore"
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

    allergens = models.ManyToManyField(
        "ingredients.Allergen", through="UserAllergen", related_name="users", blank=True
    )

    def __str__(self):
        return self.username

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
