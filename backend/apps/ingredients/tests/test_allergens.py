import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.ingredients.allergen_tags import ALLERGEN_TAGS
from apps.ingredients.management.commands.seed_allergens import ALLERGENS
from apps.ingredients.management.commands.seed_common_ingredients import INGREDIENTS
from apps.ingredients.models import Allergen, Ingredient
from apps.recipes.factories import RecipeFactory, RecipeIngredientFactory


def _allergen(slug):
    return Allergen.objects.get_or_create(slug=slug, defaults={"name": slug})[0]


def _recipe_with(*ingredients):
    recipe = RecipeFactory()
    for ingredient in ingredients:
        RecipeIngredientFactory(recipe=recipe, ingredient=ingredient)
    return recipe


def _ingredient(name, allergens=(), reviewed=True):
    ingredient = Ingredient.objects.create(name=name, allergens_reviewed=reviewed)
    ingredient.allergens.set(_allergen(s) for s in allergens)
    return ingredient


@pytest.mark.django_db
def test_seed_allergens_is_idempotent():
    call_command("seed_allergens")
    call_command("seed_allergens")
    assert Allergen.objects.count() == len(ALLERGENS)


@pytest.mark.django_db
def test_seed_common_ingredients_tags_and_reviews_allergens():
    call_command("seed_common_ingredients")

    assert set(Ingredient.objects.get(name="Pâtes").allergens.values_list("slug", flat=True)) == {"gluten"}
    assert Ingredient.objects.get(name="Tomate").allergens.count() == 0
    assert not Ingredient.objects.filter(allergens_reviewed=False).exists()


def test_allergen_tags_reference_existing_ingredients_and_allergens():
    names = {entry["name"] for entry in INGREDIENTS}
    slugs = {slug for slug, _ in ALLERGENS}
    for name, tags in ALLERGEN_TAGS.items():
        assert name in names, name
        assert set(tags) <= slugs, name


@pytest.mark.django_db
def test_allergen_list_is_public():
    call_command("seed_allergens")
    response = APIClient().get("/api/allergens/")
    assert response.status_code == 200
    assert len(response.data) == len(ALLERGENS)


@pytest.mark.django_db
def test_recipe_exposes_allergens_and_unverified_flag():
    recipe = _recipe_with(_ingredient("pâtes", ["gluten"]), _ingredient("inconnu", reviewed=False))

    data = APIClient().get(f"/api/recipes/{recipe.pk}/").data

    assert data["allergens"] == ["gluten"]
    assert data["allergens_unverified"] is True


@pytest.mark.django_db
def test_exclude_allergens_filter_keeps_unverified_recipes():
    with_gluten = _recipe_with(_ingredient("blé", ["gluten"]))
    plain = _recipe_with(_ingredient("riz"))
    unknown = _recipe_with(_ingredient("mystère", reviewed=False))

    response = APIClient().get("/api/recipes/", {"exclude_allergens": "gluten,milk"})

    ids = {r["id"] for r in response.data["results"]}
    assert with_gluten.id not in ids
    assert {plain.id, unknown.id} <= ids


@pytest.mark.django_db
def test_user_allergies_and_intolerances_roundtrip():
    call_command("seed_allergens")
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.patch(
        "/api/auth/me/", {"allergies": ["peanut"], "intolerances": ["lactose", "gluten"]}, format="json"
    )

    assert response.status_code == 200
    assert response.data["allergies"] == ["peanut"]
    assert sorted(response.data["intolerances"]) == ["gluten", "lactose"]

    # Un PATCH partiel laisse l'autre liste intacte ; une liste vide la vide.
    response = client.patch("/api/auth/me/", {"intolerances": []}, format="json")
    assert response.data["allergies"] == ["peanut"]
    assert response.data["intolerances"] == []


@pytest.mark.django_db
def test_allergen_cannot_be_both_allergy_and_intolerance():
    call_command("seed_allergens")
    client = APIClient()
    client.force_authenticate(UserFactory())

    response = client.patch(
        "/api/auth/me/", {"allergies": ["gluten"], "intolerances": ["gluten"]}, format="json"
    )

    assert response.status_code == 400
