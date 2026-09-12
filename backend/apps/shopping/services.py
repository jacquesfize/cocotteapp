from collections import defaultdict
from decimal import Decimal

from .models import ShoppingList, ShoppingListItem


def build_shopping_list(user, meal_plan_entries, name="Liste de courses"):
    meal_plan_entries = list(meal_plan_entries)
    aggregated = defaultdict(Decimal)
    for entry in meal_plan_entries:
        ratio = Decimal(entry.servings) / Decimal(entry.recipe.servings or 1)
        for recipe_ingredient in entry.recipe.recipe_ingredients.select_related("ingredient"):
            key = (recipe_ingredient.ingredient_id, recipe_ingredient.unit)
            aggregated[key] += recipe_ingredient.quantity * ratio

    shopping_list = ShoppingList.objects.create(user=user, name=name)
    shopping_list.meal_plan_entries.set(meal_plan_entries)

    items = [
        ShoppingListItem(shopping_list=shopping_list, ingredient_id=ingredient_id, unit=unit, quantity=quantity)
        for (ingredient_id, unit), quantity in aggregated.items()
    ]
    ShoppingListItem.objects.bulk_create(items)
    return shopping_list


def mark_owned(shopping_list, owned_ingredient_ids):
    shopping_list.items.filter(ingredient_id__in=owned_ingredient_ids).update(is_owned=True)


def export_as_text(shopping_list):
    lines = [shopping_list.name, ""]
    for item in shopping_list.items.filter(is_owned=False).select_related("ingredient"):
        lines.append(f"- {item.quantity}{item.unit} {item.ingredient.name}")
    return "\n".join(lines)
