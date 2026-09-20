from datetime import date as date_cls
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML

from apps.nutrition.services import (
    NUTRIENT_FIELDS,
    compute_recipe_carbon_footprint,
    compute_recipe_nutrition,
    find_deficiencies,
)

from .filters import MealPlanEntryFilter
from .ics import build_ics
from .models import CalendarFeedToken, MealPlanEntry, MealType, PlanningPermission, PlanningShare
from .serializers import (
    MealPlanEntrySerializer,
    PlanningShareReceivedSerializer,
    PlanningShareSerializer,
)

WRITE_ACTIONS = {"create", "update", "partial_update", "destroy"}


class MealPlanEntryViewSet(viewsets.ModelViewSet):
    serializer_class = MealPlanEntrySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = MealPlanEntryFilter

    def _resolve_agenda(self):
        """Resolve which user's agenda applies to this request and the requester's permission.

        Returns the agenda owner (a User) and one of "owner" (full access, it's the
        requester's own agenda), "read" or "write" (access granted via a PlanningShare).
        Raises NotFound if the ?owner= id doesn't exist, PermissionDenied if there's no
        share allowing access. Cached on the instance since a fresh viewset instance is
        created per request but several call sites (get_queryset, perform_create/update/
        destroy, the custom actions) need this within the same request.
        """
        if getattr(self, "_agenda_resolution", None) is not None:
            return self._agenda_resolution

        owner_id = self.request.query_params.get("owner")
        user = self.request.user
        if not owner_id or str(owner_id) == str(user.id):
            self._agenda_resolution = (user, "owner")
            return self._agenda_resolution

        try:
            owner = get_user_model().objects.get(pk=owner_id)
        except (get_user_model().DoesNotExist, ValueError, TypeError):
            raise NotFound("Utilisateur introuvable.")

        share = PlanningShare.objects.filter(owner=owner, shared_with=user).first()
        if share is None:
            raise PermissionDenied("Cet agenda n'est pas partagé avec vous.")
        self._agenda_resolution = (owner, share.permission)
        return self._agenda_resolution

    def get_queryset(self):
        agenda_owner, _permission = self._resolve_agenda()
        return MealPlanEntry.objects.filter(user=agenda_owner).select_related("recipe")

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if self.action in WRITE_ACTIONS:
            _agenda_owner, permission = self._resolve_agenda()
            if permission == PlanningPermission.READ:
                raise PermissionDenied("Vous n'avez qu'un accès en lecture seule à cet agenda.")

    def perform_create(self, serializer):
        agenda_owner, _permission = self._resolve_agenda()
        serializer.save(user=agenda_owner)

    def perform_update(self, serializer):
        agenda_owner, _permission = self._resolve_agenda()
        serializer.save(user=agenda_owner)

    def perform_destroy(self, instance):
        self._resolve_agenda()
        instance.delete()

    @action(detail=False, methods=["get"])
    def nutrition_summary(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        totals = {field: Decimal("0") for field in NUTRIENT_FIELDS}
        carbon_total = Decimal("0")
        for entry in queryset.select_related("recipe"):
            recipe_totals = compute_recipe_nutrition(entry.recipe)
            ratio = Decimal(entry.servings) / Decimal(entry.recipe.servings or 1)
            for field in NUTRIENT_FIELDS:
                totals[field] += recipe_totals[field] * ratio
            carbon_total += compute_recipe_carbon_footprint(entry.recipe) * ratio

        days = self._window_days(request)
        daily_average = {field: totals[field] / days for field in NUTRIENT_FIELDS}
        carbon_daily_average = carbon_total / days

        agenda_owner, _permission = self._resolve_agenda()
        deficiencies = find_deficiencies(daily_average, agenda_owner.diet_type, agenda_owner.activity_level)
        for deficiency in deficiencies:
            deficiency["amount"] = float(deficiency["amount"])
            deficiency["minimum"] = float(deficiency["minimum"])

        return Response(
            {
                "totals": {k: float(v) for k, v in totals.items()},
                "daily_average": {k: float(v) for k, v in daily_average.items()},
                "deficiencies": deficiencies,
                "carbon_footprint_kg_co2e": float(carbon_total),
                "carbon_footprint_daily_average_kg_co2e": float(carbon_daily_average),
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

    @action(detail=False, methods=["get"], url_path="ics")
    def download_ics(self, request):
        entries = self.filter_queryset(self.get_queryset()).order_by("date", "meal_type")
        response = HttpResponse(build_ics(entries), content_type="text/calendar; charset=utf-8")
        start = request.query_params.get("date_after") or "all"
        end = request.query_params.get("date_before") or "all"
        response["Content-Disposition"] = f'attachment; filename="agenda-{start}-{end}.ics"'
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


class PlanningShareViewSet(viewsets.ModelViewSet):
    """Manage shares of the current user's agenda with other users."""

    permission_classes = [IsAuthenticated]
    pagination_class = None
    http_method_names = ["get", "post", "patch", "put", "delete", "head", "options"]

    def get_queryset(self):
        return PlanningShare.objects.filter(owner=self.request.user).select_related("shared_with")

    def get_serializer_class(self):
        if self.action == "shared_with_me":
            return PlanningShareReceivedSerializer
        return PlanningShareSerializer

    @action(detail=False, methods=["get"], url_path="shared-with-me")
    def shared_with_me(self, request):
        shares = PlanningShare.objects.filter(shared_with=request.user).select_related("owner")
        serializer = self.get_serializer(shares, many=True)
        return Response(serializer.data)


def _feed_payload(request, feed):
    http_url = request.build_absolute_uri(f"/api/planning/feed/{feed.token}.ics")
    return {
        "token": feed.token,
        "url": http_url,
        "webcal_url": "webcal://" + http_url.split("://", 1)[1],
    }


class CalendarFeedView(APIView):
    """Get (creating it if needed) or regenerate (POST) the user's secret ICS subscription URL."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        feed, _ = CalendarFeedToken.objects.get_or_create(user=request.user)
        return Response(_feed_payload(request, feed))

    def post(self, request):
        feed, created = CalendarFeedToken.objects.get_or_create(user=request.user)
        if not created:
            feed.regenerate()
        return Response(_feed_payload(request, feed))


class CalendarFeedICSView(APIView):
    """Public (token-authenticated) ICS feed of the whole agenda, for calendar subscriptions."""

    authentication_classes = []
    permission_classes = []

    def get(self, request, token):
        try:
            feed = CalendarFeedToken.objects.select_related("user").get(token=token)
        except CalendarFeedToken.DoesNotExist:
            raise NotFound()
        entries = (
            MealPlanEntry.objects.filter(user=feed.user)
            .select_related("recipe")
            .order_by("date", "meal_type")
        )
        response = HttpResponse(build_ics(entries), content_type="text/calendar; charset=utf-8")
        response["Cache-Control"] = "private, max-age=300"
        return response
