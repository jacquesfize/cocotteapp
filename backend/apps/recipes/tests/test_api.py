import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.ingredients.factories import IngredientFactory
from apps.recipes.factories import RecipeFactory


@pytest.mark.django_db
def test_create_recipe_with_nested_ingredients():
    user = UserFactory()
    ingredient = IngredientFactory()
    client = APIClient()
    client.force_authenticate(user)

    payload = {
        "title": "Curry de lentilles",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "diet_type": "vegan",
        "ingredients": [
            {"ingredient_id": ingredient.id, "quantity": "200", "unit": "g", "order": 1}
        ],
        "steps": [{"order": 1, "instruction": "Faire revenir les oignons."}],
    }
    response = client.post("/api/recipes/", payload, format="json")

    assert response.status_code == 201
    assert response.data["ingredients"][0]["ingredient"]["id"] == ingredient.id
    assert response.data["steps"][0]["instruction"] == "Faire revenir les oignons."


@pytest.mark.django_db
def test_filter_recipes_by_diet_type():
    RecipeFactory(diet_type="vegan")
    RecipeFactory(diet_type="omnivore")

    client = APIClient()
    response = client.get("/api/recipes/?diet_type=vegan")
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_filter_recipes_by_max_time():
    RecipeFactory(prep_time_minutes=10, cook_time_minutes=10)
    RecipeFactory(prep_time_minutes=30, cook_time_minutes=30)

    client = APIClient()
    response = client.get("/api/recipes/?max_prep_time=15&max_cook_time=15")
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_anonymous_cannot_create_recipe():
    client = APIClient()
    response = client.post("/api/recipes/", {"title": "Test"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_random_recipe_returns_one_of_the_existing_recipes():
    recipes = RecipeFactory.create_batch(5)
    ids = {r.id for r in recipes}

    client = APIClient()
    response = client.get("/api/recipes/random/")

    assert response.status_code == 200
    assert response.data["id"] in ids


@pytest.mark.django_db
def test_random_recipe_respects_filters():
    RecipeFactory(diet_type="vegan")
    RecipeFactory(diet_type="omnivore")

    client = APIClient()
    response = client.get("/api/recipes/random/?diet_type=vegan")

    assert response.status_code == 200
    assert response.data["diet_type"] == "vegan"


@pytest.mark.django_db
def test_random_recipe_404_when_no_match():
    RecipeFactory(diet_type="omnivore")

    client = APIClient()
    response = client.get("/api/recipes/random/?diet_type=vegan")

    assert response.status_code == 404
