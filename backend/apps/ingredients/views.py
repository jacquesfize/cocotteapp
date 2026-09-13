from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .filters import IngredientFilter
from .models import Ingredient
from .serializers import IngredientSerializer
from .services import lookup_carbon_footprint, lookup_nutrition_suggestion


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = IngredientFilter
    search_fields = ["name"]

    @action(detail=False, methods=["get"], url_path="nutrition-suggestion")
    def nutrition_suggestion(self, request):
        name = request.query_params.get("name")
        if not name:
            return Response({"detail": "name is required"}, status=status.HTTP_400_BAD_REQUEST)

        suggestion = lookup_nutrition_suggestion(name) or {}

        carbon = lookup_carbon_footprint(name)
        if carbon is not None:
            suggestion["carbon_kg_co2e_per_kg"] = carbon

        if not suggestion:
            return Response({"found": False})
        return Response({"found": True, "suggestion": suggestion})
