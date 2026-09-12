from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class IngredientCategory(models.TextChoices):
    VEGETABLE = "vegetable", "Légume"
    FRUIT = "fruit", "Fruit"
    LEGUME = "legume", "Légumineuse"
    GRAIN = "grain", "Céréale"
    NUT_SEED = "nut_seed", "Noix / graine"
    DAIRY = "dairy", "Produit laitier"
    MEAT_FISH = "meat_fish", "Viande / poisson"
    EGG = "egg", "Œuf"
    FAT = "fat", "Matière grasse"
    CONDIMENT = "condiment", "Condiment / épice"
    OTHER = "other", "Autre"


class Unit(models.TextChoices):
    GRAM = "g", "gramme"
    KILOGRAM = "kg", "kilogramme"
    MILLILITER = "ml", "millilitre"
    LITER = "l", "litre"
    PIECE = "piece", "pièce"
    TABLESPOON = "tbsp", "cuillère à soupe"
    TEASPOON = "tsp", "cuillère à café"
    PINCH = "pinch", "pincée"


class Ingredient(models.Model):
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    category = models.CharField(
        max_length=20, choices=IngredientCategory.choices, default=IngredientCategory.OTHER
    )
    default_unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.GRAM)
    available_months = ArrayField(
        models.PositiveSmallIntegerField(),
        blank=True,
        default=list,
        help_text="Mois (1-12) de pleine saison. Vide = disponible toute l'année.",
    )

    # Valeurs nutritionnelles pour 100g / 100ml de produit.
    calories_kcal = models.DecimalField(max_digits=6, decimal_places=1, default=0)
    protein_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    carbs_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    fat_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    fiber_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    iron_mg = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    vitamin_b12_ug = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    calcium_mg = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    omega3_g = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    zinc_mg = models.DecimalField(max_digits=6, decimal_places=2, default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def is_in_season(self, month=None):
        if not self.available_months:
            return True
        month = month or timezone.now().month
        return month in self.available_months
