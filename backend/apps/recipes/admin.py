from django.contrib import admin

from .models import Cookware, PersonalTag, Recipe, RecipeComment, RecipeIngredient, RecipeStep, Tag, ThematicPage


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
    filter_horizontal = ["cookware"]
    inlines = [RecipeIngredientInline, RecipeStepInline]


@admin.register(Cookware)
class CookwareAdmin(admin.ModelAdmin):
    list_display = ["name", "emoji", "slug", "translations"]
    search_fields = ["name"]


admin.site.register(Tag)


@admin.register(PersonalTag)
class PersonalTagAdmin(admin.ModelAdmin):
    list_display = ["name", "emoji", "color", "owner", "created_at"]
    search_fields = ["name", "owner__email"]
    raw_id_fields = ["owner"]
    filter_horizontal = ["recipes"]


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
