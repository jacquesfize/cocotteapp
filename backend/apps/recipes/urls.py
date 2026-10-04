from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CookwareViewSet,
    PersonalTagViewSet,
    RecipeCommentHideView,
    RecipeCommentListCreateView,
    RecipeRatingView,
    RecipeViewSet,
    TagViewSet,
    ThematicPageViewSet,
)

router = DefaultRouter()
router.register("recipes", RecipeViewSet, basename="recipe")
router.register("tags", TagViewSet, basename="tag")
router.register("personal-tags", PersonalTagViewSet, basename="personal-tag")
router.register("cookware", CookwareViewSet, basename="cookware")
router.register("thematic-pages", ThematicPageViewSet, basename="thematic-page")

urlpatterns = [
    path(
        "recipes/<int:recipe_id>/comments/",
        RecipeCommentListCreateView.as_view(),
        name="recipe-comments",
    ),
    path(
        "recipes/<int:recipe_id>/comments/<int:pk>/hide/",
        RecipeCommentHideView.as_view(),
        name="recipe-comment-hide",
    ),
    path(
        "recipes/<int:recipe_id>/rate/",
        RecipeRatingView.as_view(),
        name="recipe-rate",
    ),
] + router.urls
