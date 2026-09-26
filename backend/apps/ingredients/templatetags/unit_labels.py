import math
from decimal import Decimal, InvalidOperation

from django import template

from apps.ingredients.models import Unit

register = template.Library()

# Libellés français courts pour les documents rendus côté serveur (PDF, export texte).
# Les valeurs stockées en base (g, tbsp, pinch...) ne changent pas.
UNIT_LABELS_FR = {
    Unit.GRAM: "g",
    Unit.KILOGRAM: "kg",
    Unit.MILLILITER: "ml",
    Unit.LITER: "l",
    Unit.PIECE: "pièce",
    Unit.TABLESPOON: "c. à soupe",
    Unit.TEASPOON: "c. à café",
    Unit.PINCH: "pincée",
}


def unit_label(value):
    try:
        return UNIT_LABELS_FR[Unit(value)]
    except ValueError:
        return value


register.filter("unit_label", unit_label)

# Unités qui ne se comptent qu'en entier (pas de "1.5 pièce" ni de "0.5 pincée").
INTEGER_UNITS = {Unit.PIECE, Unit.PINCH}


def format_quantity(quantity, unit=None):
    """Quantité lisible : entier (arrondi au supérieur) pour les unités entières, sinon au plus
    2 décimales sans zéros inutiles ("2.00" -> "2", "1.50" -> "1.5")."""
    try:
        value = Decimal(str(quantity))
    except (InvalidOperation, TypeError, ValueError):
        return quantity
    if unit in INTEGER_UNITS:
        return str(math.ceil(value))
    # quantize() garantit un point décimal : on peut retirer les zéros de fin sans risque.
    return f"{value.quantize(Decimal('0.01')):f}".rstrip("0").rstrip(".")


register.filter("quantity", format_quantity)
