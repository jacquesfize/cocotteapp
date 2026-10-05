from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.functions import Lower
from django.utils.text import slugify

from apps.accounts.models import DietType
from apps.ingredients.models import Ingredient, Unit, can_edit_library_item


class SourceType(models.TextChoices):
    MANUAL = "manual", "Saisie manuelle"
    URL = "url", "Import depuis une URL"
    COOKLANG = "cooklang", "Import Cooklang"
    YOUTUBE = "youtube", "Import vidéo YouTube"


class ImageLicense(models.TextChoices):
    CC_BY = "cc_by", "CC BY"
    CC_BY_SA = "cc_by_sa", "CC BY-SA"
    PUBLIC_DOMAIN = "public_domain", "Domaine public / CC0"
    PERSONAL = "personal", "Photo personnelle (droits réservés à l'auteur)"
    PERMISSION = "permission", "Utilisée avec permission"
    UNKNOWN = "unknown", "Non précisée"


class TagKind(models.TextChoices):
    MEAL_TYPE = "meal_type", "Type de repas"
    CUISINE = "cuisine", "Cuisine"
    OTHER = "other", "Autre"


class Tag(models.Model):
    name = models.CharField(max_length=60, unique=True)
    kind = models.CharField(max_length=20, choices=TagKind.choices, default=TagKind.OTHER)

    def __str__(self):
        return self.name


class Cookware(models.Model):
    """Ustensile ou appareil nécessaire à une recette (four, poêle, friteuse à air...).

    Bibliothèque partagée, comme les ingrédients : nommée en français par convention, avec des
    traductions pour la recherche et le rapprochement des imports (`#poêle` en Cooklang)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=110, unique=True, blank=True)
    translations = models.JSONField(
        default=dict,
        blank=True,
        help_text='Noms dans d\'autres langues, ex. {"en": "oven"} — utilisé par la recherche et '
        "pour rapprocher le matériel d'une recette importée.",
    )
    emoji = models.CharField(max_length=8, blank=True, help_text="Un emoji représentant ce matériel, s'il en existe un, ex. 🍳")
    image = models.ImageField(upload_to="cookware/", blank=True, null=True)
    # Crédit de la photo, mêmes règles que pour les recettes (voir image_credit.py) : une photo
    # sous CC BY / CC BY-SA doit nommer son auteur et sa source, affichés avec la photo.
    image_license = models.CharField(max_length=20, choices=ImageLicense.choices, blank=True)
    image_credit_author = models.CharField(max_length=150, blank=True)
    # Les pages Commons aux noms non latins dépassent les 200 caractères une fois encodées.
    image_credit_source_url = models.URLField(max_length=500, blank=True)
    image_credit_license_url = models.URLField(blank=True)
    # Mêmes règles que pour les ingrédients (voir `Ingredient.created_by`).
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_cookware",
    )
    is_verified = models.BooleanField(
        default=True,
        help_text="Validé par un administrateur. Faux = créé par un utilisateur, à relire.",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "cookware"
        verbose_name_plural = "cookware"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            suffix = 1
            while Cookware.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix += 1
                slug = f"{base_slug}-{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)

    def is_used_by_others(self, user):
        """Vrai si une recette d'un autre utilisateur utilise ce matériel (valeur précalculée
        `used_by_others` par `CookwareViewSet.get_queryset` quand elle est présente)."""
        precomputed = getattr(self, "used_by_others", None)
        if precomputed is not None:
            return precomputed
        return self.recipes.exclude(author=user).exists()

    def can_be_edited_by(self, user):
        return can_edit_library_item(self, user)


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
    image_license = models.CharField(max_length=20, choices=ImageLicense.choices, blank=True)
    image_credit_author = models.CharField(max_length=150, blank=True)
    image_credit_source_url = models.URLField(blank=True)
    image_credit_license_url = models.URLField(blank=True)
    image_credit_note = models.CharField(max_length=300, blank=True)
    is_public = models.BooleanField(default=True)
    content_publicly_licensed = models.BooleanField(
        default=False,
        help_text=(
            "Coché par l'auteur d'une recette importée (source_url renseignée), après avoir "
            "réécrit ses étapes et sa description avec ses propres mots, pour les rendre "
            "publiques. Sans effet sur une recette sans source_url, déjà pleinement publique."
        ),
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="recipes")
    cookware = models.ManyToManyField(Cookware, blank=True, related_name="recipes")
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
        """True si le contenu rédactionnel (description/étapes) de cette recette doit être masqué
        pour `user` — la liste d'ingrédients et les temps, simples faits non protégés par le droit
        d'auteur, restent publics : réservé aux recettes importées (source_url non vide)
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


class TagColor(models.TextChoices):
    """Palette fermée plutôt qu'un code hexadécimal libre : le frontend décline chaque couleur en
    thème clair et sombre, avec un contraste lisible garanti."""

    GRAY = "gray", "Gris"
    RED = "red", "Rouge"
    ORANGE = "orange", "Orange"
    YELLOW = "yellow", "Jaune"
    GREEN = "green", "Vert"
    TEAL = "teal", "Turquoise"
    BLUE = "blue", "Bleu"
    PURPLE = "purple", "Violet"
    PINK = "pink", "Rose"


class PersonalTag(models.Model):
    """Étiquette personnelle (ex. « 🎂 Anniversaires », « À tester ») qu'un utilisateur pose sur
    n'importe quelle recette qu'il peut voir, y compris celles des autres. Contrairement à `Tag`
    (bibliothèque partagée), elle n'est visible et modifiable que par son propriétaire."""

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="personal_tags")
    name = models.CharField(max_length=60)
    emoji = models.CharField(max_length=8, blank=True, help_text="Un emoji facultatif, ex. 🎂")
    color = models.CharField(max_length=10, choices=TagColor.choices, default=TagColor.GRAY)
    recipes = models.ManyToManyField(Recipe, blank=True, related_name="personal_tags")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = [Lower("name")]
        constraints = [
            models.UniqueConstraint(Lower("name"), "owner", name="unique_personal_tag_name_per_owner"),
        ]

    def __str__(self):
        return f"{self.emoji} {self.name}".strip()


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


class AlternativeTag(models.TextChoices):
    VEGAN = "vegan", "Végan"
    VEGETARIAN = "vegetarian", "Végétarien"
    GLUTEN_FREE = "gluten_free", "Sans gluten"
    LACTOSE_FREE = "lactose_free", "Sans lactose"
    MISSING = "missing", "Si on n'en a pas"
    LESS = "less", "Quantité réduite"


class IngredientAlternative(models.Model):
    """Une façon de remplacer une ligne de recette (`RecipeIngredient`) : par un autre ingrédient
    (régime, ingrédient manquant) ou, avec le tag `less`, en réduisant la quantité du *même*
    ingrédient (`ingredient` reste alors vide).

    Les alternatives vivent dans leur propre table, pas comme des lignes de recette
    supplémentaires : nutrition, empreinte carbone et listes de courses additionnent toutes les
    `RecipeIngredient` et compteraient sinon deux fois la même ligne."""

    recipe_ingredient = models.ForeignKey(RecipeIngredient, on_delete=models.CASCADE, related_name="alternatives")
    ingredient = models.ForeignKey(
        Ingredient, on_delete=models.PROTECT, null=True, blank=True, related_name="alternative_uses"
    )
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit = models.CharField(max_length=10, choices=Unit.choices)
    tag = models.CharField(max_length=20, choices=AlternativeTag.choices)
    note = models.CharField(max_length=200, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            # Seule la réduction de quantité peut se passer d'ingrédient de remplacement.
            models.CheckConstraint(
                check=models.Q(tag="less", ingredient__isnull=True)
                | (~models.Q(tag="less") & models.Q(ingredient__isnull=False)),
                name="alternative_ingredient_matches_tag",
            )
        ]

    def __str__(self):
        target = self.ingredient.name if self.ingredient_id else self.recipe_ingredient.ingredient.name
        return f"{self.quantity}{self.unit} {target} ({self.tag})"


class RecipeStep(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, related_name="steps")
    order = models.PositiveSmallIntegerField(default=0)
    instruction = models.TextField()
    image = models.ImageField(upload_to="recipe_steps/", blank=True, null=True)
    image_url = models.URLField(blank=True)
    image_license = models.CharField(max_length=20, choices=ImageLicense.choices, blank=True)
    image_credit_author = models.CharField(max_length=150, blank=True)
    image_credit_source_url = models.URLField(blank=True)
    image_credit_license_url = models.URLField(blank=True)
    image_credit_note = models.CharField(max_length=300, blank=True)

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
