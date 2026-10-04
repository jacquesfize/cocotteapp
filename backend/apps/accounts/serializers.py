from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from apps.ingredients.models import Allergen

from .models import AllergySeverity, UserAllergen

# Champs du profil soumis au consentement « données de santé » : ce sont ceux qu'efface
# User.withdraw_health_data_consent().
HEALTH_DATA_FIELDS = ("diet_type", "activity_level", "allergies", "intolerances")

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    # Consentement explicite (RGPD art. 9) au traitement du régime, de l'activité et des allergies.
    health_data_consent = serializers.BooleanField(write_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
            "diet_type",
            "activity_level",
            "health_data_consent",
        ]

    def validate_health_data_consent(self, value):
        if not value:
            raise serializers.ValidationError("Le consentement est requis pour créer un compte.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        validated_data.pop("health_data_consent")
        user = User(
            **validated_data,
            health_data_consent_at=timezone.now(),
            health_data_consent_version=settings.PRIVACY_POLICY_VERSION,
        )
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    # Slugs d'allergènes (cf. GET /api/allergens/). Une allergie est stricte, une
    # intolérance est un simple inconfort : un même allergène ne peut être dans les deux.
    allergies = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=Allergen.objects.all(), required=False
    )
    intolerances = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=Allergen.objects.all(), required=False
    )

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "diet_type",
            "activity_level",
            "allergies",
            "intolerances",
            "is_staff",
            "date_joined",
            "health_data_consent_at",
        ]
        read_only_fields = ["id", "is_staff", "date_joined", "health_data_consent_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["allergies"] = instance.allergen_slugs(AllergySeverity.ALLERGY)
        data["intolerances"] = instance.allergen_slugs(AllergySeverity.INTOLERANCE)
        return data

    def validate(self, attrs):
        # Données pouvant relever de la santé (RGPD art. 9) : sans consentement, on refuse de
        # les enregistrer plutôt que de les effacer au prochain retrait (cf. User.withdraw_health_data_consent).
        if self.instance is not None and not self.instance.health_data_consent_at:
            sent = sorted(field for field in HEALTH_DATA_FIELDS if field in attrs)
            if sent:
                raise serializers.ValidationError(
                    {"health_data_consent": f"Consentement requis pour modifier : {', '.join(sent)}."}
                )
        allergies = {a.slug for a in attrs.get("allergies", [])}
        intolerances = {a.slug for a in attrs.get("intolerances", [])}
        overlap = allergies & intolerances
        if overlap:
            raise serializers.ValidationError(
                {"intolerances": f"Déjà déclaré comme allergie : {', '.join(sorted(overlap))}."}
            )
        return attrs

    @transaction.atomic
    def update(self, instance, validated_data):
        allergies = validated_data.pop("allergies", None)
        intolerances = validated_data.pop("intolerances", None)
        instance = super().update(instance, validated_data)
        # Un PATCH qui ne fournit qu'une des deux listes laisse l'autre intacte.
        for severity, allergens in (
            (AllergySeverity.ALLERGY, allergies),
            (AllergySeverity.INTOLERANCE, intolerances),
        ):
            if allergens is None:
                continue
            instance.allergen_links.filter(severity=severity).exclude(allergen__in=allergens).delete()
            for allergen in allergens:
                UserAllergen.objects.update_or_create(
                    user=instance, allergen=allergen, defaults={"severity": severity}
                )
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Mot de passe actuel incorrect.")
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)


class AdminUserSerializer(serializers.ModelSerializer):
    recipe_count = serializers.SerializerMethodField()

    def get_recipe_count(self, obj):
        return obj.recipes.count()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "is_active",
            "is_staff",
            "date_joined",
            "recipe_count",
        ]
        read_only_fields = ["id", "username", "email", "date_joined", "recipe_count"]
