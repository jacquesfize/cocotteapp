import json
import zipfile
from io import BytesIO

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import filters, generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.planning.models import MealPlanEntry
from apps.planning.serializers import MealPlanEntrySerializer
from apps.recipes.models import Recipe
from apps.recipes.serializers import RecipeSerializer
from apps.shopping.models import ShoppingList
from apps.shopping.serializers import ShoppingListSerializer

from .serializers import AdminUserSerializer, ChangePasswordSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ExportDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        recipes = Recipe.objects.filter(author=user).select_related("author").prefetch_related(
            "recipe_ingredients__ingredient", "steps", "tags"
        )
        meal_plan_entries = MealPlanEntry.objects.filter(user=user).select_related("recipe")
        shopping_lists = ShoppingList.objects.filter(user=user).prefetch_related("items__ingredient")

        files = {
            "profil.json": UserSerializer(user).data,
            "recettes.json": RecipeSerializer(recipes, many=True, context={"request": request}).data,
            "agenda.json": MealPlanEntrySerializer(meal_plan_entries, many=True).data,
            "listes_de_courses.json": ShoppingListSerializer(shopping_lists, many=True).data,
        }

        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for filename, data in files.items():
                archive.writestr(filename, json.dumps(data, indent=2, ensure_ascii=False, default=str))
        buffer.seek(0)

        response = HttpResponse(buffer.read(), content_type="application/zip")
        date_str = timezone.now().strftime("%Y-%m-%d")
        response["Content-Disposition"] = f'attachment; filename="cocotte-donnees-{date_str}.zip"'
        return response


class AdminUserViewSet(ModelViewSet):
    """Réservé aux comptes staff : gestion des comptes utilisateurs."""

    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]
    http_method_names = ["get", "patch", "delete", "head", "options"]
    filter_backends = [filters.SearchFilter]
    search_fields = ["username", "email"]

    def get_queryset(self):
        return get_user_model().objects.all().order_by("-date_joined")

    def _guard_against_self(self, instance):
        if instance == self.request.user:
            raise PermissionDenied(
                "Utilisez la page « Mon compte » pour modifier ou supprimer votre propre compte."
            )

    def perform_update(self, serializer):
        self._guard_against_self(serializer.instance)
        serializer.save()

    def perform_destroy(self, instance):
        self._guard_against_self(instance)
        instance.delete()
