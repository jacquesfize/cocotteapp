import io
import json
import zipfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.ingredients.factories import IngredientFactory
from apps.ingredients.models import Ingredient
from apps.recipes.factories import RecipeFactory, RecipeIngredientFactory
from apps.recipes.models import Recipe, RecipeStep, Tag


def _client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


def _upload(content):
    return {"file": SimpleUploadedFile("export.zip", content, content_type="application/zip")}


def _zip(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, data in files.items():
            archive.writestr(name, data)
    return buffer.getvalue()


@pytest.mark.django_db
def test_export_requires_authentication():
    assert APIClient().get("/api/recipes/export/").status_code == 401


@pytest.mark.django_db
def test_export_only_contains_own_recipes():
    user = UserFactory()
    mine = RecipeFactory(author=user, title="Ma tarte")
    RecipeFactory(title="Pas la mienne")

    response = _client(user).get("/api/recipes/export/")

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        manifest = json.loads(archive.read("recipes.json"))
    assert [(r["title"], r["author"]) for r in manifest["recipes"]] == [(mine.title, user.username)]


@pytest.mark.django_db
def test_round_trip_into_another_account(tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    source_user = UserFactory()
    recipe = RecipeFactory(author=source_user, title="Curry", diet_type="vegan")
    recipe.tags.add(Tag.objects.create(name="Épicé"))
    RecipeIngredientFactory(recipe=recipe, ingredient=IngredientFactory(name="Lentilles", calories_kcal=116))
    RecipeStep.objects.create(recipe=recipe, order=1, instruction="Cuire.")
    fork = RecipeFactory(author=source_user, title="Curry doux", root_recipe=recipe, version_label="Doux")
    image = io.BytesIO()
    Image.new("RGB", (2, 2)).save(image, "PNG")
    recipe.image.save("a.png", SimpleUploadedFile("a.png", image.getvalue()))

    archive = _client(source_user).get("/api/recipes/export/").content

    # Instance cible : l'ingrédient n'existe pas encore.
    Recipe.objects.all().delete()
    Ingredient.objects.all().delete()
    Tag.objects.all().delete()
    target_user = UserFactory()
    response = _client(target_user).post("/api/recipes/import-archive/", _upload(archive), format="multipart")

    assert response.status_code == 201
    assert response.data == {"created": 2, "skipped": 0, "errors": []}
    imported = Recipe.objects.get(title="Curry")
    assert imported.author == target_user
    assert imported.diet_type == "vegan"
    assert imported.tags.get().name == "Épicé"
    assert imported.steps.get().instruction == "Cuire."
    assert imported.recipe_ingredients.get().ingredient.calories_kcal == 116
    assert imported.image
    assert Recipe.objects.get(title=fork.title).root_recipe == imported


@pytest.mark.django_db
def test_import_reuses_existing_ingredient_and_skips_duplicates():
    user = UserFactory()
    ingredient = IngredientFactory(name="Ail", calories_kcal=10)
    recipe = RecipeFactory(author=user, title="Aïoli")
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient)
    archive = _client(user).get("/api/recipes/export/").content

    response = _client(user).post("/api/recipes/import-archive/", _upload(archive), format="multipart")

    assert response.status_code == 200
    assert response.data["created"] == 0
    assert response.data["skipped"] == 1
    assert Ingredient.objects.filter(name="Ail").count() == 1

    other = UserFactory()
    response = _client(other).post("/api/recipes/import-archive/", _upload(archive), format="multipart")
    assert response.data["created"] == 1
    assert Ingredient.objects.filter(name="Ail").count() == 1
    assert Ingredient.objects.get(name="Ail").calories_kcal == 10


@pytest.mark.django_db
def test_import_rejects_invalid_archives():
    client = _client(UserFactory())
    for content in [
        b"not a zip",
        _zip({"other.txt": "x"}),
        _zip({"recipes.json": "{"}),
        _zip({"recipes.json": json.dumps({"format": "other", "version": 1, "recipes": []})}),
        _zip({"recipes.json": json.dumps({"format": "cocotte-recipes", "version": 99, "recipes": []})}),
    ]:
        response = client.post("/api/recipes/import-archive/", _upload(content), format="multipart")
        assert response.status_code == 400, content


@pytest.mark.django_db
def test_import_reports_invalid_recipe_but_imports_the_others():
    manifest = {
        "format": "cocotte-recipes",
        "version": 1,
        "recipes": [
            {"ref": "r1", "title": "Bonne", "ingredients": [], "steps": []},
            {"ref": "r2", "title": "Cassée", "ingredients": [{"ingredient": {"name": "X"}, "quantity": "abc"}]},
        ],
    }
    user = UserFactory()
    response = _client(user).post(
        "/api/recipes/import-archive/", _upload(_zip({"recipes.json": json.dumps(manifest)})), format="multipart"
    )

    assert response.data["created"] == 1
    assert [e["title"] for e in response.data["errors"]] == ["Cassée"]
    assert not Recipe.objects.filter(title="Cassée").exists()
    assert not Ingredient.objects.filter(name="X").exists()


@pytest.mark.django_db
def test_staff_can_export_every_users_recipes():
    RecipeFactory(title="A")
    RecipeFactory(title="B")
    admin = UserFactory(is_staff=True)

    response = _client(admin).get("/api/recipes/export/?scope=all")

    assert response.status_code == 200
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        titles = {r["title"] for r in json.loads(archive.read("recipes.json"))["recipes"]}
    assert titles == {"A", "B"}


@pytest.mark.django_db
def test_non_staff_cannot_export_whole_database():
    RecipeFactory(title="A")

    response = _client(UserFactory()).get("/api/recipes/export/?scope=all")

    assert response.status_code == 403
