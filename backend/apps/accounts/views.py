import json
import zipfile
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import HttpResponse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import filters, generics, permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.planning.models import MealPlanEntry, PlanningShare
from apps.planning.serializers import MealPlanEntrySerializer
from apps.recipes.models import Recipe
from apps.recipes.serializers import RecipeSerializer
from apps.shopping.models import ShoppingList
from apps.shopping.serializers import ShoppingListSerializer

from .serializers import (
    AdminUserSerializer,
    ChangePasswordSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .services import delete_account


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def perform_destroy(self, instance):
        # ?keep_recipes=true : garde les recettes publiques sous un auteur anonyme.
        keep_recipes = self.request.query_params.get("keep_recipes", "").lower() in ("1", "true")
        delete_account(instance, keep_recipes=keep_recipes)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = get_user_model().objects.filter(email__iexact=email).first()
        if user is not None:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}"
            send_mail(
                subject="Réinitialisation de votre mot de passe Cocotte",
                message=(
                    "Vous avez demandé la réinitialisation de votre mot de passe Cocotte.\n\n"
                    f"Cliquez sur ce lien pour choisir un nouveau mot de passe :\n{reset_url}\n\n"
                    "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )
        # Toujours la même réponse, que l'email corresponde à un compte ou non,
        # pour ne pas laisser deviner quels emails sont enregistrés.
        return Response(status=status.HTTP_204_NO_CONTENT)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            user_id = force_str(urlsafe_base64_decode(data["uid"]))
            user = get_user_model().objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, data["token"]):
            return Response(
                {"detail": "Ce lien de réinitialisation est invalide ou a expiré."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(data["new_password"])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HealthDataConsentView(APIView):
    """Donne ou retire le consentement au traitement des données de santé (RGPD art. 9).

    Retirer le consentement efface le régime, le niveau d'activité et les allergies.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        consent = request.data.get("consent")
        if not isinstance(consent, bool):
            return Response({"consent": ["Un booléen est attendu."]}, status=status.HTTP_400_BAD_REQUEST)
        if consent:
            request.user.grant_health_data_consent()
        else:
            request.user.withdraw_health_data_consent()
        return Response(UserSerializer(request.user).data)


class LegalInfoView(APIView):
    """Informations légales et de confidentialité de l'instance, configurées par l'admin."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response(
            {
                "policy_version": settings.PRIVACY_POLICY_VERSION,
                "publisher_name": settings.LEGAL_PUBLISHER_NAME,
                "publisher_address": settings.LEGAL_PUBLISHER_ADDRESS,
                "contact_email": settings.LEGAL_CONTACT_EMAIL,
                "host_name": settings.LEGAL_HOST_NAME,
                "host_address": settings.LEGAL_HOST_ADDRESS,
                "privacy_contact_email": settings.PRIVACY_CONTACT_EMAIL,
                "inactive_retention_days": settings.INACTIVE_ACCOUNT_RETENTION_DAYS,
                "planning_snack_enabled": settings.PLANNING_SNACK_ENABLED,
                "nutrition_alerts_enabled": settings.NUTRITION_ALERTS_ENABLED,
            }
        )


class ExportDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        recipes = Recipe.objects.filter(author=user).select_related("author").prefetch_related(
            "recipe_ingredients__ingredient", "steps", "tags"
        )
        meal_plan_entries = MealPlanEntry.objects.filter(user=user).select_related("recipe")
        shopping_lists = ShoppingList.objects.filter(user=user).prefetch_related("items__ingredient")

        shares_given = PlanningShare.objects.filter(owner=user).select_related("shared_with")
        shares_received = PlanningShare.objects.filter(shared_with=user).select_related("owner")
        comments = user.recipe_comments.select_related("recipe")
        ratings = user.recipe_ratings.select_related("recipe")
        blog_posts = user.blog_posts.all()
        blog_comments = user.blog_comments.select_related("post")

        profile = UserSerializer(user).data
        profile["health_data_consent_version"] = user.health_data_consent_version
        profile["last_login"] = user.last_login

        files = {
            "profil.json": profile,
            "partages_agenda.json": {
                "donnes": [
                    {"avec": s.shared_with.email, "permission": s.permission, "date": s.created_at}
                    for s in shares_given
                ],
                "recus": [
                    {"de": s.owner.email, "permission": s.permission, "date": s.created_at}
                    for s in shares_received
                ],
            },
            "commentaires.json": [
                {"recette": c.recipe.title, "nom_affiche": c.author_name, "texte": c.body, "date": c.created_at}
                for c in comments
            ],
            "articles_blog.json": [
                {"titre": p.title, "contenu_html": p.content, "creation": p.created_at, "modification": p.updated_at}
                for p in blog_posts
            ],
            "commentaires_blog.json": [
                {"article": c.post.title, "nom_affiche": c.author_name, "texte": c.body, "date": c.created_at}
                for c in blog_comments
            ],
            "notes.json": [
                {"recette": r.recipe.title, "note": r.value, "date": r.updated_at} for r in ratings
            ],
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
        keep_recipes = self.request.query_params.get("keep_recipes", "").lower() in ("1", "true")
        delete_account(instance, keep_recipes=keep_recipes)
