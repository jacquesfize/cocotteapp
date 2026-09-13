import requests
from django.conf import settings

OFF_SEARCH_URL = "https://world.openfoodfacts.org/api/v2/search"

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
