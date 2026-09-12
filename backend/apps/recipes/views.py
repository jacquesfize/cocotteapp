from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from apps.nutrition.services import compute_recipe_nutrition

from .filters import RecipeFilter
from .models import Recipe, Tag
from .serializers import RecipeSerializer, TagSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "recipe_ingredients__ingredient", "steps", "tags"
    )
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ["title", "description"]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(detail=False, methods=["get"])
    def random(self, request):
        recipe = self.filter_queryset(self.get_queryset()).order_by("?").first()
        if recipe is None:
            return Response({"detail": "No recipe matches these criteria."}, status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(recipe).data)

    @action(detail=True, methods=["get"])
    def nutrition(self, request, pk=None):
        recipe = self.get_object()
        totals = compute_recipe_nutrition(recipe)
        servings = recipe.servings or 1
        per_serving = {k: v / servings for k, v in totals.items()}
        return Response(
            {
                "totals": {k: float(v) for k, v in totals.items()},
                "per_serving": {k: float(v) for k, v in per_serving.items()},
            }
        )


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
