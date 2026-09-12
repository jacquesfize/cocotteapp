from rest_framework import serializers

from apps.ingredients.models import Ingredient
from apps.ingredients.serializers import IngredientSerializer

from .models import Recipe, RecipeIngredient, RecipeStep, Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "kind"]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient", write_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ["id", "ingredient", "ingredient_id", "quantity", "unit", "group_name", "order"]


class RecipeStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecipeStep
        fields = ["id", "order", "instruction"]


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(source="recipe_ingredients", many=True, required=False)
    steps = RecipeStepSerializer(many=True, required=False)
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "author",
            "servings",
            "prep_time_minutes",
            "cook_time_minutes",
            "total_time_minutes",
            "diet_type",
            "source_type",
            "source_url",
            "image",
            "is_public",
            "tags",
            "ingredients",
            "steps",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "total_time_minutes"]

    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        steps_data = validated_data.pop("steps", [])
        recipe = Recipe.objects.create(**validated_data)
        self._sync_children(recipe, ingredients_data, steps_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", None)
        steps_data = validated_data.pop("steps", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if ingredients_data is not None or steps_data is not None:
            self._sync_children(instance, ingredients_data or [], steps_data or [], replace=True)
        return instance

    @staticmethod
    def _sync_children(recipe, ingredients_data, steps_data, replace=False):
        if replace:
            recipe.recipe_ingredients.all().delete()
            recipe.steps.all().delete()
        for data in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **data)
        for data in steps_data:
            RecipeStep.objects.create(recipe=recipe, **data)
