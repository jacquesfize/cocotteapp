from unittest.mock import MagicMock, patch

import pytest

from apps.importer.services import build_import_preview, fetch_og_image
from apps.ingredients.factories import IngredientFactory
from apps.ingredients.models import Ingredient
from apps.recipes.models import Recipe


@pytest.mark.django_db
def test_build_import_preview_uses_scraper_data():
    scraper = MagicMock()
    scraper.title.return_value = "Tarte aux poireaux"
    scraper.yields.return_value = "6 servings"
    scraper.total_time = 45
    scraper.ingredients.return_value = ["2 poireaux", "1 pâte brisée"]
    scraper.instructions.return_value = "Préchauffer le four.\nCuire 30 minutes."

    with patch("apps.importer.services.scrape_url") as scrape_url, patch(
        "apps.importer.services.fetch_og_image", return_value=None
    ):
        scrape_url.return_value = {
            "title": scraper.title(),
            "servings": 6,
            "cook_time_minutes": 45,
            "ingredients": scraper.ingredients(),
            "instructions": scraper.instructions().split("\n"),
        }
        preview = build_import_preview("https://example.com/recipe")

    assert preview["title"] == "Tarte aux poireaux"
    assert preview["servings"] == 6
    assert len(preview["steps"]) == 2
    assert len(preview["ingredients"]) == 2


@pytest.mark.django_db
def test_build_import_preview_captures_scraped_image():
    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Tarte aux poireaux",
            "servings": 6,
            "cook_time_minutes": 45,
            "ingredients": ["1 pâte brisée"],
            "instructions": ["Cuire 30 minutes."],
            "image_url": "https://example.com/tarte.jpg",
        }
        preview = build_import_preview("https://example.com/recipe")

    assert preview["image_url"] == "https://example.com/tarte.jpg"


@pytest.mark.django_db
def test_build_import_preview_without_image_defaults_to_blank():
    with patch("apps.importer.services.scrape_url") as scrape_url, patch(
        "apps.importer.services.fetch_og_image", return_value=None
    ):
        scrape_url.return_value = {
            "title": "Tarte aux poireaux",
            "servings": 6,
            "cook_time_minutes": 45,
            "ingredients": ["1 pâte brisée"],
            "instructions": ["Cuire 30 minutes."],
            "image_url": "",
        }
        preview = build_import_preview("https://example.com/recipe")

    assert preview["image_url"] == ""


@pytest.mark.django_db
def test_build_import_preview_falls_back_to_og_image_when_scraper_finds_none():
    with patch("apps.importer.services.scrape_url") as scrape_url, patch(
        "apps.importer.services.fetch_og_image", return_value="https://example.com/og.jpg"
    ) as og_image:
        scrape_url.return_value = {
            "title": "Tarte aux poireaux",
            "servings": 6,
            "cook_time_minutes": 45,
            "ingredients": ["1 pâte brisée"],
            "instructions": ["Cuire 30 minutes."],
            "image_url": "",
        }
        preview = build_import_preview("https://example.com/recipe")

    og_image.assert_called_once_with("https://example.com/recipe")
    assert preview["image_url"] == "https://example.com/og.jpg"


@pytest.mark.django_db
def test_build_import_preview_does_not_use_og_image_fallback_when_scraper_found_one():
    with patch("apps.importer.services.scrape_url") as scrape_url, patch(
        "apps.importer.services.fetch_og_image"
    ) as og_image:
        scrape_url.return_value = {
            "title": "Tarte aux poireaux",
            "servings": 6,
            "cook_time_minutes": 45,
            "ingredients": ["1 pâte brisée"],
            "instructions": ["Cuire 30 minutes."],
            "image_url": "https://example.com/tarte.jpg",
        }
        preview = build_import_preview("https://example.com/recipe")

    og_image.assert_not_called()
    assert preview["image_url"] == "https://example.com/tarte.jpg"


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


def test_fetch_og_image_returns_content_when_meta_tag_present():
    response = MagicMock()
    response.text = '<html><head><meta property="og:image" content="https://example.com/og.jpg"></head></html>'
    response.raise_for_status.return_value = None

    with patch("requests.get", return_value=response):
        assert fetch_og_image("https://example.com/recipe") == "https://example.com/og.jpg"


def test_fetch_og_image_returns_none_when_tag_missing():
    response = MagicMock()
    response.text = "<html><head></head></html>"
    response.raise_for_status.return_value = None

    with patch("requests.get", return_value=response):
        assert fetch_og_image("https://example.com/recipe") is None


def test_fetch_og_image_returns_none_on_network_failure():
    with patch("requests.get", side_effect=Exception("connection refused")):
        assert fetch_og_image("https://example.com/recipe") is None


def test_fetch_og_image_returns_none_on_http_error_status():
    response = MagicMock()
    response.raise_for_status.side_effect = Exception("404")

    with patch("requests.get", return_value=response):
        assert fetch_og_image("https://example.com/recipe") is None


@pytest.mark.django_db
def test_build_import_preview_parses_quantity_and_unit():
    with patch("apps.importer.services.scrape_url") as scrape_url, patch(
        "apps.importer.services.fetch_og_image", return_value=None
    ):
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["200 g de pois chiches", "2 gousses d'ail", "sel"],
            "instructions": ["Mixer.", "Cuire."],
            "image_url": "",
        }
        preview = build_import_preview("https://example.com/falafels")

    by_name = {item["name"]: item for item in preview["ingredients"]}
    assert by_name["pois chiches"]["quantity"] == "200"
    assert by_name["pois chiches"]["unit"] == "g"
    assert by_name["ail"]["quantity"] == "2"
    assert by_name["ail"]["unit"] == "piece"
    assert by_name["sel"]["quantity"] == "1"
    assert by_name["sel"]["unit"] == "piece"


@pytest.mark.django_db
def test_build_import_preview_does_not_write_to_database():
    recipe_count_before = Recipe.objects.count()
    ingredient_count_before = Ingredient.objects.count()

    with patch("apps.importer.services.scrape_url") as scrape_url, patch(
        "apps.importer.services.fetch_og_image", return_value=None
    ):
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["200 g de pois chiches inconnus", "un ingrédient totalement inédit"],
            "instructions": ["Mixer."],
            "image_url": "",
        }
        build_import_preview("https://example.com/falafels")

    assert Recipe.objects.count() == recipe_count_before
    assert Ingredient.objects.count() == ingredient_count_before


@pytest.mark.django_db
def test_build_import_preview_matches_existing_ingredient_by_exact_name():
    existing = IngredientFactory(name="pois chiches")

    with patch("apps.importer.services.scrape_url") as scrape_url, patch(
        "apps.importer.services.fetch_og_image", return_value=None
    ):
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["200 g de pois chiches"],
            "instructions": ["Mixer."],
            "image_url": "",
        }
        preview = build_import_preview("https://example.com/falafels")

    (item,) = preview["ingredients"]
    assert item["ingredient"]["id"] == existing.id


@pytest.mark.django_db
@pytest.mark.parametrize("raw_line", ["2 cloves garlic", "2 Zehen Knoblauch", "2 dientes de ajo"])
def test_build_import_preview_matches_existing_ingredient_by_translation(raw_line):
    ail = IngredientFactory(name="Ail", translations={"en": "garlic", "de": "Knoblauch", "es": "ajo"})

    with patch("apps.importer.services.scrape_url") as scrape_url, patch(
        "apps.importer.services.fetch_og_image", return_value=None
    ):
        scrape_url.return_value = {
            "title": "Recipe",
            "servings": 4,
            "cook_time_minutes": 10,
            "ingredients": [raw_line],
            "instructions": ["Cook."],
            "image_url": "",
        }
        preview = build_import_preview("https://example.com/recipe")

    (item,) = preview["ingredients"]
    assert item["ingredient"]["id"] == ail.id
    assert item["quantity"] == "2"
    assert item["unit"] == "piece"


@pytest.mark.django_db
def test_build_import_preview_matches_existing_ingredient_by_close_match():
    existing = IngredientFactory(name="pois chiche")

    with patch("apps.importer.services.scrape_url") as scrape_url, patch(
        "apps.importer.services.fetch_og_image", return_value=None
    ):
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["200 g de pois chiches"],
            "instructions": ["Mixer."],
            "image_url": "",
        }
        preview = build_import_preview("https://example.com/falafels")

    (item,) = preview["ingredients"]
    assert item["ingredient"]["id"] == existing.id


@pytest.mark.django_db
def test_build_import_preview_leaves_unmatched_ingredient_null():
    with patch("apps.importer.services.scrape_url") as scrape_url, patch(
        "apps.importer.services.fetch_og_image", return_value=None
    ):
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["un ingrédient totalement inédit et jamais vu"],
            "instructions": ["Mixer."],
            "image_url": "",
        }
        preview = build_import_preview("https://example.com/falafels")

    (item,) = preview["ingredients"]
    assert item["ingredient"] is None
