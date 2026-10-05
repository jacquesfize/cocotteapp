from io import BytesIO

import pytest
from PIL import Image
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.recipes.factories import RecipeFactory, RecipeIngredientFactory
from apps.ingredients.factories import IngredientFactory


def _fake_image_file():
    buffer = BytesIO()
    Image.new("RGB", (10, 10), color="red").save(buffer, format="JPEG")
    buffer.seek(0)
    buffer.name = "test.jpg"
    return buffer


@pytest.mark.django_db
def test_recipe_pdf_download_returns_pdf():
    recipe = RecipeFactory(title="Curry de saison")
    ingredient = IngredientFactory()
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient)

    client = APIClient()
    response = client.get(f"/api/recipes/{recipe.id}/pdf/")

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


@pytest.mark.django_db
def test_author_can_upload_recipe_image():
    recipe = RecipeFactory()

    client = APIClient()
    client.force_authenticate(recipe.author)
    response = client.patch(
        f"/api/recipes/{recipe.id}/image/",
        {"image": _fake_image_file(), "image_license": "public_domain"},
        format="multipart",
    )

    assert response.status_code == 200
    recipe.refresh_from_db()
    assert recipe.image.name


@pytest.mark.django_db
def test_non_author_cannot_upload_recipe_image():
    recipe = RecipeFactory()
    other_user = UserFactory()

    client = APIClient()
    client.force_authenticate(other_user)
    response = client.patch(
        f"/api/recipes/{recipe.id}/image/",
        {"image": _fake_image_file(), "image_license": "public_domain"},
        format="multipart",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_non_author_cannot_update_recipe():
    recipe = RecipeFactory(title="Original")
    other_user = UserFactory()

    client = APIClient()
    client.force_authenticate(other_user)
    response = client.patch(f"/api/recipes/{recipe.id}/", {"title": "Modifié"}, format="json")

    assert response.status_code == 403
    recipe.refresh_from_db()
    assert recipe.title == "Original"


@pytest.mark.django_db
def test_author_can_update_own_recipe():
    recipe = RecipeFactory(title="Original")

    client = APIClient()
    client.force_authenticate(recipe.author)
    response = client.patch(f"/api/recipes/{recipe.id}/", {"title": "Modifié"}, format="json")

    assert response.status_code == 200
    recipe.refresh_from_db()
    assert recipe.title == "Modifié"


@pytest.mark.django_db
def test_recipe_serializer_exposes_youtube_id():
    recipe = RecipeFactory(video_url="https://youtu.be/dQw4w9WgXcQ")

    client = APIClient()
    response = client.get(f"/api/recipes/{recipe.id}/")

    assert response.data["youtube_id"] == "dQw4w9WgXcQ"


@pytest.mark.django_db
def test_recipe_pdf_template_titles_each_ingredient_part():
    from django.template.loader import render_to_string

    recipe = RecipeFactory()
    butter = IngredientFactory(name="Beurre")
    RecipeIngredientFactory(recipe=recipe, ingredient=butter, group_name="Pâte", order=1)
    RecipeIngredientFactory(recipe=recipe, ingredient=butter, group_name="Garniture", order=2)
    RecipeIngredientFactory(recipe=recipe, ingredient=IngredientFactory(name="Sucre"), group_name="Garniture", order=3)

    html = render_to_string("pdf/recipe.html", {"recipe": recipe, "image_src": None})

    assert html.count('class="ingredient-part"') == 2
    assert html.index("Pâte") < html.index("Garniture")
