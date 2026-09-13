from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.ingredients.factories import IngredientFactory


@pytest.mark.django_db
def test_nutrition_suggestion_requires_name():
    client = APIClient()
    response = client.get("/api/ingredients/nutrition-suggestion/")
    assert response.status_code == 400


@pytest.mark.django_db
def test_nutrition_suggestion_returns_found_when_service_has_a_match():
    client = APIClient()
    with (
        patch("apps.ingredients.views.lookup_nutrition_suggestion", return_value={"calories_kcal": 149}),
        patch("apps.ingredients.views.lookup_carbon_footprint", return_value=None),
    ):
        response = client.get("/api/ingredients/nutrition-suggestion/?name=ail")

    assert response.status_code == 200
    assert response.data == {"found": True, "suggestion": {"calories_kcal": 149}}


@pytest.mark.django_db
def test_nutrition_suggestion_returns_not_found_when_service_has_no_match():
    client = APIClient()
    with (
        patch("apps.ingredients.views.lookup_nutrition_suggestion", return_value=None),
        patch("apps.ingredients.views.lookup_carbon_footprint", return_value=None),
    ):
        response = client.get("/api/ingredients/nutrition-suggestion/?name=ingredient-inconnu")

    assert response.status_code == 200
    assert response.data == {"found": False}


@pytest.mark.django_db
def test_nutrition_suggestion_merges_carbon_footprint_into_suggestion():
    client = APIClient()
    with (
        patch("apps.ingredients.views.lookup_nutrition_suggestion", return_value={"calories_kcal": 149}),
        patch("apps.ingredients.views.lookup_carbon_footprint", return_value=0.383),
    ):
        response = client.get("/api/ingredients/nutrition-suggestion/?name=ail")

    assert response.status_code == 200
    assert response.data == {
        "found": True,
        "suggestion": {"calories_kcal": 149, "carbon_kg_co2e_per_kg": 0.383},
    }


@pytest.mark.django_db
def test_nutrition_suggestion_found_from_carbon_footprint_alone():
    client = APIClient()
    with (
        patch("apps.ingredients.views.lookup_nutrition_suggestion", return_value=None),
        patch("apps.ingredients.views.lookup_carbon_footprint", return_value=0.383),
    ):
        response = client.get("/api/ingredients/nutrition-suggestion/?name=ail")

    assert response.status_code == 200
    assert response.data == {"found": True, "suggestion": {"carbon_kg_co2e_per_kg": 0.383}}


@pytest.mark.django_db
def test_list_ingredients():
    IngredientFactory.create_batch(3)
    client = APIClient()
    response = client.get("/api/ingredients/")
    assert response.status_code == 200
    assert response.data["count"] == 3


@pytest.mark.django_db
def test_filter_ingredients_by_category():
    IngredientFactory(category="fruit")
    IngredientFactory(category="vegetable")
    client = APIClient()
    response = client.get("/api/ingredients/?category=fruit")
    assert response.data["count"] == 1
