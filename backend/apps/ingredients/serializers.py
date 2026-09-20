from rest_framework import serializers

from .models import Allergen, Ingredient


class AllergenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergen
        fields = ["slug", "name"]


class IngredientSerializer(serializers.ModelSerializer):
    allergens = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=Allergen.objects.all(), required=False
    )

    class Meta:
        model = Ingredient
        fields = "__all__"
        read_only_fields = ["slug"]
