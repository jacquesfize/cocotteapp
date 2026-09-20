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
