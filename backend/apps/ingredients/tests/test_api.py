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


@pytest.fixture
def staff_client(db):
    from apps.accounts.factories import UserFactory

    client = APIClient()
    client.force_authenticate(UserFactory(is_staff=True))
    return client


@pytest.fixture
def user_client(db):
    from apps.accounts.factories import UserFactory

    client = APIClient()
    client.force_authenticate(UserFactory())
    return client


@pytest.mark.django_db
def test_search_ingredients_by_english_translation():
    IngredientFactory(name="ail", translations={"en": "garlic"})
    IngredientFactory(name="oignon", translations={"en": "onion"})
    response = APIClient().get("/api/ingredients/?search=garl")
    assert response.data["count"] == 1
    assert response.data["results"][0]["name"] == "ail"


def test_regular_user_can_still_create_ingredient(user_client):
    response = user_client.post("/api/ingredients/", {"name": "Poireau"}, format="json")
    assert response.status_code == 201


@pytest.mark.django_db
def test_anonymous_cannot_create_ingredient():
    response = APIClient().post("/api/ingredients/", {"name": "Poireau"}, format="json")
    assert response.status_code in (401, 403)


def test_regular_user_cannot_update_or_delete(user_client):
    ingredient = IngredientFactory()
    url = f"/api/ingredients/{ingredient.id}/"
    assert user_client.patch(url, {"name": "x"}, format="json").status_code == 403
    assert user_client.delete(url).status_code == 403


def test_staff_can_update_ingredient(staff_client):
    ingredient = IngredientFactory()
    response = staff_client.patch(
        f"/api/ingredients/{ingredient.id}/",
        {"name": "Ail", "translations": {"en": "garlic"}, "available_months": [6, 7]},
        format="json",
    )
    assert response.status_code == 200
    ingredient.refresh_from_db()
    assert ingredient.translations == {"en": "garlic"}
    assert ingredient.available_months == [6, 7]


def test_staff_can_delete_unused_ingredient(staff_client):
    ingredient = IngredientFactory()
    assert staff_client.delete(f"/api/ingredients/{ingredient.id}/").status_code == 204


def test_delete_ingredient_used_by_recipe_is_blocked(staff_client):
    from apps.recipes.factories import RecipeIngredientFactory

    ri = RecipeIngredientFactory()
    response = staff_client.delete(f"/api/ingredients/{ri.ingredient_id}/")
    assert response.status_code == 409
    assert "detail" in response.data
