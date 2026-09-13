from django.conf import settings
from django.db import models
from django.utils.text import slugify

from apps.accounts.models import DietType
from apps.ingredients.models import Ingredient, Unit


class SourceType(models.TextChoices):
    MANUAL = "manual", "Saisie manuelle"
    URL = "url", "Import depuis une URL"
    COOKLANG = "cooklang", "Import Cooklang"


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
    tags = models.ManyToManyField(Tag, blank=True, related_name="recipes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def total_time_minutes(self):
        return self.prep_time_minutes + self.cook_time_minutes

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
