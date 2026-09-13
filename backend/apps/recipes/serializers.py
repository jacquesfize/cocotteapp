from django.db import models
from rest_framework import serializers

from apps.ingredients.models import Ingredient
from apps.ingredients.serializers import IngredientSerializer

from .models import Recipe, RecipeIngredient, RecipeStep, Tag, ThematicPage
from .youtube import extract_youtube_id


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "kind"]


class ThematicPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThematicPage
        fields = ["id", "title", "slug", "description", "icon", "filters", "order"]


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


class RecipeVersionSerializer(serializers.ModelSerializer):
    """Lightweight representation of a sibling version, used in RecipeSerializer.versions."""

    author = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = Recipe
        fields = ["id", "slug", "title", "version_label", "author"]


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(source="recipe_ingredients", many=True, required=False)
    steps = RecipeStepSerializer(many=True, required=False)
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.ReadOnlyField(source="author.username")
    author_id = serializers.ReadOnlyField(source="author.id")
    youtube_id = serializers.SerializerMethodField()
    versions = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "author",
            "author_id",
            "servings",
            "prep_time_minutes",
            "cook_time_minutes",
            "total_time_minutes",
            "diet_type",
            "source_type",
            "source_url",
            "video_url",
            "youtube_id",
            "image",
            "image_url",
            "is_public",
            "tags",
            "ingredients",
            "steps",
            "root_recipe",
            "version_label",
            "versions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "total_time_minutes", "root_recipe"]

    def get_youtube_id(self, obj):
        return extract_youtube_id(obj.video_url)

    def get_versions(self, obj):
        if obj.root_recipe_id is None and not obj.versions.exists():
            return []
        root = obj.root()
        siblings = (
            Recipe.objects.filter(models.Q(pk=root.pk) | models.Q(root_recipe=root))
            .exclude(pk=obj.pk)
            .select_related("author")
        )
        return RecipeVersionSerializer(siblings, many=True).data

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
