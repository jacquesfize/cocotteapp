from unittest.mock import MagicMock, patch

import pytest

from apps.accounts.factories import UserFactory
from apps.importer.services import create_recipe_from_url


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
