from django.contrib import admin

from .models import Recipe, RecipeIngredient, RecipeStep, Tag


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1


class RecipeStepInline(admin.TabularInline):
    model = RecipeStep
    extra = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "diet_type", "total_time_minutes", "is_public"]
    list_filter = ["diet_type", "is_public"]
    search_fields = ["title"]
    inlines = [RecipeIngredientInline, RecipeStepInline]


admin.site.register(Tag)
