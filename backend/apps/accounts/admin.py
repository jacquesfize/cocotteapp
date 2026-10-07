from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditLog, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Préférences alimentaires", {"fields": ("diet_type", "activity_level")}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Journal en lecture seule des actions de modération du staff."""

    list_display = ("created_at", "actor_label", "action", "target_type", "target_label")
    list_filter = ("action", "target_type")
    search_fields = ("actor_label", "target_label", "target_id")
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
