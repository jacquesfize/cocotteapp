from rest_framework import serializers

from .models import Allergen, Ingredient


class AllergenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Allergen
        fields = ["slug", "name"]


class LibraryItemSerializerMixin(serializers.Serializer):
    """Champs communs aux bibliothèques partagées (ingrédients, matériel) : qui a créé
    l'élément, s'il a été vérifié par un administrateur, et si l'utilisateur courant peut le
    modifier. Le modèle doit déclarer `created_by`, `is_verified` et `can_be_edited_by`."""

    created_by_username = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    def _request_user(self):
        request = self.context.get("request")
        return getattr(request, "user", None)

    def get_fields(self):
        fields = super().get_fields()
        user = self._request_user()
        # Seul le staff vérifie (ou dé-vérifie) un élément : ignoré pour les autres.
        if not (user is not None and user.is_authenticated and user.is_staff):
            fields["is_verified"].read_only = True
        return fields

    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by_id else None

    def get_can_edit(self, obj):
        return obj.can_be_edited_by(self._request_user())

    def create(self, validated_data):
        user = self._request_user()
        validated_data["created_by"] = user
        if not user.is_staff:
            validated_data["is_verified"] = False
        return super().create(validated_data)


class IngredientSerializer(LibraryItemSerializerMixin, serializers.ModelSerializer):
    allergens = serializers.SlugRelatedField(
        many=True, slug_field="slug", queryset=Allergen.objects.all(), required=False
    )

    class Meta:
        model = Ingredient
        fields = "__all__"
        read_only_fields = ["slug", "created_by"]


class MergeIntoSerializer(serializers.Serializer):
    """Corps de `POST /api/{ingredients,cookware}/{id}/merge/` : `{"into": <id cible>}`.
    `context["source"]` est l'élément fusionné (supprimé) ; renvoie la cible validée."""

    into = serializers.IntegerField()

    def validate_into(self, value):
        source = self.context["source"]
        if value == source.pk:
            raise serializers.ValidationError("Impossible de fusionner un élément avec lui-même.")
        target = type(source).objects.filter(pk=value).first()
        if target is None:
            raise serializers.ValidationError("Élément cible introuvable.")
        return target
