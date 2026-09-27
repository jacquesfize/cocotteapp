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


# Formes plurielles, uniquement pour les unités qui s'accordent (les abréviations restent invariables).
UNIT_PLURAL_LABELS_FR = {
    Unit.PIECE: "pièces",
    Unit.PINCH: "pincées",
}


def unit_label(value, quantity=None):
    """Libellé français de l'unité, accordé au pluriel si la quantité affichée est >= 2
    (règle française : "1,5 pincée" reste au singulier)."""
    try:
        unit = Unit(value)
    except ValueError:
        return value
    if quantity is not None and unit in UNIT_PLURAL_LABELS_FR:
        try:
            if Decimal(format_quantity(quantity, unit)) >= 2:
                return UNIT_PLURAL_LABELS_FR[unit]
        except InvalidOperation:
            pass
    return UNIT_LABELS_FR[unit]


register.filter("unit_label", unit_label)

# Unités qui ne se comptent qu'en entier. PIECE a été retiré : une recette peut désormais
# préciser une quantité fractionnaire en pièce (ex. "0.5 pièce" pour un demi-camembert) ;
# seule PINCH reste arrondie à l'affichage.
INTEGER_UNITS = {Unit.PINCH}


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
