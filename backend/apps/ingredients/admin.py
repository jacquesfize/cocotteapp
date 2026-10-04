from django.contrib import admin

from .models import Allergen, Ingredient


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "default_unit", "available_months", "is_verified", "created_by"]
    list_filter = ["is_verified", "category", "allergens_reviewed", "allergens", ("created_by", admin.RelatedOnlyFieldListFilter)]
    search_fields = ["name"]
    raw_id_fields = ["created_by"]


@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = ["slug", "name"]
