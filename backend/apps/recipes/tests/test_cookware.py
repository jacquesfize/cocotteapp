import io
import re

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.ingredients.factories import IngredientFactory
from apps.recipes.cooklang_import import create_recipe_from_cooklang
from apps.recipes.factories import CookwareFactory, RecipeFactory
from apps.recipes.management.commands import seed_cookware as seed_module
from apps.recipes.management.commands.seed_cookware import COOKWARE
from apps.recipes.models import Cookware


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user)
    return client


# --- Bibliothèque /api/cookware/ -------------------------------------------------------------


@pytest.mark.django_db
def test_list_is_public_unpaginated_and_searchable_in_english_without_accents():
    CookwareFactory(name="Four", translations={"en": "oven"})
    CookwareFactory(name="Poêle", translations={"en": "frying pan"})

    response = _client().get("/api/cookware/")
    assert response.status_code == 200
    assert [item["name"] for item in response.data] == ["Four", "Poêle"]

    assert [item["name"] for item in _client().get("/api/cookware/", {"search": "oven"}).data] == ["Four"]
    assert [item["name"] for item in _client().get("/api/cookware/", {"search": "poele"}).data] == ["Poêle"]


@pytest.mark.django_db
def test_any_logged_in_user_can_create_but_not_duplicate():
    assert _client().post("/api/cookware/", {"name": "Wok"}, format="json").status_code == 401

    client = _client(UserFactory())
    response = client.post("/api/cookware/", {"name": " Wok "}, format="json")
    assert response.status_code == 201
    assert (response.data["name"], response.data["slug"]) == ("Wok", "wok")

    duplicate = client.post("/api/cookware/", {"name": "wok"}, format="json")
    assert duplicate.status_code == 400


@pytest.mark.django_db
def test_only_staff_can_edit_or_delete_and_delete_detaches_from_recipes():
    cookware = CookwareFactory(name="Four")
    recipe = RecipeFactory()
    recipe.cookware.add(cookware)

    user_client = _client(UserFactory())
    assert user_client.patch(f"/api/cookware/{cookware.id}/", {"name": "x"}, format="json").status_code == 403
    assert user_client.delete(f"/api/cookware/{cookware.id}/").status_code == 403

    staff_client = _client(UserFactory(is_staff=True))
    response = staff_client.patch(
        f"/api/cookware/{cookware.id}/", {"name": "Four", "translations": {"en": "oven"}}, format="json"
    )
    assert response.status_code == 200
    assert response.data["translations"] == {"en": "oven"}

    assert staff_client.delete(f"/api/cookware/{cookware.id}/").status_code == 204
    assert recipe.cookware.count() == 0


# --- Recette : écriture, lecture, filtre, version ---------------------------------------------


@pytest.mark.django_db
def test_recipe_create_and_update_cookware():
    user = UserFactory()
    oven, pan = CookwareFactory(name="Four"), CookwareFactory(name="Poêle")
    ingredient = IngredientFactory()
    client = _client(user)

    response = client.post(
        "/api/recipes/",
        {
            "title": "Gratin",
            "cookware_ids": [oven.id],
            "ingredients": [{"ingredient_id": ingredient.id, "quantity": "200", "unit": "g", "order": 1}],
            "steps": [{"order": 1, "instruction": "Enfourner dans le #four."}],
        },
        format="json",
    )
    assert response.status_code == 201
    assert [item["name"] for item in response.data["cookware"]] == ["Four"]
    assert "cookware_ids" not in response.data

    recipe_id = response.data["id"]
    # Une modification qui ne mentionne pas le matériel le laisse en place.
    assert client.patch(f"/api/recipes/{recipe_id}/", {"title": "Gratin dauphinois"}, format="json").status_code == 200
    response = client.patch(f"/api/recipes/{recipe_id}/", {"cookware_ids": [pan.id, oven.id]}, format="json")
    assert sorted(item["name"] for item in response.data["cookware"]) == ["Four", "Poêle"]
    response = client.patch(f"/api/recipes/{recipe_id}/", {"cookware_ids": []}, format="json")
    assert response.data["cookware"] == []


@pytest.mark.django_db
def test_filter_recipes_using_any_of_the_given_cookware():
    oven, air_fryer, pan = (
        CookwareFactory(name="Four"),
        CookwareFactory(name="Friteuse à air"),
        CookwareFactory(name="Poêle"),
    )
    baked, fried, both, other = RecipeFactory(), RecipeFactory(), RecipeFactory(), RecipeFactory()
    baked.cookware.add(oven)
    fried.cookware.add(air_fryer)
    both.cookware.add(oven, air_fryer)
    other.cookware.add(pan)

    response = _client().get("/api/recipes/", {"cookware": f"{oven.slug},{air_fryer.slug}"})

    assert response.status_code == 200
    assert sorted(item["id"] for item in response.data["results"]) == sorted([baked.id, fried.id, both.id])


@pytest.mark.django_db
def test_fork_copies_cookware():
    source = RecipeFactory()
    source.cookware.add(CookwareFactory(name="Wok"))

    response = _client(UserFactory()).post(f"/api/recipes/{source.id}/fork/", {"version_label": "Épicée"}, format="json")

    assert response.status_code == 201
    assert [item["name"] for item in response.data["cookware"]] == ["Wok"]


# --- Cooklang ----------------------------------------------------------------------------------

COOKLANG_TEXT = """\
Préchauffer le #four{}.
Faire revenir l'@oignon{1} dans une #poele{} puis dans la #grande casserole{}.
Remettre le tout dans la #poêle.
"""


@pytest.mark.django_db
def test_cooklang_import_matches_or_creates_cookware_and_keeps_tags():
    oven = CookwareFactory(name="Four", translations={"en": "oven"})
    pan = CookwareFactory(name="Poêle")

    recipe = create_recipe_from_cooklang(author=UserFactory(), title="Test", raw_cooklang=COOKLANG_TEXT)

    names = sorted(item.name for item in recipe.cookware.all())
    assert names == ["Four", "Poêle", "grande casserole"]  # "poele"/"poêle" : un seul matériel
    assert set(recipe.cookware.all()) >= {oven, pan}
    steps = list(recipe.steps.order_by("order"))
    assert steps[0].instruction == "Préchauffer le #four{}."
    assert "#grande_casserole{}" in steps[1].instruction


@pytest.mark.django_db
def test_cooklang_preview_lists_cookware_without_creating_any():
    oven = CookwareFactory(name="Four", translations={"en": "oven"})
    client = _client(UserFactory())

    response = client.post(
        "/api/recipes/preview-cooklang/", {"raw_cooklang": "Bake in the #oven{} with a #whisk."}, format="json"
    )

    assert response.status_code == 200
    assert response.data["cookware"] == [
        {
            "name": "oven",
            "cookware": {
                "id": oven.id,
                "name": "Four",
                "slug": "four",
                "emoji": "",
                "image": None,
                "image_license": "",
                "image_credit_author": "",
                "image_credit_source_url": "",
                "image_credit_license_url": "",
                "translations": {"en": "oven"},
            },
        },
        {"name": "whisk", "cookware": None},
    ]
    assert Cookware.objects.count() == 1


# --- Données de référence ----------------------------------------------------------------------


def _png():
    buffer = io.BytesIO()
    Image.new("RGB", (2, 2)).save(buffer, "PNG")
    return SimpleUploadedFile("photo.png", buffer.getvalue(), content_type="image/png")


@pytest.mark.django_db
def test_staff_can_set_emoji_and_upload_or_remove_a_photo(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    cookware = CookwareFactory(name="Poêle")
    url = f"/api/cookware/{cookware.id}/image/"

    assert _client(UserFactory()).patch(url, {"image": _png()}, format="multipart").status_code == 403

    staff = _client(UserFactory(is_staff=True))
    assert staff.patch(f"/api/cookware/{cookware.id}/", {"emoji": "🍳"}, format="json").data["emoji"] == "🍳"
    assert staff.patch(url, {}, format="multipart").status_code == 400
    # Même règle que pour une photo de recette : licence obligatoire, auteur + source en CC BY-SA.
    assert staff.patch(url, {"image": _png()}, format="multipart").status_code == 400
    missing = staff.patch(url, {"image": _png(), "image_license": "cc_by_sa"}, format="multipart")
    assert set(missing.data) == {"image_credit_author", "image_credit_source_url"}

    response = staff.patch(
        url,
        {
            "image": _png(),
            "image_license": "cc_by_sa",
            "image_credit_author": "Pengo",
            "image_credit_source_url": "https://commons.wikimedia.org/wiki/File:Peeler_01_Pengo.jpg",
        },
        format="multipart",
    )
    assert response.status_code == 200
    assert response.data["image"].startswith("/media/cookware/")
    assert response.data["image_credit_author"] == "Pengo"
    assert response.data["image_credit_license_url"] == "https://creativecommons.org/licenses/by-sa/4.0/"
    path = tmp_path / response.data["image"].removeprefix("/media/")
    assert path.exists()

    response = staff.delete(url)
    assert (response.data["image"], response.data["image_license"], response.data["image_credit_author"]) == (
        None,
        "",
        "",
    )
    assert not path.exists()


def _fake_fetch(fetched):
    def fetch(file_name):
        fetched.append(file_name)
        buffer = io.BytesIO()
        Image.new("RGB", (40, 20), "red").save(buffer, "JPEG")
        return buffer.getvalue()

    return fetch


@pytest.fixture
def no_network(monkeypatch, tmp_path, settings):
    """Le seed ne télécharge rien en test : chaque photo est une image générée."""
    settings.MEDIA_ROOT = tmp_path
    fetched = []
    monkeypatch.setattr(seed_module, "fetch_image", _fake_fetch(fetched))
    monkeypatch.setattr(seed_module, "DOWNLOAD_DELAY_SECONDS", 0)
    return fetched


@pytest.mark.django_db
def test_seed_cookware_downloads_photos_with_their_credit_without_overwriting(no_network):
    wok = CookwareFactory(name="Wok", emoji="🔥")
    wok.image.save("mine.jpg", _png(), save=True)

    call_command("seed_cookware")

    pan = Cookware.objects.get(name="Poêle")
    assert pan.emoji == "🍳"
    assert re.fullmatch(r"cookware/poele-[0-9a-f]{8}\.jpg", pan.image.name)
    assert Image.open(pan.image.path).size == (480, 480)
    assert pan.image_license == "public_domain"
    assert pan.image_credit_source_url == "https://commons.wikimedia.org/wiki/File:Pfanne_%28Edelstahl%29.jpg"

    peeler = Cookware.objects.get(name="Économe")
    assert (peeler.image_license, peeler.image_credit_author) == ("cc_by_sa", "Pengo")
    assert peeler.image_credit_license_url == "https://creativecommons.org/licenses/by-sa/3.0/"

    wok.refresh_from_db()
    assert (wok.emoji, wok.image.name.startswith("cookware/mine")) == ("🔥", True)
    assert "Cooking with a wok on an outdoor stove 5.jpg" not in no_network
    assert not Cookware.objects.get(name="Cuiseur vapeur").image  # pas de photo retenue

    # Relancé, il ne retélécharge rien : toutes les photos sont déjà en place.
    no_network.clear()
    call_command("seed_cookware")
    assert no_network == []


@pytest.mark.django_db
def test_seed_cookware_survives_a_failed_download_and_can_skip_images(no_network, monkeypatch):
    def fail(file_name):
        raise OSError("offline")

    monkeypatch.setattr(seed_module, "fetch_image", fail)
    out = io.StringIO()
    call_command("seed_cookware", stdout=out)
    assert Cookware.objects.count() == len(COOKWARE)
    assert not Cookware.objects.exclude(image="").exclude(image=None).exists()
    assert "Photo non téléchargée : Poêle (offline)" in out.getvalue()

    monkeypatch.setattr(seed_module, "fetch_image", _fake_fetch(no_network))
    call_command("seed_cookware", "--skip-images")
    assert no_network == []


@pytest.mark.django_db
def test_seed_cookware_is_idempotent_and_keeps_user_cookware(no_network):
    CookwareFactory(name="four", translations={"de": "Ofen"})
    CookwareFactory(name="Siphon")

    call_command("seed_cookware")
    call_command("seed_cookware")

    assert Cookware.objects.count() == len(COOKWARE) + 1
    assert Cookware.objects.get(name="four").translations == {"de": "Ofen", "en": "oven"}
