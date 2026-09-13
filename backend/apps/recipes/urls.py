from rest_framework.routers import DefaultRouter

from .views import RecipeViewSet, TagViewSet, ThematicPageViewSet

router = DefaultRouter()
router.register("recipes", RecipeViewSet, basename="recipe")
router.register("tags", TagViewSet, basename="tag")
router.register("thematic-pages", ThematicPageViewSet, basename="thematic-page")

urlpatterns = router.urls
