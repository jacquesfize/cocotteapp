from rest_framework.routers import DefaultRouter

from .views import MealPlanEntryViewSet, PlanningShareViewSet

router = DefaultRouter()
router.register("meal-plan-entries", MealPlanEntryViewSet, basename="mealplanentry")
router.register("planning-shares", PlanningShareViewSet, basename="planningshare")

urlpatterns = router.urls
