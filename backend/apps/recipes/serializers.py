from django.db import models
from rest_framework import serializers

from apps.accounts.models import DietType
from apps.ingredients.models import Ingredient
from apps.ingredients.serializers import IngredientSerializer

from .models import Recipe, RecipeComment, RecipeIngredient, RecipeStep, Tag, ThematicPage
from .youtube import extract_youtube_id


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "kind"]


class ThematicPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThematicPage
        fields = ["id", "title", "slug", "description", "icon", "filters", "order"]


class AdminThematicPageSerializer(serializers.ModelSerializer):
    """Utilisée par l'API d'administration (`/api/admin/thematic-pages/`) : contrairement à
    `ThematicPageSerializer` (lecture seule, publique, réservée aux pages actives), celle-ci
    expose aussi `is_active` et `created_at` et autorise l'écriture pour permettre la gestion
    complète des pages thématiques depuis l'interface staff."""

    class Meta:
        model = ThematicPage
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "icon",
            "filters",
            "order",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["slug", "created_at"]


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


class RecipeCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(max_length=80, required=False, allow_blank=True)
    body = serializers.CharField(max_length=2000)
    username = serializers.SerializerMethodField()

    class Meta:
        model = RecipeComment
        fields = ["id", "recipe", "author_name", "username", "body", "is_hidden", "created_at"]
        read_only_fields = ["id", "recipe", "username", "is_hidden", "created_at"]

    def get_username(self, obj):
        return obj.user.username if obj.user_id else None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if not self._can_see_hidden(request):
            self.fields.pop("is_hidden", None)

    def _can_see_hidden(self, request):
        if request is None or not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        recipe = self.context.get("recipe")
        return recipe is not None and recipe.author_id == request.user.id

    def validate_body(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le commentaire ne peut pas être vide.")
        return value

    def validate_author_name(self, value):
        return value.strip()

    def validate(self, attrs):
        request = self.context.get("request")
        author_name = attrs.get("author_name", "")
        user = getattr(request, "user", None) if request else None
        if not author_name:
            if user is not None and user.is_authenticated:
                attrs["author_name"] = user.username
            else:
                raise serializers.ValidationError(
                    {"author_name": "Merci d'indiquer un nom."}
                )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        if user is not None and user.is_authenticated:
            validated_data["user"] = user
        return super().create(validated_data)


class CooklangImportSerializer(serializers.Serializer):
    """Input for POST /api/recipes/import-cooklang/: raw Cooklang text plus a
    handful of recipe-level fields the markup itself doesn't carry."""

    title = serializers.CharField(max_length=200)
    raw_cooklang = serializers.CharField()
    servings = serializers.IntegerField(required=False, min_value=1)
    prep_time_minutes = serializers.IntegerField(required=False, min_value=0)
    cook_time_minutes = serializers.IntegerField(required=False, min_value=0)
    diet_type = serializers.ChoiceField(choices=DietType.choices, required=False)
