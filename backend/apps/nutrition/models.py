from django.db import models

from apps.accounts.models import ActivityLevel, DietType


class NutrientRequirement(models.Model):
    diet_type = models.CharField(max_length=20, choices=DietType.choices)
    activity_level = models.CharField(max_length=20, choices=ActivityLevel.choices)
    nutrient = models.CharField(max_length=50, help_text="Doit correspondre à un champ nutritionnel d'Ingredient")
    unit = models.CharField(max_length=10)
    daily_minimum = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        unique_together = ("diet_type", "activity_level", "nutrient")

    def __str__(self):
        return f"{self.nutrient} ({self.diet_type}/{self.activity_level})"
