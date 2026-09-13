from rest_framework.routers import DefaultRouter

from .views import AdminUserViewSet

router = DefaultRouter()
router.register("users", AdminUserViewSet, basename="admin-user")

urlpatterns = router.urls
