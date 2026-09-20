import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
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


@pytest.mark.django_db
def test_admin_thematic_pages_requires_staff():
    client = APIClient()

    response = client.get("/api/admin/thematic-pages/")
    assert response.status_code == 401

    user = UserFactory()
    client.force_authenticate(user)
    response = client.get("/api/admin/thematic-pages/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_list_thematic_pages():
    ThematicPage.objects.create(title="Spécial végan", icon="🌍", filters={"diet_type": "vegan"}, order=2)
    ThematicPage.objects.create(title="Produits de saison", icon="🌱", filters={"in_season": "true"}, order=1)
    admin = UserFactory(is_staff=True)
    client = APIClient()
    client.force_authenticate(admin)

    response = client.get("/api/admin/thematic-pages/")

    assert response.status_code == 200
    titles = [page["title"] for page in response.data]
    assert titles == ["Produits de saison", "Spécial végan"]


@pytest.mark.django_db
def test_admin_can_create_thematic_page_and_slug_is_generated():
    admin = UserFactory(is_staff=True)
    client = APIClient()
    client.force_authenticate(admin)

    response = client.post(
        "/api/admin/thematic-pages/",
        {
            "title": "Prêt en 30 minutes",
            "description": "Des recettes rapides.",
            "icon": "⏱️",
            "filters": {"max_prep_time": "30"},
            "order": 3,
            "is_active": True,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["slug"] == "pret-en-30-minutes"
    page = ThematicPage.objects.get(id=response.data["id"])
    assert page.filters == {"max_prep_time": "30"}


@pytest.mark.django_db
def test_non_staff_cannot_create_thematic_page():
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post("/api/admin/thematic-pages/", {"title": "Brouillon"}, format="json")

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_can_update_thematic_page():
    page = ThematicPage.objects.create(title="Spécial végan", order=1)
    admin = UserFactory(is_staff=True)
    client = APIClient()
    client.force_authenticate(admin)

    response = client.patch(
        f"/api/admin/thematic-pages/{page.id}/",
        {"is_active": False, "order": 5},
        format="json",
    )

    assert response.status_code == 200
    page.refresh_from_db()
    assert page.is_active is False
    assert page.order == 5


@pytest.mark.django_db
def test_admin_can_delete_thematic_page():
    page = ThematicPage.objects.create(title="Brouillon")
    admin = UserFactory(is_staff=True)
    client = APIClient()
    client.force_authenticate(admin)

    response = client.delete(f"/api/admin/thematic-pages/{page.id}/")

    assert response.status_code == 204
    assert not ThematicPage.objects.filter(id=page.id).exists()


@pytest.mark.django_db
def test_admin_can_upload_and_remove_thematic_page_image(settings, tmp_path):
    from django.core.files.uploadedfile import SimpleUploadedFile
    settings.MEDIA_ROOT = tmp_path
    staff = UserFactory(is_staff=True)
    page = ThematicPage.objects.create(title="Végan")
    client = APIClient()
    client.force_authenticate(staff)
    gif = (
        b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )

    response = client.patch(
        f"/api/admin/thematic-pages/{page.id}/image/",
        {"image": SimpleUploadedFile("a.gif", gif, content_type="image/gif")},
        format="multipart",
    )
    assert response.status_code == 200
    assert response.data["image"]

    response = client.delete(f"/api/admin/thematic-pages/{page.id}/image/")
    assert response.status_code == 200
    assert response.data["image"] is None
