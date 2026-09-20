from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CalendarFeedICSView, CalendarFeedView, MealPlanEntryViewSet, PlanningShareViewSet

router = DefaultRouter()
router.register("meal-plan-entries", MealPlanEntryViewSet, basename="mealplanentry")
router.register("planning-shares", PlanningShareViewSet, basename="planningshare")

urlpatterns = [
    path("planning/calendar-feed/", CalendarFeedView.as_view(), name="calendar-feed"),
    path("planning/feed/<str:token>.ics", CalendarFeedICSView.as_view(), name="calendar-feed-ics"),
] + router.urls
