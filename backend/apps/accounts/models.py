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

    def __str__(self):
        return self.username
