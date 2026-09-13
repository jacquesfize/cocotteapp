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
    diet_type = models.CharField(max_length=20, choices=DietType.choices, default=DietType.OMNIVORE)
    activity_level = models.CharField(
        max_length=20, choices=ActivityLevel.choices, default=ActivityLevel.MODERATE
    )

    def __str__(self):
        return self.username
