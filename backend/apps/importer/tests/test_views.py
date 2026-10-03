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


@pytest.mark.django_db
def test_image_suggestions_requires_authentication():
    client = APIClient()
    response = client.get("/api/import/image-suggestions/", {"q": "tarte"})
    assert response.status_code == 401


@pytest.mark.django_db
def test_image_suggestions_requires_query():
    client = APIClient()
    client.force_authenticate(UserFactory())

    response = client.get("/api/import/image-suggestions/")

    assert response.status_code == 400


@pytest.mark.django_db
def test_image_suggestions_returns_results():
    client = APIClient()
    client.force_authenticate(UserFactory())
    suggestion = {
        "url": "https://example.com/tarte.jpg",
        "thumbnail": "https://example.com/tarte-thumb.jpg",
        "title": "Tarte",
        "image_license": "cc_by",
        "image_credit_author": "Alice",
        "image_credit_source_url": "https://example.com/photo",
        "image_credit_license_url": "https://creativecommons.org/licenses/by/4.0/",
    }

    with patch("apps.importer.views.search_free_images", return_value=[suggestion]) as search:
        response = client.get("/api/import/image-suggestions/", {"q": " tarte "})

    search.assert_called_once_with("tarte")
    assert response.status_code == 200
    assert response.data["results"] == [suggestion]


@pytest.mark.django_db
def test_image_suggestions_returns_502_when_provider_fails():
    client = APIClient()
    client.force_authenticate(UserFactory())

    with patch("apps.importer.views.search_free_images", side_effect=Exception("timeout")):
        response = client.get("/api/import/image-suggestions/", {"q": "tarte"})

    assert response.status_code == 502
