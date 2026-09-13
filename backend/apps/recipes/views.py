from django.http import HttpResponse
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from weasyprint import HTML

from apps.nutrition.services import compute_recipe_carbon_footprint, compute_recipe_nutrition

from .filters import RecipeFilter
from .models import Recipe, Tag, ThematicPage
from .permissions import IsAuthorOrReadOnly
from .serializers import AdminThematicPageSerializer, RecipeSerializer, TagSerializer, ThematicPageSerializer


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "recipe_ingredients__ingredient", "steps", "tags"
    )
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
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
        carbon_footprint = compute_recipe_carbon_footprint(recipe)
        return Response(
            {
                "totals": {k: float(v) for k, v in totals.items()},
                "per_serving": {k: float(v) for k, v in per_serving.items()},
                "carbon_footprint_kg_co2e": float(carbon_footprint),
                "carbon_footprint_per_serving_kg_co2e": float(carbon_footprint / servings),
            }
        )

    @action(detail=True, methods=["patch"], parser_classes=[MultiPartParser, FormParser])
    def image(self, request, pk=None):
        recipe = self.get_object()
        uploaded = request.FILES.get("image")
        if not uploaded:
            return Response({"detail": "An 'image' file is required."}, status=status.HTTP_400_BAD_REQUEST)
        recipe.image = uploaded
        recipe.save()
        return Response(self.get_serializer(recipe).data)

    @action(detail=True, methods=["get"], url_path="pdf")
    def download_pdf(self, request, pk=None):
        recipe = self.get_object()
        image_src = recipe.image.url if recipe.image else (recipe.image_url or None)
        html = render_to_string("pdf/recipe.html", {"recipe": recipe, "image_src": image_src})
        pdf_bytes = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{recipe.slug}.pdf"'
        return response


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ThematicPageViewSet(viewsets.ReadOnlyModelViewSet):
    """Pages thématiques gérées depuis l'admin Django, affichées en page d'accueil."""

    queryset = ThematicPage.objects.filter(is_active=True)
    serializer_class = ThematicPageSerializer
    pagination_class = None


class AdminThematicPageViewSet(viewsets.ModelViewSet):
    """Réservé aux comptes staff : gestion complète des pages thématiques (raccourcis de la
    page d'accueil), en alternative à l'admin Django (`/admin/recipes/thematicpage/`)."""

    queryset = ThematicPage.objects.all()
    serializer_class = AdminThematicPageSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = None
