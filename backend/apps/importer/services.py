import difflib

from apps.ingredients.models import Ingredient
from apps.recipes.models import Recipe, RecipeIngredient, RecipeStep, SourceType

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

    # Les recettes scrapées ne fournissent que des lignes de texte libre : on les parse pour en
    # extraire quantité/unité/nom, puis on rapproche le nom du catalogue existant plutôt que de
    # créer un nouvel ingrédient à chaque import (à affiner manuellement ensuite si besoin).
    for raw_line in data["ingredients"]:
        parsed = parse_ingredient_line(raw_line)
        ingredient = _match_or_create_ingredient(parsed.name)
        RecipeIngredient.objects.create(
            recipe=recipe, ingredient=ingredient, quantity=parsed.quantity, unit=parsed.unit
        )

    return recipe


def _match_or_create_ingredient(name: str) -> Ingredient:
    # Table nom-normalisé -> Ingredient couvrant le nom français canonique et toutes ses
    # traductions (`Ingredient.translations`), pour rapprocher un ingrédient importé quelle que
    # soit la langue de la recette source (ex. "garlic" -> Ail via translations={"en": "garlic"}).
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

    return Ingredient.objects.create(name=name)
