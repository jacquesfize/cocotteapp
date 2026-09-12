from decimal import Decimal

import pytest

from apps.accounts.factories import UserFactory
from apps.ingredients.factories import IngredientFactory
from apps.planning.models import MealPlanEntry
from apps.recipes.factories import RecipeFactory, RecipeIngredientFactory
from apps.shopping.services import build_shopping_list, export_as_text, mark_owned


@pytest.mark.django_db
def test_build_shopping_list_aggregates_quantities():
    user = UserFactory()
    ingredient = IngredientFactory(name="Riz")
    recipe = RecipeFactory(servings=2)
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("100"), unit="g")

    entry1 = MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-01", servings=2)
    entry2 = MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-02", servings=4)

    shopping_list = build_shopping_list(user, [entry1, entry2])

    item = shopping_list.items.get(ingredient=ingredient)
    assert item.quantity == Decimal("300.00")


@pytest.mark.django_db
def test_export_excludes_owned_items():
    user = UserFactory()
    ingredient = IngredientFactory(name="Sel")
    recipe = RecipeFactory(servings=1)
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("5"), unit="g")
    entry = MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-01", servings=1)

    shopping_list = build_shopping_list(user, [entry])
    mark_owned(shopping_list, [ingredient.id])

    assert "Sel" not in export_as_text(shopping_list)
