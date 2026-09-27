from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.accounts.models import DietType
from apps.ingredients.models import Ingredient, Unit


class SourceType(models.TextChoices):
    MANUAL = "manual", "Saisie manuelle"
    URL = "url", "Import depuis une URL"
    COOKLANG = "cooklang", "Import Cooklang"
    YOUTUBE = "youtube", "Import vidéo YouTube"


class TagKind(models.TextChoices):
    MEAL_TYPE = "meal_type", "Type de repas"
    CUISINE = "cuisine", "Cuisine"
    OTHER = "other", "Autre"


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    kind = models.CharField(max_length=20, choices=TagKind.choices, default=TagKind.OTHER)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recipes")
    servings = models.PositiveSmallIntegerField(default=4)
    prep_time_minutes = models.PositiveSmallIntegerField(default=0)
    cook_time_minutes = models.PositiveSmallIntegerField(default=0)
    diet_type = models.CharField(max_length=20, choices=DietType.choices, default=DietType.OMNIVORE)
    source_type = models.CharField(max_length=20, choices=SourceType.choices, default=SourceType.MANUAL)
    source_url = models.URLField(blank=True)
    video_url = models.URLField(blank=True, help_text="Lien vers une vidéo (YouTube) illustrant la recette.")
    raw_cooklang = models.TextField(blank=True)
    image = models.ImageField(upload_to="recipes/", blank=True, null=True)
    image_url = models.URLField(blank=True, help_text="Image externe, utilisée si aucun fichier n'est téléversé.")
    is_public = models.BooleanField(default=True)
    content_publicly_licensed = models.BooleanField(
        default=False,
        help_text=(
            "Coché par l'auteur d'une recette importée (source_url renseignée) pour libérer "
            "l'accès public à son contenu rédactionnel (description/ingrédients/étapes). Sans "
            "effet sur une recette sans source_url, déjà pleinement publique."
        ),
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="recipes")
    root_recipe = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="versions",
        help_text="None means this recipe IS a root. A forked recipe points at the same root as its source.",
    )
    version_label = models.CharField(
        max_length=80, blank=True, help_text="e.g. 'Sans gluten', 'Version épicée'. Blank for the root recipe."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def total_time_minutes(self):
        return self.prep_time_minutes + self.cook_time_minutes

    def rating_summary(self):
        """(average, count) of this recipe's ratings, rounded to 2 decimals. Préchargez `ratings`
        pour éviter les requêtes N+1 (voir `allergen_slugs`)."""
        values = [r.value for r in self.ratings.all()]
        if not values:
            return None, 0
        return round(sum(values) / len(values), 2), len(values)

    def allergen_slugs(self):
        """Allergènes de la recette, déduits de ses ingrédients (triés).

        Préchargez `recipe_ingredients__ingredient__allergens` pour éviter les requêtes N+1.
        """
        slugs = {a.slug for ri in self.recipe_ingredients.all() for a in ri.ingredient.allergens.all()}
        return sorted(slugs)

    def is_content_restricted(self, user):
        """True si le contenu rédactionnel (description/ingrédients/étapes) de cette recette
        doit être masqué pour `user` : réservé aux recettes importées (source_url non vide)
        non explicitement libérées par leur auteur, sauf pour l'auteur lui-même ou un membre
        du staff. Point de vérité unique, réutilisé par le serializer et la vue `fork`."""
        if not self.source_url or self.content_publicly_licensed:
            return False
        if user is not None and getattr(user, "is_authenticated", False):
            if user.is_staff or self.author_id == user.id:
                return False
        return True

    def root(self):
        return self.root_recipe or self

    def family_versions(self):
        """All versions of this recipe's family, including the root itself."""
        root = self.root()
        return Recipe.objects.filter(models.Q(pk=root.pk) | models.Q(root_recipe=root))

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            suffix = 1
            while Recipe.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix += 1
                slug = f"{base_slug}-{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)


class ThematicPage(models.Model):
    """Une page 'thématique' persistée en base (ex. Produits de saison, Spécial végan) :
    un titre + une description affichés en page d'accueil, qui pointent vers la liste des
    recettes déjà filtrée (les mêmes paramètres que ceux acceptés par /api/recipes/)."""

    title = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=8, blank=True, help_text="Un emoji, ex. 🌱")
    image = models.ImageField(upload_to="thematic_pages/", blank=True, null=True)
    filters = models.JSONField(
        default=dict,
        blank=True,
        help_text="Paramètres de filtrage, ex. {\"in_season\": \"true\"} ou {\"diet_type\": \"vegan\"}.",
    )
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            suffix = 1
            while ThematicPage.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix += 1
                slug = f"{base_slug}-{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="recipe_ingredients")
    ingredient = models.ForeignKey(Ingredient, on_delete=models.PROTECT, related_name="recipe_ingredients")
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=10, choices=Unit.choices)
    group_name = models.CharField(max_length=60, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.quantity}{self.unit} {self.ingredient.name}"


class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveSmallIntegerField(default=0)
    instruction = models.TextField()

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.recipe.title} - étape {self.order}"


class RecipeRating(models.Model):
    """A 1-5 star rating on a recipe. Fully anonymous — no display name, no account required.

    An authenticated poster is deduplicated by `user`; an anonymous one by `voter_hash`, a salted
    hash of their IP address (never the IP itself) computed in `views.py`. Either way a repeat
    vote from the same voter updates their existing row (`views.py`'s upsert) rather than adding
    a second one, so the average always reflects one vote per person, not per visit.
    """

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="recipe_ratings",
    )
    voter_hash = models.CharField(max_length=64, blank=True)
    value = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["recipe", "user"],
                condition=models.Q(user__isnull=False),
                name="unique_recipe_rating_per_user",
            ),
            models.UniqueConstraint(
                fields=["recipe", "voter_hash"],
                condition=models.Q(user__isnull=True),
                name="unique_recipe_rating_per_anon_voter",
            ),
        ]

    def __str__(self):
        return f"{self.value}★ - {self.recipe.title}"


class RecipeComment(models.Model):
    """A comment left on a recipe. No account is required to post: `author_name` is a free-text
    display name, and `user` is only stamped automatically when the poster happens to be
    authenticated (purely informational, never required)."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="comments")
    author_name = models.CharField(max_length=80)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recipe_comments",
    )
    body = models.TextField()
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.author_name} - {self.recipe.title}"
