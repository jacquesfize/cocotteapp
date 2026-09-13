from decimal import Decimal

import pytest

from apps.ingredients.factories import IngredientFactory
from apps.nutrition.models import NutrientRequirement
from apps.nutrition.services import compute_recipe_carbon_footprint, compute_recipe_nutrition, find_deficiencies
from apps.recipes.factories import RecipeFactory, RecipeIngredientFactory


@pytest.mark.django_db
def test_compute_recipe_nutrition_scales_by_quantity():
    ingredient = IngredientFactory(protein_g=Decimal("10"), calories_kcal=Decimal("100"))
    recipe = RecipeFactory()
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("200"), unit="g")

    totals = compute_recipe_nutrition(recipe)

    assert totals["protein_g"] == Decimal("20")
    assert totals["calories_kcal"] == Decimal("200")


@pytest.mark.django_db
def test_compute_recipe_carbon_footprint_scales_by_quantity():
    ingredient = IngredientFactory(carbon_kg_co2e_per_kg=Decimal("27"))
    recipe = RecipeFactory()
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("500"), unit="g")

    footprint = compute_recipe_carbon_footprint(recipe)

    assert footprint == Decimal("13.5")


@pytest.mark.django_db
def test_find_deficiencies_flags_low_nutrients():
    NutrientRequirement.objects.create(
        diet_type="vegan", activity_level="athlete", nutrient="protein_g", unit="g", daily_minimum=Decimal("100")
    )
    totals = {"protein_g": Decimal("20")}

    deficiencies = find_deficiencies(totals, "vegan", "athlete")

    assert len(deficiencies) == 1
    assert deficiencies[0]["nutrient"] == "protein_g"
