import django_filters

from .models import MealPlanEntry


class MealPlanEntryFilter(django_filters.FilterSet):
    date_after = django_filters.DateFilter(field_name="date", lookup_expr="gte")
    date_before = django_filters.DateFilter(field_name="date", lookup_expr="lte")

    class Meta:
        model = MealPlanEntry
        fields = ["date_after", "date_before", "meal_type"]
