from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from apps.accounts.factories import UserFactory
from apps.importer.services import create_recipe_from_url
from apps.ingredients.factories import IngredientFactory
from apps.ingredients.models import Ingredient, Unit


@pytest.mark.django_db
def test_create_recipe_from_url_uses_scraper_data():
    scraper = MagicMock()
    scraper.title.return_value = "Tarte aux poireaux"
    scraper.yields.return_value = "6 servings"
    scraper.total_time = 45
    scraper.ingredients.return_value = ["2 poireaux", "1 pâte brisée"]
    scraper.instructions.return_value = "Préchauffer le four.\nCuire 30 minutes."

    user = UserFactory()

    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": scraper.title(),
            "servings": 6,
            "cook_time_minutes": 45,
            "ingredients": scraper.ingredients(),
            "instructions": scraper.instructions().split("\n"),
        }
        recipe = create_recipe_from_url(user, "https://example.com/recipe")

    assert recipe.title == "Tarte aux poireaux"
    assert recipe.servings == 6
    assert recipe.steps.count() == 2
    assert recipe.recipe_ingredients.count() == 2


@pytest.mark.django_db
def test_create_recipe_from_url_captures_scraped_image():
    user = UserFactory()

    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Tarte aux poireaux",
            "servings": 6,
            "cook_time_minutes": 45,
            "ingredients": ["1 pâte brisée"],
            "instructions": ["Cuire 30 minutes."],
            "image_url": "https://example.com/tarte.jpg",
        }
        recipe = create_recipe_from_url(user, "https://example.com/recipe")

    assert recipe.image_url == "https://example.com/tarte.jpg"


@pytest.mark.django_db
def test_create_recipe_from_url_without_image_defaults_to_blank():
    user = UserFactory()

    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Tarte aux poireaux",
            "servings": 6,
            "cook_time_minutes": 45,
            "ingredients": ["1 pâte brisée"],
            "instructions": ["Cuire 30 minutes."],
            "image_url": "",
        }
        recipe = create_recipe_from_url(user, "https://example.com/recipe")

    assert recipe.image_url == ""


def test_scrape_url_extracts_image_when_available():
    from apps.importer.services import scrape_url

    scraper = MagicMock()
    scraper.title.return_value = "Tarte aux poireaux"
    scraper.yields.return_value = "6 servings"
    scraper.total_time = 45
    scraper.ingredients.return_value = ["1 pâte brisée"]
    scraper.instructions.return_value = "Cuire 30 minutes."
    scraper.image.return_value = "https://example.com/tarte.jpg"

    with patch("recipe_scrapers.scrape_me", return_value=scraper):
        data = scrape_url("https://example.com/recipe")

    assert data["image_url"] == "https://example.com/tarte.jpg"


def test_scrape_url_defaults_to_blank_when_scraper_has_no_image():
    from apps.importer.services import scrape_url

    scraper = MagicMock()
    scraper.title.return_value = "Tarte aux poireaux"
    scraper.yields.return_value = "6 servings"
    scraper.total_time = 45
    scraper.ingredients.return_value = ["1 pâte brisée"]
    scraper.instructions.return_value = "Cuire 30 minutes."
    scraper.image.side_effect = Exception("no image found")

    with patch("recipe_scrapers.scrape_me", return_value=scraper):
        data = scrape_url("https://example.com/recipe")

    assert data["image_url"] == ""


@pytest.mark.django_db
def test_create_recipe_from_url_parses_quantity_and_unit():
    user = UserFactory()

    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["200 g de pois chiches", "2 gousses d'ail", "sel"],
            "instructions": ["Mixer.", "Cuire."],
            "image_url": "",
        }
        recipe = create_recipe_from_url(user, "https://example.com/falafels")

    by_name = {ri.ingredient.name: ri for ri in recipe.recipe_ingredients.all()}
    assert by_name["pois chiches"].quantity == Decimal("200")
    assert by_name["pois chiches"].unit == Unit.GRAM
    assert by_name["ail"].quantity == Decimal("2")
    assert by_name["ail"].unit == Unit.PIECE
    assert by_name["sel"].quantity == Decimal("1")
    assert by_name["sel"].unit == Unit.PIECE


@pytest.mark.django_db
def test_create_recipe_from_url_reuses_existing_ingredient_by_exact_name():
    user = UserFactory()
    existing = IngredientFactory(name="pois chiches")

    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["200 g de pois chiches"],
            "instructions": ["Mixer."],
            "image_url": "",
        }
        recipe = create_recipe_from_url(user, "https://example.com/falafels")

    recipe_ingredient = recipe.recipe_ingredients.get()
    assert recipe_ingredient.ingredient_id == existing.id
    assert Ingredient.objects.filter(name="pois chiches").count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "raw_line",
    ["2 cloves garlic", "2 Zehen Knoblauch", "2 dientes de ajo"],
)
def test_create_recipe_from_url_reuses_existing_ingredient_by_translation(raw_line):
    user = UserFactory()
    ail = IngredientFactory(
        name="Ail", translations={"en": "garlic", "de": "Knoblauch", "es": "ajo"}
    )

    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Recipe",
            "servings": 4,
            "cook_time_minutes": 10,
            "ingredients": [raw_line],
            "instructions": ["Cook."],
            "image_url": "",
        }
        recipe = create_recipe_from_url(user, "https://example.com/recipe")

    recipe_ingredient = recipe.recipe_ingredients.get()
    assert recipe_ingredient.ingredient_id == ail.id
    assert recipe_ingredient.quantity == Decimal("2")
    assert recipe_ingredient.unit == Unit.PIECE
    assert Ingredient.objects.filter(name__iexact="ail").count() == 1


@pytest.mark.django_db
def test_create_recipe_from_url_reuses_existing_ingredient_by_close_match():
    user = UserFactory()
    existing = IngredientFactory(name="pois chiche")

    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["200 g de pois chiches"],
            "instructions": ["Mixer."],
            "image_url": "",
        }
        recipe = create_recipe_from_url(user, "https://example.com/falafels")

    recipe_ingredient = recipe.recipe_ingredients.get()
    assert recipe_ingredient.ingredient_id == existing.id
