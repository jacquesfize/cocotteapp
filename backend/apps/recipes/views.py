from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Prefetch
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

from apps.accounts.audit import StaffAuditMixin, record_staff_action
from apps.accounts.models import AuditLog
from apps.ingredients.permissions import CanEditLibraryItem
from apps.ingredients.search import FuzzySearchFilter
from apps.ingredients.serializers import MergeIntoSerializer
from apps.nutrition.services import compute_recipe_carbon_footprint, compute_recipe_nutrition

from .cooklang_import import CooklangParseError, build_cooklang_preview, create_recipe_from_cooklang
from .filters import RecipeFilter
from .models import (
    Cookware,
    PersonalTag,
    Recipe,
    RecipeComment,
    IngredientAlternative,
    RecipeIngredient,
    RecipeRating,
    RecipeStep,
    SourceType,
    Tag,
    ThematicPage,
)
from .pagination import RecipePagination
from .permissions import IsAuthorOrReadOnly, IsRecipeAuthorOrStaff
from .personal_tags import similar_tags
from .rating_utils import voter_hash_for_request
from .serializers import (
    AdminThematicPageSerializer,
    CooklangImportSerializer,
    CooklangPreviewSerializer,
    CookwareImageUploadSerializer,
    CookwareSerializer,
    PersonalTagSerializer,
    RecipeCommentSerializer,
    RecipeImageUploadSerializer,
    RecipeMyTagsSerializer,
    RecipeRatingSerializer,
    RecipeSerializer,
    RecipeStepImageUploadSerializer,
    RecipeStepSerializer,
    TagSerializer,
    ThematicPageSerializer,
    my_tags_data,
)
from .services import merge_cookware
from .throttles import CommentCreateAnonThrottle, RatingCreateAnonThrottle
from .transfer import ArchiveError, build_export_archive, import_archive


class RecipeViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "recipe_ingredients__ingredient__allergens",
        "recipe_ingredients__ingredient__created_by",
        "recipe_ingredients__alternatives__ingredient",
        "steps",
        "tags",
        "cookware__created_by",
        "ratings",
    )
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = RecipeFilter
    search_fields = ["title", "description"]
    pagination_class = RecipePagination

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.prefetch_related(
                Prefetch(
                    "personal_tags",
                    queryset=PersonalTag.objects.filter(owner=user),
                    to_attr="my_personal_tags",
                )
            )
        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_permissions(self):
        # Dupliquer une recette ou y poser ses étiquettes ne la modifie pas : ouvert à tout
        # utilisateur connecté, pas seulement à l'auteur.
        if self.action in ("fork", "my_tags"):
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=True, methods=["put"], url_path="my-tags")
    def my_tags(self, request, pk=None):
        """Remplace l'ensemble des étiquettes personnelles de l'appelant sur cette recette ;
        celles des autres utilisateurs ne sont ni visibles ni touchées."""
        recipe = self.get_object()
        serializer = RecipeMyTagsSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        tags = serializer.validated_data["tag_ids"]
        recipe.personal_tags.remove(*request.user.personal_tags.exclude(pk__in=[tag.pk for tag in tags]))
        recipe.personal_tags.add(*tags)
        return Response(my_tags_data(recipe.personal_tags.filter(owner=request.user)))

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
            fork.cookware.set(source.cookware.all())
            for ingredient in source.recipe_ingredients.all():
                line = RecipeIngredient.objects.create(
                    recipe=fork,
                    ingredient=ingredient.ingredient,
                    quantity=ingredient.quantity,
                    unit=ingredient.unit,
                    group_name=ingredient.group_name,
                    order=ingredient.order,
                )
                for alternative in ingredient.alternatives.all():
                    IngredientAlternative.objects.create(
                        recipe_ingredient=line,
                        ingredient=alternative.ingredient,
                        quantity=alternative.quantity,
                        unit=alternative.unit,
                        tag=alternative.tag,
                        note=alternative.note,
                        order=alternative.order,
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
        serializer = RecipeImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for attr, value in serializer.validated_data.items():
            setattr(recipe, attr, value)
        recipe.save()
        return Response(self.get_serializer(recipe).data)

    @action(
        detail=True,
        methods=["patch"],
        url_path=r"steps/(?P<step_id>\d+)/image",
        parser_classes=[MultiPartParser, FormParser],
    )
    def step_image(self, request, pk=None, step_id=None):
        recipe = self.get_object()
        step = get_object_or_404(RecipeStep, pk=step_id, recipe=recipe)
        serializer = RecipeStepImageUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for attr, value in serializer.validated_data.items():
            setattr(step, attr, value)
        step.save()
        return Response(RecipeStepSerializer(step).data)

    @action(
        detail=False,
        methods=["post"],
        url_path="import-cooklang",
        permission_classes=[IsAuthenticated],
    )
    def import_cooklang(self, request):
        serializer = CooklangImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            recipe = create_recipe_from_cooklang(author=request.user, **serializer.validated_data)
        except CooklangParseError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(recipe).data, status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["post"],
        url_path="preview-cooklang",
        permission_classes=[IsAuthenticated],
    )
    def preview_cooklang(self, request):
        """Parse du Cooklang collé sans rien écrire en base : le formulaire de création s'ouvre
        pré-rempli pour corriger le résultat avant `POST /api/recipes/`."""
        serializer = CooklangPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            preview = build_cooklang_preview(**serializer.validated_data)
        except CooklangParseError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(preview, status=status.HTTP_200_OK)

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
        methods=["delete"],
        url_path="delete-all",
        permission_classes=[permissions.IsAdminUser],
    )
    def delete_all(self, request):
        """Staff : supprime toutes les recettes de l'instance, de tous les auteurs. Exige
        `?confirm=true` pour éviter qu'un appel accidentel ne vide la base."""
        if request.query_params.get("confirm", "").lower() not in ("1", "true"):
            return Response(
                {"detail": "Ajoutez ?confirm=true pour confirmer la suppression de toutes les recettes."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            # Une par une : les signaux de suppression (fichiers, cascades) restent déclenchés.
            count = Recipe.objects.count()
            for recipe in Recipe.objects.all().iterator():
                recipe.delete()
            AuditLog.objects.create(
                actor=request.user,
                actor_label=request.user.email,
                action=AuditLog.Action.DELETE,
                target_type=Recipe._meta.label,
                target_label="toutes les recettes",
                details={"count": count},
            )
        return Response({"deleted": count})

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
        record_staff_action(
            request,
            AuditLog.Action.HIDE_COMMENT if comment.is_hidden else AuditLog.Action.UNHIDE_COMMENT,
            comment,
        )
        serializer = RecipeCommentSerializer(comment, context={"request": request, "recipe": comment.recipe})
        return Response(serializer.data)


class RecipeRatingView(APIView):
    """`POST /api/recipes/{recipe_id}/rate/` — creates or updates the caller's own 1-5 star
    rating. No account required and no name collected: an authenticated caller is identified by
    `user`, an anonymous one by a salted hash of their IP (never stored in the clear), so a
    repeat vote updates the same row instead of padding the average. Returns only the resulting
    aggregate — who voted what is never exposed."""

    permission_classes = [AllowAny]

    def get_throttles(self):
        return [RatingCreateAnonThrottle()]

    def post(self, request, recipe_id):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        serializer = RecipeRatingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        value = serializer.validated_data["value"]

        user = request.user if request.user.is_authenticated else None
        lookup = {"recipe": recipe, "user": user}
        if user is None:
            lookup["voter_hash"] = voter_hash_for_request(request)
        RecipeRating.objects.update_or_create(defaults={"value": value}, **lookup)

        average, count = recipe.rating_summary()
        return Response(
            {"average_rating": average, "ratings_count": count, "my_rating": value},
            status=status.HTTP_200_OK,
        )


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class PersonalTagViewSet(viewsets.ModelViewSet):
    """Étiquettes personnelles de l'utilisateur connecté, et uniquement les siennes. Liste courte,
    non paginée ; supprimer une étiquette la retire simplement des recettes concernées."""

    serializer_class = PersonalTagSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return self.request.user.personal_tags.annotate(recipes_count=Count("recipes"))

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=False, methods=["get"])
    def similar(self, request):
        """`?name=` : étiquettes de l'utilisateur proches de ce nom, à montrer avant d'en créer
        une nouvelle (doublon à un accent, un pluriel ou une faute de frappe près). `?exclude=`
        écarte l'étiquette en cours de renommage."""
        tags = self.get_queryset()
        exclude = request.query_params.get("exclude", "")
        if exclude.isdigit():
            tags = tags.exclude(pk=exclude)
        matches = similar_tags(tags, request.query_params.get("name", ""))
        return Response(self.get_serializer(matches, many=True).data)


class CookwareViewSet(StaffAuditMixin, viewsets.ModelViewSet):
    """Bibliothèque de matériel de cuisine. Liste courte (quelques dizaines d'entrées) : pas de
    pagination, le formulaire de recette et les filtres chargent tout d'un coup. Comme pour les
    ingrédients, la création est ouverte aux utilisateurs connectés (ajout à la volée depuis le
    formulaire de recette) ; modification et suppression sont réservées au staff et au créateur
    d'un matériel non vérifié qu'aucune recette d'un autre utilisateur n'utilise
    (`Cookware.can_be_edited_by`) ; photo et fusion restent réservées au staff. Supprimer un
    matériel le retire simplement des recettes qui l'utilisaient."""

    queryset = Cookware.objects.select_related("created_by")
    serializer_class = CookwareSerializer
    filter_backends = [DjangoFilterBackend, FuzzySearchFilter]
    filterset_fields = ["is_verified"]
    pagination_class = None

    def get_permissions(self):
        if self.action in ("image", "merge"):
            return [permissions.IsAdminUser()]
        if self.action in ("update", "partial_update", "destroy"):
            return [CanEditLibraryItem()]
        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and not user.is_staff:
            # Précalcule `Cookware.is_used_by_others` pour `can_edit`, sans requête par ligne.
            used_by_others = Recipe.cookware.through.objects.filter(cookware=OuterRef("pk")).exclude(
                recipe__author=user
            )
            queryset = queryset.annotate(used_by_others=Exists(used_by_others))
        return queryset

    def perform_destroy(self, instance):
        if instance.image:
            instance.image.delete(save=False)
        instance.delete()

    @action(detail=True, methods=["patch", "delete"], parser_classes=[MultiPartParser, FormParser])
    def image(self, request, pk=None):
        """Staff : `PATCH` (fichier `image` + licence et crédit, comme pour une photo de recette)
        remplace la photo du matériel, `DELETE` la retire avec son crédit."""
        cookware = self.get_object()
        credit = {field: "" for field in CookwareImageUploadSerializer.CREDIT_FIELDS}
        uploaded = None
        if request.method == "PATCH":
            serializer = CookwareImageUploadSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            uploaded = serializer.validated_data.pop("image")
            credit.update(serializer.validated_data)
        if cookware.image:
            cookware.image.delete(save=False)
        cookware.image = uploaded
        for field, value in credit.items():
            setattr(cookware, field, value)
        cookware.save()
        return Response(self.get_serializer(cookware).data)

    @action(detail=True, methods=["post"])
    def merge(self, request, pk=None):
        """Staff : fusionne ce matériel (doublon) dans `into`, puis le supprime. Renvoie le
        matériel cible. Voir `merge_cookware`."""
        source = self.get_object()
        serializer = MergeIntoSerializer(data=request.data, context={"source": source})
        serializer.is_valid(raise_exception=True)
        target = merge_cookware(source, serializer.validated_data["into"])
        record_staff_action(request, AuditLog.Action.MERGE, source, details={"into": target.pk})
        return Response(self.get_serializer(target).data)


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
