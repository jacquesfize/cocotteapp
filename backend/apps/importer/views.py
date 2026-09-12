from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .tasks import import_recipe_from_url_task


class ImportRecipeFromUrlView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response({"detail": "url is required"}, status=status.HTTP_400_BAD_REQUEST)

        async_result = import_recipe_from_url_task.delay(request.user.id, url)
        return Response({"task_id": async_result.id}, status=status.HTTP_202_ACCEPTED)
