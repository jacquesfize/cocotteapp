from rest_framework import serializers

from .models import Announcement


class AnnouncementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Announcement
        fields = [
            "id",
            "level",
            "title_fr",
            "title_en",
            "message_fr",
            "message_en",
            "link_url",
            "link_label_fr",
            "link_label_en",
            "dismissible",
            "updated_at",
        ]
