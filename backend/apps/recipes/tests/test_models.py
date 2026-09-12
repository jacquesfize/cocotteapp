import pytest

from apps.recipes.factories import RecipeFactory


@pytest.mark.django_db
def test_recipe_slug_unique_on_conflict():
    first = RecipeFactory(title="Salade de saison")
    second = RecipeFactory(title="Salade de saison")
    assert first.slug == "salade-de-saison"
    assert second.slug == "salade-de-saison-2"


@pytest.mark.django_db
def test_total_time_minutes():
    recipe = RecipeFactory(prep_time_minutes=10, cook_time_minutes=25)
    assert recipe.total_time_minutes == 35
