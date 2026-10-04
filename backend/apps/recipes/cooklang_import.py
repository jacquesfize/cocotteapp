"""Turns a parsed Cooklang recipe (see `cooklang.py`, built on the `cooklang-py` library) into
`Recipe` + `RecipeIngredient` + `RecipeStep` rows (`create_recipe_from_cooklang`, used by the
YouTube import script), or into a no-write preview that pre-fills the recipe form
(`build_cooklang_preview`, used by the "Paste Cooklang" tab).

This is the only place that bridges the free-text Cooklang world (arbitrary ingredient names,
arbitrary unit abbreviations, free-form metadata) and the app's normalized data model (a closed
`Ingredient` table, a closed `Unit` enum). Everything here is therefore best-effort: unknown
units fall back to a sane default and bad quantities default to 1 rather than raising, so a
recipe always gets created even if it then needs manual clean-up in the edit view.

Mapping summary:
- metadata `title`, `servings` (`serves`, `yield`), prep/cook times (`prep time`/`cook time`,
  or cooklang.org's `prepMinutes`/`cookMinutes`), `source` URL, `description` -> recipe fields;
  values passed explicitly by the caller always win over the metadata;
- `> notes` (and a `note` metadata entry) are appended to the description;
- `= Section` titles -> `RecipeIngredient.group_name`;
- ingredients are matched against the library like the URL import does
  (`apps.importer.services.find_matching_ingredient`: name, translations, then close match),
  and created when nothing matches;
- the same ingredient quantified twice in the same section with the same unit is summed into
  one line (e.g. sugar 70 g in one step + 30 g in another -> 100 g);
- `#cookware` is matched against the cookware library (name or translation, ignoring case and
  accents) and attached to the recipe; unknown cookware is created on import, and left for the
  user to create (or ignore) in the form on preview.
"""
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from django.db import transaction

from apps.importer.ingredient_parsing import unit_from_word
from apps.importer.services import build_ingredient_catalog, find_matching_ingredient
from apps.ingredients.models import Ingredient, Unit
from apps.ingredients.search import normalize
from apps.ingredients.serializers import IngredientSerializer

from .cooklang import CooklangParseError, ParsedRecipe, parse
from .models import Cookware, Recipe, RecipeIngredient, RecipeStep, SourceType
from .serializers import CookwareSerializer

__all__ = [
    "CooklangParseError",
    "build_cooklang_preview",
    "create_recipe_from_cooklang",
    "map_unit",
    "parse_quantity",
]

# Free-text unit abbreviations (as found in real Cooklang recipes, French and English) mapped to
# the app's closed `Unit` enum. Checked before the shared multilingual unit vocabulary of the URL
# importer (`unit_from_word`). Anything unknown - including no unit at all - falls back to PIECE,
# the least surprising default for a "1 egg" / "2 onions" style ingredient.
UNIT_ALIASES = {
    "c.à.s": Unit.TABLESPOON,
    "c.a.s": Unit.TABLESPOON,
    "càs": Unit.TABLESPOON,
    "cas": Unit.TABLESPOON,
    "tbs": Unit.TABLESPOON,
    "spsk": Unit.TABLESPOON,
    "c.à.c": Unit.TEASPOON,
    "c.a.c": Unit.TEASPOON,
    "càc": Unit.TEASPOON,
    "cac": Unit.TEASPOON,
    "tsk": Unit.TEASPOON,
    "piece": Unit.PIECE,
    "pièce": Unit.PIECE,
    "pièces": Unit.PIECE,
    "pieces": Unit.PIECE,
    "pc": Unit.PIECE,
    "pcs": Unit.PIECE,
    "stk": Unit.PIECE,
}

# Units the enum lacks but that convert exactly into one it has.
SCALED_UNITS = {
    "mg": (Unit.GRAM, Decimal("0.001")),
    "cl": (Unit.MILLILITER, Decimal("10")),
    "dl": (Unit.MILLILITER, Decimal("100")),
}

_MAX_QUANTITY = Decimal("999999.99")  # RecipeIngredient.quantity: max_digits=8, decimal_places=2
_NUMBER_RE = re.compile(r"(?:(\d+)\s+)?(\d+)\s*/\s*(\d+)|(\d+(?:[.,]\d+)?)")
_MINUTES_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(h|hr|hrs|hours?|heures?|timer?|min|mins|minutes?|minutter|m)?(?![a-zà-ÿ])", re.IGNORECASE
)


def map_unit(raw_unit: str | None) -> str:
    """Best-effort mapping from a free-text Cooklang unit to `Unit` (PIECE when unknown)."""
    if not raw_unit:
        return Unit.PIECE
    key = raw_unit.strip().lower()
    if key in UNIT_ALIASES:
        return UNIT_ALIASES[key]
    if key in SCALED_UNITS:
        return SCALED_UNITS[key][0]
    return unit_from_word(key) or unit_from_word(key.rstrip(".")) or Unit.PIECE


def parse_quantity(raw_quantity: str | None) -> Decimal:
    """Best-effort parsing of a free-text Cooklang quantity into a Decimal.

    Handles "2", "2,5", "1/2", "1 1/2", "½" and ranges ("2-3" -> 2, the first number). Falls back
    to 1 when missing or non-numeric (e.g. "quelques") - never raises, so a single odd ingredient
    never blocks the whole import.
    """
    if not raw_quantity:
        return Decimal("1")
    text = unicodedata.normalize("NFKC", raw_quantity).replace("⁄", "/")
    match = _NUMBER_RE.search(text)
    if not match:
        return Decimal("1")
    whole, numerator, denominator, plain = match.groups()
    try:
        if plain:
            value = Decimal(plain.replace(",", "."))
        else:
            fraction = Fraction(int(numerator), int(denominator)) + int(whole or 0)
            value = Decimal(fraction.numerator) / Decimal(fraction.denominator)
    except (InvalidOperation, ZeroDivisionError):
        return Decimal("1")
    if value <= 0:
        return Decimal("1")
    return min(value, _MAX_QUANTITY).quantize(Decimal("0.01"))


def _quantity_and_unit(raw_quantity: str | None, raw_unit: str | None) -> tuple[Decimal, str]:
    quantity = parse_quantity(raw_quantity)
    scaled = SCALED_UNITS.get((raw_unit or "").strip().lower())
    if scaled:
        unit, factor = scaled
        return min(quantity * factor, _MAX_QUANTITY).quantize(Decimal("0.01")), unit
    return quantity, map_unit(raw_unit)


def _first_int(value) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, dict):  # {"min": .., "max": ..} (format exporté par cooklang.org)
        return _first_int(value.get("max", value.get("min")))
    match = re.search(r"\d+", str(value or ""))
    return int(match.group()) if match else None


def _minutes(value) -> int | None:
    """"45", 45, "1h30", "1 hour 15 minutes", {"min": 30, "max": 40} -> minutes (max if range)."""
    if isinstance(value, dict):
        return _minutes(value.get("max", value.get("min")))
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    total, found = Decimal(0), False
    for amount, unit in _MINUTES_RE.findall(str(value)):
        found = True
        number = Decimal(amount.replace(",", "."))
        total += number * 60 if unit and unit.lower()[0] in "ht" else number
    return int(total) if found else None


def _metadata_value(metadata, *keys):
    for key in keys:
        value = metadata.get(key)
        if value not in (None, ""):
            return value
    return None


def _source_url(metadata) -> str | None:
    source = _metadata_value(metadata, "source.url", "source", "source.name", "url")
    if isinstance(source, dict):
        source = source.get("url")
    if isinstance(source, str) and re.match(r"https?://\S+$", source.strip()):
        return source.strip()
    return None


def _clamp(value: int | None, minimum: int, maximum: int = 32767) -> int | None:
    return None if value is None else max(minimum, min(value, maximum))


def recipe_fields_from_metadata(parsed: ParsedRecipe) -> dict:
    """Champs de `Recipe` déductibles des métadonnées Cooklang et des notes `>`."""
    metadata = parsed.metadata
    fields = {}

    title = _metadata_value(metadata, "title")
    if title:
        fields["title"] = str(title).strip()[:200]
    servings = _clamp(_first_int(_metadata_value(metadata, "servings")), 1)
    if servings:
        fields["servings"] = servings
    prep = _clamp(_minutes(_metadata_value(metadata, "time.prep", "prepMinutes", "prep_time")), 0)
    if prep is not None:
        fields["prep_time_minutes"] = prep
    cook = _clamp(_minutes(_metadata_value(metadata, "time.cook", "cookMinutes", "cook_time")), 0)
    if cook is not None:
        fields["cook_time_minutes"] = cook
    source_url = _source_url(metadata)
    if source_url:
        fields["source_url"] = source_url

    description_parts = [
        str(part).strip()
        for part in (_metadata_value(metadata, "description"), _metadata_value(metadata, "note", "notes"))
        if part
    ]
    description_parts += parsed.notes
    if description_parts:
        fields["description"] = "\n\n".join(description_parts)
    return fields


def _resolve_ingredient(name: str, catalog: dict[str, Ingredient], created: dict[str, Ingredient]) -> Ingredient:
    """Même rapprochement que l'import par URL (nom, traductions, puis nom proche) ; à défaut,
    crée l'ingrédient (sans valeurs nutritionnelles : à compléter dans la bibliothèque).

    Les ingrédients créés pendant cet import ne sont retrouvés qu'à l'identique (`created`), jamais
    par proximité : sinon "pasteuriseret æggehvide" serait fondu dans "pasteuriseret æggeblomme"
    créé une étape plus tôt."""
    key = name.strip().lower()
    if key in created:
        return created[key]
    ingredient = find_matching_ingredient(name, catalog)
    if ingredient is None:
        ingredient = Ingredient.objects.filter(name__iexact=name).first() or Ingredient.objects.create(name=name)
        created[key] = ingredient
    return ingredient


def _ingredient_lines(parsed: ParsedRecipe, resolve) -> list[dict]:
    """Lignes d'ingrédients (`ingredient`, `quantity`, `unit`, `group_name`) déduites des mentions.

    `resolve(name)` renvoie `(clé, ingrédient)` : la clé identifie l'ingrédient pour le
    regroupement des lignes, l'ingrédient est ce qui finit dans la ligne (éventuellement `None`
    pour une prévisualisation qui n'a rien rapproché).

    Une mention sans quantité d'un ingrédient déjà déclaré (ex. "@oignon" à l'étape 3 après
    "@oignon{1}" à l'étape 1) ne fait que référencer la ligne existante : pas de doublon. Deux
    mentions quantifiées dans la même section et la même unité s'additionnent."""
    lines: dict[tuple, dict] = {}
    defaulted_lines = set()  # lignes créées par une mention sans quantité (quantité 1 par défaut)
    seen_names = set()
    for parsed_ingredient in parsed.ingredients:
        key = parsed_ingredient.name.strip().lower()
        if key in seen_names and not parsed_ingredient.quantity:
            continue
        seen_names.add(key)
        quantity, unit = _quantity_and_unit(parsed_ingredient.quantity, parsed_ingredient.unit)
        ingredient_key, ingredient = resolve(parsed_ingredient.name)
        group_name = parsed_ingredient.section[:60]

        line_key = (ingredient_key, unit, group_name)
        if parsed_ingredient.quantity and line_key in lines:
            line = lines[line_key]
            if line_key in defaulted_lines:
                line["quantity"] = quantity
                defaulted_lines.discard(line_key)
            else:
                line["quantity"] = min(line["quantity"] + quantity, _MAX_QUANTITY)
            continue
        if not parsed_ingredient.quantity:
            defaulted_lines.add(line_key)
        lines[line_key] = {
            "name": parsed_ingredient.name.strip(),
            "ingredient": ingredient,
            "quantity": quantity,
            "unit": unit,
            "group_name": group_name,
        }
    return list(lines.values())


def _cookware_catalog() -> dict[str, Cookware]:
    """Nom normalisé (casse, accents) -> Cookware, pour le nom et toutes ses traductions."""
    catalog: dict[str, Cookware] = {}
    for cookware in Cookware.objects.all():
        for name in (cookware.name, *cookware.translations.values()):
            if name:
                catalog.setdefault(normalize(name), cookware)
    return catalog


def _cookware_lines(parsed: ParsedRecipe) -> list[tuple[str, Cookware | None]]:
    """(nom tel qu'écrit, matériel de la bibliothèque ou None), sans doublon, dans l'ordre."""
    catalog, seen, lines = _cookware_catalog(), set(), []
    for name in parsed.cookware:
        key = normalize(name)
        if not key or key in seen:
            continue
        seen.add(key)
        lines.append((name.strip()[:100], catalog.get(key)))
    return lines


@transaction.atomic
def create_recipe_from_cooklang(*, author, raw_cooklang, title=None, servings=None, prep_time_minutes=None,
                                 cook_time_minutes=None, diet_type=None, source_url=None, video_url=None,
                                 image_url=None, content_publicly_licensed=False) -> Recipe:
    """Parse `raw_cooklang` and persist the resulting Recipe + children.

    `raw_cooklang` is kept verbatim on the created recipe (so it can be displayed/re-parsed
    later) even though the parsed ingredients/steps are what's actually rendered. Explicit
    arguments override what the Cooklang metadata says; `title` may be omitted only when the
    metadata carries one. Raises `CooklangParseError` on unparseable text or a missing title.

    `video_url`/`source_url`/`image_url` let a YouTube import create the recipe in a single
    call (see `scripts/youtube_recipes/post_cooklang.py`): a `video_url` marks `source_type` as
    `SourceType.YOUTUBE` (purely descriptive/admin - no visibility logic reads `source_type`;
    see `Recipe.is_content_restricted`, which only looks at `source_url`).
    """
    parsed: ParsedRecipe = parse(raw_cooklang)

    explicit = {
        "title": title.strip() if title else None,
        "servings": servings,
        "prep_time_minutes": prep_time_minutes,
        "cook_time_minutes": cook_time_minutes,
        "diet_type": diet_type,
        "source_url": source_url,
        "video_url": video_url,
        "image_url": image_url,
    }
    recipe_kwargs = {
        **recipe_fields_from_metadata(parsed),
        **{key: value for key, value in explicit.items() if value not in (None, "")},
    }
    if not recipe_kwargs.get("title"):
        raise CooklangParseError("A title is required (none given and no `title` in the Cooklang metadata).")

    recipe = Recipe.objects.create(
        author=author,
        source_type=SourceType.YOUTUBE if video_url else SourceType.COOKLANG,
        raw_cooklang=raw_cooklang,
        content_publicly_licensed=content_publicly_licensed,
        **recipe_kwargs,
    )

    catalog, created = build_ingredient_catalog(), {}

    def resolve(name):
        ingredient = _resolve_ingredient(name, catalog, created)
        return ingredient.pk, ingredient

    RecipeIngredient.objects.bulk_create(
        RecipeIngredient(
            recipe=recipe,
            order=order,
            ingredient=line["ingredient"],
            quantity=line["quantity"],
            unit=line["unit"],
            group_name=line["group_name"],
        )
        for order, line in enumerate(_ingredient_lines(parsed, resolve), start=1)
    )

    RecipeStep.objects.bulk_create(
        RecipeStep(recipe=recipe, order=order, instruction=step_text)
        for order, step_text in enumerate(parsed.tagged_steps, start=1)
    )

    recipe.cookware.set(
        cookware or Cookware.objects.filter(name__iexact=name).first() or Cookware.objects.create(name=name)
        for name, cookware in _cookware_lines(parsed)
    )

    return recipe


def build_cooklang_preview(*, raw_cooklang, title=None, servings=None) -> dict:
    """Parse `raw_cooklang` sans rien écrire en base, au même format que la prévisualisation
    d'un import d'URL (`apps.importer.services.build_import_preview`) : le formulaire de recette
    s'ouvre pré-rempli et l'utilisateur corrige avant de créer la recette via `POST /api/recipes/`.

    Les ingrédients sont rapprochés du catalogue comme à l'import (`find_matching_ingredient`),
    mais ceux qui ne correspondent à rien ne sont pas créés : ils arrivent sans `ingredient`, à
    choisir ou créer dans le formulaire. Le titre peut manquer (le formulaire l'exige de toute
    façon). Lève `CooklangParseError` sur un texte illisible."""
    parsed: ParsedRecipe = parse(raw_cooklang)
    fields = recipe_fields_from_metadata(parsed)
    if title and title.strip():
        fields["title"] = title.strip()
    if servings:
        fields["servings"] = servings

    catalog = build_ingredient_catalog()

    def resolve(name):
        ingredient = find_matching_ingredient(name, catalog)
        # Les ingrédients non rapprochés ne se regroupent qu'à nom identique (comme ceux créés
        # pendant un import), jamais par proximité.
        return (ingredient.pk if ingredient else f"name:{name.strip().lower()}"), ingredient

    return {
        "title": fields.get("title", ""),
        "description": fields.get("description", ""),
        "servings": fields.get("servings"),
        "prep_time_minutes": fields.get("prep_time_minutes"),
        "cook_time_minutes": fields.get("cook_time_minutes"),
        "source_url": fields.get("source_url", ""),
        "steps": [
            {"order": order, "instruction": instruction}
            for order, instruction in enumerate(parsed.tagged_steps, start=1)
        ],
        "ingredients": [
            {
                "raw_line": line["name"],
                "name": line["name"],
                "quantity": str(line["quantity"]),
                "unit": line["unit"],
                "group_name": line["group_name"],
                "ingredient": IngredientSerializer(line["ingredient"]).data if line["ingredient"] else None,
            }
            for line in _ingredient_lines(parsed, resolve)
        ],
        "cookware": [
            {"name": name, "cookware": CookwareSerializer(cookware).data if cookware else None}
            for name, cookware in _cookware_lines(parsed)
        ],
    }
