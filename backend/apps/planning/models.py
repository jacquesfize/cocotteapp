from django.conf import settings
from django.db import models

from apps.recipes.models import Recipe


class MealType(models.TextChoices):
    BREAKFAST = "breakfast", "Petit-déjeuner"
    LUNCH = "lunch", "Déjeuner"
    DINNER = "dinner", "Dîner"
    SNACK = "snack", "Collation"


class MealPlanEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="meal_plan_entries")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="meal_plan_entries")
    date = models.DateField()
    meal_type = models.CharField(max_length=20, choices=MealType.choices, default=MealType.DINNER)
    servings = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ["date", "meal_type"]
        unique_together = ("user", "recipe", "date", "meal_type")

    def __str__(self):
        return f"{self.date} - {self.recipe.title}"
