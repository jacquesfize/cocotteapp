from django.conf import settings
from django.core.exceptions import ValidationError
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


class PlanningPermission(models.TextChoices):
    READ = "read", "Lecture seule"
    WRITE = "write", "Lecture et écriture"


class PlanningShare(models.Model):
    """Grants another user access to view (and optionally edit) one's meal-planning agenda."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="planning_shares_given"
    )
    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="planning_shares_received"
    )
    permission = models.CharField(
        max_length=10, choices=PlanningPermission.choices, default=PlanningPermission.READ
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("owner", "shared_with")

    def clean(self):
        super().clean()
        if self.owner_id is not None and self.owner_id == self.shared_with_id:
            raise ValidationError("Un agenda ne peut pas être partagé avec soi-même.")

    def __str__(self):
        return f"{self.owner} -> {self.shared_with} ({self.permission})"
