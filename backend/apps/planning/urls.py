from rest_framework.routers import DefaultRouter

from .views import MealPlanEntryViewSet

router = DefaultRouter()
router.register("meal-plan-entries", MealPlanEntryViewSet, basename="mealplanentry")

urlpatterns = router.urls
