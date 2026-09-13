from decimal import Decimal

# Conversion approximative vers grammes, utilisée uniquement pour l'estimation
# nutritionnelle (les valeurs des ingrédients sont exprimées pour 100g/100ml).
UNIT_TO_GRAMS = {
    "g": Decimal("1"),
    "kg": Decimal("1000"),
    "ml": Decimal("1"),
    "l": Decimal("1000"),
    "piece": Decimal("100"),
    "tbsp": Decimal("15"),
    "tsp": Decimal("5"),
    "pinch": Decimal("1"),
}

NUTRIENT_FIELDS = [
    "calories_kcal",
    "protein_g",
    "carbs_g",
    "fat_g",
    "fiber_g",
    "iron_mg",
    "vitamin_b12_ug",
    "calcium_mg",
    "omega3_g",
    "zinc_mg",
]

CARBON_FIELD = "carbon_kg_co2e_per_kg"


def compute_recipe_nutrition(recipe):
    totals = {field: Decimal("0") for field in NUTRIENT_FIELDS}
    for recipe_ingredient in recipe.recipe_ingredients.select_related("ingredient"):
        grams = recipe_ingredient.quantity * UNIT_TO_GRAMS.get(recipe_ingredient.unit, Decimal("1"))
        factor = grams / Decimal("100")
        for field in NUTRIENT_FIELDS:
            totals[field] += getattr(recipe_ingredient.ingredient, field) * factor
    return totals


def compute_recipe_carbon_footprint(recipe):
    """Empreinte carbone totale de la recette, en kg CO2e (pas par portion)."""
    total = Decimal("0")
    for recipe_ingredient in recipe.recipe_ingredients.select_related("ingredient"):
        grams = recipe_ingredient.quantity * UNIT_TO_GRAMS.get(recipe_ingredient.unit, Decimal("1"))
        total += getattr(recipe_ingredient.ingredient, CARBON_FIELD) * grams / Decimal("1000")
    return total


def find_deficiencies(totals, diet_type, activity_level):
    from .models import NutrientRequirement

    deficiencies = []
    requirements = NutrientRequirement.objects.filter(diet_type=diet_type, activity_level=activity_level)
    for requirement in requirements:
        amount = totals.get(requirement.nutrient)
        if amount is not None and amount < requirement.daily_minimum:
            deficiencies.append(
                {
                    "nutrient": requirement.nutrient,
                    "amount": amount,
                    "minimum": requirement.daily_minimum,
                    "unit": requirement.unit,
                }
            )
    return deficiencies
