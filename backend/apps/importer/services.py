import difflib

from apps.ingredients.models import Ingredient
from apps.ingredients.serializers import IngredientSerializer
from apps.recipes.models import ImageLicense

from .ingredient_parsing import parse_ingredient_line

OPENVERSE_IMAGES_URL = "https://api.openverse.org/v1/images/"

# Licences Openverse retenues pour une suggestion d'image, et leur équivalent `ImageLicense` :
# uniquement des licences qui autorisent la réutilisation (y compris commerciale) avec, au plus,
# une attribution — jamais de NC/ND, pour qu'une image suggérée soit réellement libre d'usage.
OPENVERSE_LICENSES = {
    "by": ImageLicense.CC_BY,
    "by-sa": ImageLicense.CC_BY_SA,
    "cc0": ImageLicense.PUBLIC_DOMAIN,
    "pdm": ImageLicense.PUBLIC_DOMAIN,
}


def scrape_url(url: str) -> dict:
    from recipe_scrapers import scrape_me

    scraper = scrape_me(url)
    return {
        "title": scraper.title(),
        "servings": _parse_servings(scraper),
        "cook_time_minutes": _safe_int(_safe_call(getattr(scraper, "total_time", None))),
        "ingredients": scraper.ingredients(),
        "instructions": scraper.instructions().split("\n"),
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
    `POST /api/recipes/`).

    La photo de la page source n'est volontairement jamais reprise (droit d'auteur du
    photographe) : l'utilisateur ajoute sa propre photo ou choisit une image libre de droits
    (`search_free_images`)."""
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
        "source_url": url,
        "steps": [
            {"order": order, "instruction": instruction.strip()}
            for order, instruction in enumerate(filter(None, data["instructions"]), start=1)
        ],
        "ingredients": ingredients,
    }


def search_free_images(query: str, limit: int = 12) -> list[dict]:
    """Images libres de droits (CC BY, CC BY-SA, CC0, domaine public) correspondant à `query`,
    via l'API publique d'Openverse (sans clé). Chaque résultat porte déjà les champs de crédit
    attendus par `RecipeSerializer` (licence, auteur, page source, URL de licence), pour être
    appliqué tel quel. Lève une exception si Openverse est injoignable : à la vue de la traduire."""
    import requests

    response = requests.get(
        OPENVERSE_IMAGES_URL,
        params={
            "q": query,
            "license": ",".join(OPENVERSE_LICENSES),
            "page_size": limit,
            "mature": "false",
        },
        timeout=8,
        headers={"User-Agent": "Cocotte recipe app"},
    )
    response.raise_for_status()

    suggestions = []
    for item in response.json().get("results", []):
        license_value = OPENVERSE_LICENSES.get(item.get("license"))
        url = item.get("url") or ""
        landing_url = item.get("foreign_landing_url") or ""
        # Les URLField de Recipe sont limités à 200 caractères : une suggestion qui n'y tiendrait
        # pas serait refusée à l'enregistrement, autant ne pas la proposer.
        if not license_value or not url or len(url) > 200 or len(landing_url) > 200:
            continue
        suggestions.append(
            {
                "url": url,
                "thumbnail": item.get("thumbnail") or url,
                "title": item.get("title") or "",
                "image_license": license_value,
                "image_credit_author": (item.get("creator") or "")[:150],
                "image_credit_source_url": landing_url,
                "image_credit_license_url": item.get("license_url") or "",
            }
        )
    return suggestions


def build_ingredient_catalog() -> dict[str, Ingredient]:
    """Table nom-normalisé -> Ingredient couvrant le nom français canonique et toutes ses
    traductions (`Ingredient.translations`). À construire une fois par import quand on rapproche
    plusieurs ingrédients d'affilée (cf. `apps.recipes.cooklang_import`)."""
    catalog: dict[str, Ingredient] = {}
    for ingredient in Ingredient.objects.all():
        catalog[ingredient.name.strip().lower()] = ingredient
        for translated_name in ingredient.translations.values():
            if translated_name:
                catalog[translated_name.strip().lower()] = ingredient
    return catalog


def find_matching_ingredient(name: str, catalog: dict[str, Ingredient] | None = None) -> Ingredient | None:
    # Rapproche un ingrédient importé du catalogue quelle que soit la langue de la recette source
    # (ex. "garlic" -> Ail via translations={"en": "garlic"}), d'abord à l'identique puis par
    # proximité (difflib). Purement en lecture : ne crée jamais d'Ingredient (l'import par URL
    # laisse l'utilisateur confirmer/corriger ; l'import Cooklang crée lui-même les manquants).
    if catalog is None:
        catalog = build_ingredient_catalog()
    name = name.strip().lower()

    if name in catalog:
        return catalog[name]

    close_matches = difflib.get_close_matches(name, catalog.keys(), n=1, cutoff=0.8)
    if close_matches:
        return catalog[close_matches[0]]

    return None
