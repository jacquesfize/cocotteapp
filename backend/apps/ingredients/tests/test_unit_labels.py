from decimal import Decimal

import pytest
from django.template.loader import render_to_string

from apps.ingredients.models import Unit
from apps.ingredients.templatetags.unit_labels import UNIT_LABELS_FR, format_quantity, unit_label
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


@pytest.mark.parametrize(
    ("quantity", "unit", "expected"),
    [
        (Decimal("200.00"), "g", "200"),
        (Decimal("1.50"), "kg", "1.5"),
        (Decimal("0.25"), "l", "0.25"),
        (Decimal("333.333"), "g", "333.33"),
        (Decimal("2.00"), "piece", "2"),
        (Decimal("1.50"), "piece", "1.5"),
        (Decimal("0.50"), "pinch", "1"),
        (Decimal("10"), "g", "10"),
    ],
)
def test_format_quantity(quantity, unit, expected):
    assert format_quantity(quantity, unit) == expected


@pytest.mark.django_db
def test_recipe_pdf_template_strips_useless_decimals():
    recipe = RecipeFactory()
    RecipeIngredientFactory(recipe=recipe, unit="g", quantity=Decimal("200.00"))

    html = render_to_string("pdf/recipe.html", {"recipe": recipe})

    assert "200 g" in html
    assert "200.00" not in html


@pytest.mark.parametrize(
    ("unit", "quantity", "expected"),
    [
        ("piece", Decimal("1"), "pièce"),
        ("piece", Decimal("2"), "pièces"),
        ("piece", Decimal("1.5"), "pièce"),  # affiché "1.5" (fractionnaire, plus arrondi au supérieur)
        ("pinch", Decimal("1"), "pincée"),
        ("pinch", Decimal("3"), "pincées"),
        ("tbsp", Decimal("3"), "c. à soupe"),
        ("g", Decimal("200"), "g"),
        ("piece", None, "pièce"),
    ],
)
def test_unit_label_agrees_with_quantity(unit, quantity, expected):
    assert unit_label(unit, quantity) == expected
