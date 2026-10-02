from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.ingredients.factories import IngredientFactory
from apps.planning.models import MealPlanEntry
from apps.recipes.factories import RecipeFactory, RecipeIngredientFactory


@pytest.mark.django_db
def test_create_shopping_list_from_meal_plan():
    user = UserFactory()
    ingredient = IngredientFactory()
    recipe = RecipeFactory(servings=2)
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("100"), unit="g")
    entry = MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-01", servings=2)

    client = APIClient()
    client.force_authenticate(user)
    response = client.post("/api/shopping-lists/", {"meal_plan_entry_ids": [entry.id]}, format="json")

    assert response.status_code == 201
    assert len(response.data["items"]) == 1


@pytest.mark.django_db
def test_mark_owned_action():
    user = UserFactory()
    ingredient = IngredientFactory()
    recipe = RecipeFactory(servings=1)
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("50"), unit="g")
    entry = MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-01", servings=1)

    client = APIClient()
    client.force_authenticate(user)
    create_response = client.post("/api/shopping-lists/", {"meal_plan_entry_ids": [entry.id]}, format="json")
    list_id = create_response.data["id"]

    response = client.post(
        f"/api/shopping-lists/{list_id}/mark_owned/", {"ingredient_ids": [ingredient.id]}, format="json"
    )
    assert response.status_code == 200
    assert response.data["items"][0]["is_owned"] is True


@pytest.mark.django_db
def test_mark_owned_action_can_unset_owned():
    user = UserFactory()
    ingredient = IngredientFactory()
    recipe = RecipeFactory(servings=1)
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("50"), unit="g")
    entry = MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-01", servings=1)

    client = APIClient()
    client.force_authenticate(user)
    create_response = client.post("/api/shopping-lists/", {"meal_plan_entry_ids": [entry.id]}, format="json")
    list_id = create_response.data["id"]

    client.post(f"/api/shopping-lists/{list_id}/mark_owned/", {"ingredient_ids": [ingredient.id]}, format="json")

    response = client.post(
        f"/api/shopping-lists/{list_id}/mark_owned/",
        {"ingredient_ids": [ingredient.id], "owned": False},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["items"][0]["is_owned"] is False


@pytest.mark.django_db
def test_shopping_list_list_is_paginated():
    from apps.shopping.models import ShoppingList

    user = UserFactory()
    for i in range(22):
        ShoppingList.objects.create(user=user, name=f"Liste {i}")

    client = APIClient()
    client.force_authenticate(user)

    response = client.get("/api/shopping-lists/")
    assert response.data["count"] == 22
    assert len(response.data["results"]) == 20
    assert response.data["next"] is not None
