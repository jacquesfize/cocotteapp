import pytest

from apps.accounts.factories import UserFactory
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


@pytest.mark.django_db
def test_manual_recipe_never_restricted():
    """No source_url at all -- the author typed it themselves -- always stays fully public,
    for anyone: anonymous, another user, even without being the author or staff."""
    author = UserFactory()
    other = UserFactory()
    recipe = RecipeFactory(author=author, source_url="")

    assert recipe.is_content_restricted(None) is False
    assert recipe.is_content_restricted(other) is False
    assert recipe.is_content_restricted(author) is False


@pytest.mark.django_db
def test_imported_recipe_restricted_for_anonymous_and_other_users():
    author = UserFactory()
    other = UserFactory()
    recipe = RecipeFactory(author=author, source_url="https://example.com/recipe")

    assert recipe.is_content_restricted(None) is True
    assert recipe.is_content_restricted(other) is True


@pytest.mark.django_db
def test_imported_recipe_not_restricted_for_author_or_staff():
    author = UserFactory()
    staff = UserFactory(is_staff=True)
    recipe = RecipeFactory(author=author, source_url="https://example.com/recipe")

    assert recipe.is_content_restricted(author) is False
    assert recipe.is_content_restricted(staff) is False


@pytest.mark.django_db
def test_imported_recipe_not_restricted_once_publicly_licensed():
    other = UserFactory()
    recipe = RecipeFactory(
        source_url="https://example.com/recipe", content_publicly_licensed=True
    )

    assert recipe.is_content_restricted(None) is False
    assert recipe.is_content_restricted(other) is False
