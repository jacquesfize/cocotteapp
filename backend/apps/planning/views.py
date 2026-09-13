from datetime import date as date_cls
from datetime import timedelta
from decimal import Decimal

from django.http import HttpResponse
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from weasyprint import HTML

from apps.nutrition.services import NUTRIENT_FIELDS, compute_recipe_nutrition, find_deficiencies

from .filters import MealPlanEntryFilter
from .models import MealPlanEntry, MealType
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

    @action(detail=False, methods=["get"], url_path="week-pdf")
    def download_week_pdf(self, request):
        entries = list(
            self.filter_queryset(self.get_queryset())
            .select_related("recipe")
            .order_by("date", "meal_type")
        )

        date_after = request.query_params.get("date_after")
        date_before = request.query_params.get("date_before")
        if date_after and date_before:
            start = date_cls.fromisoformat(date_after)
            end = date_cls.fromisoformat(date_before)
        elif entries:
            start = min(e.date for e in entries)
            end = max(e.date for e in entries)
        else:
            start = end = date_cls.today()

        days = []
        current = start
        while current <= end:
            days.append(current)
            current += timedelta(days=1)

        meal_types = [MealType.BREAKFAST, MealType.LUNCH, MealType.DINNER, MealType.SNACK]
        meal_labels = [label for _, label in MealType.choices]

        grid = []
        for day in days:
            cells = [[e for e in entries if e.date == day and e.meal_type == meal] for meal in meal_types]
            grid.append({"date": day, "cells": cells})

        unique_recipes = []
        seen_ids = set()
        for entry in entries:
            if entry.recipe_id not in seen_ids:
                seen_ids.add(entry.recipe_id)
                unique_recipes.append(entry.recipe)

        recipes = [
            {"recipe": recipe, "image_src": recipe.image.url if recipe.image else (recipe.image_url or None)}
            for recipe in unique_recipes
        ]

        html = render_to_string(
            "pdf/week.html",
            {
                "grid": grid,
                "meal_labels": meal_labels,
                "recipes": recipes,
                "start": start,
                "end": end,
            },
        )
        pdf_bytes = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="agenda-{start}-{end}.pdf"'
        return response

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
