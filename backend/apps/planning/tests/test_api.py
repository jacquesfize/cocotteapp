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
    assert response.data["count"] == 0
