import django_filters
from django.utils import timezone

from apps.ingredients.models import Ingredient

from .models import Recipe


class RecipeFilter(django_filters.FilterSet):
    max_prep_time = django_filters.NumberFilter(field_name="prep_time_minutes", lookup_expr="lte")
    max_cook_time = django_filters.NumberFilter(field_name="cook_time_minutes", lookup_expr="lte")
    ingredients = django_filters.CharFilter(method="filter_ingredients")
    in_season = django_filters.BooleanFilter(method="filter_in_season")

    class Meta:
        model = Recipe
        fields = ["diet_type", "max_prep_time", "max_cook_time"]

    def filter_ingredients(self, queryset, name, value):
        names = [n.strip() for n in value.split(",") if n.strip()]
        for ingredient_name in names:
            queryset = queryset.filter(recipe_ingredients__ingredient__name__iexact=ingredient_name)
        return queryset.distinct()

    def filter_in_season(self, queryset, name, value):
        if not value:
            return queryset
        month = timezone.now().month
        out_of_season_ids = Ingredient.objects.exclude(available_months=[]).exclude(
            available_months__contains=[month]
        ).values("id")
        return queryset.exclude(recipe_ingredients__ingredient_id__in=out_of_season_ids).distinct()
