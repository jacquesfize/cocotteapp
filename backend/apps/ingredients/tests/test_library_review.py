"""Ingrédients créés par les utilisateurs : non vérifiés, modifiables par leur créateur tant que
personne d'autre ne les utilise, file de relecture et fusion côté staff."""

from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.ingredients.factories import IngredientFactory
from apps.ingredients.models import Allergen, Ingredient
from apps.recipes.factories import RecipeFactory, RecipeIngredientFactory
from apps.shopping.models import ShoppingList, ShoppingListItem

pytestmark = pytest.mark.django_db


def _client(user=None):
    client = APIClient()
    if user is not None:
        client.force_authenticate(user)
    return client


def _url(ingredient, suffix=""):
    return f"/api/ingredients/{ingredient.id}/{suffix}"


def _list_item(user, ingredient, quantity="100", unit="g", **kwargs):
    shopping_list = ShoppingList.objects.filter(user=user).first() or ShoppingList.objects.create(user=user)
    return ShoppingListItem.objects.create(
        shopping_list=shopping_list, ingredient=ingredient, quantity=Decimal(quantity), unit=unit, **kwargs
    )


# --- Création -----------------------------------------------------------------------------------


def test_user_created_ingredient_is_unverified_and_attributed():
    user = UserFactory(username="alice")
    response = _client(user).post(
        "/api/ingredients/", {"name": "Poireau", "is_verified": True}, format="json"
    )
    assert response.status_code == 201
    assert response.data["is_verified"] is False
    assert response.data["created_by"] == user.id
    assert response.data["created_by_username"] == "alice"
    assert response.data["can_edit"] is True
    ingredient = Ingredient.objects.get(name="Poireau")
    assert (ingredient.is_verified, ingredient.created_by) == (False, user)


def test_staff_created_ingredient_is_verified_unless_explicitly_not():
    staff = UserFactory(is_staff=True)
    client = _client(staff)
    response = client.post("/api/ingredients/", {"name": "Poireau"}, format="json")
    assert (response.data["is_verified"], response.data["created_by"]) == (True, staff.id)

    response = client.post("/api/ingredients/", {"name": "Navet", "is_verified": False}, format="json")
    assert response.data["is_verified"] is False


# --- Droits du créateur ------------------------------------------------------------------------


def test_creator_can_edit_and_delete_own_unverified_ingredient():
    user = UserFactory()
    ingredient = IngredientFactory(created_by=user, is_verified=False)
    client = _client(user)

    response = client.patch(_url(ingredient), {"name": "Poireau"}, format="json")
    assert response.status_code == 200
    assert response.data["name"] == "Poireau"
    assert client.delete(_url(ingredient)).status_code == 204


def test_creator_can_still_edit_when_only_used_by_own_data_but_delete_is_protected():
    user = UserFactory()
    ingredient = IngredientFactory(created_by=user, is_verified=False)
    RecipeIngredientFactory(recipe=RecipeFactory(author=user), ingredient=ingredient)
    _list_item(user, ingredient)
    client = _client(user)

    assert client.get(_url(ingredient)).data["can_edit"] is True
    assert client.patch(_url(ingredient), {"name": "Poireau"}, format="json").status_code == 200
    response = client.delete(_url(ingredient))
    assert response.status_code == 409
    assert "detail" in response.data


def test_creator_cannot_set_is_verified():
    user = UserFactory()
    ingredient = IngredientFactory(created_by=user, is_verified=False)
    response = _client(user).patch(_url(ingredient), {"is_verified": True}, format="json")
    assert response.status_code == 200
    ingredient.refresh_from_db()
    assert ingredient.is_verified is False


def test_creator_locked_out_once_verified():
    user = UserFactory()
    ingredient = IngredientFactory(created_by=user, is_verified=True)
    client = _client(user)
    assert client.get(_url(ingredient)).data["can_edit"] is False
    assert client.patch(_url(ingredient), {"name": "x"}, format="json").status_code == 403
    assert client.delete(_url(ingredient)).status_code == 403


def test_creator_locked_out_once_another_users_recipe_uses_it():
    user = UserFactory()
    ingredient = IngredientFactory(created_by=user, is_verified=False)
    RecipeIngredientFactory(recipe=RecipeFactory(), ingredient=ingredient)
    client = _client(user)
    assert client.get(_url(ingredient)).data["can_edit"] is False
    assert client.patch(_url(ingredient), {"name": "x"}, format="json").status_code == 403
    assert client.delete(_url(ingredient)).status_code == 403


def test_creator_locked_out_once_on_another_users_shopping_list():
    user = UserFactory()
    ingredient = IngredientFactory(created_by=user, is_verified=False)
    _list_item(UserFactory(), ingredient)
    client = _client(user)
    assert client.get(_url(ingredient)).data["can_edit"] is False
    assert client.patch(_url(ingredient), {"name": "x"}, format="json").status_code == 403


def test_other_users_and_anonymous_cannot_edit():
    ingredient = IngredientFactory(created_by=UserFactory(), is_verified=False)
    other = _client(UserFactory())
    assert other.get(_url(ingredient)).data["can_edit"] is False
    assert other.patch(_url(ingredient), {"name": "x"}, format="json").status_code == 403
    assert other.delete(_url(ingredient)).status_code == 403
    assert _client().get(_url(ingredient)).data["can_edit"] is False
    assert _client().patch(_url(ingredient), {"name": "x"}, format="json").status_code == 401


def test_staff_can_always_edit_and_verify():
    ingredient = IngredientFactory(created_by=UserFactory(), is_verified=False)
    RecipeIngredientFactory(ingredient=ingredient)
    client = _client(UserFactory(is_staff=True))
    assert client.get(_url(ingredient)).data["can_edit"] is True
    response = client.patch(_url(ingredient), {"is_verified": True}, format="json")
    assert response.status_code == 200
    assert response.data["is_verified"] is True


def test_can_edit_in_list_matches_rule_without_query_per_row(django_assert_max_num_queries):
    user = UserFactory()
    mine = IngredientFactory(name="a-mine", created_by=user, is_verified=False)
    used = IngredientFactory(name="b-used", created_by=user, is_verified=False)
    RecipeIngredientFactory(ingredient=used)
    verified = IngredientFactory(name="c-verified", created_by=user)
    IngredientFactory.create_batch(5, created_by=user, is_verified=False)
    client = _client(user)

    with django_assert_max_num_queries(4):
        results = client.get("/api/ingredients/").data["results"]
    can_edit = {item["name"]: item["can_edit"] for item in results}
    assert can_edit[mine.name] is True
    assert can_edit[used.name] is False
    assert can_edit[verified.name] is False


# --- File de relecture -------------------------------------------------------------------------


def test_filter_by_is_verified():
    IngredientFactory(name="vérifié")
    IngredientFactory(name="à relire", is_verified=False)
    client = _client()
    assert [i["name"] for i in client.get("/api/ingredients/?is_verified=false").data["results"]] == [
        "à relire"
    ]
    assert [i["name"] for i in client.get("/api/ingredients/?is_verified=true").data["results"]] == [
        "vérifié"
    ]


# --- Fusion ------------------------------------------------------------------------------------


def test_merge_repoints_recipes_and_shopping_lists_and_merges_metadata():
    gluten, milk, egg = (Allergen.objects.create(slug=s, name=s) for s in ("gluten", "lait", "oeuf"))
    target = IngredientFactory(name="poireau", translations={"en": "leek", "de": "Lauch"})
    target.allergens.add(gluten)
    source = IngredientFactory(
        name="poirreau", is_verified=False, translations={"en": "leeks", "es": "puerro"}
    )
    source.allergens.add(milk, egg)
    line = RecipeIngredientFactory(ingredient=source)

    alice, bob = UserFactory(), UserFactory()
    # Même liste, même unité : quantités additionnées dans l'article existant.
    kept = _list_item(alice, target, "200", is_owned=True, is_checked=True)
    collided = _list_item(alice, source, "50", is_owned=False, is_checked=True)
    # Même liste, autre unité : simple repointage.
    other_unit = _list_item(alice, source, "2", unit="piece")
    # Autre liste sans la cible : simple repointage.
    moved = _list_item(bob, source, "30", is_owned=True)

    response = _client(UserFactory(is_staff=True)).post(
        _url(source, "merge/"), {"into": target.id}, format="json"
    )
    assert response.status_code == 200
    assert response.data["id"] == target.id
    assert response.data["translations"] == {"en": "leek", "de": "Lauch", "es": "puerro"}
    assert sorted(response.data["allergens"]) == ["gluten", "lait", "oeuf"]

    assert not Ingredient.objects.filter(pk=source.pk).exists()
    line.refresh_from_db()
    assert line.ingredient == target

    kept.refresh_from_db()
    assert (kept.quantity, kept.is_owned, kept.is_checked) == (Decimal("250"), False, True)
    assert not ShoppingListItem.objects.filter(pk=collided.pk).exists()
    other_unit.refresh_from_db()
    assert (other_unit.ingredient, other_unit.unit) == (target, "piece")
    moved.refresh_from_db()
    assert (moved.ingredient, moved.quantity, moved.is_owned) == (target, Decimal("30"), True)


def test_merge_rejects_missing_unknown_or_same_target():
    source = IngredientFactory()
    client = _client(UserFactory(is_staff=True))
    assert client.post(_url(source, "merge/"), {}, format="json").status_code == 400
    assert client.post(_url(source, "merge/"), {"into": 999999}, format="json").status_code == 400
    assert client.post(_url(source, "merge/"), {"into": source.id}, format="json").status_code == 400
    assert Ingredient.objects.filter(pk=source.pk).exists()


def test_merge_is_staff_only():
    user = UserFactory()
    source = IngredientFactory(created_by=user, is_verified=False)
    target = IngredientFactory()
    response = _client(user).post(_url(source, "merge/"), {"into": target.id}, format="json")
    assert response.status_code == 403
    assert Ingredient.objects.filter(pk=source.pk).exists()
