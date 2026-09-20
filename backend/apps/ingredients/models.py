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


class Allergen(models.Model):
    """Allergène ou intolérance alimentaire de référence (les 14 allergènes UE + lactose)."""

    slug = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=80)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


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
    translations = models.JSONField(
        default=dict,
        blank=True,
        help_text='Noms de l\'ingrédient dans d\'autres langues, ex. {"en": "garlic", '
        '"de": "Knoblauch", "es": "ajo"} — utilisé pour rapprocher les ingrédients importés '
        "depuis une recette non francophone.",
    )

    allergens = models.ManyToManyField(Allergen, blank=True, related_name="ingredients")
    allergens_reviewed = models.BooleanField(
        default=False,
        help_text="Les allergènes ont été vérifiés. Faux = inconnu (ex. ingrédient créé à la "
        "volée ou importé) : l'absence d'allergène renseigné ne garantit rien.",
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

    # Empreinte carbone, en kg CO2e par kg (ou litre) de produit — ordre de grandeur
    # issu de l'ACV (Agribalyse/ADEME, Poore & Nemecek 2018), pas une valeur de labo.
    carbon_kg_co2e_per_kg = models.DecimalField(
        max_digits=7,
        decimal_places=3,
        default=0,
        help_text="Empreinte carbone en kg CO2e par kg de produit (ordre de grandeur ACV).",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            suffix = 1
            while Ingredient.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix += 1
                slug = f"{base_slug}-{suffix}"
            self.slug = slug
        super().save(*args, **kwargs)

    def is_in_season(self, month=None):
        if not self.available_months:
            return True
        month = month or timezone.now().month
        return month in self.available_months
