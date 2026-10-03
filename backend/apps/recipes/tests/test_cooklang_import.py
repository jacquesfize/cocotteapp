from decimal import Decimal
from pathlib import Path

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.ingredients.factories import IngredientFactory
from apps.ingredients.models import Ingredient, Unit
from apps.recipes.cooklang_import import create_recipe_from_cooklang, map_unit, parse_quantity
from apps.recipes.models import Recipe, RecipeIngredient, RecipeStep, SourceType

# Fichier réel fourni par le PO : https://recipes.cooklang.org/api/recipes/9441/download
TIRAMISU = (Path(__file__).parent / "fixtures" / "tiramisu.cook").read_text(encoding="utf-8")

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
    # Les balises @ingrédient et ~{durée} sont conservées (le matériel #pan{} est aplati).
    assert steps[0].instruction == "Peel and dice @onion{1%piece} and @garlic clove."
    assert "~{5 minutes}" in steps[1].instruction
    assert "#" not in steps[1].instruction
    assert "in a pan" in steps[1].instruction


@pytest.mark.django_db
def test_repeated_mention_without_quantity_does_not_duplicate_ingredient():
    user = UserFactory()

    recipe = create_recipe_from_cooklang(
        author=user,
        title="Oignons",
        raw_cooklang="Émincer @oignon{2}.\nFaire dorer l'@oignon dans @huile_olive{1%cs}.",
    )

    names = [ri.ingredient.name for ri in recipe.recipe_ingredients.order_by("order")]
    assert names == ["oignon", "huile olive"]


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
def test_create_recipe_from_cooklang_with_video_url_sets_youtube_source_type():
    user = UserFactory()

    recipe = create_recipe_from_cooklang(
        author=user,
        title="Tarte au citron",
        raw_cooklang="Ajouter @citron{2%piece}.",
        video_url="https://www.youtube.com/watch?v=abc123",
        source_url="https://www.youtube.com/watch?v=abc123",
        image_url="https://img.youtube.com/vi/abc123/hqdefault.jpg",
    )

    assert recipe.source_type == SourceType.YOUTUBE
    assert recipe.video_url == "https://www.youtube.com/watch?v=abc123"
    assert recipe.source_url == "https://www.youtube.com/watch?v=abc123"
    assert recipe.image_url == "https://img.youtube.com/vi/abc123/hqdefault.jpg"
    assert recipe.content_publicly_licensed is False


@pytest.mark.django_db
def test_import_cooklang_endpoint_creates_youtube_recipe_in_a_single_call():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    payload = {
        "title": "Tarte au citron",
        "raw_cooklang": "Ajouter @citron{2%piece}.",
        "video_url": "https://www.youtube.com/watch?v=abc123",
        "source_url": "https://www.youtube.com/watch?v=abc123",
        "image_url": "https://img.youtube.com/vi/abc123/hqdefault.jpg",
    }
    response = client.post("/api/recipes/import-cooklang/", payload, format="json")

    assert response.status_code == 201
    assert response.data["source_type"] == SourceType.YOUTUBE
    assert response.data["video_url"] == payload["video_url"]
    assert response.data["content_publicly_licensed"] is False
    # The response is seen by its own author here (force_authenticate(user) == recipe author),
    # so it's not restricted for *this* viewer even though content_publicly_licensed is False --
    # see test_imported_recipe_hides_content_for_anonymous_and_other_users in test_api.py for
    # the restricted-for-others case.
    assert response.data["content_restricted"] is False


@pytest.mark.django_db
def test_import_cooklang_endpoint_requires_authentication():
    client = APIClient()
    response = client.post(
        "/api/recipes/import-cooklang/",
        {"title": "Test", "raw_cooklang": "Add @salt{1%pinch}."},
        format="json",
    )
    assert response.status_code == 401


# --- Mapping d'une vraie recette (recipes.cooklang.org) sur le modèle ------------------------


@pytest.mark.django_db
def test_real_world_recipe_maps_metadata_sections_and_notes():
    recipe = create_recipe_from_cooklang(author=UserFactory(), raw_cooklang=TIRAMISU)

    assert recipe.title == "Tiramisu"
    assert recipe.servings == 6
    assert recipe.prep_time_minutes == 40  # {"min": 30, "max": 40} -> borne haute
    assert recipe.cook_time_minutes == 0
    assert recipe.source_type == SourceType.COOKLANG
    assert recipe.source_url == ""  # "source: Anders" n'est pas une URL
    assert recipe.description.startswith("Til et fad på cirka 20 × 20 cm")
    assert "Lav helst desserten dagen før." in recipe.description

    assert recipe.steps.count() == 10
    rows = list(recipe.recipe_ingredients.select_related("ingredient").order_by("order"))
    by_name = {ri.ingredient.name: ri for ri in rows}
    assert len(rows) == 9  # "sukker" 70 g + 30 g dans la même section -> une seule ligne
    assert by_name["sukker"].quantity == Decimal("100")
    assert by_name["sukker"].unit == Unit.GRAM
    assert by_name["sukker"].group_name == "Mascarponecreme"
    assert by_name["kaffe"].group_name == "Kaffe"
    assert by_name["vand"].unit == Unit.MILLILITER


@pytest.mark.django_db
def test_existing_ingredients_are_matched_and_missing_ones_created():
    # Même rapprochement que l'import par URL : nom, traductions, puis nom proche.
    sucre = IngredientFactory(name="Sucre", translations={"da": "sukker"})
    mascarpone = IngredientFactory(name="Mascarpone")
    cacao = IngredientFactory(name="kakaoo")  # nom proche (difflib, cutoff 0.8)
    before = Ingredient.objects.count()

    recipe = create_recipe_from_cooklang(author=UserFactory(), raw_cooklang=TIRAMISU)

    ingredient_ids = set(recipe.recipe_ingredients.values_list("ingredient_id", flat=True))
    assert {sucre.id, mascarpone.id, cacao.id} <= ingredient_ids
    assert not Ingredient.objects.filter(name="sukker").exists()
    # 9 ingrédients distincts dont 3 déjà connus -> 6 créés.
    assert Ingredient.objects.count() == before + 6
    assert Ingredient.objects.filter(name="pasteuriseret æggeblomme").exists()


@pytest.mark.django_db
def test_explicit_fields_override_metadata():
    recipe = create_recipe_from_cooklang(
        author=UserFactory(), raw_cooklang=TIRAMISU, title="Mon tiramisu", servings=8, cook_time_minutes=5
    )
    assert (recipe.title, recipe.servings, recipe.cook_time_minutes) == ("Mon tiramisu", 8, 5)
    assert recipe.prep_time_minutes == 40


@pytest.mark.django_db
def test_metadata_source_url_and_textual_durations():
    text = (
        "---\ntitle: Soupe\nsource: https://example.com/soupe\nprep time: 1h15\ncook time: 20 minutes\n"
        "servings: 4 personnes\n---\nCuire @poireau{2} ~{20%minutes}."
    )
    recipe = create_recipe_from_cooklang(author=UserFactory(), raw_cooklang=text)
    assert recipe.source_url == "https://example.com/soupe"
    assert (recipe.prep_time_minutes, recipe.cook_time_minutes, recipe.servings) == (75, 20, 4)


@pytest.mark.django_db
def test_bare_mention_then_quantified_mention_keeps_the_given_quantity():
    recipe = create_recipe_from_cooklang(
        author=UserFactory(), title="Oignons", raw_cooklang="Éplucher l'@oignon.\nÉmincer @oignon{3}."
    )
    rows = list(recipe.recipe_ingredients.all())
    assert len(rows) == 1
    assert rows[0].quantity == Decimal("3")


def test_parse_quantity_fractions_ranges_and_unicode():
    assert parse_quantity("1/2") == Decimal("0.50")
    assert parse_quantity("1 1/2") == Decimal("1.50")
    assert parse_quantity("½") == Decimal("0.50")
    assert parse_quantity("2-3") == Decimal("2")
    assert parse_quantity("0") == Decimal("1")


def test_map_unit_reuses_url_importer_vocabulary():
    assert map_unit("grams") == Unit.GRAM
    assert map_unit("Esslöffel") == Unit.TABLESPOON
    assert map_unit("gousses") == Unit.PIECE
    assert map_unit("dl") == Unit.MILLILITER


@pytest.mark.django_db
def test_scaled_units_convert_quantity():
    recipe = create_recipe_from_cooklang(author=UserFactory(), title="Lait", raw_cooklang="Verser @lait{2%dl}.")
    row = recipe.recipe_ingredients.get()
    assert (row.quantity, row.unit) == (Decimal("200"), Unit.MILLILITER)


@pytest.mark.django_db
def test_import_cooklang_endpoint_takes_title_from_metadata():
    client = APIClient()
    client.force_authenticate(UserFactory())

    response = client.post("/api/recipes/import-cooklang/", {"raw_cooklang": TIRAMISU}, format="json")

    assert response.status_code == 201
    assert response.data["title"] == "Tiramisu"
    assert response.data["servings"] == 6
    assert response.data["source_type"] == SourceType.COOKLANG


@pytest.mark.django_db
def test_import_cooklang_endpoint_rejects_missing_title_and_invalid_text():
    client = APIClient()
    client.force_authenticate(UserFactory())

    no_title = client.post("/api/recipes/import-cooklang/", {"raw_cooklang": "Add @salt{1%pinch}."}, format="json")
    assert no_title.status_code == 400

    invalid = client.post(
        "/api/recipes/import-cooklang/",
        {"title": "X", "raw_cooklang": "---\ntitle: [oops\n---\nAdd @salt."},
        format="json",
    )
    assert invalid.status_code == 400
    assert not Recipe.objects.exists()
