from django.contrib import admin

from .models import Recipe, RecipeComment, RecipeIngredient, RecipeStep, Tag, ThematicPage


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


@admin.register(RecipeComment)
class RecipeCommentAdmin(admin.ModelAdmin):
    list_display = ["recipe", "author_name", "user", "created_at", "is_hidden"]
    list_filter = ["is_hidden"]
    search_fields = ["author_name", "body", "recipe__title"]


@admin.register(ThematicPage)
class ThematicPageAdmin(admin.ModelAdmin):
    list_display = ["title", "icon", "order", "is_active"]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"slug": ["title"]}
