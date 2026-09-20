from django.contrib import admin

from .models import Allergen, Ingredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "default_unit", "available_months"]
    list_filter = ["category", "allergens_reviewed", "allergens"]
    search_fields = ["name"]


@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = ["slug", "name"]
