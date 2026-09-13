import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.recipes.factories import RecipeCommentFactory, RecipeFactory
from apps.recipes.throttles import CommentCreateAnonThrottle


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_anonymous_can_post_a_comment():
    recipe = RecipeFactory()
    client = APIClient()

    response = client.post(
        f"/api/recipes/{recipe.id}/comments/",
        {"author_name": "Camille", "body": "Délicieux, merci !"},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["author_name"] == "Camille"
    assert response.data["body"] == "Délicieux, merci !"
    assert "is_hidden" not in response.data
    comment = recipe.comments.get()
    assert comment.user is None


@pytest.mark.django_db
def test_anonymous_can_list_comments():
    recipe = RecipeFactory()
    RecipeCommentFactory(recipe=recipe, author_name="A")
    RecipeCommentFactory(recipe=recipe, author_name="B")
    other_recipe_comment = RecipeCommentFactory()

    client = APIClient()
    response = client.get(f"/api/recipes/{recipe.id}/comments/")

    assert response.status_code == 200
    names = {c["author_name"] for c in response.data["results"]}
    assert names == {"A", "B"}
    assert other_recipe_comment.author_name not in names


@pytest.mark.django_db
def test_authenticated_user_comment_stamps_user_and_defaults_author_name():
    user = UserFactory(username="chef42")
    recipe = RecipeFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(
        f"/api/recipes/{recipe.id}/comments/",
        {"body": "Testé et approuvé."},
        format="json",
    )

    assert response.status_code == 201
    assert response.data["author_name"] == "chef42"
    comment = recipe.comments.get()
    assert comment.user_id == user.id


@pytest.mark.django_db
def test_hidden_comments_excluded_from_listing_for_anonymous_and_other_users():
    recipe = RecipeFactory()
    visible = RecipeCommentFactory(recipe=recipe, author_name="Visible")
    RecipeCommentFactory(recipe=recipe, author_name="Hidden", is_hidden=True)
    other_user = UserFactory()

    anon_client = APIClient()
    response = anon_client.get(f"/api/recipes/{recipe.id}/comments/")
    assert [c["author_name"] for c in response.data["results"]] == [visible.author_name]

    other_client = APIClient()
    other_client.force_authenticate(other_user)
    response = other_client.get(f"/api/recipes/{recipe.id}/comments/")
    assert [c["author_name"] for c in response.data["results"]] == [visible.author_name]


@pytest.mark.django_db
def test_recipe_author_sees_hidden_comments_and_is_hidden_field():
    recipe = RecipeFactory()
    RecipeCommentFactory(recipe=recipe, author_name="Visible")
    RecipeCommentFactory(recipe=recipe, author_name="Hidden", is_hidden=True)

    client = APIClient()
    client.force_authenticate(recipe.author)
    response = client.get(f"/api/recipes/{recipe.id}/comments/")

    names = {c["author_name"] for c in response.data["results"]}
    assert names == {"Visible", "Hidden"}
    assert "is_hidden" in response.data["results"][0]


@pytest.mark.django_db
def test_staff_sees_hidden_comments():
    recipe = RecipeFactory()
    RecipeCommentFactory(recipe=recipe, is_hidden=True)
    staff = UserFactory(is_staff=True)

    client = APIClient()
    client.force_authenticate(staff)
    response = client.get(f"/api/recipes/{recipe.id}/comments/")

    assert response.data["count"] == 1


@pytest.mark.django_db
def test_recipe_author_can_hide_a_comment():
    recipe = RecipeFactory()
    comment = RecipeCommentFactory(recipe=recipe)
    client = APIClient()
    client.force_authenticate(recipe.author)

    response = client.post(f"/api/recipes/{recipe.id}/comments/{comment.id}/hide/")

    assert response.status_code == 200
    comment.refresh_from_db()
    assert comment.is_hidden is True

    # Posting again toggles it back to visible.
    response = client.post(f"/api/recipes/{recipe.id}/comments/{comment.id}/hide/")
    assert response.status_code == 200
    comment.refresh_from_db()
    assert comment.is_hidden is False


@pytest.mark.django_db
def test_other_user_cannot_hide_a_comment():
    recipe = RecipeFactory()
    comment = RecipeCommentFactory(recipe=recipe)
    other_user = UserFactory()
    client = APIClient()
    client.force_authenticate(other_user)

    response = client.post(f"/api/recipes/{recipe.id}/comments/{comment.id}/hide/")

    assert response.status_code == 403
    comment.refresh_from_db()
    assert comment.is_hidden is False


@pytest.mark.django_db
def test_anonymous_cannot_hide_a_comment():
    recipe = RecipeFactory()
    comment = RecipeCommentFactory(recipe=recipe)
    client = APIClient()

    response = client.post(f"/api/recipes/{recipe.id}/comments/{comment.id}/hide/")

    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_empty_body_is_rejected():
    recipe = RecipeFactory()
    client = APIClient()

    response = client.post(
        f"/api/recipes/{recipe.id}/comments/",
        {"author_name": "Camille", "body": "   "},
        format="json",
    )

    assert response.status_code == 400
    assert "body" in response.data


@pytest.mark.django_db
def test_anonymous_comment_without_author_name_is_rejected():
    recipe = RecipeFactory()
    client = APIClient()

    response = client.post(
        f"/api/recipes/{recipe.id}/comments/",
        {"author_name": "   ", "body": "Sympa"},
        format="json",
    )

    assert response.status_code == 400
    assert "author_name" in response.data


@pytest.mark.django_db
def test_anonymous_comment_creation_is_throttled(monkeypatch):
    # DRF resolves DEFAULT_THROTTLE_RATES into a class attribute at import time, so
    # override_settings alone doesn't affect an already-imported throttle class — patch the
    # class attribute directly to keep this test fast (real limit stays 10/hour).
    monkeypatch.setattr(CommentCreateAnonThrottle, "THROTTLE_RATES", {"comment_create": "2/hour"})

    recipe = RecipeFactory()
    client = APIClient()

    for _ in range(2):
        response = client.post(
            f"/api/recipes/{recipe.id}/comments/",
            {"author_name": "Camille", "body": "Encore un commentaire"},
            format="json",
        )
        assert response.status_code == 201

    response = client.post(
        f"/api/recipes/{recipe.id}/comments/",
        {"author_name": "Camille", "body": "Un commentaire de trop"},
        format="json",
    )
    assert response.status_code == 429
