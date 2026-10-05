from django.db.models import BooleanField, Exists, ExpressionWrapper, OuterRef, ProtectedError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .filters import IngredientFilter
from .search import FuzzySearchFilter
from .models import Allergen, Ingredient
from .permissions import CanEditLibraryItem
from .serializers import AllergenSerializer, IngredientSerializer, MergeIntoSerializer
from .services import lookup_carbon_footprint, lookup_nutrition_suggestion, merge_ingredients


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
        # formulaire de recette) ; modification et suppression réservées au staff et au
        # créateur d'un ingrédient non vérifié que personne d'autre n'utilise
        # (`Ingredient.can_be_edited_by`) ; fusion réservée au staff.
        if self.action == "merge":
            return [IsAdminUser()]
        if self.action in ("update", "partial_update", "destroy"):
            return [CanEditLibraryItem()]
        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        queryset = super().get_queryset().select_related("created_by")
        user = self.request.user
        if user.is_authenticated and not user.is_staff:
            # Précalcule `Ingredient.is_used_by_others` pour `can_edit`, sans requête par ligne.
            from apps.recipes.models import IngredientAlternative, RecipeIngredient
            from apps.shopping.models import ShoppingListItem

            used_in_recipes = RecipeIngredient.objects.filter(ingredient=OuterRef("pk")).exclude(
                recipe__author=user
            )
            used_as_alternative = IngredientAlternative.objects.filter(ingredient=OuterRef("pk")).exclude(
                recipe_ingredient__recipe__author=user
            )
            used_in_lists = ShoppingListItem.objects.filter(ingredient=OuterRef("pk")).exclude(
                shopping_list__user=user
            )
            queryset = queryset.annotate(
                used_by_others=ExpressionWrapper(
                    Exists(used_in_recipes) | Exists(used_as_alternative) | Exists(used_in_lists), output_field=BooleanField()
                )
            )
        return queryset

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Cet ingrédient est utilisé par des recettes ou des listes de courses."},
                status=status.HTTP_409_CONFLICT,
            )

    @action(detail=True, methods=["post"])
    def merge(self, request, pk=None):
        """Staff : fusionne cet ingrédient (doublon) dans `into`, puis le supprime. Renvoie
        l'ingrédient cible. Voir `merge_ingredients`."""
        source = self.get_object()
        serializer = MergeIntoSerializer(data=request.data, context={"source": source})
        serializer.is_valid(raise_exception=True)
        target = merge_ingredients(source, serializer.validated_data["into"])
        return Response(self.get_serializer(self.get_queryset().get(pk=target.pk)).data)

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
