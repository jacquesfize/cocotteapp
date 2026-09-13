from rest_framework.routers import DefaultRouter

from apps.recipes.views import AdminThematicPageViewSet

from .views import AdminUserViewSet

router = DefaultRouter()
router.register("users", AdminUserViewSet, basename="admin-user")
router.register("thematic-pages", AdminThematicPageViewSet, basename="admin-thematic-page")

urlpatterns = router.urls
