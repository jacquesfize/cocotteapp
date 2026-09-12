from django.urls import path

from .views import ImportRecipeFromUrlView

urlpatterns = [
    path("import/url/", ImportRecipeFromUrlView.as_view(), name="import-recipe-from-url"),
]
