from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, TagViewSet

router = DefaultRouter()
router.register("recipes", RecipeViewSet, basename="recipe")
router.register("tags", TagViewSet, basename="tag")

urlpatterns = router.urls
