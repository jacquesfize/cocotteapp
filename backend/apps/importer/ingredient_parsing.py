"""Parses a free-text ingredient line (as returned by recipe_scrapers) into a quantity,
a Unit, and a clean ingredient name, so imported ingredients can be matched against the
existing catalog instead of stored as one raw ingredient per line."""
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from apps.ingredients.models import Unit

# Mots (français, anglais, allemand, espagnol) pointant vers une unité de Unit. Les mots de
# comptage sans équivalent (gousse/clove/Zehe/diente...) ne figurent pas ici : ils restent en
# Unit.PIECE mais sans être conservés dans le nom (cf. _WORD_UNITS_BARE ci-dessous). Un seul jeu
# de tables combiné : pas de détection de langue, on reconnaît simplement tout mot connu.
_WORD_UNITS = {
    # gramme
    "g": Unit.GRAM,
    "gr": Unit.GRAM,
    "gramme": Unit.GRAM,
    "grammes": Unit.GRAM,
    "gram": Unit.GRAM,
    "grams": Unit.GRAM,
    "gramm": Unit.GRAM,
    "gramo": Unit.GRAM,
    "gramos": Unit.GRAM,
    # kilogramme
    "kg": Unit.KILOGRAM,
    "kilo": Unit.KILOGRAM,
    "kilos": Unit.KILOGRAM,
    "kilogramme": Unit.KILOGRAM,
    "kilogrammes": Unit.KILOGRAM,
    "kilogram": Unit.KILOGRAM,
    "kilograms": Unit.KILOGRAM,
    "kilogramm": Unit.KILOGRAM,
    "kilogramo": Unit.KILOGRAM,
    "kilogramos": Unit.KILOGRAM,
    # millilitre
    "ml": Unit.MILLILITER,
    "millilitre": Unit.MILLILITER,
    "millilitres": Unit.MILLILITER,
    "milliliter": Unit.MILLILITER,
    "milliliters": Unit.MILLILITER,
    "mililitro": Unit.MILLILITER,
    "mililitros": Unit.MILLILITER,
    # litre
    "l": Unit.LITER,
    "litre": Unit.LITER,
    "litres": Unit.LITER,
    "liter": Unit.LITER,
    "liters": Unit.LITER,
    "litro": Unit.LITER,
    "litros": Unit.LITER,
    # cuillère à soupe
    "cuillere a soupe": Unit.TABLESPOON,
    "cuilleres a soupe": Unit.TABLESPOON,
    "c a soupe": Unit.TABLESPOON,
    "cs": Unit.TABLESPOON,
    "tablespoon": Unit.TABLESPOON,
    "tablespoons": Unit.TABLESPOON,
    "tbsp": Unit.TABLESPOON,
    "essloffel": Unit.TABLESPOON,
    "el": Unit.TABLESPOON,
    "cucharada": Unit.TABLESPOON,
    "cucharadas": Unit.TABLESPOON,
    # cuillère à café
    "cuillere a cafe": Unit.TEASPOON,
    "cuilleres a cafe": Unit.TEASPOON,
    "c a cafe": Unit.TEASPOON,
    "cc": Unit.TEASPOON,
    "teaspoon": Unit.TEASPOON,
    "teaspoons": Unit.TEASPOON,
    "tsp": Unit.TEASPOON,
    "teeloffel": Unit.TEASPOON,
    "tl": Unit.TEASPOON,
    "cucharadita": Unit.TEASPOON,
    "cucharaditas": Unit.TEASPOON,
    # pincée
    "pincee": Unit.PINCH,
    "pincees": Unit.PINCH,
    "pinch": Unit.PINCH,
    "pinches": Unit.PINCH,
    "prise": Unit.PINCH,
    "prisen": Unit.PINCH,
    "pizca": Unit.PINCH,
    "pizcas": Unit.PINCH,
}

# Mots de comptage : quantifient l'ingrédient (unité = piece) mais ne font pas partie de son nom.
_WORD_UNITS_BARE = {
    # français
    "gousse",
    "gousses",
    "bouquet",
    "bouquets",
    "tranche",
    "tranches",
    "branche",
    "branches",
    "feuille",
    "feuilles",
    "sachet",
    "sachets",
    "boite",
    "boites",
    "botte",
    "bottes",
    # anglais
    "clove",
    "cloves",
    "bunch",
    "bunches",
    "slice",
    "slices",
    "sprig",
    "sprigs",
    "leaf",
    "leaves",
    "can",
    "cans",
    "packet",
    "packets",
    # allemand
    "zehe",
    "zehen",
    "bund",
    "scheibe",
    "scheiben",
    "blatt",
    "blatter",
    # espagnol
    "diente",
    "dientes",
    "manojo",
    "manojos",
    "rodaja",
    "rodajas",
    "hoja",
    "hojas",
    "lata",
    "latas",
}

_LEADING_NUMBER_RE = re.compile(r"^\s*(\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?)\s+(.*)$")
_LEADING_CONNECTOR_RE = re.compile(r"^(?:de |d'|du |des |of )", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedImportIngredient:
    quantity: Decimal
    unit: str
    name: str


def _strip_accents(text: str) -> str:
    # Couvre les accents français, les trémas/ß allemands et les accents/ñ espagnols, pour que
    # la reconnaissance d'unité fonctionne quelle que soit la langue de la ligne d'origine.
    replacements = {
        "é": "e", "è": "e", "ê": "e", "ë": "e",
        "à": "a", "â": "a", "ä": "a", "á": "a",
        "î": "i", "ï": "i", "í": "i",
        "ô": "o", "ö": "o", "ó": "o",
        "ù": "u", "û": "u", "ü": "u", "ú": "u",
        "ç": "c",
        "ñ": "n",
        "ß": "ss",
    }
    for accented, plain in replacements.items():
        text = text.replace(accented, plain)
    return text


def _parse_number(raw: str) -> Decimal:
    raw = raw.strip()
    if "/" in raw:
        numerator, denominator = raw.split("/", 1)
        try:
            return Decimal(numerator.strip()) / Decimal(denominator.strip())
        except (InvalidOperation, ZeroDivisionError):
            return Decimal("1")
    try:
        return Decimal(raw.replace(",", "."))
    except InvalidOperation:
        return Decimal("1")


def _strip_leading_connector(text: str) -> str:
    return _LEADING_CONNECTOR_RE.sub("", text, count=1).strip()


def unit_from_word(word: str) -> str | None:
    """`Unit` désigné par un mot d'unité isolé (français, anglais, allemand ou espagnol, accents
    ignorés), ex. "grammes" -> "g", "Esslöffel" -> "tbsp", "gousses" -> "piece" ; None si inconnu.
    Réutilisé par l'import Cooklang, dont les unités sont du texte libre."""
    normalized = _strip_accents(word.strip().lower())
    if normalized in _WORD_UNITS:
        return _WORD_UNITS[normalized]
    if normalized in _WORD_UNITS_BARE:
        return Unit.PIECE
    return None


def _match_word_unit(rest: str) -> tuple[str | None, str | None]:
    """Essaie de reconnaître une unité en tête de `rest`. Retourne (unit, remaining_name)
    ou (None, None) si aucune unité n'est reconnue en tête de chaîne."""
    normalized = _strip_accents(rest.lower())

    for word, unit in sorted(_WORD_UNITS.items(), key=lambda item: -len(item[0])):
        if normalized == word or normalized.startswith(word + " "):
            remaining = rest[len(word):].strip()
            return unit, _strip_leading_connector(remaining)

    for word in sorted(_WORD_UNITS_BARE, key=len, reverse=True):
        if normalized == word or normalized.startswith(word + " "):
            remaining = rest[len(word):].strip()
            return Unit.PIECE, _strip_leading_connector(remaining)

    return None, None


def parse_ingredient_line(raw_line: str) -> ParsedImportIngredient:
    """Extrait (quantité, unité, nom) d'une ligne d'ingrédient en texte libre (français, anglais,
    allemand ou espagnol — un seul jeu de règles combiné, sans détection de langue).

    Ex. "200 g de pois chiches" -> (200, "g", "pois chiches")
        "2 gousses d'ail"       -> (2, "piece", "ail")
        "2 cloves garlic"       -> (2, "piece", "garlic")
        "2 Zehen Knoblauch"     -> (2, "piece", "knoblauch")
        "1 oignon moyen"        -> (1, "piece", "oignon moyen")
        "sel"                   -> (1, "piece", "sel")
    """
    line = raw_line.strip()
    match = _LEADING_NUMBER_RE.match(line)
    if not match:
        return ParsedImportIngredient(quantity=Decimal("1"), unit=Unit.PIECE, name=line.lower())

    quantity = _parse_number(match.group(1))
    rest = match.group(2).strip()

    unit, name = _match_word_unit(rest)
    if unit is None:
        unit, name = Unit.PIECE, rest

    return ParsedImportIngredient(quantity=quantity, unit=unit, name=name.lower())
