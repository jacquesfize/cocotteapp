from django.db import models
from rest_framework import serializers

from apps.accounts.models import DietType
from apps.ingredients.models import Ingredient
from apps.ingredients.serializers import IngredientSerializer
from apps.nutrition.services import compute_recipe_carbon_footprint

from .image_credit import validate_image_credit
from .models import (
    Cookware,
    ImageLicense,
    PersonalTag,
    Recipe,
    RecipeComment,
    RecipeIngredient,
    RecipeRating,
    RecipeStep,
    Tag,
    ThematicPage,
)
from .rating_utils import voter_hash_for_request
from .youtube import extract_youtube_id


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name", "kind"]


class PersonalTagSerializer(serializers.ModelSerializer):
    """Étiquette personnelle de l'utilisateur connecté (`/api/personal-tags/`). `recipes_count`
    vient de l'annotation du viewset, sinon (juste après une création) d'une requête."""

    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = PersonalTag
        fields = ["id", "name", "emoji", "color", "recipes_count"]

    def get_recipes_count(self, obj):
        count = getattr(obj, "recipes_count", None)
        return obj.recipes.count() if count is None else count

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le nom de l'étiquette ne peut pas être vide.")
        owner = self.instance.owner if self.instance is not None else self.context["request"].user
        duplicate = PersonalTag.objects.filter(owner=owner, name__iexact=value)
        if self.instance is not None:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError("Vous avez déjà une étiquette de ce nom.")
        return value

    def validate_emoji(self, value):
        return value.strip()


class RecipeMyTagsSerializer(serializers.Serializer):
    """Input for `PUT /api/recipes/{id}/my-tags/`: the complete set of the caller's own tags to
    put on the recipe. Another user's tag id is rejected as unknown."""

    tag_ids = serializers.PrimaryKeyRelatedField(many=True, queryset=PersonalTag.objects.none())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context["request"].user
        self.fields["tag_ids"].child_relation.queryset = PersonalTag.objects.filter(owner=user)


def my_tags_data(tags):
    return [{"id": tag.id, "name": tag.name, "emoji": tag.emoji, "color": tag.color} for tag in tags]


class RelativeImageField(serializers.ImageField):
    """Renvoie l'URL de l'image relative (`/media/...`) plutôt qu'absolue : l'hôte vu par Django
    derrière un reverse proxy / Docker (ex. `backend:8000`) n'est pas joignable par le navigateur."""

    def to_representation(self, value):
        return value.url if value else None


class CookwareSerializer(serializers.ModelSerializer):
    image = RelativeImageField(read_only=True)

    class Meta:
        model = Cookware
        fields = [
            "id",
            "name",
            "slug",
            "emoji",
            "image",
            "image_license",
            "image_credit_author",
            "image_credit_source_url",
            "image_credit_license_url",
            "translations",
        ]
        # Le crédit ne change qu'avec la photo, via `PATCH /api/cookware/{id}/image/`.
        read_only_fields = [
            "slug",
            "image_license",
            "image_credit_author",
            "image_credit_source_url",
            "image_credit_license_url",
        ]

    def validate_name(self, value):
        value = value.strip()
        duplicate = Cookware.objects.filter(name__iexact=value)
        if self.instance is not None:
            duplicate = duplicate.exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise serializers.ValidationError("Ce matériel existe déjà.")
        return value


class ThematicPageSerializer(serializers.ModelSerializer):
    image = RelativeImageField(read_only=True)

    class Meta:
        model = ThematicPage
        fields = ["id", "title", "slug", "description", "icon", "image", "filters", "order"]


class AdminThematicPageSerializer(serializers.ModelSerializer):
    """Utilisée par l'API d'administration (`/api/admin/thematic-pages/`) : contrairement à
    `ThematicPageSerializer` (lecture seule, publique, réservée aux pages actives), celle-ci
    expose aussi `is_active` et `created_at` et autorise l'écriture pour permettre la gestion
    complète des pages thématiques depuis l'interface staff."""

    image = RelativeImageField(read_only=True)

    class Meta:
        model = ThematicPage
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "icon",
            "image",
            "filters",
            "order",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["slug", "image", "created_at"]


class RecipeIngredientSerializer(serializers.ModelSerializer):
    ingredient = IngredientSerializer(read_only=True)
    ingredient_id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(), source="ingredient", write_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ["id", "ingredient", "ingredient_id", "quantity", "unit", "group_name", "order"]


class RecipeStepSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(required=False)
    image = RelativeImageField(read_only=True)

    class Meta:
        model = RecipeStep
        fields = [
            "id",
            "order",
            "instruction",
            "image",
            "image_url",
            "image_license",
            "image_credit_author",
            "image_credit_source_url",
            "image_credit_license_url",
            "image_credit_note",
        ]

    def validate(self, attrs):
        if attrs.get("image_url"):
            validate_image_credit(attrs)
        return attrs


class RecipeVersionSerializer(serializers.ModelSerializer):
    """Lightweight representation of a sibling version, used in RecipeSerializer.versions."""

    author = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = Recipe
        fields = ["id", "slug", "title", "version_label", "author"]


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(source="recipe_ingredients", many=True, required=False)
    steps = RecipeStepSerializer(many=True, required=False)
    tags = TagSerializer(many=True, read_only=True)
    cookware = CookwareSerializer(many=True, read_only=True)
    cookware_ids = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Cookware.objects.all(), source="cookware", write_only=True, required=False
    )
    author = serializers.ReadOnlyField(source="author.username")
    author_id = serializers.ReadOnlyField(source="author.id")
    youtube_id = serializers.SerializerMethodField()
    versions = serializers.SerializerMethodField()
    allergens = serializers.SerializerMethodField()
    allergens_unverified = serializers.SerializerMethodField()
    content_restricted = serializers.SerializerMethodField()
    carbon_footprint_kg_co2e = serializers.SerializerMethodField()
    carbon_footprint_per_serving_kg_co2e = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    ratings_count = serializers.SerializerMethodField()
    my_rating = serializers.SerializerMethodField()
    my_tags = serializers.SerializerMethodField()

    # Champs retirés de la réponse par `to_representation` quand `content_restricted` est vrai
    # pour le visiteur : le contenu rédactionnel copié de la source (texte des étapes, description),
    # pas les ingrédients ni les temps, qui ne sont pas protégés par le droit d'auteur.
    RESTRICTED_HIDDEN_FIELDS = ("description", "steps")

    class Meta:
        model = Recipe
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "author",
            "author_id",
            "servings",
            "prep_time_minutes",
            "cook_time_minutes",
            "total_time_minutes",
            "diet_type",
            "source_type",
            "source_url",
            "video_url",
            "youtube_id",
            "image",
            "image_url",
            "image_license",
            "image_credit_author",
            "image_credit_source_url",
            "image_credit_license_url",
            "image_credit_note",
            "is_public",
            "content_publicly_licensed",
            "content_restricted",
            "carbon_footprint_kg_co2e",
            "carbon_footprint_per_serving_kg_co2e",
            "average_rating",
            "ratings_count",
            "my_rating",
            "my_tags",
            "tags",
            "cookware",
            "cookware_ids",
            "ingredients",
            "allergens",
            "allergens_unverified",
            "steps",
            "root_recipe",
            "version_label",
            "versions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["slug", "total_time_minutes", "root_recipe"]

    def get_allergens(self, obj):
        return obj.allergen_slugs()

    def get_allergens_unverified(self, obj):
        """Vrai si un ingrédient n'a pas d'allergènes vérifiés : l'absence de badge ne prouve rien."""
        return any(not ri.ingredient.allergens_reviewed for ri in obj.recipe_ingredients.all())

    def get_youtube_id(self, obj):
        return extract_youtube_id(obj.video_url)

    def get_content_restricted(self, obj):
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        return obj.is_content_restricted(user)

    def _carbon_footprint(self, obj):
        # Mis en cache sur l'instance : les deux champs carbone (total et par portion) ne
        # déclenchent qu'un seul calcul (une requête) par recette sérialisée.
        if not hasattr(obj, "_carbon_footprint_cache"):
            obj._carbon_footprint_cache = compute_recipe_carbon_footprint(obj)
        return obj._carbon_footprint_cache

    def get_carbon_footprint_kg_co2e(self, obj):
        return float(self._carbon_footprint(obj))

    def get_carbon_footprint_per_serving_kg_co2e(self, obj):
        """Empreinte par portion (même formule que le filtre `carbon_level`) ; 0 sans portions."""
        if not obj.servings:
            return 0.0
        return float(self._carbon_footprint(obj) / obj.servings)

    def get_average_rating(self, obj):
        average, _count = obj.rating_summary()
        return average

    def get_ratings_count(self, obj):
        _average, count = obj.rating_summary()
        return count

    def get_my_rating(self, obj):
        """The requester's own rating, if any — anonymous voters are matched by the same salted
        IP hash `RecipeRatingView` uses to upsert their vote, never exposed to the client."""
        request = self.context.get("request")
        if request is None:
            return None
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            match = next((r for r in obj.ratings.all() if r.user_id == user.id), None)
        else:
            voter_hash = voter_hash_for_request(request)
            match = next(
                (r for r in obj.ratings.all() if r.user_id is None and r.voter_hash == voter_hash), None
            )
        return match.value if match else None

    def get_my_tags(self, obj):
        """The requester's own personal tags on this recipe (never anyone else's). Prefetched as
        `my_personal_tags` by `RecipeViewSet.get_queryset`; queried otherwise."""
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        if user is None or not user.is_authenticated:
            return []
        tags = getattr(obj, "my_personal_tags", None)
        if tags is None:
            tags = obj.personal_tags.filter(owner=user)
        return my_tags_data(tags)

    def get_versions(self, obj):
        if obj.root_recipe_id is None and not obj.versions.exists():
            return []
        root = obj.root()
        siblings = (
            Recipe.objects.filter(models.Q(pk=root.pk) | models.Q(root_recipe=root))
            .exclude(pk=obj.pk)
            .select_related("author")
        )
        return RecipeVersionSerializer(siblings, many=True).data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data["content_restricted"]:
            for field in self.RESTRICTED_HIDDEN_FIELDS:
                data.pop(field, None)
        return data

    def validate(self, attrs):
        # Grandfathering boundary: credit is only required when `image_url` is actually being
        # set/changed to a new non-blank value, never for an untouched pre-existing image (e.g.
        # editing just the recipe's title must never trigger this check).
        new_image_url = attrs.get("image_url")
        if new_image_url and new_image_url != getattr(self.instance, "image_url", ""):
            validate_image_credit(attrs)
        return attrs

    def create(self, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", [])
        steps_data = validated_data.pop("steps", [])
        cookware = validated_data.pop("cookware", [])
        recipe = Recipe.objects.create(**validated_data)
        recipe.cookware.set(cookware)
        self._sync_children(recipe, ingredients_data, replace=False)
        self._sync_steps(recipe, steps_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop("recipe_ingredients", None)
        steps_data = validated_data.pop("steps", None)
        cookware = validated_data.pop("cookware", None)
        if steps_data is not None:
            provided_ids = {data["id"] for data in steps_data if data.get("id")}
            unknown_ids = provided_ids - set(instance.steps.values_list("id", flat=True))
            if unknown_ids:
                raise serializers.ValidationError(
                    {"steps": f"Étape(s) inconnue(s) pour cette recette : {sorted(unknown_ids)}."}
                )
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if cookware is not None:
            instance.cookware.set(cookware)
        if ingredients_data is not None:
            self._sync_children(instance, ingredients_data, replace=True)
        if steps_data is not None:
            self._sync_steps(instance, steps_data)
        return instance

    @staticmethod
    def _sync_children(recipe, ingredients_data, replace=False):
        if replace:
            recipe.recipe_ingredients.all().delete()
        for data in ingredients_data:
            RecipeIngredient.objects.create(recipe=recipe, **data)

    @staticmethod
    def _sync_steps(recipe, steps_data):
        """Upsert-by-id, never delete-and-recreate: a step referencing an existing `id` is
        updated in place so an uploaded step image (a real file on disk, tied to that PK) isn't
        orphaned by an unrelated recipe edit. A step missing from `steps_data` is deleted, along
        with its image file if any; a step with no `id` is genuinely new."""
        keep_ids = {data["id"] for data in steps_data if data.get("id")}
        stale = recipe.steps.exclude(id__in=keep_ids)
        for step in stale:
            if step.image:
                step.image.delete(save=False)
        stale.delete()
        for data in steps_data:
            step_id = data.pop("id", None)
            if step_id:
                RecipeStep.objects.filter(id=step_id, recipe=recipe).update(**data)
            else:
                RecipeStep.objects.create(recipe=recipe, **data)


class RecipeImageUploadSerializer(serializers.Serializer):
    """Backs `PATCH /api/recipes/{id}/image/`: a file upload always requires credit info (there is
    no grandfathering for a brand-new upload, only for an untouched pre-existing image)."""

    image = serializers.ImageField()
    image_license = serializers.ChoiceField(choices=ImageLicense.choices)
    image_credit_author = serializers.CharField(required=False, allow_blank=True, max_length=150)
    image_credit_source_url = serializers.URLField(required=False, allow_blank=True)
    image_credit_license_url = serializers.URLField(required=False, allow_blank=True)
    image_credit_note = serializers.CharField(required=False, allow_blank=True, max_length=300)

    def validate(self, attrs):
        return validate_image_credit(attrs)

    def validate_image(self, value):
        max_size = 8 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError("L'image ne doit pas dépasser 8 Mo.")
        return value


class CookwareImageUploadSerializer(RecipeImageUploadSerializer):
    """Backs `PATCH /api/cookware/{id}/image/` : même validation de licence et de crédit que pour
    une photo de recette, sans la note libre (inutile pour une photo de matériel)."""

    image_credit_note = None

    CREDIT_FIELDS = (
        "image_license",
        "image_credit_author",
        "image_credit_source_url",
        "image_credit_license_url",
    )


class RecipeStepImageUploadSerializer(RecipeImageUploadSerializer):
    """Identical validation to `RecipeImageUploadSerializer`, semantically for a `RecipeStep`
    (backs `PATCH /api/recipes/{id}/steps/{step_id}/image/`)."""


class RecipeCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(max_length=80, required=False, allow_blank=True)
    body = serializers.CharField(max_length=2000)
    username = serializers.SerializerMethodField()

    class Meta:
        model = RecipeComment
        fields = ["id", "recipe", "author_name", "username", "body", "is_hidden", "created_at"]
        read_only_fields = ["id", "recipe", "username", "is_hidden", "created_at"]

    def get_username(self, obj):
        return obj.user.username if obj.user_id else None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if not self._can_see_hidden(request):
            self.fields.pop("is_hidden", None)

    def _can_see_hidden(self, request):
        if request is None or not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        recipe = self.context.get("recipe")
        return recipe is not None and recipe.author_id == request.user.id

    def validate_body(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Le commentaire ne peut pas être vide.")
        return value

    def validate_author_name(self, value):
        return value.strip()

    def validate(self, attrs):
        request = self.context.get("request")
        author_name = attrs.get("author_name", "")
        user = getattr(request, "user", None) if request else None
        if not author_name:
            if user is not None and user.is_authenticated:
                attrs["author_name"] = user.username
            else:
                raise serializers.ValidationError(
                    {"author_name": "Merci d'indiquer un nom."}
                )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        user = getattr(request, "user", None) if request else None
        if user is not None and user.is_authenticated:
            validated_data["user"] = user
        return super().create(validated_data)


class RecipeRatingSerializer(serializers.ModelSerializer):
    """Input for `POST /api/recipes/{id}/rate/`: just the 1-5 value — no name, no account
    required. The view resolves *who* is voting (user or IP hash) itself."""

    class Meta:
        model = RecipeRating
        fields = ["value"]


class CooklangPreviewSerializer(serializers.Serializer):
    """Input for POST /api/recipes/preview-cooklang/: raw Cooklang text plus the optional title
    and servings that override its metadata."""

    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    raw_cooklang = serializers.CharField()
    servings = serializers.IntegerField(required=False, min_value=1)


class CooklangImportSerializer(serializers.Serializer):
    """Input for POST /api/recipes/import-cooklang/: raw Cooklang text plus optional
    recipe-level fields. Each field given here overrides the Cooklang metadata (front matter);
    `title` may be omitted only if the metadata has one."""

    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    raw_cooklang = serializers.CharField()
    servings = serializers.IntegerField(required=False, min_value=1)
    prep_time_minutes = serializers.IntegerField(required=False, min_value=0)
    cook_time_minutes = serializers.IntegerField(required=False, min_value=0)
    diet_type = serializers.ChoiceField(choices=DietType.choices, required=False)
    source_url = serializers.URLField(required=False, allow_blank=True)
    video_url = serializers.URLField(required=False, allow_blank=True)
    image_url = serializers.URLField(required=False, allow_blank=True)
    content_publicly_licensed = serializers.BooleanField(required=False, default=False)
