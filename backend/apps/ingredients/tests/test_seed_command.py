import pytest
from django.core.management import call_command

from apps.ingredients.factories import IngredientFactory
from apps.ingredients.management.commands.seed_common_ingredients import INGREDIENTS
from apps.ingredients.models import Ingredient


@pytest.mark.django_db
def test_seed_command_creates_every_ingredient():
    call_command("seed_common_ingredients")

    assert Ingredient.objects.count() == len(INGREDIENTS)


@pytest.mark.django_db
def test_seed_command_is_idempotent():
    call_command("seed_common_ingredients")
    call_command("seed_common_ingredients")

    assert Ingredient.objects.count() == len(INGREDIENTS)


@pytest.mark.django_db
def test_seed_command_enriches_an_existing_differently_cased_ingredient():
    # Simule un ingrédient créé à la volée via le sélecteur de recette, sans
    # valeurs nutritionnelles.
    placeholder = IngredientFactory(name="tomate", calories_kcal=0)

    call_command("seed_common_ingredients")

    placeholder.refresh_from_db()
    assert placeholder.calories_kcal > 0
    assert Ingredient.objects.filter(name__iexact="tomate").count() == 1


@pytest.mark.django_db
def test_seeded_ingredient_has_realistic_nutrition():
    call_command("seed_common_ingredients")

    lentils = Ingredient.objects.get(name="Lentilles corail")
    assert lentils.protein_g > 20
    assert lentils.iron_mg > 0


@pytest.mark.django_db
def test_nutritional_yeast_provides_vitamin_b12():
    call_command("seed_common_ingredients")

    yeast = Ingredient.objects.get(name="Levure maltée enrichie en B12")
    assert yeast.vitamin_b12_ug > 0


@pytest.mark.django_db
def test_seeded_ingredient_has_carbon_footprint():
    call_command("seed_common_ingredients")

    beef = Ingredient.objects.get(name="Bœuf haché 5%")
    lentils = Ingredient.objects.get(name="Lentilles corail")
    assert beef.carbon_kg_co2e_per_kg > lentils.carbon_kg_co2e_per_kg > 0
