from django.db import transaction
from django.http import HttpResponse
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from weasyprint import HTML

from apps.nutrition.services import compute_recipe_carbon_footprint, compute_recipe_nutrition

from .filters import RecipeFilter
from .models import Recipe, RecipeIngredient, RecipeStep, SourceType, Tag, ThematicPage
from .permissions import IsAuthorOrReadOnly
from .serializers import RecipeSerializer, TagSerializer, ThematicPageSerializer


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

    def get_permissions(self):
        if self.action == "fork":
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=True, methods=["post"])
    def fork(self, request, pk=None):
        source = self.get_object()
        version_label = (request.data.get("version_label") or "").strip()
        if not version_label:
            return Response(
                {"detail": "version_label is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            fork = Recipe.objects.create(
                title=f"{source.title} ({version_label})",
                description=source.description,
                author=request.user,
                servings=source.servings,
                prep_time_minutes=source.prep_time_minutes,
                cook_time_minutes=source.cook_time_minutes,
                diet_type=source.diet_type,
                source_type=SourceType.MANUAL,
                is_public=True,
                root_recipe=source.root_recipe or source,
                version_label=version_label,
            )
            fork.tags.set(source.tags.all())
            for ingredient in source.recipe_ingredients.all():
                RecipeIngredient.objects.create(
                    recipe=fork,
                    ingredient=ingredient.ingredient,
                    quantity=ingredient.quantity,
                    unit=ingredient.unit,
                    group_name=ingredient.group_name,
                    order=ingredient.order,
                )
            for step in source.steps.all():
                RecipeStep.objects.create(recipe=fork, order=step.order, instruction=step.instruction)

        return Response(self.get_serializer(fork).data, status=status.HTTP_201_CREATED)

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
