import pytest
from rest_framework.test import APIClient

from apps.ingredients.factories import IngredientFactory
from apps.recipes.factories import RecipeFactory, RecipeIngredientFactory


def make_recipe(title, carbon_per_kg, quantity, servings=2, unit="g"):
    recipe = RecipeFactory(title=title, servings=servings)
    RecipeIngredientFactory(
        recipe=recipe,
        ingredient=IngredientFactory(carbon_kg_co2e_per_kg=carbon_per_kg),
        quantity=quantity,
        unit=unit,
    )
    return recipe


@pytest.fixture
def recipes(db):
    # par portion : 0.2, 1.0, 3.0 kg CO2e ; et une recette sans ingrédient (0)
    make_recipe("Faible", 1, 400)
    make_recipe("Moyen", 10, 200)
    make_recipe("Eleve", 30, 200)
    RecipeFactory(title="Vide")


def titles(params):
    response = APIClient().get("/api/recipes/", params)
    assert response.status_code == 200
    return {r["title"] for r in response.json()["results"]}


def test_max_carbon(recipes):
    assert titles({"max_carbon": "1"}) == {"Faible", "Moyen", "Vide"}
    assert titles({"max_carbon": "0.1"}) == {"Vide"}


def test_carbon_levels(recipes):
    assert titles({"carbon_level": "low"}) == {"Faible", "Vide"}
    assert titles({"carbon_level": "medium"}) == {"Moyen"}
    assert titles({"carbon_level": "high"}) == {"Eleve"}


def test_carbon_uses_unit_conversion_and_servings(db):
    make_recipe("Kg", 2, 1, servings=4, unit="kg")  # 2 kg CO2e / 4 = 0.5 par portion
    assert titles({"carbon_level": "low"}) == {"Kg"}


def test_carbon_filter_combines(recipes):
    assert titles({"carbon_level": "high", "max_carbon": "5"}) == {"Eleve"}


def test_invalid_carbon_level_rejected(recipes):
    assert APIClient().get("/api/recipes/", {"carbon_level": "x"}).status_code == 400
