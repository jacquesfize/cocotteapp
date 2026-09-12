from rest_framework import serializers

from .models import MealPlanEntry


class MealPlanEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MealPlanEntry
        fields = ["id", "recipe", "date", "meal_type", "servings"]
