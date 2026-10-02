from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.planning.models import MealPlanEntry

from .models import ShoppingList
from .serializers import ShoppingListSerializer
from .services import build_shopping_list, export_as_text


class ShoppingListViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet
):
    serializer_class = ShoppingListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ShoppingList.objects.filter(user=self.request.user).prefetch_related("items__ingredient")

    def create(self, request, *args, **kwargs):
        entry_ids = request.data.get("meal_plan_entry_ids", [])
        name = request.data.get("name", "Liste de courses")
        entries = MealPlanEntry.objects.filter(user=request.user, id__in=entry_ids)
        shopping_list = build_shopping_list(request.user, entries, name=name)
        serializer = self.get_serializer(shopping_list)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def mark_owned(self, request, pk=None):
        shopping_list = self.get_object()
        ingredient_ids = request.data.get("ingredient_ids", [])
        # `owned` defaults to True so existing callers that only ever ticked items keep working
        # unchanged; passing `owned: false` is how the UI unticks an item.
        owned = request.data.get("owned", True)
        shopping_list.items.filter(ingredient_id__in=ingredient_ids).update(is_owned=owned)
        shopping_list.refresh_from_db()
        return Response(self.get_serializer(shopping_list).data)

    @action(detail=True, methods=["get"])
    def export(self, request, pk=None):
        shopping_list = self.get_object()
        return Response({"content": export_as_text(shopping_list)})
