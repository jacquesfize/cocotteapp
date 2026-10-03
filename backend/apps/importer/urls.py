from django.urls import path

from .views import FreeImageSuggestionsView, ImportRecipeFromUrlView

urlpatterns = [
    path("import/url/", ImportRecipeFromUrlView.as_view(), name="import-recipe-from-url"),
    path("import/image-suggestions/", FreeImageSuggestionsView.as_view(), name="free-image-suggestions"),
]
