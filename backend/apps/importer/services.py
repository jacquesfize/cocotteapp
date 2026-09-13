import difflib

from apps.ingredients.models import Ingredient
from apps.ingredients.serializers import IngredientSerializer

from .ingredient_parsing import parse_ingredient_line


def scrape_url(url: str) -> dict:
    from recipe_scrapers import scrape_me

    scraper = scrape_me(url)
    return {
        "title": scraper.title(),
        "servings": _parse_servings(scraper),
        "cook_time_minutes": _safe_int(_safe_call(getattr(scraper, "total_time", None))),
        "ingredients": scraper.ingredients(),
        "instructions": scraper.instructions().split("\n"),
        "image_url": _safe_call(getattr(scraper, "image", None)) or "",
    }


def _safe_call(func):
    if func is None:
        return None
    try:
        return func()
    except Exception:
        return None


def _safe_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _parse_servings(scraper):
    try:
        yields = scraper.yields()
        digits = "".join(filter(str.isdigit, yields))
        return int(digits) if digits else 4
    except Exception:
        return 4


def build_import_preview(url: str) -> dict:
    """Scrape et parse une recette sans rien écrire en base : chaque ligne d'ingrédient est
    rapprochée du catalogue existant (`find_matching_ingredient`) si possible, laissant à
    l'appelant le soin de confirmer/corriger avant l'import final (création réelle via
    `POST /api/recipes/`)."""
    data = scrape_url(url)

    ingredients = []
    for raw_line in data["ingredients"]:
        parsed = parse_ingredient_line(raw_line)
        matched = find_matching_ingredient(parsed.name)
        ingredients.append(
            {
                "raw_line": raw_line,
                "quantity": str(parsed.quantity),
                "unit": parsed.unit,
                "name": parsed.name,
                "ingredient": IngredientSerializer(matched).data if matched else None,
            }
        )

    return {
        "title": data["title"],
        "servings": data["servings"],
        "cook_time_minutes": data["cook_time_minutes"],
        "image_url": data.get("image_url", ""),
        "source_url": url,
        "steps": [
            {"order": order, "instruction": instruction.strip()}
            for order, instruction in enumerate(filter(None, data["instructions"]), start=1)
        ],
        "ingredients": ingredients,
    }


def find_matching_ingredient(name: str) -> Ingredient | None:
    # Table nom-normalisé -> Ingredient couvrant le nom français canonique et toutes ses
    # traductions (`Ingredient.translations`), pour rapprocher un ingrédient importé quelle que
    # soit la langue de la recette source (ex. "garlic" -> Ail via translations={"en": "garlic"}).
    # Purement en lecture : ne crée jamais d'Ingredient (l'utilisateur confirme/corrige avant).
    catalog: dict[str, Ingredient] = {}
    for ingredient in Ingredient.objects.all():
        catalog[ingredient.name.strip().lower()] = ingredient
        for translated_name in ingredient.translations.values():
            if translated_name:
                catalog[translated_name.strip().lower()] = ingredient

    if name in catalog:
        return catalog[name]

    close_matches = difflib.get_close_matches(name, catalog.keys(), n=1, cutoff=0.8)
    if close_matches:
        return catalog[close_matches[0]]

    return None
