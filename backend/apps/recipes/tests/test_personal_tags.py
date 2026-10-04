import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.recipes.factories import PersonalTagFactory, RecipeFactory
from apps.recipes.personal_tags import similarity


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user)
    return client


# --- /api/personal-tags/ ---------------------------------------------------------------------


@pytest.mark.django_db
def test_requires_authentication():
    assert _client().get("/api/personal-tags/").status_code == 401
    assert _client().post("/api/personal-tags/", {"name": "Été"}, format="json").status_code == 401


@pytest.mark.django_db
def test_list_only_own_tags_unpaginated_sorted_with_recipe_count():
    user = UserFactory()
    birthday = PersonalTagFactory(owner=user, name="anniversaire", emoji="🎂")
    PersonalTagFactory(owner=user, name="Brunch")
    PersonalTagFactory(name="Pas à moi")
    birthday.recipes.add(RecipeFactory(), RecipeFactory())

    response = _client(user).get("/api/personal-tags/")

    assert response.status_code == 200
    assert [(t["name"], t["emoji"], t["recipes_count"]) for t in response.data] == [
        ("anniversaire", "🎂", 2),
        ("Brunch", "", 0),
    ]


@pytest.mark.django_db
def test_create_strips_and_rejects_duplicates_per_owner_only():
    user = UserFactory()
    client = _client(user)

    response = client.post("/api/personal-tags/", {"name": " Apéro ", "emoji": " 🥂 "}, format="json")
    assert response.status_code == 201
    assert (response.data["name"], response.data["emoji"], response.data["recipes_count"]) == ("Apéro", "🥂", 0)
    assert response.data["color"] == "gray"

    assert client.post("/api/personal-tags/", {"name": "apéro"}, format="json").status_code == 400
    assert client.post("/api/personal-tags/", {"name": "  "}, format="json").status_code == 400
    # Un autre utilisateur peut avoir une étiquette du même nom.
    assert _client(UserFactory()).post("/api/personal-tags/", {"name": "Apéro"}, format="json").status_code == 201


@pytest.mark.django_db
def test_owner_can_rename_and_delete_but_not_others_tags():
    user = UserFactory()
    tag = PersonalTagFactory(owner=user, name="Été")
    other_tag = PersonalTagFactory(owner=user, name="Hiver")
    recipe = RecipeFactory()
    tag.recipes.add(recipe)
    client = _client(user)

    response = client.patch(
        f"/api/personal-tags/{tag.id}/", {"name": "Été 🌞", "emoji": "☀️", "color": "yellow"}, format="json"
    )
    assert response.status_code == 200
    assert (response.data["name"], response.data["emoji"], response.data["color"]) == ("Été 🌞", "☀️", "yellow")
    assert client.patch(f"/api/personal-tags/{tag.id}/", {"color": "#ff0000"}, format="json").status_code == 400
    # Renommer en conservant la casse près de son propre nom est permis, pas vers un autre.
    assert client.patch(f"/api/personal-tags/{tag.id}/", {"name": "été 🌞"}, format="json").status_code == 200
    assert client.patch(f"/api/personal-tags/{tag.id}/", {"name": "hiver"}, format="json").status_code == 400

    stranger = _client(UserFactory())
    assert stranger.patch(f"/api/personal-tags/{tag.id}/", {"name": "x"}, format="json").status_code == 404
    assert stranger.delete(f"/api/personal-tags/{tag.id}/").status_code == 404

    assert client.delete(f"/api/personal-tags/{other_tag.id}/").status_code == 204
    assert client.delete(f"/api/personal-tags/{tag.id}/").status_code == 204
    recipe.refresh_from_db()
    assert recipe.personal_tags.count() == 0


@pytest.mark.django_db
def test_similar_suggests_close_names_among_own_tags_only():
    user = UserFactory()
    pates = PersonalTagFactory(owner=user, name="Pâtes")
    fresh = PersonalTagFactory(owner=user, name="Pâtes fraîches")
    PersonalTagFactory(owner=user, name="Desserts")
    PersonalTagFactory(name="pates")
    client = _client(user)

    response = client.get("/api/personal-tags/similar/", {"name": "pates"})
    assert response.status_code == 200
    assert [t["id"] for t in response.data] == [pates.id, fresh.id]

    assert [t["name"] for t in client.get("/api/personal-tags/similar/", {"name": "Desert"}).data] == ["Desserts"]
    assert client.get("/api/personal-tags/similar/", {"name": "Apéro"}).data == []
    assert client.get("/api/personal-tags/similar/", {"name": ""}).data == []

    excluded = client.get("/api/personal-tags/similar/", {"name": "Pâtes", "exclude": pates.id}).data
    assert [t["id"] for t in excluded] == [fresh.id]


def test_similarity_ignores_case_accents_and_short_inclusions():
    assert similarity("Gâteau", "gateau") == 1.0
    assert similarity("Gâteaux", "gateau") >= 0.75
    assert similarity("Pâtes", "Pâtes fraîches") >= 0.75
    assert similarity("Été", "Thé glacé") < 0.75
    assert similarity("", "Été") == 0.0


# --- Étiquettes d'une recette ----------------------------------------------------------------


@pytest.mark.django_db
def test_any_user_sets_own_tags_on_any_recipe_without_touching_others():
    user = UserFactory()
    other = UserFactory()
    recipe = RecipeFactory()
    keep, add = PersonalTagFactory(owner=user, name="Garder"), PersonalTagFactory(owner=user, name="Ajouter")
    drop = PersonalTagFactory(owner=user, name="Retirer")
    others_tag = PersonalTagFactory(owner=other, name="Celle d'un autre")
    recipe.personal_tags.add(keep, drop, others_tag)
    url = f"/api/recipes/{recipe.id}/my-tags/"

    assert _client().put(url, {"tag_ids": []}, format="json").status_code == 401

    response = _client(user).put(url, {"tag_ids": [keep.id, add.id]}, format="json")

    assert response.status_code == 200
    assert response.data == [
        {"id": add.id, "name": "Ajouter", "emoji": "", "color": "gray"},
        {"id": keep.id, "name": "Garder", "emoji": "", "color": "gray"},
    ]
    assert set(recipe.personal_tags.all()) == {keep, add, others_tag}


@pytest.mark.django_db
def test_cannot_put_someone_elses_tag_on_a_recipe():
    user = UserFactory()
    recipe = RecipeFactory()
    others_tag = PersonalTagFactory(name="Celle d'un autre")

    response = _client(user).put(f"/api/recipes/{recipe.id}/my-tags/", {"tag_ids": [others_tag.id]}, format="json")

    assert response.status_code == 400
    assert recipe.personal_tags.count() == 0


@pytest.mark.django_db
def test_recipe_exposes_only_the_requesters_own_tags():
    user = UserFactory()
    recipe = RecipeFactory()
    mine = PersonalTagFactory(owner=user, name="À refaire", emoji="🔁", color="blue")
    recipe.personal_tags.add(mine, PersonalTagFactory(name="Secret"))

    detail = _client(user).get(f"/api/recipes/{recipe.id}/").data
    assert detail["my_tags"] == [{"id": mine.id, "name": "À refaire", "emoji": "🔁", "color": "blue"}]
    listed = _client(user).get("/api/recipes/").data["results"][0]
    assert listed["my_tags"] == detail["my_tags"]
    assert _client().get(f"/api/recipes/{recipe.id}/").data["my_tags"] == []


@pytest.mark.django_db
def test_filter_recipes_by_own_personal_tags():
    user = UserFactory()
    summer, winter = PersonalTagFactory(owner=user, name="Été"), PersonalTagFactory(owner=user, name="Hiver")
    salad, soup, cake = RecipeFactory(title="Salade"), RecipeFactory(title="Soupe"), RecipeFactory(title="Gâteau")
    summer.recipes.add(salad)
    winter.recipes.add(soup, salad)
    others_tag = PersonalTagFactory(name="Autre")
    others_tag.recipes.add(cake)
    client = _client(user)

    def titles(value, c=client):
        return sorted(r["title"] for r in c.get("/api/recipes/", {"personal_tags": value}).data["results"])

    assert titles(str(summer.id)) == ["Salade"]
    assert titles(f"{summer.id},{winter.id}") == ["Salade", "Soupe"]
    assert titles(str(others_tag.id)) == []
    assert titles(str(summer.id), _client()) == []
    random = client.get("/api/recipes/random/", {"personal_tags": str(summer.id)})
    assert random.data["title"] == "Salade"
