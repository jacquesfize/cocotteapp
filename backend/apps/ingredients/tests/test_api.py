import pytest
from rest_framework.test import APIClient

from apps.ingredients.factories import IngredientFactory


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
