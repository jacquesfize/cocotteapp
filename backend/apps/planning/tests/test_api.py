import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.planning.models import MealPlanEntry
from apps.recipes.factories import RecipeFactory


@pytest.mark.django_db
def test_create_meal_plan_entry():
    user = UserFactory()
    recipe = RecipeFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(
        "/api/meal-plan-entries/",
        {"recipe": recipe.id, "date": "2026-01-15", "meal_type": "dinner", "servings": 2},
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_meal_plan_entries_scoped_to_user():
    owner = UserFactory()
    other = UserFactory()
    recipe = RecipeFactory()
    MealPlanEntry.objects.create(user=owner, recipe=recipe, date="2026-01-01")

    client = APIClient()
    client.force_authenticate(other)
    response = client.get("/api/meal-plan-entries/")
    assert response.data == []


@pytest.mark.django_db
def test_meal_plan_entries_not_paginated():
    user = UserFactory()
    recipe = RecipeFactory()
    for day in range(1, 23):
        MealPlanEntry.objects.create(user=user, recipe=recipe, date=f"2026-01-{day:02d}", meal_type="lunch")
        MealPlanEntry.objects.create(user=user, recipe=recipe, date=f"2026-01-{day:02d}", meal_type="dinner")

    client = APIClient()
    client.force_authenticate(user)
    response = client.get("/api/meal-plan-entries/")

    assert isinstance(response.data, list)
    assert len(response.data) == 44


@pytest.mark.django_db
def test_meal_plan_entries_filtered_by_date_range():
    user = UserFactory()
    recipe = RecipeFactory()
    MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-05", meal_type="lunch")
    MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-12", meal_type="lunch")

    client = APIClient()
    client.force_authenticate(user)
    response = client.get("/api/meal-plan-entries/?date_after=2026-01-01&date_before=2026-01-07")

    assert len(response.data) == 1
    assert response.data[0]["date"] == "2026-01-05"


@pytest.mark.django_db
def test_nutrition_summary_flags_deficiencies():
    from apps.ingredients.factories import IngredientFactory
    from apps.nutrition.models import NutrientRequirement
    from apps.recipes.factories import RecipeFactory as RecipeFactory2
    from apps.recipes.factories import RecipeIngredientFactory
    from decimal import Decimal

    user = UserFactory(diet_type="vegan", activity_level="athlete")
    NutrientRequirement.objects.create(
        diet_type="vegan", activity_level="athlete", nutrient="protein_g", unit="g", daily_minimum=Decimal("100")
    )
    ingredient = IngredientFactory(protein_g=Decimal("10"))
    recipe = RecipeFactory2(servings=1)
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("100"), unit="g")
    MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-05", meal_type="lunch", servings=1)

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        "/api/meal-plan-entries/nutrition_summary/?date_after=2026-01-05&date_before=2026-01-05"
    )

    assert response.status_code == 200
    assert response.data["daily_average"]["protein_g"] == 10.0
    deficient_nutrients = [d["nutrient"] for d in response.data["deficiencies"]]
    assert "protein_g" in deficient_nutrients


@pytest.mark.django_db
def test_nutrition_summary_returns_carbon_footprint():
    from apps.ingredients.factories import IngredientFactory
    from apps.recipes.factories import RecipeFactory as RecipeFactory2
    from apps.recipes.factories import RecipeIngredientFactory
    from decimal import Decimal

    user = UserFactory()
    ingredient = IngredientFactory(carbon_kg_co2e_per_kg=Decimal("10"))
    recipe = RecipeFactory2(servings=1)
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("1000"), unit="g")
    MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-05", meal_type="lunch", servings=1)

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        "/api/meal-plan-entries/nutrition_summary/?date_after=2026-01-05&date_before=2026-01-05"
    )

    assert response.status_code == 200
    assert response.data["carbon_footprint_kg_co2e"] == 10.0
    assert response.data["carbon_footprint_daily_average_kg_co2e"] == 10.0


@pytest.mark.django_db
def test_week_pdf_download_returns_pdf():
    user = UserFactory()
    recipe = RecipeFactory(title="Curry de saison")
    MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-05", meal_type="dinner")

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        "/api/meal-plan-entries/week-pdf/?date_after=2026-01-05&date_before=2026-01-11"
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


@pytest.mark.django_db
def test_week_pdf_download_works_with_no_entries():
    user = UserFactory()

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        "/api/meal-plan-entries/week-pdf/?date_after=2026-01-05&date_before=2026-01-11"
    )

    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")


@pytest.mark.django_db
def test_meal_plan_entry_exposes_recipe_allergens():
    from apps.ingredients.models import Allergen, Ingredient
    from apps.recipes.factories import RecipeIngredientFactory

    user = UserFactory()
    recipe = RecipeFactory()
    ingredient = Ingredient.objects.create(name="pâtes")
    ingredient.allergens.add(Allergen.objects.create(slug="gluten", name="Gluten"))
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient)
    MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-01")

    client = APIClient()
    client.force_authenticate(user)
    response = client.get("/api/meal-plan-entries/")

    assert response.data[0]["recipe_allergens"] == ["gluten"]
