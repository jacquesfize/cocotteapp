from django.conf import settings
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Announcement
from .serializers import AnnouncementSerializer


class AnnouncementListView(APIView):
    """`GET /api/announcements/` — public. Les annonces actives du Django admin, plus un bandeau
    « instance de test » (id `test-instance`, texte fourni par le frontend) quand `TEST_INSTANCE`
    est activé. Les plus sévères d'abord."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        items = list(AnnouncementSerializer(Announcement.objects.active(), many=True).data)
        if settings.TEST_INSTANCE:
            items.append({"id": "test-instance", "level": "warning", "dismissible": False})
        order = {"critical": 0, "warning": 1, "info": 2}
        items.sort(key=lambda a: order[a["level"]])
        return Response(items)
