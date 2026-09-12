from datetime import date as date_cls
from decimal import Decimal

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.nutrition.services import NUTRIENT_FIELDS, compute_recipe_nutrition, find_deficiencies

from .filters import MealPlanEntryFilter
from .models import MealPlanEntry
from .serializers import MealPlanEntrySerializer


class MealPlanEntryViewSet(viewsets.ModelViewSet):
    serializer_class = MealPlanEntrySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = MealPlanEntryFilter

    def get_queryset(self):
        return MealPlanEntry.objects.filter(user=self.request.user).select_related("recipe")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=["get"])
    def nutrition_summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        totals = {field: Decimal("0") for field in NUTRIENT_FIELDS}
        for entry in queryset.select_related("recipe"):
            recipe_totals = compute_recipe_nutrition(entry.recipe)
            ratio = Decimal(entry.servings) / Decimal(entry.recipe.servings or 1)
            for field in NUTRIENT_FIELDS:
                totals[field] += recipe_totals[field] * ratio

        days = self._window_days(request)
        daily_average = {field: totals[field] / days for field in NUTRIENT_FIELDS}

        deficiencies = find_deficiencies(daily_average, request.user.diet_type, request.user.activity_level)
        for deficiency in deficiencies:
            deficiency["amount"] = float(deficiency["amount"])
            deficiency["minimum"] = float(deficiency["minimum"])

        return Response(
            {
                "totals": {k: float(v) for k, v in totals.items()},
                "daily_average": {k: float(v) for k, v in daily_average.items()},
                "deficiencies": deficiencies,
            }
        )

    @staticmethod
    def _window_days(request):
        date_after = request.query_params.get("date_after")
        date_before = request.query_params.get("date_before")
        if date_after and date_before:
            try:
                delta = (date_cls.fromisoformat(date_before) - date_cls.fromisoformat(date_after)).days + 1
                if delta > 0:
                    return delta
            except ValueError:
                pass
        return 7
