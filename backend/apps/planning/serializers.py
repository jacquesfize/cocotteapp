from rest_framework import serializers

from .models import MealPlanEntry


class MealPlanEntrySerializer(serializers.ModelSerializer):
    recipe_title = serializers.ReadOnlyField(source="recipe.title")

    class Meta:
        model = MealPlanEntry
        fields = ["id", "recipe", "recipe_title", "date", "meal_type", "servings"]
