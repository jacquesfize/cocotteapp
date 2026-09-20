"""Turns a parsed Cooklang recipe (see `cooklang.py`) into `Recipe` +
`RecipeIngredient` + `RecipeStep` rows.

This is the only place that bridges the free-text Cooklang world (arbitrary
ingredient names, arbitrary unit abbreviations) and the app's normalized data
model (a closed `Ingredient` table, a closed `Unit` enum). Everything here is
therefore best-effort: unknown units fall back to a sane default and bad
quantities default to 1 rather than raising, so a recipe always gets created
even if it then needs manual clean-up in the edit view.
"""
from decimal import Decimal, InvalidOperation

from django.db import transaction

from apps.ingredients.models import Ingredient, Unit

from .cooklang import ParsedRecipe, parse
from .models import Recipe, RecipeIngredient, RecipeStep, SourceType

# Free-text unit abbreviations (as found in real Cooklang recipes, French and
# English) mapped to the app's closed `Unit` enum. This is a judgment call,
# not a lossless mapping: Cooklang units aren't validated against any enum,
# so several abbreviations must collapse onto the same `Unit` member (e.g.
# "cs"/"c.à.s"/"tbsp" all mean tablespoon), and anything not listed here -
# including no unit at all - falls back to PIECE, the least surprising
# default for a "1 egg" / "2 onions" style ingredient.
UNIT_ALIASES = {
    "g": Unit.GRAM,
    "gr": Unit.GRAM,
    "gramme": Unit.GRAM,
    "grammes": Unit.GRAM,
    "kg": Unit.KILOGRAM,
    "kilogramme": Unit.KILOGRAM,
    "kilogrammes": Unit.KILOGRAM,
    "ml": Unit.MILLILITER,
    "millilitre": Unit.MILLILITER,
    "millilitres": Unit.MILLILITER,
    "l": Unit.LITER,
    "litre": Unit.LITER,
    "litres": Unit.LITER,
    "cs": Unit.TABLESPOON,
    "c.à.s": Unit.TABLESPOON,
    "c.a.s": Unit.TABLESPOON,
    "càs": Unit.TABLESPOON,
    "cas": Unit.TABLESPOON,
    "tbsp": Unit.TABLESPOON,
    "tbs": Unit.TABLESPOON,
    "cuillère à soupe": Unit.TABLESPOON,
    "cuillères à soupe": Unit.TABLESPOON,
    "cc": Unit.TEASPOON,
    "c.à.c": Unit.TEASPOON,
    "c.a.c": Unit.TEASPOON,
    "càc": Unit.TEASPOON,
    "cac": Unit.TEASPOON,
    "tsp": Unit.TEASPOON,
    "cuillère à café": Unit.TEASPOON,
    "cuillères à café": Unit.TEASPOON,
    "pincée": Unit.PINCH,
    "pincees": Unit.PINCH,
    "pincées": Unit.PINCH,
    "pinch": Unit.PINCH,
    "piece": Unit.PIECE,
    "pièce": Unit.PIECE,
    "pièces": Unit.PIECE,
    "pieces": Unit.PIECE,
}


def map_unit(raw_unit: str | None) -> str:
    """Best-effort mapping from a free-text Cooklang unit to `Unit`.

    Missing or unrecognized units fall back to `Unit.PIECE` (see the module
    docstring/table above for the reasoning).
    """
    if not raw_unit:
        return Unit.PIECE
    return UNIT_ALIASES.get(raw_unit.strip().lower(), Unit.PIECE)


def parse_quantity(raw_quantity: str | None) -> Decimal:
    """Best-effort parsing of a free-text Cooklang quantity into a Decimal.

    Falls back to 1 when missing, non-numeric (e.g. "quelques"), or a
    fraction/range Cooklang doesn't itself normalize (e.g. "1/2", "2-3") -
    never raises, so a single odd ingredient never blocks the whole import.
    """
    if not raw_quantity:
        return Decimal("1")
    text = raw_quantity.strip().replace(",", ".")
    try:
        return Decimal(text)
    except InvalidOperation:
        return Decimal("1")


def get_or_create_ingredient(name: str) -> Ingredient:
    """Find-or-create an `Ingredient` by case-insensitive name match.

    Mirrors the merge logic in `seed_common_ingredients`: an ingredient
    referenced as "@tomate" should reuse an existing "Tomate" row rather than
    creating a duplicate that would collide on slug anyway.
    """
    existing = Ingredient.objects.filter(name__iexact=name).first()
    if existing:
        return existing
    return Ingredient.objects.create(name=name)


@transaction.atomic
def create_recipe_from_cooklang(*, author, title, raw_cooklang, servings=None, prep_time_minutes=None,
                                 cook_time_minutes=None, diet_type=None) -> Recipe:
    """Parse `raw_cooklang` and persist the resulting Recipe + children.

    `raw_cooklang` is kept verbatim on the created recipe (so it can be
    displayed/re-parsed later) even though the parsed ingredients/steps are
    what's actually rendered.
    """
    parsed: ParsedRecipe = parse(raw_cooklang)

    recipe_kwargs = {
        "author": author,
        "title": title,
        "source_type": SourceType.COOKLANG,
        "raw_cooklang": raw_cooklang,
    }
    if servings is not None:
        recipe_kwargs["servings"] = servings
    if prep_time_minutes is not None:
        recipe_kwargs["prep_time_minutes"] = prep_time_minutes
    if cook_time_minutes is not None:
        recipe_kwargs["cook_time_minutes"] = cook_time_minutes
    if diet_type is not None:
        recipe_kwargs["diet_type"] = diet_type

    recipe = Recipe.objects.create(**recipe_kwargs)

    # Une mention sans quantité d'un ingrédient déjà déclaré (ex. "@oignon" à l'étape 3 après
    # "@oignon{1}" à l'étape 1) ne fait que référencer la ligne existante : pas de doublon.
    seen_names = set()
    order = 0
    for parsed_ingredient in parsed.ingredients:
        key = parsed_ingredient.name.strip().lower()
        if key in seen_names and not parsed_ingredient.quantity:
            continue
        seen_names.add(key)
        order += 1
        ingredient = get_or_create_ingredient(parsed_ingredient.name)
        RecipeIngredient.objects.create(
            recipe=recipe,
            ingredient=ingredient,
            quantity=parse_quantity(parsed_ingredient.quantity),
            unit=map_unit(parsed_ingredient.unit),
            order=order,
        )

    order = 0
    for step_text in parsed.tagged_steps:
        if not step_text.strip():
            continue
        order += 1
        RecipeStep.objects.create(recipe=recipe, order=order, instruction=step_text.strip())

    return recipe
