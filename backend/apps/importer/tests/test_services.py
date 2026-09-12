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
