from django.db.models import ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .filters import IngredientFilter
from .search import FuzzySearchFilter
from .models import Allergen, Ingredient
from .serializers import AllergenSerializer, IngredientSerializer
from .services import lookup_carbon_footprint, lookup_nutrition_suggestion


class AllergenViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Allergen.objects.all()
    serializer_class = AllergenSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.prefetch_related("allergens")
    serializer_class = IngredientSerializer
    filter_backends = [DjangoFilterBackend, FuzzySearchFilter]
    filterset_class = IngredientFilter

    def get_permissions(self):
        # Création ouverte aux utilisateurs connectés (création à la volée depuis le
        # formulaire de recette) ; modification et suppression réservées au staff.
        if self.action in ("update", "partial_update", "destroy"):
            return [IsAdminUser()]
        return [IsAuthenticatedOrReadOnly()]

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cet ingrédient est utilisé par des recettes ou des listes de courses."},
                status=status.HTTP_409_CONFLICT,
            )

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
