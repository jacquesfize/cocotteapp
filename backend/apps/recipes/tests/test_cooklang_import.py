from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.ingredients.models import Ingredient, Unit
from apps.recipes.cooklang_import import create_recipe_from_cooklang, map_unit, parse_quantity
from apps.recipes.models import RecipeIngredient, RecipeStep, SourceType

COOKLANG_TEXT = """\
Peel and dice @onion{1%piece} and @garlic clove.
Heat @olive_oil{2%tbsp} in a #pan{} for ~{5 minutes}.
Add @tomato{400%g} and a pinch of salt.
"""


@pytest.mark.django_db
def test_creates_recipe_with_ingredients_and_steps():
    user = UserFactory()

    recipe = create_recipe_from_cooklang(
        author=user,
        title="Tomato pan-fry",
        raw_cooklang=COOKLANG_TEXT,
        servings=3,
    )

    assert recipe.source_type == SourceType.COOKLANG
    assert recipe.raw_cooklang == COOKLANG_TEXT
    assert recipe.servings == 3
    assert recipe.author_id == user.id

    ingredients = list(recipe.recipe_ingredients.select_related("ingredient").order_by("order"))
    names = [ri.ingredient.name for ri in ingredients]
    assert names == ["onion", "garlic", "olive oil", "tomato"]

    onion = ingredients[0]
    assert onion.quantity == Decimal("1")
    assert onion.unit == Unit.PIECE

    garlic = ingredients[1]
    # No quantity/unit in the markup at all -> defaults.
    assert garlic.quantity == Decimal("1")
    assert garlic.unit == Unit.PIECE

    olive_oil = ingredients[2]
    assert olive_oil.quantity == Decimal("2")
    assert olive_oil.unit == Unit.TABLESPOON

    tomato = ingredients[3]
    assert tomato.quantity == Decimal("400")
    assert tomato.unit == Unit.GRAM

    steps = list(recipe.steps.order_by("order"))
    assert len(steps) == 3
    assert steps[0].instruction == "Peel and dice onion and garlic clove."
    assert "5 minutes" in steps[1].instruction
    assert "pan" in steps[1].instruction


@pytest.mark.django_db
def test_reuses_ingredient_across_recipes_case_insensitively():
    user = UserFactory()
    Ingredient.objects.create(name="Tomate")

    create_recipe_from_cooklang(author=user, title="Recette 1", raw_cooklang="Ajouter @tomate{2%piece}.")
    create_recipe_from_cooklang(author=user, title="Recette 2", raw_cooklang="Couper la @tomate{1%piece}.")

    assert Ingredient.objects.filter(name__iexact="tomate").count() == 1


@pytest.mark.django_db
def test_unrecognized_unit_falls_back_to_piece():
    user = UserFactory()

    recipe = create_recipe_from_cooklang(
        author=user, title="Mystery unit", raw_cooklang="Add @flour{2%bushel}."
    )

    ri = recipe.recipe_ingredients.first()
    assert ri.unit == Unit.PIECE


def test_map_unit_aliases():
    assert map_unit("g") == Unit.GRAM
    assert map_unit("cs") == Unit.TABLESPOON
    assert map_unit("c.à.c") == Unit.TEASPOON
    assert map_unit("pincée") == Unit.PINCH
    assert map_unit(None) == Unit.PIECE
    assert map_unit("bushel") == Unit.PIECE


def test_parse_quantity_defaults_on_bad_input():
    assert parse_quantity("2") == Decimal("2")
    assert parse_quantity("2,5") == Decimal("2.5")
    assert parse_quantity(None) == Decimal("1")
    assert parse_quantity("quelques") == Decimal("1")


@pytest.mark.django_db
def test_import_cooklang_endpoint_creates_recipe():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    payload = {
        "title": "Curry rapide",
        "raw_cooklang": "Faire revenir @oignon{1%piece} puis ajouter @lait_de_coco{200%ml}.",
        "servings": 2,
    }
    response = client.post("/api/recipes/import-cooklang/", payload, format="json")

    assert response.status_code == 201
    assert response.data["source_type"] == SourceType.COOKLANG
    assert response.data["servings"] == 2
    assert len(response.data["ingredients"]) == 2
    assert RecipeStep.objects.filter(recipe_id=response.data["id"]).exists()
    assert RecipeIngredient.objects.filter(recipe_id=response.data["id"]).count() == 2


@pytest.mark.django_db
def test_import_cooklang_endpoint_requires_authentication():
    client = APIClient()
    response = client.post(
        "/api/recipes/import-cooklang/",
        {"title": "Test", "raw_cooklang": "Add @salt{1%pinch}."},
        format="json",
    )
    assert response.status_code == 401
