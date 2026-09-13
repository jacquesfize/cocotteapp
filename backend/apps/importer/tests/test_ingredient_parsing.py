from decimal import Decimal

import pytest

from apps.ingredients.models import Unit
from apps.importer.ingredient_parsing import parse_ingredient_line


@pytest.mark.parametrize(
    "raw_line, quantity, unit, name",
    [
        ("200 g de pois chiches", Decimal("200"), Unit.GRAM, "pois chiches"),
        ("500 g de fèves sèches", Decimal("500"), Unit.GRAM, "fèves sèches"),
        ("1 oignon moyen", Decimal("1"), Unit.PIECE, "oignon moyen"),
        ("2 gousses d'ail", Decimal("2"), Unit.PIECE, "ail"),
        ("1 bouquet de persil", Decimal("1"), Unit.PIECE, "persil"),
        ("3 cuillères à soupe de farine", Decimal("3"), Unit.TABLESPOON, "farine"),
        ("1 cuillère à café de cumin en poudre", Decimal("1"), Unit.TEASPOON, "cumin en poudre"),
        ("sel", Decimal("1"), Unit.PIECE, "sel"),
        ("huile de friture", Decimal("1"), Unit.PIECE, "huile de friture"),
        # anglais
        ("2 cloves garlic", Decimal("2"), Unit.PIECE, "garlic"),
        ("2 cloves of garlic", Decimal("2"), Unit.PIECE, "garlic"),
        ("1 tbsp flour", Decimal("1"), Unit.TABLESPOON, "flour"),
        ("200 g flour", Decimal("200"), Unit.GRAM, "flour"),
        ("1 pinch salt", Decimal("1"), Unit.PINCH, "salt"),
        # allemand
        ("200 g Mehl", Decimal("200"), Unit.GRAM, "mehl"),
        ("2 Zehen Knoblauch", Decimal("2"), Unit.PIECE, "knoblauch"),
        ("1 Prise Salz", Decimal("1"), Unit.PINCH, "salz"),
        ("1 EL Olivenöl", Decimal("1"), Unit.TABLESPOON, "olivenöl"),
        # espagnol
        ("2 dientes de ajo", Decimal("2"), Unit.PIECE, "ajo"),
        ("1 cucharadita de comino", Decimal("1"), Unit.TEASPOON, "comino"),
        ("200 g de harina", Decimal("200"), Unit.GRAM, "harina"),
    ],
)
def test_parse_ingredient_line(raw_line, quantity, unit, name):
    parsed = parse_ingredient_line(raw_line)
    assert parsed.quantity == quantity
    assert parsed.unit == unit
    assert parsed.name == name


def test_parse_ingredient_line_handles_decimal_comma():
    parsed = parse_ingredient_line("1,5 l de bouillon")
    assert parsed.quantity == Decimal("1.5")
    assert parsed.unit == Unit.LITER
    assert parsed.name == "bouillon"


def test_parse_ingredient_line_handles_fraction():
    parsed = parse_ingredient_line("1/2 kg de carottes")
    assert parsed.quantity == Decimal("0.5")
    assert parsed.unit == Unit.KILOGRAM
    assert parsed.name == "carottes"
