import pytest
from django.template.loader import render_to_string

from apps.ingredients.models import Unit
from apps.ingredients.templatetags.unit_labels import UNIT_LABELS_FR, unit_label
from apps.recipes.factories import RecipeFactory, RecipeIngredientFactory


def test_unit_label_covers_all_units():
    assert set(UNIT_LABELS_FR) == set(Unit)
    assert unit_label("pinch") == "pincée"
    assert unit_label("tbsp") == "c. à soupe"
    assert unit_label("tsp") == "c. à café"
    assert unit_label("piece") == "pièce"
    assert unit_label("unknown") == "unknown"


@pytest.mark.django_db
def test_recipe_pdf_template_renders_translated_units():
    recipe = RecipeFactory()
    RecipeIngredientFactory(recipe=recipe, unit="pinch")

    html = render_to_string("pdf/recipe.html", {"recipe": recipe})

    assert "pincée" in html
    assert "pinch" not in html
