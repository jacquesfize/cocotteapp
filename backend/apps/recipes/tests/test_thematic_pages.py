import pytest
from rest_framework.test import APIClient

from apps.recipes.models import ThematicPage


@pytest.mark.django_db
def test_list_thematic_pages_is_public_and_ordered():
    ThematicPage.objects.create(title="Spécial végan", icon="🌍", filters={"diet_type": "vegan"}, order=2)
    ThematicPage.objects.create(title="Produits de saison", icon="🌱", filters={"in_season": "true"}, order=1)

    response = APIClient().get("/api/thematic-pages/")

    assert response.status_code == 200
    titles = [page["title"] for page in response.data]
    assert titles == ["Produits de saison", "Spécial végan"]
    assert response.data[0]["filters"] == {"in_season": "true"}


@pytest.mark.django_db
def test_inactive_thematic_page_is_hidden():
    ThematicPage.objects.create(title="Brouillon", is_active=False)

    response = APIClient().get("/api/thematic-pages/")

    assert response.status_code == 200
    assert response.data == []


@pytest.mark.django_db
def test_thematic_page_slug_is_generated_from_title():
    page = ThematicPage.objects.create(title="Produits de saison")

    assert page.slug == "produits-de-saison"
