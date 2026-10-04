from django.contrib import admin

from .models import Announcement


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ["__str__", "level", "is_active", "dismissible", "starts_at", "ends_at"]
    list_filter = ["level", "is_active"]
    fieldsets = [
        (None, {"fields": ["level", "is_active", "dismissible"]}),
        ("Français", {"fields": ["title_fr", "message_fr", "link_label_fr"]}),
        ("English", {"fields": ["title_en", "message_en", "link_label_en"]}),
        ("Lien", {"fields": ["link_url"]}),
        ("Période d'affichage", {"fields": ["starts_at", "ends_at"]}),
    ]
