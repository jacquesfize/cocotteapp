from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.template.loader import render_to_string
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView
from weasyprint import HTML

from apps.nutrition.services import compute_recipe_carbon_footprint, compute_recipe_nutrition

from .cooklang_import import create_recipe_from_cooklang
from .filters import RecipeFilter
from .models import Recipe, RecipeComment, RecipeIngredient, RecipeStep, SourceType, Tag, ThematicPage
from .permissions import IsAuthorOrReadOnly, IsRecipeAuthorOrStaff
from .serializers import (
    AdminThematicPageSerializer,
    CooklangImportSerializer,
    RecipeCommentSerializer,
    RecipeSerializer,
    TagSerializer,
    ThematicPageSerializer,
)
from .throttles import CommentCreateAnonThrottle
from .transfer import ArchiveError, build_export_archive, import_archive


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "recipe_ingredients__ingredient__allergens", "steps", "tags"
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
        if source.is_content_restricted(request.user):
            return Response(
                {"detail": "Cette recette est protégée : seul l'auteur peut la dupliquer."},
                status=status.HTTP_403_FORBIDDEN,
            )
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

    @action(
        detail=False,
        methods=["post"],
        url_path="import-cooklang",
        permission_classes=[IsAuthenticated],
    )
    def import_cooklang(self, request):
        serializer = CooklangImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = create_recipe_from_cooklang(author=request.user, **serializer.validated_data)
        return Response(self.get_serializer(recipe).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="export", permission_classes=[IsAuthenticated])
    def export_library(self, request):
        """Archive ZIP rejouable (`import-archive`) des recettes de l'utilisateur ; avec
        `?scope=all`, réservé au staff, de toutes les recettes de l'instance."""
        recipes = Recipe.objects.all()
        scope = "toutes" if request.query_params.get("scope") == "all" else "mes"
        if scope == "toutes":
            if not request.user.is_staff:
                return Response(
                    {"detail": "Réservé aux administrateurs."}, status=status.HTTP_403_FORBIDDEN
                )
        else:
            recipes = recipes.filter(author=request.user)
        content = build_export_archive(recipes)
        response = HttpResponse(content, content_type="application/zip")
        date_str = timezone.now().strftime("%Y-%m-%d")
        name = "cocotte-base-recettes" if scope == "toutes" else "cocotte-recettes"
        response["Content-Disposition"] = f'attachment; filename="{name}-{date_str}.zip"'
        return response

    @action(
        detail=False,
        methods=["post"],
        url_path="import-archive",
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser],
    )
    def import_library(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            return Response({"detail": "A 'file' upload is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            result = import_archive(uploaded, request.user)
        except ArchiveError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(result, status=status.HTTP_201_CREATED if result["created"] else status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="pdf")
    def download_pdf(self, request, pk=None):
        recipe = self.get_object()
        if recipe.is_content_restricted(request.user):
            return Response(
                {"detail": "Cette recette est protégée : seul l'auteur peut en télécharger le PDF."},
                status=status.HTTP_403_FORBIDDEN,
            )
        image_src = recipe.image.url if recipe.image else (recipe.image_url or None)
        html = render_to_string("pdf/recipe.html", {"recipe": recipe, "image_src": image_src})
        pdf_bytes = HTML(string=html, base_url=request.build_absolute_uri("/")).write_pdf()
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{recipe.slug}.pdf"'
        return response


class RecipeCommentListCreateView(generics.ListCreateAPIView):
    """`GET`/`POST /api/recipes/{recipe_id}/comments/` — anyone can read or post a comment, no
    account required. Hidden comments are excluded from the list unless the requester is the
    recipe's author or staff."""

    serializer_class = RecipeCommentSerializer
    permission_classes = [AllowAny]

    def get_throttles(self):
        if self.request.method == "POST":
            return [CommentCreateAnonThrottle()]
        return []

    def get_recipe(self):
        if not hasattr(self, "_recipe"):
            self._recipe = get_object_or_404(Recipe, pk=self.kwargs["recipe_id"])
        return self._recipe

    def _can_see_hidden(self, recipe):
        user = self.request.user
        return bool(user and user.is_authenticated and (user.is_staff or recipe.author_id == user.id))

    def get_queryset(self):
        recipe = self.get_recipe()
        queryset = recipe.comments.all()
        if not self._can_see_hidden(recipe):
            queryset = queryset.filter(is_hidden=False)
        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["recipe"] = self.get_recipe()
        return context

    def perform_create(self, serializer):
        serializer.save(recipe=self.get_recipe())


class RecipeCommentHideView(APIView):
    """`POST /api/recipes/{recipe_id}/comments/{id}/hide/` — toggles `is_hidden`, restricted to
    the recipe's author or staff, for basic spam/abuse moderation."""

    permission_classes = [IsRecipeAuthorOrStaff]

    def post(self, request, recipe_id, pk):
        comment = get_object_or_404(RecipeComment, pk=pk, recipe_id=recipe_id)
        self.check_object_permissions(request, comment)
        comment.is_hidden = not comment.is_hidden
        comment.save(update_fields=["is_hidden"])
        serializer = RecipeCommentSerializer(comment, context={"request": request, "recipe": comment.recipe})
        return Response(serializer.data)


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
    page d'accueil), en alternative à l'admin Django (`/django-admin/recipes/thematicpage/`)."""

    queryset = ThematicPage.objects.all()
    serializer_class = AdminThematicPageSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = None

    @action(detail=True, methods=["patch", "delete"], parser_classes=[MultiPartParser, FormParser])
    def image(self, request, pk=None):
        page = self.get_object()
        if request.method == "DELETE":
            if page.image:
                page.image.delete(save=False)
            page.image = None
            page.save()
            return Response(self.get_serializer(page).data)
        uploaded = request.FILES.get("image")
        if not uploaded:
            return Response({"detail": "An 'image' file is required."}, status=status.HTTP_400_BAD_REQUEST)
        page.image = uploaded
        page.save()
        return Response(self.get_serializer(page).data)
