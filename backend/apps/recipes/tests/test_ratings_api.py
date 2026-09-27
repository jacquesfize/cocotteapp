import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.recipes.factories import RecipeFactory, RecipeRatingFactory
from apps.recipes.models import RecipeRating
from apps.recipes.throttles import RatingCreateAnonThrottle


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_anonymous_can_rate_a_recipe():
    recipe = RecipeFactory()
    client = APIClient()

    response = client.post(f"/api/recipes/{recipe.id}/rate/", {"value": 4}, format="json")

    assert response.status_code == 200
    assert response.data == {"average_rating": 4.0, "ratings_count": 1, "my_rating": 4}
    rating = RecipeRating.objects.get(recipe=recipe)
    assert rating.user is None
    assert rating.voter_hash


@pytest.mark.django_db
def test_anonymous_vote_never_collects_a_name():
    recipe = RecipeFactory()
    client = APIClient()

    response = client.post(f"/api/recipes/{recipe.id}/rate/", {"value": 3}, format="json")

    assert "author_name" not in response.data
    assert set(response.data.keys()) == {"average_rating", "ratings_count", "my_rating"}


@pytest.mark.django_db
def test_repeat_anonymous_vote_updates_instead_of_adding():
    recipe = RecipeFactory()
    client = APIClient()

    client.post(f"/api/recipes/{recipe.id}/rate/", {"value": 2}, format="json")
    response = client.post(f"/api/recipes/{recipe.id}/rate/", {"value": 5}, format="json")

    assert response.status_code == 200
    assert response.data == {"average_rating": 5.0, "ratings_count": 1, "my_rating": 5}
    assert RecipeRating.objects.filter(recipe=recipe).count() == 1


@pytest.mark.django_db
def test_different_anonymous_voters_are_not_merged(monkeypatch):
    recipe = RecipeFactory()
    client = APIClient()

    hashes = iter(["voter-a", "voter-b"])
    monkeypatch.setattr(
        "apps.recipes.views.voter_hash_for_request", lambda request: next(hashes)
    )

    client.post(f"/api/recipes/{recipe.id}/rate/", {"value": 1}, format="json")
    response = client.post(f"/api/recipes/{recipe.id}/rate/", {"value": 5}, format="json")

    assert RecipeRating.objects.filter(recipe=recipe).count() == 2
    assert response.data["ratings_count"] == 2
    assert response.data["average_rating"] == 3.0


@pytest.mark.django_db
def test_authenticated_user_rating_is_stamped_and_updatable():
    user = UserFactory()
    recipe = RecipeFactory()
    client = APIClient()
    client.force_authenticate(user)

    client.post(f"/api/recipes/{recipe.id}/rate/", {"value": 3}, format="json")
    response = client.post(f"/api/recipes/{recipe.id}/rate/", {"value": 1}, format="json")

    assert response.status_code == 200
    rating = RecipeRating.objects.get(recipe=recipe, user=user)
    assert rating.value == 1
    assert rating.voter_hash == ""
    assert RecipeRating.objects.filter(recipe=recipe).count() == 1


@pytest.mark.parametrize("value", [0, 6, -1])
@pytest.mark.django_db
def test_out_of_range_value_is_rejected(value):
    recipe = RecipeFactory()
    client = APIClient()

    response = client.post(f"/api/recipes/{recipe.id}/rate/", {"value": value}, format="json")

    assert response.status_code == 400
    assert "value" in response.data


@pytest.mark.django_db
def test_rating_creation_is_throttled(monkeypatch):
    monkeypatch.setattr(RatingCreateAnonThrottle, "THROTTLE_RATES", {"rating_create": "2/hour"})

    recipe = RecipeFactory()
    client = APIClient()

    for _ in range(2):
        response = client.post(f"/api/recipes/{recipe.id}/rate/", {"value": 5}, format="json")
        assert response.status_code == 200

    response = client.post(f"/api/recipes/{recipe.id}/rate/", {"value": 5}, format="json")
    assert response.status_code == 429


@pytest.mark.django_db
def test_recipe_serializer_exposes_aggregate_and_my_rating(rf, monkeypatch):
    recipe = RecipeFactory()
    RecipeRatingFactory(recipe=recipe, value=4)
    mine = RecipeRatingFactory(recipe=recipe, value=2)
    monkeypatch.setattr("apps.recipes.serializers.voter_hash_for_request", lambda req: mine.voter_hash)

    from apps.recipes.serializers import RecipeSerializer

    class _AnonUser:
        is_authenticated = False

    request = rf.get(f"/api/recipes/{recipe.id}/")
    request.user = _AnonUser()
    data = RecipeSerializer(recipe, context={"request": request}).data

    assert data["ratings_count"] == 2
    assert data["average_rating"] == 3.0
    assert data["my_rating"] == 2


@pytest.mark.django_db
def test_recipe_without_ratings_has_null_average():
    recipe = RecipeFactory()

    from apps.recipes.serializers import RecipeSerializer

    data = RecipeSerializer(recipe, context={"request": None}).data

    assert data["average_rating"] is None
    assert data["ratings_count"] == 0
    assert data["my_rating"] is None
