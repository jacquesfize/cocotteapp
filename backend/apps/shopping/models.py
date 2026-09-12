from django.conf import settings
from django.db import models

from apps.ingredients.models import Ingredient, Unit
from apps.planning.models import MealPlanEntry


class ShoppingList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shopping_lists")
    name = models.CharField(max_length=120, default="Liste de courses")
    meal_plan_entries = models.ManyToManyField(MealPlanEntry, blank=True, related_name="shopping_lists")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class ShoppingListItem(models.Model):
    shopping_list = models.ForeignKey(ShoppingList, on_delete=models.CASCADE, related_name="items")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name="shopping_list_items")
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=10, choices=Unit.choices)
    is_owned = models.BooleanField(default=False)
    is_checked = models.BooleanField(default=False)

    class Meta:
        ordering = ["ingredient__category", "ingredient__name"]
        unique_together = ("shopping_list", "ingredient", "unit")

    def __str__(self):
        return f"{self.quantity}{self.unit} {self.ingredient.name}"
