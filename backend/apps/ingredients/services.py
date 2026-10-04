import requests
from django.conf import settings
from django.db import transaction

OFF_SEARCH_URL = "https://world.openfoodfacts.org/api/v2/search"
AGRIBALYSE_LINES_URL = "https://data.ademe.fr/data-fair/api/v1/datasets/agribalyse-31-synthese/lines"

# Mapping des nutriments Open Food Facts (par 100g) vers nos champs Ingredient : uniquement les
# macronutriments principaux, dont l'unité (kcal / g) est sans ambiguïté dans les données OFF.
# Les micronutriments (fer, calcium, zinc, B12, oméga-3) ne sont pas mappés : leur unité varie
# trop d'un produit à l'autre dans OFF pour être fiable (risque d'erreur x1000).
_NUTRIMENT_FIELD_MAP = {
    "energy-kcal_100g": "calories_kcal",
    "proteins_100g": "protein_g",
    "carbohydrates_100g": "carbs_g",
    "fat_100g": "fat_g",
    "fiber_100g": "fiber_g",
}


def lookup_nutrition_suggestion(name: str) -> dict | None:
    """Cherche un produit correspondant sur Open Food Facts et renvoie les macronutriments
    fiables trouvés (par 100g). Ne lève jamais d'exception : tout échec (réseau, statut,
    parsing, absence de résultat) renvoie None, à traiter comme "aucune suggestion"."""
    try:
        response = requests.get(
            OFF_SEARCH_URL,
            params={"search_terms": name, "page_size": 1},
            headers={"User-Agent": f"Cocotte/1.0 ({settings.DEFAULT_FROM_EMAIL})"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    products = data.get("products") or []
    if not products:
        return None

    nutriments = products[0].get("nutriments") or {}
    suggestion = {}
    for off_key, field in _NUTRIMENT_FIELD_MAP.items():
        value = _as_float(nutriments.get(off_key))
        if value is not None:
            suggestion[field] = value

    return suggestion or None


def lookup_carbon_footprint(name: str) -> float | None:
    """Cherche l'ingrédient correspondant dans AGRIBALYSE (base ADEME/INRAE d'impacts
    environnementaux par analyse de cycle de vie, indexée par nom de produit en français —
    contrairement à Open Food Facts, mieux adaptée à un ingrédient brut) et renvoie son impact
    "Changement climatique" en kg CO2e/kg, déjà dans l'unité de `carbon_kg_co2e_per_kg`. Ne lève
    jamais d'exception : tout échec renvoie None."""
    try:
        response = requests.get(
            AGRIBALYSE_LINES_URL,
            params={"q": name, "size": 1},
            headers={"User-Agent": f"Cocotte/1.0 ({settings.DEFAULT_FROM_EMAIL})"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    results = data.get("results") or []
    if not results:
        return None

    return _as_float(results[0].get("Changement_climatique"))


def _as_float(value) -> float | None:
    # L'API Open Food Facts renvoie parfois les valeurs numériques sous forme de chaînes
    # ("80.6" au lieu de 80.6) selon les champs : on accepte les deux plutôt que d'écarter
    # silencieusement une donnée valide.
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


@transaction.atomic
def merge_ingredients(source, target):
    """Fusionne le doublon `source` dans `target`, puis supprime `source`.

    - les lignes de recettes pointent désormais vers `target` ;
    - les articles de listes de courses aussi, sauf si `target` figure déjà sur la même liste
      avec la même unité (contrainte d'unicité) : les quantités sont alors additionnées dans
      l'article existant, qui ne reste « déjà en stock » / « coché » que si les deux l'étaient
      (sinon il manquerait de quoi acheter la part de `source`) ;
    - les traductions sont fusionnées (celles de `target` priment) et les allergènes de
      `source` ajoutés à `target`.

    Le texte des étapes (`@nom`) n'est pas réécrit."""
    from apps.recipes.models import RecipeIngredient
    from apps.shopping.models import ShoppingListItem

    RecipeIngredient.objects.filter(ingredient=source).update(ingredient=target)

    for item in ShoppingListItem.objects.select_for_update().filter(ingredient=source):
        existing = (
            ShoppingListItem.objects.select_for_update()
            .filter(shopping_list_id=item.shopping_list_id, ingredient=target, unit=item.unit)
            .first()
        )
        if existing is None:
            item.ingredient = target
            item.save(update_fields=["ingredient"])
            continue
        existing.quantity += item.quantity
        existing.is_owned = existing.is_owned and item.is_owned
        existing.is_checked = existing.is_checked and item.is_checked
        existing.save(update_fields=["quantity", "is_owned", "is_checked"])
        item.delete()

    target.translations = merge_translations(source.translations, target.translations)
    target.save(update_fields=["translations"])
    target.allergens.add(*source.allergens.all())
    source.delete()
    return target


def merge_translations(source, target):
    """Union de deux dictionnaires de traductions ; en cas de conflit, `target` l'emporte."""
    source = source if isinstance(source, dict) else {}
    target = target if isinstance(target, dict) else {}
    return {**source, **target}
