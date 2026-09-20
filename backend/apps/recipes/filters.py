from decimal import Decimal

import django_filters
from django.db.models import Case, DecimalField, ExpressionWrapper, F, OuterRef, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.ingredients.models import Ingredient
from apps.ingredients.search import fuzzy_exact_ingredients
from apps.nutrition.services import UNIT_TO_GRAMS

from .models import Recipe, RecipeIngredient

# Paliers d'impact carbone par portion (kg CO2e) : faible <= 0,5 < moyen <= 1,5 < élevé.
CARBON_LOW_MAX = Decimal("0.5")
CARBON_MEDIUM_MAX = Decimal("1.5")

_DEC = DecimalField(max_digits=18, decimal_places=6)


def annotate_carbon_per_serving(queryset):
    """Ajoute `carbon_per_serving` (kg CO2e), même formule que compute_recipe_carbon_footprint."""
    grams = Case(
        *[When(unit=unit, then=Value(factor, output_field=_DEC)) for unit, factor in UNIT_TO_GRAMS.items()],
        default=Value(Decimal("1"), output_field=_DEC),
        output_field=_DEC,
    )
    line = ExpressionWrapper(
        F("ingredient__carbon_kg_co2e_per_kg") * F("quantity") * grams / Value(Decimal("1000"), output_field=_DEC),
        output_field=_DEC,
    )
    total = (
        RecipeIngredient.objects.filter(recipe=OuterRef("pk"))
        .order_by()
        .values("recipe")
        .annotate(t=Sum(line))
        .values("t")
    )
    return queryset.annotate(
        carbon_per_serving=ExpressionWrapper(
            Coalesce(Subquery(total, output_field=_DEC), Value(Decimal("0"), output_field=_DEC)) / F("servings"),
            output_field=_DEC,
        )
    )


class RecipeFilter(django_filters.FilterSet):
    max_prep_time = django_filters.NumberFilter(field_name="prep_time_minutes", lookup_expr="lte")
    max_cook_time = django_filters.NumberFilter(field_name="cook_time_minutes", lookup_expr="lte")
    ingredients = django_filters.CharFilter(method="filter_ingredients")
    in_season = django_filters.BooleanFilter(method="filter_in_season")
    max_carbon = django_filters.NumberFilter(method="filter_max_carbon")
    carbon_level = django_filters.ChoiceFilter(
        method="filter_carbon_level",
        choices=[("low", "low"), ("medium", "medium"), ("high", "high")],
    )

    class Meta:
        model = Recipe
        fields = ["diet_type", "max_prep_time", "max_cook_time"]

    def filter_ingredients(self, queryset, name, value):
        names = [n.strip() for n in value.split(",") if n.strip()]
        for ingredient_name in names:
            queryset = queryset.filter(
                recipe_ingredients__ingredient__in=fuzzy_exact_ingredients(ingredient_name)
            )
        return queryset.distinct()

    def filter_max_carbon(self, queryset, name, value):
        return annotate_carbon_per_serving(queryset).filter(carbon_per_serving__lte=value)

    def filter_carbon_level(self, queryset, name, value):
        queryset = annotate_carbon_per_serving(queryset)
        if value == "low":
            return queryset.filter(carbon_per_serving__lte=CARBON_LOW_MAX)
        if value == "medium":
            return queryset.filter(carbon_per_serving__gt=CARBON_LOW_MAX, carbon_per_serving__lte=CARBON_MEDIUM_MAX)
        return queryset.filter(carbon_per_serving__gt=CARBON_MEDIUM_MAX)

    def filter_in_season(self, queryset, name, value):
        if not value:
            return queryset
        month = timezone.now().month
        out_of_season_ids = Ingredient.objects.exclude(available_months=[]).exclude(
            available_months__contains=[month]
        ).values("id")
        return queryset.exclude(recipe_ingredients__ingredient_id__in=out_of_season_ids).distinct()
