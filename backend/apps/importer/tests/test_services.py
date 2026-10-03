from unittest.mock import MagicMock, patch

import pytest

from apps.importer.services import build_import_preview, search_free_images
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

    with patch("apps.importer.services.scrape_url") as scrape_url:
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
def test_build_import_preview_parses_quantity_and_unit():
    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["200 g de pois chiches", "2 gousses d'ail", "sel"],
            "instructions": ["Mixer.", "Cuire."],
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

    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["200 g de pois chiches inconnus", "un ingrédient totalement inédit"],
            "instructions": ["Mixer."],
        }
        build_import_preview("https://example.com/falafels")

    assert Recipe.objects.count() == recipe_count_before
    assert Ingredient.objects.count() == ingredient_count_before


@pytest.mark.django_db
def test_build_import_preview_matches_existing_ingredient_by_exact_name():
    existing = IngredientFactory(name="pois chiches")

    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["200 g de pois chiches"],
            "instructions": ["Mixer."],
        }
        preview = build_import_preview("https://example.com/falafels")

    (item,) = preview["ingredients"]
    assert item["ingredient"]["id"] == existing.id


@pytest.mark.django_db
@pytest.mark.parametrize("raw_line", ["2 cloves garlic", "2 Zehen Knoblauch", "2 dientes de ajo"])
def test_build_import_preview_matches_existing_ingredient_by_translation(raw_line):
    ail = IngredientFactory(name="Ail", translations={"en": "garlic", "de": "Knoblauch", "es": "ajo"})

    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Recipe",
            "servings": 4,
            "cook_time_minutes": 10,
            "ingredients": [raw_line],
            "instructions": ["Cook."],
        }
        preview = build_import_preview("https://example.com/recipe")

    (item,) = preview["ingredients"]
    assert item["ingredient"]["id"] == ail.id
    assert item["quantity"] == "2"
    assert item["unit"] == "piece"


@pytest.mark.django_db
def test_build_import_preview_matches_existing_ingredient_by_close_match():
    existing = IngredientFactory(name="pois chiche")

    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["200 g de pois chiches"],
            "instructions": ["Mixer."],
        }
        preview = build_import_preview("https://example.com/falafels")

    (item,) = preview["ingredients"]
    assert item["ingredient"]["id"] == existing.id


@pytest.mark.django_db
def test_build_import_preview_leaves_unmatched_ingredient_null():
    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "ingredients": ["un ingrédient totalement inédit et jamais vu"],
            "instructions": ["Mixer."],
        }
        preview = build_import_preview("https://example.com/falafels")

    (item,) = preview["ingredients"]
    assert item["ingredient"] is None


@pytest.mark.django_db
def test_build_import_preview_never_includes_the_source_image():
    """The source site's photo is copyrighted by its photographer: the preview must not carry
    it (nor any pre-filled credit for it), so the user picks their own or a free one."""
    with patch("apps.importer.services.scrape_url") as scrape_url:
        scrape_url.return_value = {
            "title": "Tarte aux poireaux",
            "servings": 6,
            "cook_time_minutes": 45,
            "ingredients": ["1 pâte brisée"],
            "instructions": ["Cuire 30 minutes."],
        }
        preview = build_import_preview("https://example.com/recipe")

    assert "image_url" not in preview
    assert "image_license" not in preview
    assert "image_credit_note" not in preview


def test_scrape_url_does_not_read_the_image():
    from apps.importer.services import scrape_url

    scraper = MagicMock()
    scraper.title.return_value = "Tarte aux poireaux"
    scraper.yields.return_value = "6 servings"
    scraper.total_time = 45
    scraper.ingredients.return_value = ["1 pâte brisée"]
    scraper.instructions.return_value = "Cuire 30 minutes."

    with patch("recipe_scrapers.scrape_me", return_value=scraper):
        data = scrape_url("https://example.com/recipe")

    scraper.image.assert_not_called()
    assert "image_url" not in data


def _openverse_response(results):
    response = MagicMock()
    response.json.return_value = {"results": results}
    response.raise_for_status.return_value = None
    return response


def test_search_free_images_maps_openverse_results_to_credit_fields():
    results = [
        {
            "url": "https://live.staticflickr.com/1/tarte.jpg",
            "thumbnail": "https://api.openverse.org/v1/images/abc/thumb/",
            "title": "Tarte",
            "creator": "Alice",
            "license": "by",
            "license_url": "https://creativecommons.org/licenses/by/2.0/",
            "foreign_landing_url": "https://www.flickr.com/photos/alice/1",
        },
        {
            "url": "https://upload.wikimedia.org/tarte.jpg",
            "title": "Tarte 2",
            "creator": None,
            "license": "cc0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "foreign_landing_url": "https://commons.wikimedia.org/wiki/File:Tarte.jpg",
        },
    ]
    with patch("requests.get", return_value=_openverse_response(results)) as get:
        suggestions = search_free_images("tarte aux poireaux")

    params = get.call_args.kwargs["params"]
    assert params["q"] == "tarte aux poireaux"
    assert set(params["license"].split(",")) == {"by", "by-sa", "cc0", "pdm"}
    assert suggestions == [
        {
            "url": "https://live.staticflickr.com/1/tarte.jpg",
            "thumbnail": "https://api.openverse.org/v1/images/abc/thumb/",
            "title": "Tarte",
            "image_license": "cc_by",
            "image_credit_author": "Alice",
            "image_credit_source_url": "https://www.flickr.com/photos/alice/1",
            "image_credit_license_url": "https://creativecommons.org/licenses/by/2.0/",
        },
        {
            "url": "https://upload.wikimedia.org/tarte.jpg",
            "thumbnail": "https://upload.wikimedia.org/tarte.jpg",
            "title": "Tarte 2",
            "image_license": "public_domain",
            "image_credit_author": "",
            "image_credit_source_url": "https://commons.wikimedia.org/wiki/File:Tarte.jpg",
            "image_credit_license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
        },
    ]


def test_search_free_images_skips_non_free_licenses_and_too_long_urls():
    results = [
        {"url": "https://example.com/nc.jpg", "license": "by-nc", "foreign_landing_url": ""},
        {"url": "https://example.com/" + "x" * 200 + ".jpg", "license": "by", "foreign_landing_url": ""},
    ]
    with patch("requests.get", return_value=_openverse_response(results)):
        assert search_free_images("tarte") == []
