from rest_framework import serializers

from apps.ingredients.serializers import IngredientSerializer

from .models import ShoppingList, ShoppingListItem


class ShoppingListItemSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)

    class Meta:
        model = ShoppingListItem
        fields = ["id", "ingredient", "quantity", "unit", "is_owned", "is_checked"]


class ShoppingListSerializer(serializers.ModelSerializer):
    items = ShoppingListItemSerializer(many=True, read_only=True)

    class Meta:
        model = ShoppingList
        fields = ["id", "name", "items", "created_at"]
