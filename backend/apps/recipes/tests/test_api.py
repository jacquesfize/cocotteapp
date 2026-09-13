import pytest
from rest_framework.test import APIClient

from apps.accounts.factories import UserFactory
from apps.ingredients.factories import IngredientFactory
from apps.recipes.factories import RecipeFactory, RecipeIngredientFactory
from apps.recipes.models import RecipeStep, SourceType, Tag


@pytest.mark.django_db
def test_create_recipe_with_nested_ingredients():
    user = UserFactory()
    ingredient = IngredientFactory()
    client = APIClient()
    client.force_authenticate(user)

    payload = {
        "title": "Curry de lentilles",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "diet_type": "vegan",
        "ingredients": [
            {"ingredient_id": ingredient.id, "quantity": "200", "unit": "g", "order": 1}
        ],
        "steps": [{"order": 1, "instruction": "Faire revenir les oignons."}],
    }
    response = client.post("/api/recipes/", payload, format="json")

    assert response.status_code == 201
    assert response.data["ingredients"][0]["ingredient"]["id"] == ingredient.id
    assert response.data["steps"][0]["instruction"] == "Faire revenir les oignons."


@pytest.mark.django_db
def test_create_recipe_rejects_non_integer_quantity_for_piece_unit():
    user = UserFactory()
    ingredient = IngredientFactory()
    client = APIClient()
    client.force_authenticate(user)

    payload = {
        "title": "Curry de lentilles",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "diet_type": "vegan",
        "ingredients": [
            {"ingredient_id": ingredient.id, "quantity": "1.5", "unit": "piece", "order": 1}
        ],
        "steps": [{"order": 1, "instruction": "Faire revenir les oignons."}],
    }
    response = client.post("/api/recipes/", payload, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_create_recipe_accepts_integer_quantity_for_piece_unit():
    user = UserFactory()
    ingredient = IngredientFactory()
    client = APIClient()
    client.force_authenticate(user)

    payload = {
        "title": "Curry de lentilles",
        "servings": 4,
        "prep_time_minutes": 15,
        "cook_time_minutes": 30,
        "diet_type": "vegan",
        "ingredients": [
            {"ingredient_id": ingredient.id, "quantity": "2", "unit": "piece", "order": 1}
        ],
        "steps": [{"order": 1, "instruction": "Faire revenir les oignons."}],
    }
    response = client.post("/api/recipes/", payload, format="json")

    assert response.status_code == 201


@pytest.mark.django_db
def test_filter_recipes_by_diet_type():
    RecipeFactory(diet_type="vegan")
    RecipeFactory(diet_type="omnivore")

    client = APIClient()
    response = client.get("/api/recipes/?diet_type=vegan")
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_filter_recipes_by_max_time():
    RecipeFactory(prep_time_minutes=10, cook_time_minutes=10)
    RecipeFactory(prep_time_minutes=30, cook_time_minutes=30)

    client = APIClient()
    response = client.get("/api/recipes/?max_prep_time=15&max_cook_time=15")
    assert response.data["count"] == 1


@pytest.mark.django_db
def test_recipe_list_is_paginated():
    RecipeFactory.create_batch(25)
    client = APIClient()

    first_page = client.get("/api/recipes/")
    assert first_page.data["count"] == 25
    assert len(first_page.data["results"]) == 20
    assert first_page.data["next"] is not None
    assert first_page.data["previous"] is None

    second_page = client.get("/api/recipes/?page=2")
    assert len(second_page.data["results"]) == 5
    assert second_page.data["next"] is None
    assert second_page.data["previous"] is not None


@pytest.mark.django_db
def test_anonymous_cannot_create_recipe():
    client = APIClient()
    response = client.post("/api/recipes/", {"title": "Test"}, format="json")
    assert response.status_code == 401


@pytest.mark.django_db
def test_random_recipe_returns_one_of_the_existing_recipes():
    recipes = RecipeFactory.create_batch(5)
    ids = {r.id for r in recipes}

    client = APIClient()
    response = client.get("/api/recipes/random/")

    assert response.status_code == 200
    assert response.data["id"] in ids


@pytest.mark.django_db
def test_random_recipe_respects_filters():
    RecipeFactory(diet_type="vegan")
    RecipeFactory(diet_type="omnivore")

    client = APIClient()
    response = client.get("/api/recipes/random/?diet_type=vegan")

    assert response.status_code == 200
    assert response.data["diet_type"] == "vegan"


@pytest.mark.django_db
def test_random_recipe_404_when_no_match():
    RecipeFactory(diet_type="omnivore")

    client = APIClient()
    response = client.get("/api/recipes/random/?diet_type=vegan")

    assert response.status_code == 404


@pytest.mark.django_db
def test_recipe_nutrition_action_returns_per_serving_values():
    from decimal import Decimal

    from apps.recipes.factories import RecipeIngredientFactory

    ingredient = IngredientFactory(protein_g=Decimal("10"), calories_kcal=Decimal("100"))
    recipe = RecipeFactory(servings=2)
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("200"), unit="g")

    client = APIClient()
    response = client.get(f"/api/recipes/{recipe.id}/nutrition/")

    assert response.status_code == 200
    assert response.data["totals"]["protein_g"] == 20.0
    assert response.data["per_serving"]["protein_g"] == 10.0


@pytest.mark.django_db
def test_recipe_nutrition_action_returns_carbon_footprint():
    from decimal import Decimal

    from apps.recipes.factories import RecipeIngredientFactory

    ingredient = IngredientFactory(carbon_kg_co2e_per_kg=Decimal("10"))
    recipe = RecipeFactory(servings=2)
    RecipeIngredientFactory(recipe=recipe, ingredient=ingredient, quantity=Decimal("1000"), unit="g")

    client = APIClient()
    response = client.get(f"/api/recipes/{recipe.id}/nutrition/")

    assert response.status_code == 200
    assert response.data["carbon_footprint_kg_co2e"] == 10.0
    assert response.data["carbon_footprint_per_serving_kg_co2e"] == 5.0


@pytest.mark.django_db
def test_fork_recipe_creates_linked_version_with_copied_content():
    original_author = UserFactory()
    forker = UserFactory()
    tag = Tag.objects.create(name="Végétarien")
    ingredient = IngredientFactory()
    source = RecipeFactory(
        title="Curry de légumes",
        author=original_author,
        description="Un bon curry",
        servings=4,
        prep_time_minutes=10,
        cook_time_minutes=20,
        diet_type="vegan",
        image_url="https://example.com/photo.jpg",
        source_url="https://example.com/recette",
    )
    source.tags.add(tag)
    RecipeIngredientFactory(recipe=source, ingredient=ingredient, quantity="150", unit="g", order=1)
    RecipeStep.objects.create(recipe=source, order=1, instruction="Couper les légumes.")

    client = APIClient()
    client.force_authenticate(forker)
    response = client.post(f"/api/recipes/{source.id}/fork/", {"version_label": "Sans gluten"}, format="json")

    assert response.status_code == 201
    fork_id = response.data["id"]
    assert fork_id != source.id
    assert response.data["version_label"] == "Sans gluten"
    assert response.data["author"] == forker.username
    assert response.data["root_recipe"] == source.id
    assert "Sans gluten" in response.data["title"]
    assert response.data["image_url"] == ""
    assert response.data["source_url"] == ""

    fork = source.__class__.objects.get(pk=fork_id)
    assert fork.root_recipe_id == source.id
    assert fork.diet_type == "vegan"
    assert list(fork.tags.values_list("id", flat=True)) == [tag.id]
    assert fork.recipe_ingredients.count() == 1
    fork_ingredient = fork.recipe_ingredients.first()
    assert fork_ingredient.ingredient_id == ingredient.id
    assert str(fork_ingredient.quantity) == "150.00"
    assert fork_ingredient.unit == "g"
    assert fork.steps.count() == 1
    assert fork.steps.first().instruction == "Couper les légumes."
    assert fork.source_type == SourceType.MANUAL
    assert fork.is_public is True


@pytest.mark.django_db
def test_forking_a_fork_points_to_the_same_root():
    root_author = UserFactory()
    root = RecipeFactory(author=root_author, title="Recette originale")

    first_forker = UserFactory()
    client = APIClient()
    client.force_authenticate(first_forker)
    first_fork_response = client.post(
        f"/api/recipes/{root.id}/fork/", {"version_label": "Version épicée"}, format="json"
    )
    assert first_fork_response.status_code == 201
    first_fork_id = first_fork_response.data["id"]

    second_forker = UserFactory()
    client.force_authenticate(second_forker)
    second_fork_response = client.post(
        f"/api/recipes/{first_fork_id}/fork/", {"version_label": "Sans gluten"}, format="json"
    )

    assert second_fork_response.status_code == 201
    assert second_fork_response.data["root_recipe"] == root.id


@pytest.mark.django_db
def test_fork_requires_a_version_label():
    source = RecipeFactory()
    user = UserFactory()
    client = APIClient()
    client.force_authenticate(user)

    response = client.post(f"/api/recipes/{source.id}/fork/", {"version_label": ""}, format="json")

    assert response.status_code == 400


@pytest.mark.django_db
def test_anonymous_cannot_fork_recipe():
    source = RecipeFactory()
    client = APIClient()

    response = client.post(f"/api/recipes/{source.id}/fork/", {"version_label": "Ma variante"}, format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_any_authenticated_user_can_fork_someone_elses_recipe():
    """Forking is not limited to the recipe's own author -- that is the point of versioning."""
    source = RecipeFactory(author=UserFactory())
    other_user = UserFactory()
    client = APIClient()
    client.force_authenticate(other_user)

    response = client.post(f"/api/recipes/{source.id}/fork/", {"version_label": "Ma variante"}, format="json")

    assert response.status_code == 201


@pytest.mark.django_db
def test_recipe_detail_lists_sibling_versions():
    root = RecipeFactory(title="Recette originale")
    forker = UserFactory()
    client = APIClient()
    client.force_authenticate(forker)
    fork_response = client.post(f"/api/recipes/{root.id}/fork/", {"version_label": "Sans gluten"}, format="json")
    fork_id = fork_response.data["id"]

    root_detail = client.get(f"/api/recipes/{root.id}/")
    assert root_detail.status_code == 200
    root_versions = root_detail.data["versions"]
    assert len(root_versions) == 1
    assert root_versions[0]["id"] == fork_id
    assert root_versions[0]["version_label"] == "Sans gluten"
    assert root_versions[0]["author"] == forker.username

    fork_detail = client.get(f"/api/recipes/{fork_id}/")
    assert fork_detail.status_code == 200
    fork_versions = fork_detail.data["versions"]
    assert len(fork_versions) == 1
    assert fork_versions[0]["id"] == root.id
    assert fork_versions[0]["version_label"] == ""


@pytest.mark.django_db
def test_recipe_detail_has_no_versions_when_not_forked():
    recipe = RecipeFactory()
    client = APIClient()

    response = client.get(f"/api/recipes/{recipe.id}/")

    assert response.status_code == 200
    assert response.data["versions"] == []
