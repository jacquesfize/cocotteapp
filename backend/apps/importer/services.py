from decimal import Decimal

from apps.ingredients.models import Ingredient, Unit
from apps.recipes.models import Recipe, RecipeIngredient, RecipeStep, SourceType


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


def create_recipe_from_url(user, url: str) -> Recipe:
    data = scrape_url(url)
    recipe = Recipe.objects.create(
        title=data["title"],
        author=user,
        servings=data["servings"],
        cook_time_minutes=data["cook_time_minutes"],
        source_type=SourceType.URL,
        source_url=url,
        image_url=data.get("image_url", ""),
    )
    for order, instruction in enumerate(filter(None, data["instructions"]), start=1):
        RecipeStep.objects.create(recipe=recipe, order=order, instruction=instruction.strip())

    # Les recettes scrapées ne fournissent que des lignes de texte libre :
    # on crée un ingrédient "brut" par ligne, à affiner manuellement ensuite.
    for raw_line in data["ingredients"]:
        ingredient, _ = Ingredient.objects.get_or_create(name=raw_line.strip().lower())
        RecipeIngredient.objects.create(recipe=recipe, ingredient=ingredient, quantity=Decimal("1"), unit=Unit.PIECE)

    return recipe
