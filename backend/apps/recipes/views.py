from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

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


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
