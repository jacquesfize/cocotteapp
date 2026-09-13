from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import MealPlanEntry, PlanningShare


class MealPlanEntrySerializer(serializers.ModelSerializer):
    recipe_title = serializers.ReadOnlyField(source="recipe.title")

    class Meta:
        model = MealPlanEntry
        fields = ["id", "recipe", "recipe_title", "date", "meal_type", "servings"]


class PlanningShareSerializer(serializers.ModelSerializer):
    """Shares owned by the requesting user (`GET/POST /planning-shares/`)."""

    email = serializers.EmailField(write_only=True)
    shared_with_username = serializers.ReadOnlyField(source="shared_with.username")
    shared_with_email = serializers.ReadOnlyField(source="shared_with.email")

    class Meta:
        model = PlanningShare
        fields = [
            "id",
            "email",
            "shared_with_username",
            "shared_with_email",
            "permission",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_email(self, value):
        request = self.context["request"]
        user = get_user_model().objects.filter(email__iexact=value).first()
        if user is None:
            raise serializers.ValidationError("Aucun compte ne correspond à cet email.")
        if user == request.user:
            raise serializers.ValidationError("Vous ne pouvez pas partager votre agenda avec vous-même.")
        self._shared_with = user
        return value

    def create(self, validated_data):
        validated_data.pop("email", None)
        owner = self.context["request"].user
        shared_with = self._shared_with
        share, _created = PlanningShare.objects.update_or_create(
            owner=owner,
            shared_with=shared_with,
            defaults={"permission": validated_data["permission"]},
        )
        return share


class PlanningShareReceivedSerializer(serializers.ModelSerializer):
    """Shares granted to the requesting user (`GET /planning-shares/shared-with-me/`)."""

    owner_username = serializers.ReadOnlyField(source="owner.username")
    owner_email = serializers.ReadOnlyField(source="owner.email")

    class Meta:
        model = PlanningShare
        fields = ["id", "owner", "owner_username", "owner_email", "permission", "created_at"]
