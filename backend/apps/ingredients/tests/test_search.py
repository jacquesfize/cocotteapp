import pytest
from rest_framework.test import APIClient

from apps.ingredients.factories import IngredientFactory
from apps.ingredients.search import normalize


def search(term):
    response = APIClient().get("/api/ingredients/", {"search": term})
    assert response.status_code == 200
    data = response.data["results"] if isinstance(response.data, dict) else response.data
    return [i["name"] for i in data]


def test_normalize():
    assert normalize("  Œuf Élevé ") == "oeuf eleve"
    assert normalize("Æther") == "aether"


@pytest.mark.django_db
def test_oeuf_matches_ligature_and_reverse():
    IngredientFactory(name="œuf")
    IngredientFactory(name="carotte")
    assert search("oeuf") == ["œuf"]
    assert search("ŒUF") == ["œuf"]
    IngredientFactory(name="boeuf haché")
    assert "boeuf haché" in search("bœuf")


@pytest.mark.django_db
def test_reverse_ligature_stored_as_oe():
    IngredientFactory(name="oeuf dur")
    assert search("œuf") == ["oeuf dur"]


@pytest.mark.django_db
def test_accent_and_case_insensitive():
    IngredientFactory(name="Crème fraîche")
    assert search("creme fraiche") == ["Crème fraîche"]
    assert search("CRÈME") == ["Crème fraîche"]


@pytest.mark.django_db
def test_typo_tolerance():
    IngredientFactory(name="tomate")
    IngredientFactory(name="carotte")
    assert search("tomatte") == ["tomate"]
    assert search("carote") == ["carotte"]
    assert search("zzzzzz") == []


@pytest.mark.django_db
def test_translated_name_search():
    IngredientFactory(name="ail", translations={"en": "Garlic"})
    assert search("garlic") == ["ail"]
    assert search("garlik") == ["ail"]


@pytest.mark.django_db
def test_relevance_order_exact_prefix_contains_similar():
    IngredientFactory(name="pomme de terre")  # préfixe
    IngredientFactory(name="grosse pomme")  # contient
    IngredientFactory(name="pomme")  # exact
    IngredientFactory(name="pomne")  # similaire seulement
    assert search("pomme") == ["pomme", "pomme de terre", "grosse pomme", "pomne"]


@pytest.mark.django_db
def test_no_search_returns_all_by_name():
    IngredientFactory(name="b")
    IngredientFactory(name="a")
    assert search("") == ["a", "b"]
