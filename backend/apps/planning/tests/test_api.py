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
def test_nutrition_summary_flags_deficiencies(settings):
    from apps.ingredients.factories import IngredientFactory
    from apps.nutrition.models import NutrientRequirement
    from apps.recipes.factories import RecipeFactory as RecipeFactory2
    from apps.recipes.factories import RecipeIngredientFactory
    from decimal import Decimal

    settings.NUTRITION_ALERTS_ENABLED = True
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


def _protein_deficient_setup(user):
    from decimal import Decimal

    from apps.ingredients.factories import IngredientFactory
    from apps.nutrition.models import NutrientRequirement
    from apps.recipes.factories import RecipeIngredientFactory

    NutrientRequirement.objects.create(
        diet_type=user.diet_type,
        activity_level=user.activity_level,
        nutrient="protein_g",
        unit="g",
        daily_minimum=Decimal("100"),
    )
    ingredient = IngredientFactory(protein_g=Decimal("10"))
    recipe = RecipeFactory(servings=1)
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("100"), unit="g")
    return recipe


@pytest.mark.django_db
def test_nutrition_summary_skips_alerts_on_sparse_week(settings):
    """Une semaine avec un seul jour planifié : la moyenne journalière n'a pas de sens, aucune
    alerte n'est émise et la réponse indique pourquoi."""
    settings.NUTRITION_ALERTS_ENABLED = True
    user = UserFactory(diet_type="vegan", activity_level="athlete")
    recipe = _protein_deficient_setup(user)
    MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-05", meal_type="lunch", servings=1)

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        "/api/meal-plan-entries/nutrition_summary/?date_after=2026-01-05&date_before=2026-01-11"
    )

    assert response.status_code == 200
    assert response.data["deficiencies"] == []
    assert response.data["alerts_skipped_insufficient_data"] is True
    assert response.data["planned_days"] == 1
    assert response.data["min_planned_days_for_alerts"] == 4


@pytest.mark.django_db
def test_nutrition_summary_skips_alerts_on_empty_week(settings):
    settings.NUTRITION_ALERTS_ENABLED = True
    user = UserFactory(diet_type="vegan", activity_level="athlete")
    _protein_deficient_setup(user)

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        "/api/meal-plan-entries/nutrition_summary/?date_after=2026-01-05&date_before=2026-01-11"
    )

    assert response.data["deficiencies"] == []
    assert response.data["alerts_skipped_insufficient_data"] is True
    assert response.data["planned_days"] == 0


@pytest.mark.django_db
def test_nutrition_summary_flags_deficiencies_once_enough_days_are_planned(settings):
    settings.NUTRITION_ALERTS_ENABLED = True
    user = UserFactory(diet_type="vegan", activity_level="athlete")
    recipe = _protein_deficient_setup(user)
    # Plusieurs repas le même jour ne comptent que pour un jour planifié.
    for day in (5, 6, 7, 8):
        MealPlanEntry.objects.create(user=user, recipe=recipe, date=f"2026-01-{day:02d}", meal_type="lunch")
    MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-08", meal_type="dinner")

    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        "/api/meal-plan-entries/nutrition_summary/?date_after=2026-01-05&date_before=2026-01-11"
    )

    assert response.data["alerts_skipped_insufficient_data"] is False
    assert response.data["planned_days"] == 4
    assert [d["nutrient"] for d in response.data["deficiencies"]] == ["protein_g"]


@pytest.mark.django_db
def test_nutrition_summary_does_not_flag_insufficient_data_when_alerts_disabled(settings):
    settings.NUTRITION_ALERTS_ENABLED = False
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)
    response = client.get(
        "/api/meal-plan-entries/nutrition_summary/?date_after=2026-01-05&date_before=2026-01-11"
    )

    assert response.data["alerts_skipped_insufficient_data"] is False


@pytest.mark.django_db
def test_nutrition_summary_hides_deficiencies_when_alerts_disabled():
    """NUTRITION_ALERTS_ENABLED defaults to False: deficiencies must stay empty even though the
    underlying intake would otherwise be flagged (see test_nutrition_summary_flags_deficiencies)."""
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
    assert response.data["deficiencies"] == []


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


@pytest.mark.django_db
def test_meal_plan_entry_exposes_recipe_image_url():
    user = UserFactory()
    recipe = RecipeFactory(image_url="https://example.com/photo.jpg")
    MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-01")

    client = APIClient()
    client.force_authenticate(user)
    response = client.get("/api/meal-plan-entries/")

    assert response.data[0]["recipe_image"] is None
    assert response.data[0]["recipe_image_url"] == "https://example.com/photo.jpg"
