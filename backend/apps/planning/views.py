from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import MealPlanEntry
from .serializers import MealPlanEntrySerializer


class MealPlanEntryViewSet(viewsets.ModelViewSet):
    serializer_class = MealPlanEntrySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MealPlanEntry.objects.filter(user=self.request.user).select_related("recipe")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
