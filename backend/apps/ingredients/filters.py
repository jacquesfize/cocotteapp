import django_filters
from django.db.models import Q
from django.utils import timezone

from .models import Ingredient


class IngredientFilter(django_filters.FilterSet):
    in_season = django_filters.BooleanFilter(method="filter_in_season")

    class Meta:
        model = Ingredient
        fields = ["category", "is_verified"]

    def filter_in_season(self, queryset, name, value):
        month = timezone.now().month
        seasonal_now = Q(available_months=[]) | Q(available_months__contains=[month])
        if value:
            return queryset.filter(seasonal_now)
        return queryset.exclude(seasonal_now)
