"""Matériel créé par les utilisateurs : non vérifié, modifiable par son créateur tant qu'aucune
recette d'un autre utilisateur ne l'utilise, file de relecture et fusion côté staff."""

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.recipes.factories import CookwareFactory, RecipeFactory
from apps.recipes.models import Cookware

pytestmark = pytest.mark.django_db


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user)
    return client


def _url(cookware, suffix=""):
    return f"/api/cookware/{cookware.id}/{suffix}"


def _by_name(response):
    return {item["name"]: item for item in response.data}


def test_user_created_cookware_is_unverified_and_attributed():
    user = UserFactory(username="alice")
    response = _client(user).post("/api/cookware/", {"name": "Wok", "is_verified": True}, format="json")
    assert response.status_code == 201
    assert response.data["is_verified"] is False
    assert (response.data["created_by"], response.data["created_by_username"]) == (user.id, "alice")
    assert response.data["can_edit"] is True


def test_staff_created_cookware_is_verified_unless_explicitly_not():
    staff = UserFactory(is_staff=True)
    client = _client(staff)
    response = client.post("/api/cookware/", {"name": "Wok"}, format="json")
    assert (response.data["is_verified"], response.data["created_by"]) == (True, staff.id)
    response = client.post("/api/cookware/", {"name": "Tajine", "is_verified": False}, format="json")
    assert response.data["is_verified"] is False


def test_creator_can_edit_and_delete_own_unverified_cookware_used_by_own_recipe():
    user = UserFactory()
    cookware = CookwareFactory(created_by=user, is_verified=False)
    recipe = RecipeFactory(author=user)
    recipe.cookware.add(cookware)
    client = _client(user)

    response = client.patch(_url(cookware), {"name": "Wok", "is_verified": True}, format="json")
    assert response.status_code == 200
    assert (response.data["name"], response.data["is_verified"]) == ("Wok", False)
    assert client.delete(_url(cookware)).status_code == 204
    assert recipe.cookware.count() == 0


def test_creator_locked_out_once_verified_or_used_by_another_users_recipe():
    user = UserFactory()
    verified = CookwareFactory(name="a", created_by=user)
    shared = CookwareFactory(name="b", created_by=user, is_verified=False)
    RecipeFactory().cookware.add(shared)
    client = _client(user)

    items = _by_name(client.get("/api/cookware/"))
    assert (items["a"]["can_edit"], items["b"]["can_edit"]) == (False, False)
    for cookware in (verified, shared):
        assert client.patch(_url(cookware), {"name": "x"}, format="json").status_code == 403
        assert client.delete(_url(cookware)).status_code == 403


def test_other_users_cannot_edit_and_staff_always_can():
    cookware = CookwareFactory(created_by=UserFactory(), is_verified=False)
    RecipeFactory().cookware.add(cookware)
    other = _client(UserFactory())
    assert other.get(_url(cookware)).data["can_edit"] is False
    assert other.patch(_url(cookware), {"name": "x"}, format="json").status_code == 403

    staff = _client(UserFactory(is_staff=True))
    assert staff.get(_url(cookware)).data["can_edit"] is True
    response = staff.patch(_url(cookware), {"is_verified": True}, format="json")
    assert response.data["is_verified"] is True


def test_creator_cannot_change_photo():
    user = UserFactory()
    cookware = CookwareFactory(created_by=user, is_verified=False)
    assert _client(user).delete(_url(cookware, "image/")).status_code == 403


def test_can_edit_in_list_without_query_per_row(django_assert_max_num_queries):
    user = UserFactory()
    for n in range(6):
        CookwareFactory(name=f"c{n}", created_by=user, is_verified=False)
    mine = CookwareFactory(name="mine", created_by=user, is_verified=False)
    RecipeFactory(author=user).cookware.add(mine)
    with django_assert_max_num_queries(3):
        items = _by_name(_client(user).get("/api/cookware/"))
    assert all(item["can_edit"] for item in items.values())


def test_filter_by_is_verified():
    CookwareFactory(name="Four")
    CookwareFactory(name="Wok", is_verified=False)
    client = _client()
    assert [c["name"] for c in client.get("/api/cookware/?is_verified=false").data] == ["Wok"]
    assert [c["name"] for c in client.get("/api/cookware/?is_verified=true").data] == ["Four"]


def test_merge_moves_recipes_merges_translations_and_deletes_source(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    target = CookwareFactory(name="Poêle", translations={"en": "frying pan"})
    source = CookwareFactory(
        name="Poele", is_verified=False, translations={"en": "pan", "de": "Pfanne"},
        image=SimpleUploadedFile("poele.png", b"fake", content_type="image/png"),
    )
    image_path = tmp_path / source.image.name
    assert image_path.exists()
    only_source, both = RecipeFactory(), RecipeFactory()
    only_source.cookware.add(source)
    both.cookware.add(source, target)

    response = _client(UserFactory(is_staff=True)).post(
        _url(source, "merge/"), {"into": target.id}, format="json"
    )
    assert response.status_code == 200
    assert response.data["id"] == target.id
    assert response.data["translations"] == {"en": "frying pan", "de": "Pfanne"}
    assert not Cookware.objects.filter(pk=source.pk).exists()
    assert not image_path.exists()
    assert list(only_source.cookware.all()) == [target]
    assert list(both.cookware.all()) == [target]


def test_merge_rejects_bad_target_and_non_staff():
    source, target = CookwareFactory(), CookwareFactory()
    staff = _client(UserFactory(is_staff=True))
    assert staff.post(_url(source, "merge/"), {}, format="json").status_code == 400
    assert staff.post(_url(source, "merge/"), {"into": 999999}, format="json").status_code == 400
    assert staff.post(_url(source, "merge/"), {"into": source.id}, format="json").status_code == 400
    assert _client(UserFactory()).post(_url(source, "merge/"), {"into": target.id}, format="json").status_code == 403
    assert Cookware.objects.filter(pk=source.pk).exists()
