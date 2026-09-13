from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import build_import_preview


class ImportRecipeFromUrlView(APIView):
    """Scrape et parse une recette pour prévisualisation (aucune écriture en base) : l'appelant
    doit confirmer/corriger les ingrédients puis créer la recette via `POST /api/recipes/`."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        url = request.data.get("url")
        if not url:
            return Response({"detail": "url is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            preview = build_import_preview(url)
        except Exception:
            return Response(
                {"detail": "Impossible de récupérer cette recette."}, status=status.HTTP_400_BAD_REQUEST
            )

        return Response(preview, status=status.HTTP_200_OK)
