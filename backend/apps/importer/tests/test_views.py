from unittest.mock import patch

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory


@pytest.mark.django_db
def test_import_preview_requires_authentication():
    client = APIClient()
    response = client.post("/api/import/url/", {"url": "https://example.com/recipe"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_import_preview_requires_url():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post("/api/import/url/", {}, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_import_preview_returns_scraped_draft():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    with patch("apps.importer.views.build_import_preview") as build_import_preview:
        build_import_preview.return_value = {
            "title": "Falafels",
            "servings": 4,
            "cook_time_minutes": 20,
            "image_url": "",
            "source_url": "https://example.com/falafels",
            "steps": [{"order": 1, "instruction": "Mixer."}],
            "ingredients": [
                {"raw_line": "sel", "quantity": "1", "unit": "piece", "name": "sel", "ingredient": None}
            ],
        }
        response = client.post("/api/import/url/", {"url": "https://example.com/falafels"}, format="json")

    assert response.status_code == 200
    assert response.data["title"] == "Falafels"
    assert response.data["ingredients"][0]["ingredient"] is None


@pytest.mark.django_db
def test_import_preview_returns_400_when_scraping_fails():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    with patch("apps.importer.views.build_import_preview", side_effect=Exception("unsupported site")):
        response = client.post("/api/import/url/", {"url": "https://example.com/unsupported"}, format="json")

    assert response.status_code == 400
