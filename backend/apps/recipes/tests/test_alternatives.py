import io
import json
import zipfile
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.ingredients.factories import IngredientFactory
from apps.ingredients.models import Ingredient
from apps.ingredients.services import merge_ingredients
from apps.nutrition.services import compute_recipe_carbon_footprint, compute_recipe_nutrition
from apps.planning.models import MealPlanEntry
from apps.recipes.factories import (
    IngredientAlternativeFactory,
    RecipeFactory,
    RecipeIngredientFactory,
)
from apps.recipes.models import IngredientAlternative, Recipe
from apps.shopping.services import build_shopping_list


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def _payload(milk, oat_milk, sugar):
    return {
        "title": "Pancakes",
        "servings": 4,
        "prep_time_minutes": 10,
        "cook_time_minutes": 10,
        "diet_type": "vegetarian",
        "ingredients": [
            {
                "ingredient_id": milk.id,
                "quantity": "250",
                "unit": "ml",
                "order": 1,
                "alternatives": [
                    {"ingredient_id": oat_milk.id, "quantity": "250", "unit": "ml", "tag": "vegan", "note": "Marche aussi avec du soja."},
                    {"ingredient_id": oat_milk.id, "quantity": "200", "unit": "ml", "tag": "missing"},
                ],
            },
            {
                "ingredient_id": sugar.id,
                "quantity": "40",
                "unit": "g",
                "order": 2,
                "alternatives": [{"quantity": "20", "unit": "g", "tag": "less"}],
            },
        ],
        "steps": [{"order": 1, "instruction": "Mélanger."}],
    }


@pytest.fixture
def milk_oat_sugar():
    return IngredientFactory(name="Lait"), IngredientFactory(name="Lait d'avoine"), IngredientFactory(name="Sucre")


@pytest.mark.django_db
def test_create_recipe_with_alternatives_returns_them_on_each_line(milk_oat_sugar):
    milk, oat_milk, sugar = milk_oat_sugar

    response = _client(UserFactory()).post("/api/recipes/", _payload(milk, oat_milk, sugar), format="json")

    assert response.status_code == 201
    milk_line, sugar_line = response.data["ingredients"]
    assert [(a["tag"], a["ingredient"]["name"], a["quantity"]) for a in milk_line["alternatives"]] == [
        ("vegan", "Lait d'avoine", "250.00"),
        ("missing", "Lait d'avoine", "200.00"),
    ]
    assert milk_line["alternatives"][0]["note"] == "Marche aussi avec du soja."
    # Réduction de quantité : pas d'autre ingrédient, c'est celui de la ligne.
    assert [(a["tag"], a["ingredient"], a["quantity"]) for a in sugar_line["alternatives"]] == [("less", None, "20.00")]

    detail = _client(UserFactory()).get(f"/api/recipes/{response.data['id']}/")
    assert len(detail.data["ingredients"][0]["alternatives"]) == 2


@pytest.mark.django_db
def test_a_line_without_alternatives_has_an_empty_list():
    recipe = RecipeFactory()
    RecipeIngredientFactory(recipe=recipe)

    response = APIClient().get(f"/api/recipes/{recipe.id}/")

    assert response.data["ingredients"][0]["alternatives"] == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "alternative",
    [
        {"quantity": "10", "unit": "g", "tag": "vegan"},  # remplacement sans ingrédient
        {"quantity": "10", "unit": "g", "tag": "less", "ingredient_id": "OTHER"},  # réduction avec ingrédient
        {"ingredient_id": "OTHER", "quantity": "10", "unit": "g", "tag": "unknown-tag"},
    ],
)
def test_invalid_alternative_is_rejected(alternative, milk_oat_sugar):
    milk, oat_milk, sugar = milk_oat_sugar
    payload = _payload(milk, oat_milk, sugar)
    if alternative.get("ingredient_id") == "OTHER":
        alternative = {**alternative, "ingredient_id": oat_milk.id}
    payload["ingredients"][0]["alternatives"] = [alternative]

    response = _client(UserFactory()).post("/api/recipes/", payload, format="json")

    assert response.status_code == 400
    assert not Recipe.objects.exists()


@pytest.mark.django_db
def test_update_replaces_the_alternatives_of_a_line(milk_oat_sugar):
    milk, oat_milk, sugar = milk_oat_sugar
    user = UserFactory()
    created = _client(user).post("/api/recipes/", _payload(milk, oat_milk, sugar), format="json")
    payload = _payload(milk, oat_milk, sugar)
    payload["ingredients"][0]["alternatives"] = [
        {"ingredient_id": oat_milk.id, "quantity": "300", "unit": "ml", "tag": "lactose_free"}
    ]
    payload["ingredients"][1]["alternatives"] = []

    response = _client(user).patch(f"/api/recipes/{created.data['id']}/", payload, format="json")

    assert response.status_code == 200
    milk_line, sugar_line = response.data["ingredients"]
    assert [(a["tag"], a["quantity"]) for a in milk_line["alternatives"]] == [("lactose_free", "300.00")]
    assert sugar_line["alternatives"] == []
    assert IngredientAlternative.objects.count() == 1


@pytest.mark.django_db
def test_database_refuses_a_replacement_without_ingredient():
    line = RecipeIngredientFactory()

    with pytest.raises(IntegrityError), transaction.atomic():
        IngredientAlternative.objects.create(recipe_ingredient=line, quantity=1, unit="g", tag="vegan")


@pytest.mark.django_db
def test_alternatives_are_not_counted_in_nutrition_carbon_or_shopping_list():
    user = UserFactory()
    milk = IngredientFactory(calories_kcal=60, carbon_kg_co2e_per_kg=1)
    oat_milk = IngredientFactory(calories_kcal=45, carbon_kg_co2e_per_kg=0.3)
    recipe = RecipeFactory(servings=2)
    line = RecipeIngredientFactory(recipe=recipe, ingredient=milk, quantity=Decimal("200"), unit="g")
    entry = MealPlanEntry.objects.create(user=user, recipe=recipe, date="2026-01-01", servings=2)
    before = (
        compute_recipe_nutrition(recipe),
        compute_recipe_carbon_footprint(recipe),
        sorted(build_shopping_list(user, [entry]).items.values_list("ingredient_id", "quantity")),
    )

    IngredientAlternativeFactory(recipe_ingredient=line, ingredient=oat_milk, quantity=Decimal("200"), unit="g")
    IngredientAlternativeFactory(recipe_ingredient=line, ingredient=None, quantity=Decimal("100"), unit="g", tag="less")

    assert compute_recipe_nutrition(recipe) == before[0]
    assert compute_recipe_carbon_footprint(recipe) == before[1]
    assert sorted(build_shopping_list(user, [entry]).items.values_list("ingredient_id", "quantity")) == before[2]
    assert oat_milk.id not in [item[0] for item in before[2]]


@pytest.mark.django_db
def test_fork_copies_the_alternatives():
    source = RecipeFactory(content_publicly_licensed=True)
    line = RecipeIngredientFactory(recipe=source)
    oat_milk = IngredientFactory(name="Lait d'avoine")
    IngredientAlternativeFactory(recipe_ingredient=line, ingredient=oat_milk, note="Au choix", order=2)
    IngredientAlternativeFactory(recipe_ingredient=line, ingredient=None, tag="less", quantity=Decimal("50"))

    response = _client(UserFactory()).post(f"/api/recipes/{source.id}/fork/", {"version_label": "Vegan"}, format="json")

    assert response.status_code == 201
    fork_line = Recipe.objects.get(pk=response.data["id"]).recipe_ingredients.get()
    assert fork_line.pk != line.pk
    copied = sorted((a.tag, a.ingredient_id, a.note, a.quantity) for a in fork_line.alternatives.all())
    assert copied == sorted([("vegan", oat_milk.id, "Au choix", Decimal("100")), ("less", None, "", Decimal("50"))])
    assert line.alternatives.count() == 2  # la source n'a pas bougé


@pytest.mark.django_db
def test_merging_ingredients_repoints_alternatives_too():
    duplicate = IngredientFactory(name="avoine lait")
    target = IngredientFactory(name="lait d'avoine")
    alternative = IngredientAlternativeFactory(ingredient=duplicate)

    merge_ingredients(duplicate, target)

    alternative.refresh_from_db()
    assert alternative.ingredient == target
    assert not Ingredient.objects.filter(pk=duplicate.pk).exists()


@pytest.mark.django_db
def test_ingredient_used_only_as_an_alternative_counts_as_used_by_others():
    author, other = UserFactory(), UserFactory()
    oat_milk = IngredientFactory(name="Lait d'avoine")
    line = RecipeIngredientFactory(recipe=RecipeFactory(author=author))
    IngredientAlternativeFactory(recipe_ingredient=line, ingredient=oat_milk)

    assert oat_milk.is_used_by_others(other) is True
    assert oat_milk.is_used_by_others(author) is False


@pytest.mark.django_db
def test_archive_round_trip_keeps_alternatives(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    author = UserFactory()
    recipe = RecipeFactory(author=author, title="Pancakes")
    line = RecipeIngredientFactory(recipe=recipe, ingredient=IngredientFactory(name="Lait"), unit="ml")
    IngredientAlternativeFactory(
        recipe_ingredient=line, ingredient=IngredientFactory(name="Lait d'avoine"), note="Au choix", tag="vegan", unit="ml"
    )
    IngredientAlternativeFactory(recipe_ingredient=line, ingredient=None, tag="less", quantity=Decimal("120"), unit="ml")

    archive = _client(author).get("/api/recipes/export/").content
    manifest = json.loads(zipfile.ZipFile(io.BytesIO(archive)).read("recipes.json"))
    exported = manifest["recipes"][0]["ingredients"][0]["alternatives"]
    assert [(a["tag"], a["ingredient"] and a["ingredient"]["name"]) for a in exported] == [
        ("vegan", "Lait d'avoine"),
        ("less", None),
    ]

    Recipe.objects.all().delete()
    Ingredient.objects.all().delete()
    target_user = UserFactory()
    upload = SimpleUploadedFile("export.zip", archive, content_type="application/zip")
    response = _client(target_user).post("/api/recipes/import-archive/", {"file": upload}, format="multipart")

    assert response.status_code == 201
    imported_line = Recipe.objects.get(title="Pancakes").recipe_ingredients.get()
    assert sorted((a.tag, a.ingredient.name if a.ingredient else None, a.note) for a in imported_line.alternatives.all()) == [
        ("less", None, ""),
        ("vegan", "Lait d'avoine", "Au choix"),
    ]
